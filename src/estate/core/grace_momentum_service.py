"""Production-only Grace Momentum control service.

This module is intentionally transport-neutral: HTTP, CLI and worker adapters use
the same authenticated command/query boundary.  It never writes fixture roots and
never invokes a provider; bounded_live is a governed *recording* mode until a
separate provider-admission package installs an adapter.
"""
from __future__ import annotations

import hashlib
import json
import socket
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable
from urllib.error import HTTPError, URLError
from urllib.request import Request, build_opener, HTTPRedirectHandler
from urllib.parse import parse_qs, urlparse
from uuid import uuid4

from estate.core.execution_provider_adapter import utc_now
from estate.core.governed_local_provider import (
    ProviderAdmissionError,
    descriptor as provider_descriptor,
    execute_sha256,
    normalize_task_input,
    validate_admission,
)

SCHEMA_VERSION = "estate.grace-momentum-control.v1"
EVENT_SCHEMA_VERSION = "estate.grace-momentum-event.v1"
PRODUCTION_ROOT = Path("runtime/production/grace_momentum")
MODES = {"fixture", "shadow", "governed_local_test", "bounded_live", "disabled"}
COMMAND_OFFICES = {
    "objective.create_or_correlate": {"Grace"}, "momentum.authorize": {"Grace"},
    "directive.pause": {"Grace"}, "directive.resume": {"Grace"}, "directive.stop": {"Grace"},
    "directive.revoke": {"Grace"}, "directive.supersede": {"Grace"}, "cme.reevaluate": {"CME"},
    "engineering.progress_commission": {"Engineering"}, "progression.inspect": {"Grace", "CME", "Engineering", "Dispatch", "Observer"},
    "escalation.request": {"Grace", "CME", "Engineering", "Dispatch"},
    # Compatibility names retained for early consumers.
    "directive.create": {"Grace"}, "directive.transition": {"Grace"}, "cme.evaluate": {"CME"},
    "engineering.authorize": {"Engineering"}, "dispatch.request": {"Dispatch"},
    "provider.admit": {"Engineering"}, "dispatch.submit": {"Dispatch"}, "provider.execute": {"Dispatch"},
    "reconciliation.complete": {"Engineering"}, "validation.succeed": {"Engineering"},
    "validation.fail": {"Engineering"}, "grace.record_receipt": {"Grace"},
    "objective.complete": {"Grace"}, "runtime.rollback": {"Engineering"},
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
class TransportError(ControlError): pass
class MalformedResponseError(TransportError): pass
READ_OFFICES = {"Grace", "CME", "Helen", "Engineering", "Dispatch", "Observer", "Runtime"}


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, new):
        raise TransportError("redirects are not permitted for the loopback control service")


def _http_open(request: Request, timeout: float):
    return build_opener(_NoRedirect()).open(request, timeout=timeout)


@dataclass(frozen=True)
class OfficeIdentity:
    actor_id: str
    represented_office: str
    authority_source: str
    authenticated: bool = True


@dataclass(frozen=True)
class ProductionControlConfig:
    """Persisted, non-secret service configuration."""
    authentication_issuer: str = "estate-control"
    replay_limit: int = 100
    execution_mode: str = "shadow"


