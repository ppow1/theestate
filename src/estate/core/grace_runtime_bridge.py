"""Read-only authoritative operation bridge for Grace conversational consumers.

The bridge owns no state.  It calls the published LoopbackGraceMomentumClient
and returns a typed envelope so a conversational surface can distinguish facts,
absence, ambiguity, and transport failure without inventing a lifecycle.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from estate.core.grace_momentum_service import MalformedResponseError, LoopbackGraceMomentumClient, TransportError

BRIDGE_SCHEMA = "estate.grace-runtime-bridge.v1"
SOURCE_SYSTEM = "grace-momentum-runtime"
STATUSES = {"AUTHORITATIVE_RESULT", "NO_RECORD", "AMBIGUOUS_CORRELATION", "RUNTIME_UNAVAILABLE", "OPERATION_UNAVAILABLE", "UNAUTHORIZED", "MALFORMED_RUNTIME_RESPONSE", "CONVERSATIONAL_ONLY"}

OPERATIONS = (
    "get_current_objective", "get_objective_by_id", "get_runtime_readiness", "get_runtime_availability",
    "get_lifecycle_projection", "get_replay_cursor", "get_recent_lifecycle_events", "get_provider_admission",
    "get_last_dispatch", "get_last_provider_result", "get_last_reconciliation", "get_last_validation",
    "get_last_grace_receipt", "get_current_blocker", "get_responsible_office", "get_next_lawful_action",
    "list_grace_runtime_operations",
)


class GraceRuntimeBridge:
    """Expose only runtime-backed reads; no command or persistence method exists."""

    def __init__(self, client: Any):
        self.client = client

    @staticmethod
    def _envelope(operation: str, status: str, payload: Any = None, **extra: Any) -> dict[str, Any]:
        body = {"schema_version": BRIDGE_SCHEMA, "status": status, "source_system": SOURCE_SYSTEM,
                "source_operation": operation, "retrieved_at": datetime.now(timezone.utc).isoformat(),
                "payload": payload}
        body.update(extra)
        return body

    def _call(self, operation: str, fn, *, no_record_is_success: bool = False) -> dict[str, Any]:
        try:
            payload = fn()
        except MalformedResponseError as exc:
            return self._envelope(operation, "MALFORMED_RUNTIME_RESPONSE", None, error={"code": "malformed_runtime_response", "message": str(exc)})
        except TransportError as exc:
            message = str(exc)
            status = "UNAUTHORIZED" if "401" in message or "403" in message or "unauthorized" in message.lower() else "RUNTIME_UNAVAILABLE"
            return self._envelope(operation, status, None, error={"code": "runtime_transport", "message": message})
        except (KeyError, TypeError, ValueError) as exc:
            return self._envelope(operation, "MALFORMED_RUNTIME_RESPONSE", None, error={"code": "malformed_runtime_response", "message": str(exc)})
        if not isinstance(payload, dict):
            return self._envelope(operation, "MALFORMED_RUNTIME_RESPONSE", None, error={"code": "response_not_object"})
        if payload.get("disposition") == "unauthorized":
            return self._envelope(operation, "UNAUTHORIZED", None, error=payload.get("error"))
        if not payload:
            return self._envelope(operation, "MALFORMED_RUNTIME_RESPONSE", None, error={"code": "empty_response"})
        return self._envelope(operation, "AUTHORITATIVE_RESULT", payload)

    def list_grace_runtime_operations(self) -> dict[str, Any]:
        return self._envelope("list_grace_runtime_operations", "AUTHORITATIVE_RESULT", {"operations": list(OPERATIONS), "mutations_exposed": False})

    def get_runtime_readiness(self) -> dict[str, Any]: return self._call("get_runtime_readiness", self.client.readiness)
    def get_runtime_availability(self) -> dict[str, Any]: return self._call("get_runtime_availability", self.client.availability)

    def _summary(self, objective_id: str | None = None) -> dict[str, Any]:
        return self.client.query("objective.summary", **({"objective_id": objective_id} if objective_id else {}))

    @staticmethod
    def _objective_ids(summary: dict[str, Any]) -> list[str]:
        ids = []
        completed = {e.get("objective_id") or e.get("payload", {}).get("objective_id") for e in summary.get("events", []) if e.get("event_type") == "objective.completed"}
        for event in summary.get("events", []):
            if event.get("event_type") != "objective.created_or_correlated": continue
            value = event.get("objective_id") or event.get("payload", {}).get("objective_id")
            if isinstance(value, str) and value not in completed and value not in ids: ids.append(value)
        return ids

    def get_current_objective(self) -> dict[str, Any]:
        result = self._call("get_current_objective", self._summary)
        if result["status"] != "AUTHORITATIVE_RESULT": return result
        summary = result["payload"].get("result") if isinstance(result["payload"].get("result"), dict) else result["payload"]
        ids = self._objective_ids(summary)
        if not ids: return self._envelope("get_current_objective", "NO_RECORD", None, reason="no_explicitly_active_objective")
        if len(ids) != 1: return self._envelope("get_current_objective", "AMBIGUOUS_CORRELATION", {"candidate_objective_ids": ids})
        return self.get_objective_by_id(ids[0])

    def get_objective_by_id(self, objective_id: str) -> dict[str, Any]:
        if not isinstance(objective_id, str) or not objective_id.strip(): return self._envelope("get_objective_by_id", "MALFORMED_RUNTIME_RESPONSE", None, error={"code": "objective_id_required"})
        result = self._call("get_objective_by_id", lambda: self.client.lifecycle_projection(objective_id))
        if result["status"] == "AUTHORITATIVE_RESULT" and not result["payload"].get("timeline"):
            return self._envelope("get_objective_by_id", "NO_RECORD", None, objective_id=objective_id)
        return result

    def get_lifecycle_projection(self, objective_id: str) -> dict[str, Any]: return self.get_objective_by_id(objective_id)

    def get_replay_cursor(self) -> dict[str, Any]:
        return self._call("get_replay_cursor", lambda: self.client.replay(0))

    def get_recent_lifecycle_events(self, cursor: int = 0, limit: int = 100) -> dict[str, Any]:
        return self._call("get_recent_lifecycle_events", lambda: self.client.replay(cursor, limit=limit))

    def _record(self, operation: str, query_name: str, objective_id: str | None = None) -> dict[str, Any]:
        result = self._call(operation, lambda: self.client.query(query_name, **({"objective_id": objective_id} if objective_id else {})))
        if result["status"] == "AUTHORITATIVE_RESULT" and result["payload"].get("result") is None:
            return self._envelope(operation, "NO_RECORD", None, objective_id=objective_id)
        return result

    def get_provider_admission(self, objective_id: str | None = None): return self._record("get_provider_admission", "provider_admission.record", objective_id)
    def get_last_provider_result(self, objective_id: str | None = None): return self._record("get_last_provider_result", "provider_result.last", objective_id)
    def get_last_reconciliation(self, objective_id: str | None = None): return self._record("get_last_reconciliation", "reconciliation.last", objective_id)
    def get_last_validation(self, objective_id: str | None = None): return self._record("get_last_validation", "validation.last", objective_id)
    def get_last_grace_receipt(self, objective_id: str | None = None): return self._record("get_last_grace_receipt", "grace_receipt.last", objective_id)
    def get_last_dispatch(self, objective_id: str | None = None): return self._record("get_last_dispatch", "dispatch.state", objective_id)

    def _projection_field(self, operation: str, field: str, objective_id: str) -> dict[str, Any]:
        result = self.get_objective_by_id(objective_id)
        if result["status"] != "AUTHORITATIVE_RESULT": return result
        value = result["payload"].get(field)
        return self._envelope(operation, "NO_RECORD" if value is None else "AUTHORITATIVE_RESULT", value, objective_id=objective_id)

    def get_current_blocker(self, objective_id: str): return self._projection_field("get_current_blocker", "current_blocker", objective_id)
    def get_responsible_office(self, objective_id: str): return self._projection_field("get_responsible_office", "current_responsible_office", objective_id)
    def get_next_lawful_action(self, objective_id: str): return self._projection_field("get_next_lawful_action", "next_lawful_action", objective_id)
