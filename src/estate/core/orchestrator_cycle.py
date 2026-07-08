from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from uuid import uuid4

from estate.core.operational_events import OperationalEvent
from estate.core.operational_status import record_operational_event
from estate.core.orchestrator_dispatch import DispatchRecord, safe_dispatch_summary
from estate.core.orchestrator_runtime import OrchestratorRuntimeState
from estate.core.orchestrator_scheduler import ALLOWED_SCHEDULE_STATES, CLASSIFICATION_RANK
from estate.core.paths import ESTATE_ROOT
from estate.core.provider_catalog import load_provider_catalog
from estate.core.provider_capacity import latest_capacity_by_provider
from estate.core.provider_health import latest_health_by_provider
from estate.core.worker_assignment_runtime import WorkerAssignmentRuntime

RUNTIME_ROOT = Path("runtime/orchestrator/runtime")
DISPATCH_ROOT = Path("runtime/orchestrator/dispatch")
TERMINAL_ASSIGNMENT_STATES = {"completed", "cancelled", "failed"}
BLOCKING_HEALTH = {"blocked", "offline", "out_of_quota"}


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


class OrchestratorCycleRuntime:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root or ESTATE_ROOT
        self.status_dir = self.root / RUNTIME_ROOT / "status"
        self.cycles_dir = self.root / RUNTIME_ROOT / "cycles"
        self.dispatch_dirs = {state: self.root / DISPATCH_ROOT / state for state in ["pending", "blocked", "deferred", "completed"]}
        self.dispatch_status_dir = self.root / DISPATCH_ROOT / "status"

    def ensure_dirs(self) -> None:
        for path in [self.status_dir, self.cycles_dir, self.dispatch_status_dir, *self.dispatch_dirs.values()]:
            path.mkdir(parents=True, exist_ok=True)

    def run_cycle(self, *, dry_run: bool = False) -> OrchestratorRuntimeState:
        self.ensure_dirs()
        mode = "dry_run" if dry_run else "single_cycle"
        state = OrchestratorRuntimeState.create(cycle_id=f"cyc-{uuid4().hex}", mode=mode)
        dispatches: list[DispatchRecord] = []
        try:
            scheduled = self._load_scheduled(state)
            catalog = self._load_catalog(state)
            health = self._load_health(state)
            capacity = self._load_capacity(state)
            assignments = self._load_assignments(state)
            for item in scheduled:
                state.items_evaluated += 1
                outcome, reason = self._evaluate(item, catalog, health, capacity, assignments)
                if outcome == "pending_dispatch":
                    state.dispatches_created += 1
                elif outcome == "blocked":
                    state.items_blocked += 1
                elif outcome == "deferred":
                    state.items_deferred += 1
                dispatches.append(DispatchRecord.create(cycle_id=state.cycle_id, state=outcome, schedule=item, reason=reason))
            if not dry_run:
                for rec in dispatches:
                    self._write_dispatch(rec)
                    if self._emit_event(rec, state):
                        state.events_emitted += 1
                self._write_queue()
            else:
                state.metadata["dry_run_dispatches"] = [rec.to_dict() for rec in dispatches]
                self._write_queue()
        except Exception as exc:
            state.errors.append(str(exc))
        state.finish()
        self._write_status(state)
        return state

    def _load_scheduled(self, state: OrchestratorRuntimeState) -> list[dict[str, Any]]:
        queue = self.root / "runtime/orchestrator/schedule/status/queue.json"
        if not queue.exists():
            state.warnings.append("Schedule queue unavailable; no work evaluated.")
            return []
        try:
            data = json.loads(queue.read_text(encoding="utf-8"))
        except Exception as exc:
            state.errors.append(f"Malformed schedule queue: {exc}")
            return []
        items = data.get("scheduled") or []
        if not isinstance(items, list):
            state.errors.append("Malformed schedule queue: scheduled must be a list")
            return []
        return [item for item in items if isinstance(item, dict) and item.get("state") == "scheduled"]

    def _load_catalog(self, state):
        try: return load_provider_catalog(self.root / "config/providers/catalog.json")
        except Exception as exc:
            state.warnings.append(f"Provider catalog unavailable: {exc}"); return None

    def _load_health(self, state):
        try: return latest_health_by_provider(self.root)
        except Exception as exc:
            state.warnings.append(f"Provider health unavailable: {exc}"); return {}

    def _load_capacity(self, state):
        try: return latest_capacity_by_provider(self.root)
        except Exception as exc:
            state.warnings.append(f"Provider capacity unavailable: {exc}"); return {}

    def _load_assignments(self, state):
        try: return {a.assignment_id: a for a in WorkerAssignmentRuntime(root=self.root).load_assignments()}
        except Exception as exc:
            state.warnings.append(f"Assignment board unavailable: {exc}"); return {}

    def _evaluate(self, item, catalog, health, capacity, assignments) -> tuple[str, str | None]:
        if item.get("classification") not in CLASSIFICATION_RANK: return "blocked", "Classification is invalid."
        if item.get("state") not in ALLOWED_SCHEDULE_STATES or item.get("state") != "scheduled": return "blocked", "Item is not in scheduled state."
        if not item.get("approval_reference") and not (item.get("metadata") or {}).get("approval_reference"): return "blocked", "Approval is required but missing."
        if item.get("boundary_review_required") and not ((item.get("metadata") or {}).get("boundary_review_completed") or (item.get("metadata") or {}).get("boundary_review_reference")): return "blocked", "Boundary review is required but missing."
        if item.get("source") == "work_package" and not item.get("work_package_path"): return "blocked", "Work package path is missing for work package execution."
        if not item.get("provider_id") and not item.get("provider_type"): return "deferred", "Provider ID or type is not known enough to dispatch."
        provider = None
        if catalog is None: return "deferred", "Provider catalog unavailable."
        try:
            if item.get("provider_id"): provider = catalog.get_provider(item["provider_id"])
            else:
                candidates = catalog.providers_by_type(item["provider_type"])
                provider = next((p for p in candidates if p.status not in {"deprecated", "blocked"}), None)
                if provider and not item.get("provider_id"): item["provider_id"] = provider.provider_id
        except Exception as exc:
            return "deferred", f"Provider catalog lookup failed: {exc}"
        if not provider: return "deferred", "No eligible provider found in catalog."
        if provider.status in {"deprecated", "blocked"}: return "blocked", f"Provider is {provider.status}."
        if set(item.get("required_capabilities") or []) - set(provider.capabilities): return "blocked", "Provider lacks required capabilities."
        if CLASSIFICATION_RANK[item["classification"]] > CLASSIFICATION_RANK[provider.classification_ceiling]: return "blocked", "Classification exceeds provider ceiling."
        h = health.get(provider.provider_id)
        c = capacity.get(provider.provider_id)
        if h is None: return "deferred", "Provider health is unknown."
        if h.status in BLOCKING_HEALTH: return "blocked", f"Provider health is {h.status}."
        if h.status == "saturated":
            return "deferred", "Provider health is saturated; queueing deferred."
        if c is None: return "deferred", "Provider capacity is unknown."
        if c.capacity_state in {"saturated", "quota_limited", "busy"}: return "deferred", f"Provider capacity is {c.capacity_state}."
        aid = item.get("assignment_id")
        if aid and aid in assignments:
            a = assignments[aid]
            if a.state in TERMINAL_ASSIGNMENT_STATES: return "blocked", f"Assignment state is {a.state}."
            if a.state == "blocked" and not (item.get("metadata") or {}).get("assignment_override"): return "blocked", "Assignment state is blocked without override."
        elif aid:
            return "deferred", "Assignment state is unavailable."
        return "pending_dispatch", None

    def _write_dispatch(self, rec: DispatchRecord) -> None:
        folder = {"pending_dispatch": "pending", "blocked": "blocked", "deferred": "deferred", "cancelled": "blocked"}[rec.state]
        path = self.dispatch_dirs[folder] / f"{rec.dispatch_id}.json"
        rec.artifact_paths.append(str(path.relative_to(self.root)))
        _write_json(path, rec.to_dict())

    def _write_queue(self) -> None:
        payload = {"pending": [], "blocked": [], "deferred": []}
        for key in payload:
            d = self.dispatch_dirs[key]
            if d.exists():
                payload[key] = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(d.glob("*.json"))]
        _write_json(self.dispatch_status_dir / "queue.json", payload)

    def _write_status(self, state):
        data = state.to_dict()
        _write_json(self.status_dir / "latest.json", data)
        _write_json(self.cycles_dir / f"{state.cycle_id}.json", data)
        (self.status_dir / "summary.md").write_text(format_cycle_summary(state), encoding="utf-8")

    def _emit_event(self, rec, state):
        event_type = "Job Accepted" if rec.state == "pending_dispatch" else "Worker Blocked" if rec.state == "blocked" else "Checkpoint Reached"
        event_state = "Waiting" if rec.state == "pending_dispatch" else "Blocked" if rec.state == "blocked" else "Deferred"
        message = safe_dispatch_summary(rec.to_dict()) if rec.state == "pending_dispatch" else rec.blocked_reason or rec.deferred_reason or "Dispatch state changed."
        event = OperationalEvent.create(event_type=event_type, state=event_state, classification=rec.classification, message=message, provider_id=rec.provider_id, provider_type=rec.provider_type, assignment_id=rec.assignment_id, work_package_id=rec.work_package_id, request_id=rec.intake_id, validation_status="not_validated" if rec.validation_required else "not_required", requires_attention=rec.state == "blocked", artifact_paths=rec.artifact_paths, metadata={"dispatch_id": rec.dispatch_id, "cycle_id": rec.cycle_id, "summary_safe": rec.metadata.get("summary_safe", False)})
        try:
            record_operational_event(event, root=self.root); return True
        except Exception as exc:
            state.warnings.append(f"Operational event not emitted for {rec.dispatch_id}: {exc}"); return False

    def dispatch_queue(self) -> dict[str, Any]:
        self.ensure_dirs(); path = self.dispatch_status_dir / "queue.json"
        if not path.exists(): self._write_queue()
        return json.loads(path.read_text(encoding="utf-8"))


def format_cycle_summary(state: OrchestratorRuntimeState) -> str:
    return "\n".join(["Orchestrator Cycle Summary", f"Cycle: {state.cycle_id}", f"Mode: {state.mode}", f"State: {state.state}", f"Items evaluated: {state.items_evaluated}", f"Dispatches created: {state.dispatches_created}", f"Blocked: {state.items_blocked}", f"Deferred: {state.items_deferred}", f"Events emitted: {state.events_emitted}"])


def format_dispatch_queue(queue: dict[str, Any]) -> str:
    lines = ["Orchestrator Dispatch Queue"]
    for label in ["pending", "blocked", "deferred"]:
        lines.append(label.upper())
        items = queue.get(label) or []
        if not items: lines.append("- None")
        for item in items:
            reason = item.get("blocked_reason") or item.get("deferred_reason") or ""
            lines.append(f"- {item.get('dispatch_id')} | schedule={item.get('schedule_id')} | provider={item.get('provider_id') or item.get('provider_type')} | {safe_dispatch_summary(item)}" + (f" | {reason}" if reason else ""))
    return "\n".join(lines)
