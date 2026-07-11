"""Staged local AI service supervision and recovery for WP-4028.

This module is intentionally uninstalled. It models truthful health,
dependency, diagnostics, and approval-bound recovery plans for local resident
AI services without creating a second active registry, scheduler, event loop,
or approval path. WP-4031 is expected to adapt these contracts into the
existing Estate AI Services, background operations, audit, approval, resident
gateway, CLI, and Office action systems.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Iterable

RUNNING_STATES = {"running", "ready", "degraded", "cold_loading"}
READY_STATES = {"ready", "degraded"}
DOWN_STATES = {"stopped", "missing", "failed", "timeout", "unknown"}
ACTIONS = {"start", "stop", "restart", "status"}


@dataclass(frozen=True)
class ServiceSpec:
    service_id: str
    display_name: str
    command: tuple[str, ...]
    port: int | None = None
    dependencies: tuple[str, ...] = ()
    startup_timeout_seconds: float = 30.0
    cold_load_seconds: float = 0.0
    max_recovery_attempts: int = 2
    resident_impact: str = "resident AI capability may be unavailable"
    recovery_hints: tuple[str, ...] = ()
    office_payload_kind: str = "ai_service_control"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RuntimeFact:
    service_id: str
    state: str
    pid: int | None = None
    port_owner_pid: int | None = None
    port_owner_name: str | None = None
    process_started_at: str | None = None
    last_heartbeat_at: str | None = None
    log_path: str | None = None
    stderr_tail: str = ""
    checked_at: str | None = None
    detail: str = ""


@dataclass(frozen=True)
class RecoveryPolicy:
    attempts_by_service: dict[str, int] = field(default_factory=dict)
    require_approval: bool = True
    bounded_window_seconds: int = 900


class LocalAIServiceSupervisor:
    """Deterministic staged supervisor planning surface.

    The supervisor consumes externally supplied runtime facts from authorized
    service-control integrations. It does not probe sockets, start processes,
    or schedule background work itself, making deterministic fake-runner tests
    safe and repeatable.
    """

    def __init__(self, services: Iterable[ServiceSpec], *, now: str | None = None) -> None:
        self.services = {service.service_id: service for service in services}
        self.now = now
        self.audit_events: list[dict[str, Any]] = []

    def inspect(self, facts: Iterable[RuntimeFact]) -> dict[str, dict[str, Any]]:
        supplied = {fact.service_id: fact for fact in facts}
        states: dict[str, dict[str, Any]] = {}
        for service_id, spec in sorted(self.services.items()):
            fact = supplied.get(service_id)
            state = fact.state if fact else "unknown"
            diagnostics = self._diagnostics(spec, fact)
            dependency_states = {dep: supplied.get(dep).state if supplied.get(dep) else "unknown" for dep in spec.dependencies}
            dependency_ready = all(dependency_states.get(dep) in READY_STATES for dep in spec.dependencies)
            resident_available = state in READY_STATES and dependency_ready and not diagnostics["occupied_port"] and not diagnostics["stale_process"]
            states[service_id] = {
                "service_id": service_id,
                "display_name": spec.display_name,
                "state": state,
                "resident_available": resident_available,
                "dependencies": list(spec.dependencies),
                "dependency_states": dependency_states,
                "dependency_ready": dependency_ready,
                "startup_timeout_seconds": spec.startup_timeout_seconds,
                "cold_load_seconds": spec.cold_load_seconds,
                "diagnostics": diagnostics,
                "logs": {"path": fact.log_path if fact else None, "stderr_tail": fact.stderr_tail if fact else ""},
                "resident_impact": "available" if resident_available else spec.resident_impact,
                "recovery_hints": list(spec.recovery_hints or self._default_hints(spec, diagnostics, state)),
                "checked_at": (fact.checked_at if fact else None) or self._timestamp(),
            }
        return states

    def plan(self, action: str, service_id: str, facts: Iterable[RuntimeFact], policy: RecoveryPolicy | None = None) -> dict[str, Any]:
        if action not in ACTIONS:
            raise ValueError(f"unsupported action: {action}")
        if service_id not in self.services:
            raise KeyError(service_id)
        policy = policy or RecoveryPolicy()
        inspection = self.inspect(facts)
        ordered = self._ordered_services_for(action, service_id)
        steps = []
        blocked_reasons = []
        for sid in ordered:
            row = inspection[sid]
            attempts = policy.attempts_by_service.get(sid, 0)
            diagnostics = row["diagnostics"]
            blocked = []
            if action in {"start", "restart"} and attempts >= self.services[sid].max_recovery_attempts:
                blocked.append("bounded recovery attempts exhausted")
            if action in {"start", "restart"} and diagnostics["occupied_port"]:
                blocked.append("port occupied by non-service process")
            if action in {"start", "restart"} and any(inspection[dep]["resident_available"] is False for dep in self.services[sid].dependencies):
                blocked.append("dependency not resident-available")
            if blocked:
                blocked_reasons.extend(f"{sid}: {reason}" for reason in blocked)
            steps.append({
                "service_id": sid,
                "action": "status" if action == "status" else action,
                "current_state": row["state"],
                "requires_approval": action != "status" and policy.require_approval,
                "auto_execute": False,
                "blocked": blocked,
                "startup_timeout_seconds": row["startup_timeout_seconds"],
                "cold_load_seconds": row["cold_load_seconds"],
                "diagnostics": diagnostics,
                "resident_impact": row["resident_impact"],
            })
        payload = self.office_payload(action, service_id, inspection, steps, blocked_reasons)
        self.audit_events.append({"event": "service_plan_created", "payload": payload})
        return payload

    def office_payload(self, action: str, service_id: str, inspection: dict[str, dict[str, Any]], steps: list[dict[str, Any]], blocked_reasons: list[str]) -> dict[str, Any]:
        return {
            "kind": self.services[service_id].office_payload_kind,
            "service_id": service_id,
            "requested_action": action,
            "created_at": self._timestamp(),
            "approval_bound": action != "status",
            "auto_execute": False,
            "blocked": bool(blocked_reasons),
            "blocked_reasons": blocked_reasons,
            "steps": steps,
            "status": inspection[service_id],
            "resident_available": inspection[service_id]["resident_available"],
            "resident_impact": inspection[service_id]["resident_impact"],
            "audit_required": action != "status",
        }

    def _ordered_services_for(self, action: str, service_id: str) -> list[str]:
        if action == "status":
            return [service_id]
        dependencies = self._dependency_closure(service_id)
        if action in {"start", "restart"}:
            return [*dependencies, service_id]
        return [service_id, *reversed(dependencies)]

    def _dependency_closure(self, service_id: str, seen: set[str] | None = None) -> list[str]:
        seen = seen or set()
        ordered: list[str] = []
        for dep in self.services[service_id].dependencies:
            if dep in seen:
                continue
            if dep not in self.services:
                raise KeyError(f"unknown dependency {dep} for {service_id}")
            seen.add(dep)
            ordered.extend(self._dependency_closure(dep, seen))
            ordered.append(dep)
        return ordered

    def _diagnostics(self, spec: ServiceSpec, fact: RuntimeFact | None) -> dict[str, Any]:
        occupied = bool(spec.port and fact and fact.port_owner_pid and fact.pid != fact.port_owner_pid)
        stale = bool(fact and fact.pid and fact.state in DOWN_STATES)
        timeout = bool(fact and fact.state == "timeout")
        cold_loading = bool(fact and fact.state == "cold_loading")
        return {
            "port": spec.port,
            "occupied_port": occupied,
            "port_owner_pid": fact.port_owner_pid if fact else None,
            "port_owner_name": fact.port_owner_name if fact else None,
            "stale_process": stale,
            "pid": fact.pid if fact else None,
            "timeout": timeout,
            "cold_loading": cold_loading,
            "detail": fact.detail if fact else "no runtime fact supplied",
        }

    def _default_hints(self, spec: ServiceSpec, diagnostics: dict[str, Any], state: str) -> tuple[str, ...]:
        if diagnostics["occupied_port"]:
            return (f"inspect PID {diagnostics['port_owner_pid']} before starting {spec.service_id}",)
        if diagnostics["stale_process"]:
            return (f"clear stale PID {diagnostics['pid']} through approved service control",)
        if state == "cold_loading":
            return (f"allow up to {spec.cold_load_seconds} seconds for cold model load",)
        if state in DOWN_STATES:
            return ("request approved restart after dependency status is confirmed",)
        return ()

    def _timestamp(self) -> str:
        return self.now or datetime.now(timezone.utc).isoformat()
