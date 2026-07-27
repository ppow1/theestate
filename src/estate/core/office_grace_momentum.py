"""WP-4231 Estate UI consumer for the merged WP-4229 contract.

Production UI code uses the loopback transport client.  The fake service is
available only through the explicit fixture helper used by contract tests.
"""
from __future__ import annotations

import os
from typing import Any, Protocol
from urllib.parse import quote
from uuid import uuid4

from estate.core.grace_momentum_service import (
    FakeGraceMomentumService,
    GraceMomentumClient,
    LoopbackGraceMomentumClient,
    OfficeIdentity,
    TEST_IDENTITIES,
    reference_command,
)

LAWFUL_ACTIONS = (
    "momentum.authorize", "directive.pause", "directive.resume",
    "directive.stop", "directive.revoke", "directive.supersede",
    "cme.reevaluate", "progression.inspect", "escalation.request",
)
PROJECTION_FIELDS = (
    "objective", "directive", "current_responsible_office", "current_blocker",
    "next_lawful_action", "replay_cursor", "stages",
)
PROJECTION_STAGES = (
    "capability", "commission", "cme_evaluation", "provider_governance",
    "execution_authorization", "dispatch", "reconciliation", "validation",
    "grace_receipt", "completion",
)


class MomentumClient(Protocol):
    def send(self, command: dict[str, Any]) -> dict[str, Any]: ...
    def replay(self, cursor: int = 0, *, limit: int = 100) -> dict[str, Any]: ...
    def subscribe(self, cursor: int = 0, *, limit: int = 100) -> dict[str, Any]: ...
    def availability(self) -> dict[str, Any]: ...
    def lifecycle_projection(self, objective_id: str) -> dict[str, Any]: ...


def canonical_links(objective_id: str, directive_id: str | None, cursor: int, conversation_id: str | None) -> dict[str, str | None]:
    objective = quote(str(objective_id), safe="")
    directive = quote(str(directive_id or ""), safe="")
    conversation = quote(str(conversation_id or ""), safe="")
    return {
        "objective_url": f"/estate/objectives/{objective}",
        "directive_url": f"/estate/directives/{directive}" if directive_id else None,
        "lifecycle_url": f"/estate/objectives/{objective}/lifecycle?cursor={int(cursor)}",
        "conversation_url": (f"/open-webui/conversations/{conversation}?objective_id={objective}&directive_id={directive}"
                             if conversation_id else None),
    }


def _event_key(event: dict[str, Any]) -> tuple[Any, Any]:
    return event.get("event_id"), event.get("position")


def _valid_availability(payload: Any) -> tuple[bool, str]:
    """Apply the v1 availability shape without coercing truthy values."""
    if not isinstance(payload, dict):
        return False, "availability is not an object"
    health = payload.get("health")
    readiness = payload.get("readiness")
    if not isinstance(health, dict) or not isinstance(readiness, dict):
        return False, "availability health/readiness objects are required"
    if type(health.get("healthy")) is not bool:
        return False, "availability health.healthy must be boolean"
    if type(readiness.get("ready")) is not bool:
        return False, "availability readiness.ready must be boolean"
    if "provider_effects_enabled" in readiness and type(readiness["provider_effects_enabled"]) is not bool:
        return False, "availability readiness.provider_effects_enabled must be boolean"
    if readiness.get("provider_effects_enabled") is True:
        return False, "provider effects are enabled"
    if "mode" in readiness and (not isinstance(readiness["mode"], str) or readiness["mode"] == "disabled"):
        return False, "availability readiness.mode is invalid"
    if health["healthy"] is not True or readiness["ready"] is not True:
        return False, "provider is not healthy and ready"
    return True, "ok"


def _valid_projection(payload: Any, objective_id: str) -> tuple[bool, str]:
    """Validate the provider projection before exposing any authoritative state."""
    if not isinstance(payload, dict):
        return False, "lifecycle projection is not an object"
    if payload.get("objective_id") != objective_id or not isinstance(payload.get("objective_id"), str) or not objective_id:
        return False, "lifecycle projection objective identity is invalid"
    if not isinstance(payload.get("timeline"), list):
        return False, "lifecycle projection timeline is invalid"
    for event in payload["timeline"]:
        if not isinstance(event, dict) or not isinstance(event.get("event_id"), str) or not isinstance(event.get("event_type"), str) or type(event.get("position")) is not int:
            return False, "lifecycle projection timeline event is invalid"
    directive = payload.get("directive")
    if directive is not None and (not isinstance(directive, dict) or not isinstance(directive.get("directive_id"), str) or not directive.get("directive_id")):
        return False, "lifecycle projection directive identity is invalid"
    if not isinstance(payload.get("current_responsible_office"), str) or not payload["current_responsible_office"]:
        return False, "lifecycle projection responsible office is invalid"
    if payload.get("current_blocker") is not None and not isinstance(payload["current_blocker"], dict):
        return False, "lifecycle projection blocker state is invalid"
    if not isinstance(payload.get("next_lawful_action"), str) or not payload["next_lawful_action"]:
        return False, "lifecycle projection next lawful action is invalid"
    if type(payload.get("replay_cursor")) is not int or payload["replay_cursor"] < 0:
        return False, "lifecycle projection replay cursor is invalid"
    stages = payload.get("stages")
    if not isinstance(stages, dict) or any(stage not in stages for stage in PROJECTION_STAGES):
        return False, "lifecycle projection stages are incomplete"
    if any(value is not None and not isinstance(value, dict) for value in stages.values()):
        return False, "lifecycle projection stage is invalid"
    return True, "ok"


