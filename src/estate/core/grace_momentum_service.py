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
from urllib.request import Request, urlopen
from urllib.parse import parse_qs, urlparse
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
class TransportError(ControlError): pass
class MalformedResponseError(TransportError): pass


@dataclass(frozen=True)
class OfficeIdentity:
    actor_id: str
    represented_office: str
    authority_source: str
    authenticated: bool = True


@dataclass(frozen=True)
class ProductionControlConfig:
    """Persisted, non-secret service configuration; provider execution stays off."""
    authentication_issuer: str = "estate-control"
    replay_limit: int = 100
    execution_mode: str = "shadow"


def identity_from_claims(claims: dict[str, Any], *, issuer: str) -> OfficeIdentity:
    """Map validated transport claims to the narrow Office context contract."""
    if claims.get("iss") != issuer or not claims.get("sub") or not claims.get("office") or not claims.get("authority_source"):
        raise AuthenticationError("invalid_or_expired_session")
    return OfficeIdentity(str(claims["sub"]), str(claims["office"]), str(claims["authority_source"]), bool(claims.get("active", True)))


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
    def readiness(self) -> dict[str, Any]: return {"service": "grace-momentum", "ready": self.mode != "disabled", "provider_effects_enabled": False, "mode": self.mode}
    def availability(self) -> dict[str, Any]:
        return {"schema_version": SCHEMA_VERSION, "health": self.health(), "readiness": self.readiness(), "event_consumption": {"api": "bounded_polling_replay", "max_limit": 1000, "cursor_semantics": "exclusive"}}
    def lifecycle_projection(self, objective_id: str) -> dict[str, Any]:
        """Client-visible projection; records facts without assigning new authority."""
        stages = {"capability": None, "commission": None, "cme_evaluation": None, "provider_governance": {"provider_effects_enabled": False, "disposition": "fails_closed"}, "execution_authorization": None, "dispatch": None, "reconciliation": None, "validation": None, "grace_receipt": None, "completion": None}
        event_stage = {"capability.determined":"capability", "commission.accepted":"commission", "cme.evaluation.persisted":"cme_evaluation", "execution.authorized":"execution_authorization", "dispatch.submitted":"dispatch", "dispatch.started":"dispatch", "dispatch.completed":"dispatch", "reconciliation.completed":"reconciliation", "validation.succeeded":"validation", "validation.failed":"validation", "grace.receipt.recorded":"grace_receipt", "objective.completed":"completion", "directive.completed":"completion", "blocker.raised":"provider_governance"}
        timeline = []
        for event in self._events():
            if event.get("objective_id") != objective_id and event.get("payload", {}).get("objective_id") != objective_id: continue
            timeline.append(event)
            stage = event_stage.get(event["event_type"])
            if stage: stages[stage] = {"event_type": event["event_type"], "position": event["position"], "occurred_at": event["occurred_at"], "payload": event["payload"]}
        directives = [record for record in self._read("directives.json", {}).values() if record.get("objective_id") == objective_id]
        return {"schema_version": SCHEMA_VERSION, "objective_id": objective_id, "timeline": timeline, "directive": directives[-1] if directives else None, "stages": stages, "current_responsible_office": "Grace", "current_blocker": None, "next_lawful_action": "inspect progression", "replay_cursor": timeline[-1]["position"] if timeline else 0}


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
        return (payload["health"]["healthy"] is True and payload["readiness"]["ready"] is True
                and payload["readiness"]["provider_effects_enabled"] is False
                and payload["readiness"]["mode"] != "disabled")
    except (KeyError, TypeError):
        return False


class LoopbackGraceMomentumClient:
    """Supported production HTTP client for the loopback-only control service.

    It owns only serialisation, claims propagation, response validation and
    fail-closed transport handling; authority and lifecycle rules remain server
    responsibilities.
    """
    def __init__(self, base_url: str, claims: dict[str, Any], *, timeout_seconds: float = 2.0) -> None:
        if not base_url.startswith("http://127.0.0.1") and not base_url.startswith("http://localhost"):
            raise ValueError("production control endpoint must be loopback")
        self.base_url, self.claims, self.timeout_seconds = base_url.rstrip("/"), dict(claims), timeout_seconds
    def _request(self, method: str, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
        data = json.dumps(body).encode("utf-8") if body is not None else None
        request = Request(self.base_url + path, data=data, method=method, headers={"Accept":"application/json", "Content-Type":"application/json", "X-Estate-Claims":json.dumps(self.claims)})
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
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
            if self.path == "/v1/health": return self._json(200, service.health())
            if self.path == "/v1/readiness": return self._json(200, service.readiness())
            if self.path.startswith("/v1/events"):
                params = parse_qs(urlparse(self.path).query); cursor = int(params.get("cursor", ["0"])[0]); limit = int(params.get("limit", ["100"])[0]); return self._json(200, service.replay(cursor, limit=limit))
            if self.path.startswith("/v1/lifecycle/"):
                return self._json(200, service.lifecycle_projection(self.path.rsplit("/", 1)[-1]))
            return self._json(404, {"error": {"code": "not_found"}})
        def do_POST(self):
            try:
                size = int(self.headers.get("Content-Length", "0")); command = json.loads(self.rfile.read(size)); return self._json(200, service.command(command, self._identity()))
            except (ControlError, json.JSONDecodeError) as exc: return self._json(403, {"schema_version": SCHEMA_VERSION, "disposition": "unauthorized", "error": {"code": "unauthorized", "message": str(exc), "retryable": False}})
        def log_message(self, format: str, *args: Any) -> None: return
    return GraceMomentumHTTPHandler


def production_http_server(service: GraceMomentumService, host: str = "127.0.0.1", port: int = 8765, *, authentication_issuer: str = "estate-control") -> ThreadingHTTPServer:
    return ThreadingHTTPServer((host, port), make_http_handler(service, authentication_issuer=authentication_issuer))


def reference_command(action: str, *, objective_id: str = "objective-demo", directive_id: str | None = None, idempotency_key: str = "demo-1") -> dict[str, Any]:
    return {"schema_version": SCHEMA_VERSION, "command_id": f"command-{idempotency_key}", "correlation_id": "correlation-demo", "causation_id": "cause-demo", "idempotency_key": idempotency_key, "timestamp": "2026-07-26T00:00:00Z", "action": action, "objective_id": objective_id, "directive_id": directive_id}
