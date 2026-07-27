"""Production-only Grace Momentum control service.

This module is intentionally transport-neutral: HTTP, CLI and worker adapters use
the same authenticated command/query boundary.  It never writes fixture roots and
never invokes a provider; bounded_live is a governed *recording* mode until a
separate provider-admission package installs an adapter.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable
from uuid import uuid4

from estate.core.execution_provider_adapter import utc_now

SCHEMA_VERSION = "estate.grace-momentum-control.v1"
EVENT_SCHEMA_VERSION = "estate.grace-momentum-event.v1"
PRODUCTION_ROOT = Path("runtime/production/grace_momentum")
MODES = {"fixture", "shadow", "bounded_live", "disabled"}
COMMAND_OFFICES = {
    "objective.create_or_correlate": {"Grace"}, "momentum.authorize": {"Grace"},
    "directive.pause": {"Grace"}, "directive.resume": {"Grace"}, "directive.stop": {"Grace"},
    "directive.revoke": {"Grace"}, "directive.supersede": {"Grace"}, "cme.reevaluate": {"CME"},
    "engineering.progress_commission": {"Engineering"}, "progression.inspect": {"Grace", "CME", "Engineering", "Dispatch", "Observer"},
    "escalation.request": {"Grace", "CME", "Engineering", "Dispatch"},
    # Compatibility names retained for early consumers.
    "directive.create": {"Grace"}, "directive.transition": {"Grace"}, "cme.evaluate": {"CME"},
    "engineering.authorize": {"Engineering"}, "dispatch.request": {"Dispatch"},
}
QUERY_NAMES = {"objective.summary", "lifecycle.timeline", "responsibility.current", "blocker.current", "action.next_lawful", "directive.state", "capability.state", "commission.state", "provider_governance.state", "dispatch.state", "validation.state", "replay.state", "audit.trail"}
EVENT_FOR_ACTION = {
    "objective.create_or_correlate": "objective.created_or_correlated", "momentum.authorize": "directive.authorized",
    "directive.pause": "directive.paused", "directive.resume": "directive.resumed", "directive.stop": "directive.stopped",
    "directive.revoke": "directive.revoked", "directive.supersede": "directive.superseded",
    "cme.reevaluate": "cme.evaluation.persisted", "engineering.progress_commission": "progression.changed",
    "progression.inspect": "progression.inspected", "escalation.request": "escalation.requested",
    "directive.create": "directive.authorized", "directive.transition": "directive.transitioned",
    "cme.evaluate": "cme.evaluation.persisted", "engineering.authorize": "execution.authorized", "dispatch.request": "dispatch.submitted",
}


class ControlError(ValueError): pass
class AuthenticationError(ControlError): pass
class AuthorizationError(ControlError): pass


@dataclass(frozen=True)
class OfficeIdentity:
    actor_id: str
    represented_office: str
    authority_source: str
    authenticated: bool = True


TEST_IDENTITIES = {
    "grace": OfficeIdentity("test-grace", "Grace", "test/grace-authority"),
    "cme": OfficeIdentity("test-cme", "CME", "test/cme-delegation"),
    "engineering": OfficeIdentity("test-engineering", "Engineering", "test/engineering-authority"),
    "dispatch": OfficeIdentity("test-dispatch", "Dispatch", "test/dispatch-authority"),
    "observer": OfficeIdentity("test-observer", "Observer", "test/read-only"),
}


class GraceMomentumService:
    """Durable command/event service shared by all Estate control surfaces."""
    def __init__(self, root: str | Path, *, mode: str = "shadow") -> None:
        if mode not in MODES: raise ControlError("unknown execution mode")
        self.root, self.mode = Path(root), mode
        self.base = self.root / PRODUCTION_ROOT
        self.base.mkdir(parents=True, exist_ok=True)

    def _path(self, name: str) -> Path: return self.base / name
    def _read(self, name: str, default: Any) -> Any:
        path = self._path(name)
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default
    def _write(self, name: str, value: Any) -> None:
        path = self._path(name); path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    def _audit(self, event: dict[str, Any]) -> None:
        with self._path("audit.jsonl").open("a", encoding="utf-8") as stream: stream.write(json.dumps(event, sort_keys=True) + "\n")
    def _events(self) -> list[dict[str, Any]]:
        path = self._path("events.jsonl")
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line] if path.exists() else []
    def _publish(self, event_type: str, envelope: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
        events = self._events(); event = {**envelope, "schema_version": EVENT_SCHEMA_VERSION,
            "event_id": f"gms-{uuid4().hex}", "event_type": event_type, "position": len(events) + 1,
            "occurred_at": utc_now(), "payload": payload}
        with self._path("events.jsonl").open("a", encoding="utf-8") as stream: stream.write(json.dumps(event, sort_keys=True) + "\n")
        self._audit({"kind": "event", **event}); return event
    def _envelope(self, command: dict[str, Any], identity: OfficeIdentity) -> dict[str, Any]:
        required = {"schema_version", "command_id", "correlation_id", "causation_id", "idempotency_key", "timestamp"}
        missing = required - command.keys()
        if missing or command.get("schema_version") != SCHEMA_VERSION: raise ControlError("invalid command envelope")
        if not identity.authenticated or not identity.authority_source: raise AuthenticationError("authenticated Office authority is required")
        return {key: command.get(key) for key in required} | {"actor": identity.actor_id,
            "represented_office": identity.represented_office, "authority_source": identity.authority_source,
            "objective_id": command.get("objective_id"), "directive_id": command.get("directive_id"),
            "disposition": command.get("disposition", "accepted"), "diagnostic_reference": command.get("diagnostic_reference"),
            "audit_reference": f"audit:{command['command_id']}"}
    def _assert_authority(self, action: str, identity: OfficeIdentity) -> None:
        if identity.represented_office not in COMMAND_OFFICES[action]:
            raise AuthorizationError(f"{identity.represented_office} may not execute {action}")
    def _idempotent(self, key: str) -> dict[str, Any] | None:
        return self._read("idempotency.json", {}).get(key)
    def _remember(self, key: str, response: dict[str, Any]) -> None:
        records = self._read("idempotency.json", {}); records[key] = response; self._write("idempotency.json", records)

    def command(self, command: dict[str, Any], identity: OfficeIdentity) -> dict[str, Any]:
        envelope = self._envelope(command, identity); action = command.get("action")
        if action not in COMMAND_OFFICES: raise ControlError("unknown command action")
        if self.mode == "disabled": raise AuthorizationError("Grace Momentum runtime is disabled")
        self._assert_authority(action, identity)
        if prior := self._idempotent(command["idempotency_key"]): return prior
        directives = self._read("directives.json", {})
        if action in {"directive.create", "momentum.authorize"}:
            directive_id = command.get("directive_id") or f"gmd-{uuid4().hex[:12]}"
            record = {"directive_id": directive_id, "objective_id": command["objective_id"], "status": "active", "operational_owner": "Grace", "continuation_mode": "event_driven", "created_at": utc_now()}
            directives[directive_id] = record; self._write("directives.json", directives); kind = EVENT_FOR_ACTION[action]
        elif action in {"directive.transition", "directive.pause", "directive.resume", "directive.stop", "directive.revoke", "directive.supersede"}:
            record = directives.get(command.get("directive_id"))
            if action == "directive.supersede":
                directive_id = f"gmd-{uuid4().hex[:12]}"; record = {"directive_id": directive_id, "objective_id": command["objective_id"], "status": "active", "supersedes_directive_id": command.get("directive_id"), "operational_owner": "Grace", "created_at": utc_now()}
            else:
                if not record: raise ControlError("directive not found")
                status = command.get("status") or action.rsplit(".", 1)[1] + "d"
                record = {**record, "status": status, "updated_at": utc_now()}
            directives[record["directive_id"]] = record; self._write("directives.json", directives); kind = EVENT_FOR_ACTION[action]
        elif action in {"cme.evaluate", "cme.reevaluate"}:
            record = {"objective_id": command.get("objective_id"), "directive_id": command.get("directive_id"), "operational_owner": "Grace", "continuation_owner": "CME", "disposition": "shadow_evaluated" if self.mode == "shadow" else "evaluated", "provider_effect_suppressed": True}; kind = EVENT_FOR_ACTION[action]
        elif action in {"engineering.authorize", "engineering.progress_commission"}:
            record = {"objective_id": command.get("objective_id"), "commission_id": command.get("commission_id"), "technical_owner": "Engineering", "disposition": "authorized_for_dispatch", "provider_effect_suppressed": True}; kind = EVENT_FOR_ACTION[action]
        elif action == "objective.create_or_correlate":
            record = {"objective_id": command.get("objective_id") or f"objective-{uuid4().hex[:12]}", "correlation_id": command["correlation_id"], "operational_owner": "Grace", "disposition": "created_or_correlated"}; kind = EVENT_FOR_ACTION[action]
        elif action == "progression.inspect":
            record = {"objective_id": command.get("objective_id"), "disposition": "inspection_recorded", "provider_effect_suppressed": True}; kind = EVENT_FOR_ACTION[action]
        elif action == "escalation.request":
            record = {"objective_id": command.get("objective_id"), "directive_id": command.get("directive_id"), "disposition": "escalation_requested", "provider_effect_suppressed": True}; kind = EVENT_FOR_ACTION[action]
        else:
            record = {"objective_id": command.get("objective_id"), "dispatch_id": command.get("dispatch_id") or f"dispatch-{uuid4().hex[:12]}", "logistics_owner": "Dispatch", "disposition": "recorded_no_provider_execution", "provider_effect_suppressed": True}; kind = "dispatch.requested"
        event = self._publish(kind, envelope, record)
        response = {"schema_version": SCHEMA_VERSION, "disposition": record.get("disposition", "accepted"), "record": record, "event": event, "provider_effect_suppressed": True}
        self._remember(command["idempotency_key"], response); return response

    def query(self, name: str, identity: OfficeIdentity, **filters: Any) -> dict[str, Any]:
        if not identity.authenticated: raise AuthenticationError("authenticated identity required")
        if name == "lifecycle": result = self._read("directives.json", {})
        elif name == "audit": result = self._read("audit.jsonl", "")
        elif name == "governance": result = {"mode": self.mode, "provider_effects_enabled": False, "provider_governance": "fails_closed"}
        elif name in QUERY_NAMES:
            events = self._events(); objective_id = filters.get("objective_id")
            related = [event for event in events if not objective_id or event.get("objective_id") == objective_id or event.get("payload", {}).get("objective_id") == objective_id]
            result = {"objective_id": objective_id, "events": related, "directives": self._read("directives.json", {}), "provider_effects_enabled": False, "mode": self.mode}
        else: raise ControlError("unknown query")
        return {"schema_version": SCHEMA_VERSION, "query": name, "result": result}
    def subscribe(self, cursor: int = 0) -> dict[str, Any]:
        events = [event for event in self._events() if event["position"] > cursor]
        return {"schema_version": EVENT_SCHEMA_VERSION, "cursor": cursor, "next_cursor": events[-1]["position"] if events else cursor, "events": events}
    def checkpoint(self) -> dict[str, Any]:
        event_count = len(self._events()); snapshot = {"schema_version": SCHEMA_VERSION, "event_position": event_count, "directives": self._read("directives.json", {}), "completed_effects": list(self._read("idempotency.json", {})), "created_at": utc_now()}
        self._write("checkpoints/latest.json", snapshot); return snapshot
    def recover(self) -> dict[str, Any]:
        checkpoint = self._read("checkpoints/latest.json", None)
        if checkpoint is None: return {"recovered": False, "reason": "no checkpoint"}
        return {"recovered": True, "checkpoint_position": checkpoint["event_position"], "replay": self.subscribe(checkpoint["event_position"])}
    def health(self) -> dict[str, Any]: return {"service": "grace-momentum", "healthy": True, "mode": self.mode, "storage": str(self.base)}
    def readiness(self) -> dict[str, Any]: return {"service": "grace-momentum", "ready": self.mode != "disabled", "provider_effects_enabled": False, "mode": self.mode}


class FakeGraceMomentumService(GraceMomentumService):
    """Contract-test fake; behavior and event envelopes match the reference service."""
    def __init__(self, root: str | Path, *, mode: str = "fixture") -> None: super().__init__(root, mode=mode)


class GraceMomentumClient:
    """Reference client used by both UI lanes; clients contain no lifecycle policy."""
    def __init__(self, service: GraceMomentumService, identity: OfficeIdentity) -> None: self.service, self.identity = service, identity
    def send(self, command: dict[str, Any]) -> dict[str, Any]:
        try: return self.service.command(command, self.identity)
        except (AuthenticationError, AuthorizationError) as exc:
            return {"schema_version": SCHEMA_VERSION, "disposition": "unauthorized", "error": {"code": "unauthorized", "message": str(exc), "retryable": False}}
    def query(self, name: str, **filters: Any) -> dict[str, Any]:
        try: return self.service.query(name, self.identity, **filters)
        except AuthenticationError as exc: return {"schema_version": SCHEMA_VERSION, "disposition": "unauthorized", "error": {"code": "invalid_or_expired_session", "message": str(exc), "retryable": False}}


def reference_command(action: str, *, objective_id: str = "objective-demo", directive_id: str | None = None, idempotency_key: str = "demo-1") -> dict[str, Any]:
    return {"schema_version": SCHEMA_VERSION, "command_id": f"command-{idempotency_key}", "correlation_id": "correlation-demo", "causation_id": "cause-demo", "idempotency_key": idempotency_key, "timestamp": "2026-07-26T00:00:00Z", "action": action, "objective_id": objective_id, "directive_id": directive_id}