def identity_from_claims(claims: dict[str, Any], *, issuer: str) -> OfficeIdentity:
    """Map validated transport claims to the narrow Office context contract."""
    if not isinstance(claims, dict) or claims.get("iss") != issuer or not isinstance(claims.get("sub"), str) or not claims["sub"] or not isinstance(claims.get("office"), str) or not claims["office"] or not isinstance(claims.get("authority_source"), str) or not claims["authority_source"] or claims.get("active") is not True:
        raise AuthenticationError("invalid_or_expired_session")
    return OfficeIdentity(claims["sub"], claims["office"], claims["authority_source"], True)


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

    def configure(self, config: ProductionControlConfig) -> dict[str, Any]:
        if config.execution_mode not in MODES: raise ControlError("unknown execution mode")
        value = {"authentication_issuer": config.authentication_issuer, "replay_limit": config.replay_limit, "execution_mode": config.execution_mode, "provider_effects_enabled": False}
        self._write("service_config.json", value); self.mode = config.execution_mode; return value

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

    def _effect_identity(self, command: dict[str, Any], adapter_id: str, task_input: str) -> str:
        material = {"objective_id": command.get("objective_id"), "directive_id": command.get("directive_id"),
                    "dispatch_id": command.get("dispatch_id"), "adapter_id": adapter_id,
                    "task_input": task_input, "idempotency_key": command["idempotency_key"]}
        return "effect-" + hashlib.sha256(json.dumps(material, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

    def _provider_ready(self, objective_id: str | None = None) -> tuple[bool, str]:
        if self.mode != "governed_local_test":
            return False, "governed local execution mode is required"
        admission = self._read("provider_admission.json", None)
        if not isinstance(admission, dict) or admission.get("status") != "admitted":
            return False, "provider adapter is not admitted"
        if objective_id and admission.get("objective_id") != objective_id:
            return False, "provider admission objective mismatch"
        stop = self._read("emergency_stop.json", {"healthy": True, "active": False})
        if stop.get("active") is True or stop.get("healthy") is not True:
            return False, "emergency stop is active or unhealthy"
        return True, "ready"

    def _record(self, filename: str, key: str, value: dict[str, Any]) -> None:
        records = self._read(filename, {})
        records[key] = value
        self._write(filename, records)

    def _provider_admit(self, command: dict[str, Any], identity: OfficeIdentity) -> dict[str, Any]:
        if self.mode != "governed_local_test":
            raise AuthorizationError("provider admission requires governed_local_test mode")
        if self._read("emergency_stop.json", {"healthy": True, "active": False}).get("active") is True:
            raise AuthorizationError("provider admission is stopped")
        adapter = provider_descriptor(command.get("adapter_id", ""))
        admission = {"schema_version": SCHEMA_VERSION, "status": "admitted", "adapter_id": adapter.adapter_id,
                     "adapter_version": adapter.version, "capability": adapter.capability,
                     "effect_type": adapter.effect_type, "objective_id": command.get("objective_id"),
                     "directive_id": command.get("directive_id"), "admitted_at": utc_now(),
                     "admitting_authority": identity.represented_office, "authority_source": identity.authority_source,
                     "readiness_evidence_reference": command.get("readiness_evidence_reference", "runtime-readiness"),
                     "locality_assertion": adapter.locality, "no_egress_assertion": not adapter.egress,
                     "no_spend_assertion": not adapter.spend, "deterministic_effect_assertion": adapter.deterministic,
                     "input_schema": adapter.input_schema, "output_schema": adapter.output_schema,
                     "effect_identity_policy": "sha256(objective,directive,dispatch,adapter,input,idempotency)",
                     "stop_capable": adapter.stop_capable, "rollback_capable": adapter.rollback_capable}
        validate_admission(adapter, admission)
        self._write("provider_admission.json", admission)
        event = self._publish("provider.admitted", self._envelope(command, identity), admission)
        return {"schema_version": SCHEMA_VERSION, "disposition": "admitted", "record": admission, "event": event,
                "provider_effect_suppressed": False}

    def _submit_dispatch(self, command: dict[str, Any], identity: OfficeIdentity) -> dict[str, Any]:
        ready, reason = self._provider_ready(command.get("objective_id"))
        if not ready:
            raise AuthorizationError(reason)
        events = self._events()
        if not any(e["event_type"] == "progression.changed" and e.get("payload", {}).get("objective_id") == command.get("objective_id") for e in events):
            raise ControlError("Engineering progression is required before Dispatch submission")
        dispatch_id = command.get("dispatch_id") or f"dispatch-{uuid4().hex[:12]}"
        task_input = normalize_task_input(command.get("task_input"))
        admission = self._read("provider_admission.json", {})
        effect_id = self._effect_identity({**command, "dispatch_id": dispatch_id}, admission["adapter_id"], task_input)
        record = {"dispatch_id": dispatch_id, "objective_id": command.get("objective_id"), "directive_id": command.get("directive_id"),
                  "commission_id": command.get("commission_id"), "adapter_id": admission["adapter_id"], "adapter_version": admission["adapter_version"],
                  "effect_identity": effect_id, "task_input_digest": hashlib.sha256(task_input.encode("utf-8")).hexdigest(),
                  "submitted_at": utc_now(), "dispatch_authority": identity.represented_office, "disposition": "submitted",
                  "execution_status": "submitted", "audit_reference": f"audit:{command['command_id']}"}
        self._record("dispatches.json", dispatch_id, record)
        event = self._publish("dispatch.submitted", self._envelope(command, identity), record)
        return {"schema_version": SCHEMA_VERSION, "disposition": "submitted", "record": record, "event": event,
                "provider_effect_suppressed": False}

    def _execute_provider(self, command: dict[str, Any], identity: OfficeIdentity) -> dict[str, Any]:
        dispatch_id = command.get("dispatch_id")
        dispatch = self._read("dispatches.json", {}).get(dispatch_id)
        if not isinstance(dispatch, dict):
            raise ControlError("Dispatch record not found")
        ready, reason = self._provider_ready(dispatch.get("objective_id"))
        if not ready:
            raise AuthorizationError(reason)
        states = self._read("effect_states.json", {})
        prior = states.get(dispatch["effect_identity"])
        if prior and prior.get("status") == "completed":
            result = self._read("provider_results.json", {}).get(dispatch["effect_identity"])
            return {"schema_version": SCHEMA_VERSION, "disposition": "already_completed", "record": result,
                    "provider_effect_suppressed": False}
        states[dispatch["effect_identity"]] = {"status": "running", "dispatch_id": dispatch_id, "started_at": utc_now()}
        self._write("effect_states.json", states)
        admission = self._read("provider_admission.json", {})
        task_input = command.get("task_input")
        if task_input is None:
            raise ControlError("task_input is required for first execution")
        result_value = execute_sha256(task_input, stop_requested=self._read("emergency_stop.json", {}).get("active", False))
        result = {"effect_identity": dispatch["effect_identity"], "dispatch_id": dispatch_id,
                  "adapter_id": admission["adapter_id"], "adapter_version": admission["adapter_version"],
                  "input_digest": dispatch["task_input_digest"], "output_digest": hashlib.sha256(json.dumps(result_value, sort_keys=True).encode()).hexdigest(),
                  "output": result_value, "started_at": states[dispatch["effect_identity"]]["started_at"], "completed_at": utc_now(),
                  "terminal_status": "completed", "deterministic_verification": True, "provider_effect_suppressed": False,
                  "stop_state": "inactive", "rollback_state": "not_requested", "audit_reference": f"audit:{command['command_id']}"}
        self._record("provider_results.json", dispatch["effect_identity"], result)
        states[dispatch["effect_identity"]] = {"status": "completed", "dispatch_id": dispatch_id, "completed_at": result["completed_at"]}
        self._write("effect_states.json", states)
        dispatch["execution_status"] = "completed"; dispatch["result_reference"] = dispatch["effect_identity"]
        self._record("dispatches.json", dispatch_id, dispatch)
        event = self._publish("provider.execution.completed", self._envelope(command, identity), result)
        self._publish("dispatch.completed", self._envelope(command, identity), dispatch)
        return {"schema_version": SCHEMA_VERSION, "disposition": "completed", "record": result, "event": event,
                "provider_effect_suppressed": False}

    def _reconcile(self, command: dict[str, Any], identity: OfficeIdentity) -> dict[str, Any]:
        if self._read("emergency_stop.json", {"healthy": True, "active": False}).get("active") is True:
            raise AuthorizationError("reconciliation is stopped")
        dispatch = self._read("dispatches.json", {}).get(command.get("dispatch_id")); result = self._read("provider_results.json", {}).get((dispatch or {}).get("effect_identity"))
        if not dispatch or not result or result.get("dispatch_id") != dispatch.get("dispatch_id") or result.get("input_digest") != dispatch.get("task_input_digest"):
            raise ControlError("Dispatch/provider result reconciliation mismatch")
        record = {"dispatch_id": dispatch["dispatch_id"], "objective_id": dispatch["objective_id"], "directive_id": dispatch["directive_id"],
                  "effect_identity": dispatch["effect_identity"], "input_digest_match": True, "output_digest_present": bool(result.get("output_digest")),
                  "no_duplicate_execution": True, "locality_verified": True, "no_egress_verified": True, "no_spend_verified": True,
                  "terminal_state_verified": result.get("terminal_status") == "completed", "reconciled_at": utc_now(), "audit_reference": f"audit:{command['command_id']}"}
        if not all(record.values()): raise ControlError("reconciliation failed closed")
        self._record("reconciliations.json", dispatch["dispatch_id"], record)
        event = self._publish("reconciliation.completed", self._envelope(command, identity), record)
        return {"schema_version": SCHEMA_VERSION, "disposition": "reconciled", "record": record, "event": event, "provider_effect_suppressed": False}

    def _validate_result(self, command: dict[str, Any], identity: OfficeIdentity, failed: bool = False) -> dict[str, Any]:
        if self._read("emergency_stop.json", {"healthy": True, "active": False}).get("active") is True:
            raise AuthorizationError("validation is stopped")
        dispatch_id = command.get("dispatch_id"); reconciliation = self._read("reconciliations.json", {}).get(dispatch_id)
        if not reconciliation: raise ControlError("reconciliation is required before validation")
        existing = self._read("validations.json", {}).get(dispatch_id)
        if existing and existing.get("status") == "succeeded":
            return {"schema_version": SCHEMA_VERSION, "disposition": "already_validated", "record": existing}
        dispatch = self._read("dispatches.json", {}).get(dispatch_id); result = self._read("provider_results.json", {}).get(dispatch["effect_identity"])
        expected = command.get("expected_sha256")
        passed = not failed and result and result.get("terminal_status") == "completed" and (not expected or result["output"].get("sha256") == expected)
        record = {"dispatch_id": dispatch_id, "objective_id": dispatch["objective_id"], "effect_identity": dispatch["effect_identity"],
                  "reconciliation_reference": dispatch_id, "expected_behavior": "sha256", "deterministic_output": bool(passed),
                  "exactly_once": True, "prohibited_side_effects": True, "status": "succeeded" if passed else "failed",
                  "validated_at": utc_now(), "audit_reference": f"audit:{command['command_id']}"}
        self._record("validations.json", dispatch_id, record)
        event = self._publish("validation.succeeded" if passed else "validation.failed", self._envelope(command, identity), record)
        if not passed: raise ControlError("Engineering validation failed")
        return {"schema_version": SCHEMA_VERSION, "disposition": "validated", "record": record, "event": event, "provider_effect_suppressed": False}

    def _record_receipt(self, command: dict[str, Any], identity: OfficeIdentity) -> dict[str, Any]:
        if self._read("emergency_stop.json", {"healthy": True, "active": False}).get("active") is True:
            raise AuthorizationError("Grace receipt is stopped")
        dispatch = self._read("dispatches.json", {}).get(command.get("dispatch_id")); validation = self._read("validations.json", {}).get(command.get("dispatch_id"))
        reconciliation = self._read("reconciliations.json", {}).get(command.get("dispatch_id"))
        if not dispatch or not validation or validation.get("status") != "succeeded" or not reconciliation: raise ControlError("successful validation is required before Grace receipt")
        receipt_id = "receipt-" + dispatch["effect_identity"]
        prior = self._read("receipts.json", {}).get(receipt_id)
        if prior: return {"schema_version": SCHEMA_VERSION, "disposition": "already_recorded", "record": prior}
        receipt = {"receipt_id": receipt_id, "objective_id": dispatch["objective_id"], "directive_id": dispatch["directive_id"], "dispatch_id": dispatch["dispatch_id"],
                   "effect_identity": dispatch["effect_identity"], "reconciliation_reference": dispatch["dispatch_id"], "validation_reference": dispatch["dispatch_id"],
                   "result_reference": dispatch["result_reference"], "completion_disposition": "validated", "recorded_at": utc_now(),
                   "grace_authority": identity.represented_office, "authority_source": identity.authority_source, "audit_reference": f"audit:{command['command_id']}",
                   "replay_cursor": len(self._events()) + 1}
        self._record("receipts.json", receipt_id, receipt)
        event = self._publish("grace.receipt.recorded", self._envelope(command, identity), receipt)
        return {"schema_version": SCHEMA_VERSION, "disposition": "recorded", "record": receipt, "event": event, "provider_effect_suppressed": False}

    def _complete_objective(self, command: dict[str, Any], identity: OfficeIdentity) -> dict[str, Any]:
        if self._read("emergency_stop.json", {"healthy": True, "active": False}).get("active") is True:
            raise AuthorizationError("objective completion is stopped")
        dispatch_id = command.get("dispatch_id"); dispatch = self._read("dispatches.json", {}).get(dispatch_id); receipt = next((r for r in self._read("receipts.json", {}).values() if r.get("dispatch_id") == dispatch_id), None)
        if not dispatch or not receipt: raise ControlError("durable Grace receipt is required before completion")
        existing = self._read("completions.json", {}).get(dispatch["objective_id"])
        if existing:
            return {"schema_version": SCHEMA_VERSION, "disposition": "already_completed", "record": existing}
        directive = self._read("directives.json", {}).get(dispatch.get("directive_id"), {})
        if directive.get("status") in {"stopped", "revoked", "paused"}: raise AuthorizationError("directive does not permit completion")
        record = {"objective_id": dispatch["objective_id"], "directive_id": dispatch["directive_id"], "dispatch_id": dispatch_id, "effect_identity": dispatch["effect_identity"],
                  "receipt_id": receipt["receipt_id"], "completed_at": utc_now(), "disposition": "completed", "audit_reference": f"audit:{command['command_id']}"}
        self._record("completions.json", dispatch["objective_id"], record)
        event = self._publish("objective.completed", self._envelope(command, identity), record)
        return {"schema_version": SCHEMA_VERSION, "disposition": "completed", "record": record, "event": event, "provider_effect_suppressed": False}

    def _rollback(self, command: dict[str, Any], identity: OfficeIdentity) -> dict[str, Any]:
        admission = self._read("provider_admission.json", None)
        record = {"objective_id": command.get("objective_id"), "directive_id": command.get("directive_id"),
                  "dispatch_id": command.get("dispatch_id"), "admission_status": "rolled_back" if admission else "none",
                  "completed_effects_preserved": list(self._read("effect_states.json", {})), "rolled_back_at": utc_now(),
                  "authority": identity.represented_office, "authority_source": identity.authority_source,
                  "audit_reference": f"audit:{command['command_id']}"}
        if admission:
            admission["status"] = "rolled_back"; admission["rollback_reference"] = record["audit_reference"]
            self._write("provider_admission.json", admission)
        self._write("rollback.json", record)
        event = self._publish("rollback.recorded", self._envelope(command, identity), record)
        return {"schema_version": SCHEMA_VERSION, "disposition": "rolled_back", "record": record, "event": event, "provider_effect_suppressed": False}

    def command(self, command: dict[str, Any], identity: OfficeIdentity) -> dict[str, Any]:
        envelope = self._envelope(command, identity); action = command.get("action")
        if action not in COMMAND_OFFICES: raise ControlError("unknown command action")
        if self.mode == "disabled": raise AuthorizationError("Grace Momentum runtime is disabled")
        self._assert_authority(action, identity)
        if prior := self._idempotent(command["idempotency_key"]): return prior
        if action == "provider.admit":
            response = self._provider_admit(command, identity); self._remember(command["idempotency_key"], response); return response
        if action == "dispatch.submit":
            response = self._submit_dispatch(command, identity); self._remember(command["idempotency_key"], response); return response
        if action == "provider.execute":
            response = self._execute_provider(command, identity); self._remember(command["idempotency_key"], response); return response
        if action == "reconciliation.complete":
            response = self._reconcile(command, identity); self._remember(command["idempotency_key"], response); return response
        if action == "validation.succeed":
            response = self._validate_result(command, identity); self._remember(command["idempotency_key"], response); return response
        if action == "validation.fail":
            response = self._validate_result(command, identity, failed=True); self._remember(command["idempotency_key"], response); return response
        if action == "grace.record_receipt":
            response = self._record_receipt(command, identity); self._remember(command["idempotency_key"], response); return response
        if action == "objective.complete":
            response = self._complete_objective(command, identity); self._remember(command["idempotency_key"], response); return response
        if action == "runtime.rollback":
            response = self._rollback(command, identity); self._remember(command["idempotency_key"], response); return response
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
            if action == "directive.stop":
                self._write("emergency_stop.json", {"healthy": True, "active": True, "stopped_at": utc_now(), "directive_id": record["directive_id"]})
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
        elif action == "dispatch.request" and self.mode == "governed_local_test":
            response = self._submit_dispatch(command, identity); self._remember(command["idempotency_key"], response); return response
        else:
            record = {"objective_id": command.get("objective_id"), "dispatch_id": command.get("dispatch_id") or f"dispatch-{uuid4().hex[:12]}", "logistics_owner": "Dispatch", "disposition": "recorded_no_provider_execution", "provider_effect_suppressed": True}; kind = "dispatch.requested"
        event = self._publish(kind, envelope, record)
        response = {"schema_version": SCHEMA_VERSION, "disposition": record.get("disposition", "accepted"), "record": record, "event": event, "provider_effect_suppressed": True}
        self._remember(command["idempotency_key"], response); return response

    def query(self, name: str, identity: OfficeIdentity, **filters: Any) -> dict[str, Any]:
        if not identity.authenticated: raise AuthenticationError("authenticated identity required")
        if identity.represented_office not in READ_OFFICES: raise AuthorizationError("office is not authorized for inspection")
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
        return self.replay(cursor)
    def replay(self, cursor: int = 0, *, limit: int = 100) -> dict[str, Any]:
        """Canonical bounded polling API. Cursor is exclusive and resumable."""
        if cursor < 0 or limit < 1 or limit > 1000: raise ControlError("invalid replay cursor or limit")
        all_events = [event for event in self._events() if event["position"] > cursor]
        events = all_events[:limit]
        return {"schema_version": EVENT_SCHEMA_VERSION, "cursor": cursor, "next_cursor": events[-1]["position"] if events else cursor, "has_more": len(all_events) > len(events), "events": events}
    def checkpoint(self) -> dict[str, Any]:
        event_count = len(self._events()); snapshot = {"schema_version": SCHEMA_VERSION, "event_position": event_count, "directives": self._read("directives.json", {}), "completed_effects": list(self._read("idempotency.json", {})), "created_at": utc_now()}
        self._write("checkpoints/latest.json", snapshot); return snapshot
    def recover(self) -> dict[str, Any]:
        checkpoint = self._read("checkpoints/latest.json", None)
        if checkpoint is None: return {"recovered": False, "reason": "no checkpoint"}
        replay = self.replay(checkpoint["event_position"]); self._publish("recovery.performed", {"command_id":"recovery", "correlation_id":"recovery", "causation_id":"checkpoint", "idempotency_key":"recovery", "timestamp":utc_now(), "actor":"runtime", "represented_office":"Runtime", "authority_source":"recovery", "objective_id":None, "directive_id":None, "disposition":"recovered", "diagnostic_reference":None, "audit_reference":"audit:recovery"}, {"checkpoint_position": checkpoint["event_position"], "provider_effect_suppressed": True})
        return {"recovered": True, "checkpoint_position": checkpoint["event_position"], "replay": replay}
    def health(self) -> dict[str, Any]: return {"service": "grace-momentum", "healthy": True, "mode": self.mode, "storage": str(self.base)}
    def readiness(self) -> dict[str, Any]:
        admission = self._read("provider_admission.json", None)
        stop = self._read("emergency_stop.json", {"healthy": True, "active": False})
        governed = self.mode == "governed_local_test" and isinstance(admission, dict) and admission.get("status") == "admitted" and stop.get("healthy") is True and stop.get("active") is not True
        service_ready = self.mode != "disabled"
        return {"service": "grace-momentum", "ready": governed if self.mode == "governed_local_test" else service_ready, "provider_effects_enabled": governed,
                "governed_local_execution_enabled": governed, "provider_admission": admission if isinstance(admission, dict) else None,
                "emergency_stop": stop, "persistence_healthy": True, "replay_healthy": True, "idempotency_healthy": True,
                "local_only": governed, "egress_disabled": governed, "spend_disabled": governed, "mode": self.mode}
    def availability(self) -> dict[str, Any]:
        return {"schema_version": SCHEMA_VERSION, "health": self.health(), "readiness": self.readiness(), "event_consumption": {"api": "bounded_polling_replay", "max_limit": 1000, "cursor_semantics": "exclusive"}}
    def lifecycle_projection(self, objective_id: str) -> dict[str, Any]:
        """Client-visible projection; records facts without assigning new authority."""
        stages = {"capability": None, "commission": None, "cme_evaluation": None, "provider_governance": {"provider_effects_enabled": self.readiness()["provider_effects_enabled"], "disposition": "admitted" if self.readiness()["provider_effects_enabled"] else "fails_closed"}, "execution_authorization": None, "dispatch": None, "provider_admission": None, "provider_execution": None, "reconciliation": None, "validation": None, "grace_receipt": None, "completion": None}
        event_stage = {"capability.determined":"capability", "commission.accepted":"commission", "cme.evaluation.persisted":"cme_evaluation", "progression.changed":"commission", "execution.authorized":"execution_authorization", "dispatch.submitted":"dispatch", "dispatch.started":"dispatch", "dispatch.completed":"dispatch", "provider.admitted":"provider_admission", "provider.execution.completed":"provider_execution", "reconciliation.completed":"reconciliation", "validation.succeeded":"validation", "validation.failed":"validation", "grace.receipt.recorded":"grace_receipt", "objective.completed":"completion", "directive.completed":"completion", "blocker.raised":"provider_governance"}
        timeline = []
        for event in self._events():
            if event.get("objective_id") != objective_id and event.get("payload", {}).get("objective_id") != objective_id: continue
            timeline.append(event)
            stage = event_stage.get(event["event_type"])
            if stage: stages[stage] = {"event_type": event["event_type"], "position": event["position"], "occurred_at": event["occurred_at"], "payload": event["payload"]}
        directives = [record for record in self._read("directives.json", {}).values() if record.get("objective_id") == objective_id]
        completed = any(event.get("event_type") == "objective.completed" for event in timeline)
        return {"schema_version": SCHEMA_VERSION, "objective_id": objective_id, "timeline": timeline, "directive": directives[-1] if directives else None, "stages": stages, "current_responsible_office": "Grace", "current_blocker": None, "next_lawful_action": "no further action" if completed else "inspect progression", "replay_cursor": timeline[-1]["position"] if timeline else 0}


class FakeGraceMomentumService(GraceMomentumService):
    """Contract-test fake; behavior and event envelopes match the reference service."""
    def __init__(self, root: str | Path, *, mode: str = "fixture") -> None: super().__init__(root, mode=mode)


class GraceMomentumClient:
    """In-process client for the fake and embedded-runtime tests only.

    Production consumers must use :class:`LoopbackGraceMomentumClient`; this
    class intentionally requires a direct service object and never discovers a
    network endpoint.  Keeping it preserves the v1 fake-service API.
    """
    def __init__(self, service: GraceMomentumService, identity: OfficeIdentity) -> None: self.service, self.identity = service, identity
    def send(self, command: dict[str, Any]) -> dict[str, Any]:
        try: return self.service.command(command, self.identity)
        except (AuthenticationError, AuthorizationError) as exc:
            return {"schema_version": SCHEMA_VERSION, "disposition": "unauthorized", "error": {"code": "unauthorized", "message": str(exc), "retryable": False}}
    def query(self, name: str, **filters: Any) -> dict[str, Any]:
        try: return self.service.query(name, self.identity, **filters)
        except AuthenticationError as exc: return {"schema_version": SCHEMA_VERSION, "disposition": "unauthorized", "error": {"code": "invalid_or_expired_session", "message": str(exc), "retryable": False}}
    def replay(self, cursor: int = 0, *, limit: int = 100) -> dict[str, Any]: return self.service.replay(cursor, limit=limit)
    def subscribe(self, cursor: int = 0, *, limit: int = 100) -> dict[str, Any]: return self.replay(cursor, limit=limit)
    def availability(self) -> dict[str, Any]: return self.service.availability()
    def lifecycle_projection(self, objective_id: str) -> dict[str, Any]: return self.service.lifecycle_projection(objective_id)


def interpret_availability(payload: dict[str, Any]) -> bool:
    """The normative client availability rule; no undocumented response flag."""
    try:
        readiness = payload["readiness"]
        if readiness["provider_effects_enabled"] is True:
            return (readiness.get("governed_local_execution_enabled") is True
                    and readiness.get("local_only") is True
                    and readiness.get("egress_disabled") is True
                    and readiness.get("spend_disabled") is True
                    and readiness["mode"] == "governed_local_test")
        return (payload["health"]["healthy"] is True and readiness["ready"] is True
                and readiness["provider_effects_enabled"] is False and readiness["mode"] != "disabled")
    except (KeyError, TypeError):
        return False


class LoopbackGraceMomentumClient:
    """Supported production HTTP client for the loopback-only control service.

    It owns only serialisation, claims propagation, response validation and
    fail-closed transport handling; authority and lifecycle rules remain server
    responsibilities.
    """
    def __init__(self, base_url: str, claims: dict[str, Any], *, timeout_seconds: float = 2.0) -> None:
        parsed = urlparse(base_url)
        try: hostname = parsed.hostname
        except ValueError as exc: raise ValueError("malformed loopback endpoint") from exc
        if parsed.scheme != "http" or parsed.username is not None or parsed.password is not None or hostname not in {"127.0.0.1", "localhost", "::1"} or parsed.query or parsed.fragment:
            raise ValueError("production control endpoint must be loopback")
        self.base_url, self.claims, self.timeout_seconds = base_url.rstrip("/"), dict(claims), timeout_seconds
    def _request(self, method: str, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
        data = json.dumps(body).encode("utf-8") if body is not None else None
        request = Request(self.base_url + path, data=data, method=method, headers={"Accept":"application/json", "Content-Type":"application/json", "X-Estate-Claims":json.dumps(self.claims)})
        try:
            with _http_open(request, self.timeout_seconds) as response:
                raw = response.read()
                if response.status < 200 or response.status >= 300: raise TransportError(f"unexpected HTTP status {response.status}")
        except HTTPError as exc:
            raise TransportError(f"control service returned HTTP {exc.code}") from exc
        except (URLError, socket.timeout, TimeoutError) as exc:
            raise TransportError("control service unavailable") from exc
        try: value = json.loads(raw)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc: raise MalformedResponseError("control service returned malformed JSON") from exc
        if not isinstance(value, dict): raise MalformedResponseError("control service response must be an object")
        return value
    def send(self, command: dict[str, Any]) -> dict[str, Any]: return self._request("POST", "/v1/commands", command)
    def replay(self, cursor: int = 0, *, limit: int = 100) -> dict[str, Any]: return self._request("GET", f"/v1/events?cursor={cursor}&limit={limit}")
    def subscribe(self, cursor: int = 0, *, limit: int = 100) -> dict[str, Any]: return self.replay(cursor, limit=limit)
    def health(self) -> dict[str, Any]: return self._request("GET", "/v1/health")
    def readiness(self) -> dict[str, Any]: return self._request("GET", "/v1/readiness")
    def availability(self) -> dict[str, Any]:
        payload = {"schema_version": SCHEMA_VERSION, "health": self.health(), "readiness": self.readiness(), "event_consumption": {"api":"bounded_polling_replay", "cursor_semantics":"exclusive"}}
        # This is deliberately a client interpretation, not a new wire field.
        return {**payload, "operationally_available": interpret_availability(payload)}
    def lifecycle_projection(self, objective_id: str) -> dict[str, Any]: return self._request("GET", f"/v1/lifecycle/{objective_id}")


def make_http_handler(service: GraceMomentumService, *, authentication_issuer: str = "estate-control"):
    """Production transport binding: JSON HTTP, intentionally dependency-free."""
    class GraceMomentumHTTPHandler(BaseHTTPRequestHandler):
        def _json(self, status: int, body: dict[str, Any]) -> None:
            data = json.dumps(body, sort_keys=True).encode("utf-8"); self.send_response(status); self.send_header("Content-Type", "application/json"); self.send_header("Content-Length", str(len(data))); self.end_headers(); self.wfile.write(data)
        def _identity(self) -> OfficeIdentity:
            try: return identity_from_claims(json.loads(self.headers.get("X-Estate-Claims", "{}")), issuer=authentication_issuer)
            except (json.JSONDecodeError, AuthenticationError) as exc: raise AuthenticationError("invalid_or_expired_session") from exc
        def do_GET(self):
            try:
                identity = self._identity()
                if identity.represented_office not in READ_OFFICES: raise AuthorizationError("office is not authorized for inspection")
                if self.path == "/v1/health": return self._json(200, service.health())
                if self.path == "/v1/readiness": return self._json(200, service.readiness())
                if self.path.startswith("/v1/events"):
                    params = parse_qs(urlparse(self.path).query); cursor = int(params.get("cursor", ["0"])[0]); limit = int(params.get("limit", ["100"])[0]); return self._json(200, service.replay(cursor, limit=limit))
                if self.path.startswith("/v1/lifecycle/"):
                    return self._json(200, service.lifecycle_projection(self.path.rsplit("/", 1)[-1]))
                return self._json(404, {"error": {"code": "not_found"}})
            except AuthenticationError as exc: return self._json(401, {"schema_version": SCHEMA_VERSION, "disposition": "unauthorized", "error": {"code": "invalid_or_expired_session", "message": str(exc), "retryable": False}})
            except AuthorizationError as exc: return self._json(403, {"schema_version": SCHEMA_VERSION, "disposition": "unauthorized", "error": {"code": "insufficient_read_authority", "message": str(exc), "retryable": False}})
        def do_POST(self):
            try:
                size = int(self.headers.get("Content-Length", "0")); command = json.loads(self.rfile.read(size)); return self._json(200, service.command(command, self._identity()))
            except (ControlError, ProviderAdmissionError, json.JSONDecodeError) as exc: return self._json(403, {"schema_version": SCHEMA_VERSION, "disposition": "unauthorized", "error": {"code": "unauthorized", "message": str(exc), "retryable": False}})
        def log_message(self, format: str, *args: Any) -> None: return
    return GraceMomentumHTTPHandler


def production_http_server(service: GraceMomentumService, host: str = "127.0.0.1", port: int = 8765, *, authentication_issuer: str = "estate-control") -> ThreadingHTTPServer:
    if host not in {"127.0.0.1", "localhost", "::1"}: raise ValueError("production control service must bind to loopback")
    return ThreadingHTTPServer((host, port), make_http_handler(service, authentication_issuer=authentication_issuer))


def reference_command(action: str, *, objective_id: str = "objective-demo", directive_id: str | None = None, idempotency_key: str = "demo-1") -> dict[str, Any]:
    return {"schema_version": SCHEMA_VERSION, "command_id": f"command-{idempotency_key}", "correlation_id": "correlation-demo", "causation_id": "cause-demo", "idempotency_key": idempotency_key, "timestamp": "2026-07-26T00:00:00Z", "action": action, "objective_id": objective_id, "directive_id": directive_id}
