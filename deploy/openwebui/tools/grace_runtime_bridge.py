"""
title: Grace authoritative runtime bridge
id: grace_runtime_bridge
version: 1.0.0
description: Read-only Grace Momentum runtime operations. Every operational fact is returned from the authenticated loopback runtime.
"""
from __future__ import annotations

import json
import os
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import HTTPRedirectHandler, Request, build_opener

from pydantic import BaseModel, Field


class Valves(BaseModel):
    runtime_url: str = Field(default="http://127.0.0.1:8766")
    authentication_issuer: str = Field(default="estate-control")
    timeout_seconds: float = Field(default=2.0, ge=0.1, le=10.0)
    office: str = Field(default="Grace")
    authority_source: str = Field(default="openwebui/grace-runtime-bridge")


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, new):
        raise RuntimeError("redirects are not permitted")


class Tools:
    """Open WebUI Tool API. This class contains reads only; no command endpoint is callable."""

    valves = Valves()

    def _claims(self, __user__: dict | None) -> dict:
        user = __user__ if isinstance(__user__, dict) else {}
        subject = user.get("id") or user.get("email")
        if not isinstance(subject, str) or not subject:
            raise RuntimeError("UNAUTHORIZED: authenticated Open WebUI subject is unavailable")
        return {"iss": self.valves.authentication_issuer, "sub": subject, "office": self.valves.office,
                "authority_source": self.valves.authority_source, "active": True}

    def _request(self, path: str, __user__: dict | None = None) -> dict:
        from urllib.parse import urlparse
        parsed = urlparse(self.valves.runtime_url)
        if parsed.scheme != "http" or parsed.username or parsed.password or parsed.hostname not in {"127.0.0.1", "localhost", "::1"} or parsed.query or parsed.fragment:
            return {"schema_version": "estate.grace-runtime-bridge.v1", "status": "RUNTIME_UNAVAILABLE", "error": {"code": "non_loopback_runtime"}}
        request = Request(self.valves.runtime_url.rstrip("/") + path, method="GET", headers={"Accept": "application/json", "X-Estate-Claims": json.dumps(self._claims(__user__))})
        try:
            with build_opener(_NoRedirect()).open(request, timeout=self.valves.timeout_seconds) as response:
                if response.status < 200 or response.status >= 300:
                    status = "UNAUTHORIZED" if response.status in (401, 403) else "RUNTIME_UNAVAILABLE"
                    return {"schema_version": "estate.grace-runtime-bridge.v1", "status": status, "error": {"code": f"http_{response.status}"}}
                value = json.loads(response.read())
                if not isinstance(value, dict): raise ValueError("response is not an object")
                return value
        except HTTPError as exc:
            return {"schema_version": "estate.grace-runtime-bridge.v1", "status": "UNAUTHORIZED" if exc.code in (401, 403) else "RUNTIME_UNAVAILABLE", "error": {"code": f"http_{exc.code}"}}
        except json.JSONDecodeError as exc:
            return {"schema_version": "estate.grace-runtime-bridge.v1", "status": "MALFORMED_RUNTIME_RESPONSE", "error": {"code": "malformed_runtime_response", "message": str(exc)}}
        except (URLError, TimeoutError, OSError, ValueError, RuntimeError) as exc:
            return {"schema_version": "estate.grace-runtime-bridge.v1", "status": "RUNTIME_UNAVAILABLE", "error": {"code": "runtime_unavailable", "message": str(exc)}}

    def _query(self, operation: str, name: str, __user__: dict | None = None, **filters) -> dict:
        value = self._request("/v1/query?" + urlencode({"name": name, **{k: v for k, v in filters.items() if v is not None}}), __user__)
        if "status" in value: return value
        if not isinstance(value.get("result"), (dict, list, str, int, float, type(None))):
            return {"schema_version": "estate.grace-runtime-bridge.v1", "status": "MALFORMED_RUNTIME_RESPONSE", "source_operation": operation, "error": {"code": "missing_result"}}
        return {"schema_version": "estate.grace-runtime-bridge.v1", "status": "AUTHORITATIVE_RESULT", "source_system": "grace-momentum-runtime", "source_operation": operation, "payload": value, "raw": value}

    def _authoritative(self, operation: str, value: dict) -> dict:
        if "status" in value and value.get("schema_version") == "estate.grace-runtime-bridge.v1":
            return value
        if not isinstance(value, dict):
            return {"schema_version": "estate.grace-runtime-bridge.v1", "status": "MALFORMED_RUNTIME_RESPONSE", "source_operation": operation, "error": {"code": "response_not_object"}}
        return {"schema_version": "estate.grace-runtime-bridge.v1", "status": "AUTHORITATIVE_RESULT", "source_system": "grace-momentum-runtime", "source_operation": operation, "payload": value, "raw": value}

    def list_grace_runtime_operations(self, __user__: dict | None = None) -> dict:
        """List exact registered authoritative read operations. No mutations are exposed."""
        return {"schema_version": "estate.grace-runtime-bridge.v1", "status": "AUTHORITATIVE_RESULT", "source_system": "openwebui/grace-runtime-bridge", "operations": ["get_current_objective", "get_objective_by_id", "get_runtime_readiness", "get_runtime_availability", "get_lifecycle_projection", "get_replay_cursor", "get_recent_lifecycle_events", "get_provider_admission", "get_last_dispatch", "get_last_provider_result", "get_last_reconciliation", "get_last_validation", "get_last_grace_receipt", "get_current_blocker", "get_responsible_office", "get_next_lawful_action", "get_assignment_record", "get_execution_progress", "get_execution_completion", "get_execution_failure", "get_execution_artifact", "list_grace_runtime_operations"], "mutations_exposed": False}

    def get_runtime_readiness(self, __user__: dict | None = None) -> dict:
        """Return the current readiness payload verbatim from Grace Momentum."""
        return self._authoritative("get_runtime_readiness", self._request("/v1/readiness", __user__))

    def get_assignment_record(self, assignment_id: str | None = None, __user__: dict | None = None) -> dict:
        return self._query("get_assignment_record", "assignment.record", __user__, assignment_id=assignment_id)

    def get_execution_progress(self, assignment_id: str | None = None, __user__: dict | None = None) -> dict:
        return self._query("get_execution_progress", "execution.progress", __user__, assignment_id=assignment_id)

    def get_execution_completion(self, objective_id: str | None = None, __user__: dict | None = None) -> dict:
        return self._query("get_execution_completion", "execution.completion", __user__, objective_id=objective_id)

    def get_execution_failure(self, assignment_id: str | None = None, __user__: dict | None = None) -> dict:
        return self._query("get_execution_failure", "execution.failure", __user__, assignment_id=assignment_id)

    def get_execution_artifact(self, dispatch_id: str | None = None, __user__: dict | None = None) -> dict:
        return self._query("get_execution_artifact", "execution.artifact", __user__, dispatch_id=dispatch_id)

    def get_runtime_availability(self, __user__: dict | None = None) -> dict:
        """Return the current health/readiness availability payload verbatim."""
        health = self._request("/v1/health", __user__); readiness = self._request("/v1/readiness", __user__)
        if health.get("status") or readiness.get("status"):
            return health if health.get("status") else readiness
        return self._authoritative("get_runtime_availability", {"health": health, "readiness": readiness})

    def get_objective_by_id(self, objective_id: str, __user__: dict | None = None) -> dict:
        """Return one persisted objective projection; never infer missing stages."""
        return self._authoritative("get_objective_by_id", self._request("/v1/lifecycle/" + quote(objective_id, safe=""), __user__))

    def get_current_objective(self, __user__: dict | None = None) -> dict:
        """Select only one explicit nonterminal objective; ambiguity is returned, never guessed."""
        summary = self._query("get_current_objective", "objective.summary", __user__)
        if summary.get("status") != "AUTHORITATIVE_RESULT": return summary
        events = summary.get("payload", {}).get("result", {}).get("events", [])
        completed = {e.get("objective_id") or e.get("payload", {}).get("objective_id") for e in events if e.get("event_type") == "objective.completed"}
        ids = []
        for event in events:
            if event.get("event_type") == "objective.created_or_correlated":
                oid = event.get("objective_id") or event.get("payload", {}).get("objective_id")
                if isinstance(oid, str) and oid not in completed and oid not in ids: ids.append(oid)
        if not ids: return {"schema_version": "estate.grace-runtime-bridge.v1", "status": "NO_RECORD", "reason": "no_explicitly_active_objective"}
        if len(ids) != 1: return {"schema_version": "estate.grace-runtime-bridge.v1", "status": "AMBIGUOUS_CORRELATION", "candidate_objective_ids": ids}
        return self.get_objective_by_id(ids[0], __user__)

    def get_lifecycle_projection(self, objective_id: str, __user__: dict | None = None) -> dict: return self.get_objective_by_id(objective_id, __user__)
    def get_replay_cursor(self, __user__: dict | None = None) -> dict: return self._authoritative("get_replay_cursor", self._request("/v1/events?cursor=0&limit=1000", __user__))
    def get_recent_lifecycle_events(self, cursor: int = 0, limit: int = 100, __user__: dict | None = None) -> dict: return self._authoritative("get_recent_lifecycle_events", self._request("/v1/events?" + urlencode({"cursor": cursor, "limit": limit}), __user__))

    def _record(self, operation: str, name: str, objective_id: str | None = None, __user__: dict | None = None) -> dict:
        result = self._query(operation, name, __user__, objective_id=objective_id)
        if result.get("status") == "AUTHORITATIVE_RESULT" and result.get("payload", {}).get("result") is None:
            return {"schema_version": "estate.grace-runtime-bridge.v1", "status": "NO_RECORD", "source_system": "grace-momentum-runtime", "source_operation": operation, "payload": None, "raw": None, "objective_id": objective_id}
        return result

    def get_provider_admission(self, objective_id: str | None = None, __user__: dict | None = None): return self._record("get_provider_admission", "provider_admission.record", objective_id, __user__)
    def get_last_dispatch(self, objective_id: str | None = None, __user__: dict | None = None): return self._record("get_last_dispatch", "dispatch.state", objective_id, __user__)
    def get_last_provider_result(self, objective_id: str | None = None, __user__: dict | None = None): return self._record("get_last_provider_result", "provider_result.last", objective_id, __user__)
    def get_last_reconciliation(self, objective_id: str | None = None, __user__: dict | None = None): return self._record("get_last_reconciliation", "reconciliation.last", objective_id, __user__)
    def get_last_validation(self, objective_id: str | None = None, __user__: dict | None = None): return self._record("get_last_validation", "validation.last", objective_id, __user__)
    def get_last_grace_receipt(self, objective_id: str | None = None, __user__: dict | None = None): return self._record("get_last_grace_receipt", "grace_receipt.last", objective_id, __user__)

    def _projection_field(self, field: str, objective_id: str, __user__: dict | None = None) -> dict:
        projection = self.get_objective_by_id(objective_id, __user__)
        if projection.get("status") in {"NO_RECORD", "RUNTIME_UNAVAILABLE", "UNAUTHORIZED"}: return projection
        value = projection.get(field)
        return {"schema_version": "estate.grace-runtime-bridge.v1", "status": "NO_RECORD" if value is None else "AUTHORITATIVE_RESULT", "source_system": "grace-momentum-runtime", "payload": value, "raw": value}

    def get_current_blocker(self, objective_id: str, __user__: dict | None = None): return self._projection_field("current_blocker", objective_id, __user__)
    def get_responsible_office(self, objective_id: str, __user__: dict | None = None): return self._projection_field("current_responsible_office", objective_id, __user__)
    def get_next_lawful_action(self, objective_id: str, __user__: dict | None = None): return self._projection_field("next_lawful_action", objective_id, __user__)
