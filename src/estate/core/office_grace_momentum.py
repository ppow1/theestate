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
    TransportError,
    interpret_availability,
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


class GraceMomentumEstateUI:
    """Projection/command adapter; lifecycle policy remains provider-owned."""
    def __init__(self, client: MomentumClient) -> None:
        self.client = client

    def snapshot(self, *, objective_id: str = "objective-demo", directive_id: str | None = None,
                 cursor: int = 0, conversation_id: str | None = None) -> dict[str, Any]:
        availability = self.client.availability()
        projection = self.client.lifecycle_projection(objective_id)
        replay = self.client.replay(cursor)
        subscription = self.client.subscribe(cursor)
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
        # The provider projection identifies the objective by objective_id; expose
        # that canonical identifier in the UI's objective field without deriving
        # any lifecycle state locally.
        projection_fields["objective"] = projection_fields["objective"] or projection.get("objective_id") or objective_id
        projection_fields["replay_cursor"] = projection_fields["replay_cursor"] if projection_fields["replay_cursor"] is not None else next_cursor
        return {
            "contract": "estate.grace-momentum-client.v1",
            "transport": "loopback",
            "provider_effects_enabled": False,
            "available": bool(availability.get("operationally_available", interpret_availability(availability))),
            "availability": availability,
            "objective_id": objective_id,
            "directive_id": selected_directive,
            "projection": projection_fields,
            "replay": replay,
            "subscription": subscription,
            "cursor": next_cursor,
            "events": events,
            "links": canonical_links(objective_id, selected_directive, next_cursor, conversation_id),
            "controls": [{"action": action, "availability": "provider_authorized" if bool(availability.get("operationally_available")) else "unavailable"} for action in LAWFUL_ACTIONS],
            "recovery": {"replay": replay, "lawful_action": "progression.inspect", "arbitrary_rerun": False},
        }

    def command(self, action: str, *, objective_id: str, directive_id: str | None = None,
                idempotency_key: str | None = None, **fields: Any) -> dict[str, Any]:
        if action not in LAWFUL_ACTIONS:
            return {"disposition": "blocked", "error": {"code": "unsupported_control", "retryable": False}}
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