def _fail_closed_snapshot(objective_id: str, reason: str, *, availability: Any = None) -> dict[str, Any]:
    return {
        "contract": "estate.grace-momentum-client.v1", "transport": "loopback", "available": False,
        "provider_effects_enabled": False, "objective_id": objective_id, "directive_id": None,
        "availability": availability if isinstance(availability, dict) else {},
        "error": {"code": "invalid_provider_state", "message": reason, "retryable": True},
        "projection": {field: None for field in PROJECTION_FIELDS}, "events": [], "cursor": 0,
        "controls": [{"action": action, "availability": "unavailable"} for action in LAWFUL_ACTIONS],
        "links": {}, "recovery": {"lawful_action": "progression.inspect", "arbitrary_rerun": False},
    }


class GraceMomentumEstateUI:
    """Projection/command adapter; lifecycle policy remains provider-owned."""
    def __init__(self, client: MomentumClient) -> None:
        self.client = client

    def snapshot(self, *, objective_id: str = "objective-demo", directive_id: str | None = None,
                 cursor: int = 0, conversation_id: str | None = None) -> dict[str, Any]:
        try:
            availability = self.client.availability()
            valid, reason = _valid_availability(availability)
            if not valid:
                return _fail_closed_snapshot(objective_id, reason, availability=availability)
            validated_available = True
            projection = self.client.lifecycle_projection(objective_id)
            valid, reason = _valid_projection(projection, objective_id)
            if not valid:
                return _fail_closed_snapshot(objective_id, reason, availability=availability)
            replay = self.client.replay(cursor)
            subscription = self.client.subscribe(cursor)
        except Exception as exc:
            return _fail_closed_snapshot(objective_id, "provider unavailable or invalid", availability=locals().get("availability"))
        events: list[dict[str, Any]] = []
        seen: set[tuple[Any, Any]] = set()
        for event in [*(replay.get("events") or []), *(subscription.get("events") or [])]:
            key = _event_key(event)
            if key not in seen:
                seen.add(key)
                events.append(event)
        events.sort(key=lambda event: int(event.get("position", 0)))
        projection_directive = (projection.get("directive") or {}).get("directive_id") if isinstance(projection.get("directive"), dict) else None
        selected_directive = directive_id or projection_directive
        next_cursor = max([cursor, int(replay.get("next_cursor", cursor)), int(subscription.get("next_cursor", cursor))])
        projection_fields = {field: projection.get(field) for field in PROJECTION_FIELDS}
        projection_fields["objective"] = projection.get("objective_id")
        return {
            "contract": "estate.grace-momentum-client.v1",
            "transport": "loopback",
            "provider_effects_enabled": False,
            "available": validated_available,
            "availability": availability,
            "objective_id": objective_id,
            "directive_id": selected_directive,
            "projection": projection_fields,
            "replay": replay,
            "subscription": subscription,
            "cursor": next_cursor,
            "events": events,
            "links": canonical_links(objective_id, selected_directive, next_cursor, conversation_id),
            "controls": [{"action": action, "availability": "provider_authorized" if validated_available else "unavailable"} for action in LAWFUL_ACTIONS],
            "recovery": {"replay": replay, "lawful_action": "progression.inspect", "arbitrary_rerun": False},
        }

    def command(self, action: str, *, objective_id: str, directive_id: str | None = None,
                idempotency_key: str | None = None, **fields: Any) -> dict[str, Any]:
        if action not in LAWFUL_ACTIONS:
            return {"disposition": "blocked", "error": {"code": "unsupported_control", "retryable": False}}
        try:
            availability = self.client.availability()
            valid, reason = _valid_availability(availability)
            if valid:
                projection = self.client.lifecycle_projection(objective_id)
                valid, reason = _valid_projection(projection, objective_id)
            if not valid:
                return {"disposition": "blocked", "error": {"code": "invalid_provider_state", "message": reason, "retryable": True}}
        except Exception:
            return {"disposition": "blocked", "error": {"code": "provider_unavailable", "retryable": True}}
        key = idempotency_key or f"estate-ui-{uuid4().hex}"
        command = reference_command(action, objective_id=objective_id, directive_id=directive_id, idempotency_key=key)
        command.update(fields)
        return self.client.send(command)


def fixture_surface(root: str, identity: OfficeIdentity | None = None) -> GraceMomentumEstateUI:
    """Explicit fake binding for local contract tests only."""
    return GraceMomentumEstateUI(GraceMomentumClient(FakeGraceMomentumService(root), identity or TEST_IDENTITIES["grace"]))


def loopback_surface(*, endpoint: str | None = None, claims: dict[str, Any] | None = None) -> GraceMomentumEstateUI:
    url = endpoint or os.environ.get("ESTATE_GRACE_MOMENTUM_URL", "http://127.0.0.1:8765")
    identity = claims or {"iss": "estate-control", "sub": "estate-ui", "office": "Observer", "authority_source": "estate-ui", "active": True}
    return GraceMomentumEstateUI(LoopbackGraceMomentumClient(url, identity, timeout_seconds=0.25))


def build_grace_momentum_surface(root: str) -> dict[str, Any]:
    del root  # production UI state is never read from the Estate root
    try:
        return loopback_surface().snapshot()
    except Exception as exc:
        return {
            "contract": "estate.grace-momentum-client.v1", "transport": "loopback", "available": False,
            "provider_effects_enabled": False, "error": {"code": "provider_unavailable", "message": str(exc), "retryable": True},
            "projection": {field: None for field in PROJECTION_FIELDS}, "events": [], "cursor": 0,
            "controls": [{"action": action, "availability": "unavailable"} for action in LAWFUL_ACTIONS],
            "links": {}, "recovery": {"lawful_action": "progression.inspect", "arbitrary_rerun": False},
        }
