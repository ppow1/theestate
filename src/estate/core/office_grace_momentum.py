"""WP-4231 Estate UI projection over the public Grace Momentum client contract.

This module deliberately contains no persistence access or lifecycle policy.  It
is a consumer of ``GraceMomentumClient`` only; the fixture factory is retained
solely until network transport binding is installed by the integration lane.
"""
from __future__ import annotations

from typing import Any
from urllib.parse import quote
from uuid import uuid4

from estate.core.grace_momentum_service import (
    FakeGraceMomentumService,
    GraceMomentumClient,
    OfficeIdentity,
    TEST_IDENTITIES,
    reference_command,
)

QUERY_NAMES = (
    "objective.summary", "lifecycle.timeline", "responsibility.current",
    "blocker.current", "action.next_lawful", "directive.state",
    "capability.state", "commission.state", "provider_governance.state",
    "dispatch.state", "validation.state", "replay.state", "audit.trail",
)
LAWFUL_ACTIONS = (
    "momentum.authorize", "directive.pause", "directive.resume",
    "directive.stop", "directive.revoke", "directive.supersede",
    "cme.reevaluate", "progression.inspect", "escalation.request",
)


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


class GraceMomentumEstateUI:
    """Read-model and command adapter shared by existing Estate UI panels."""
    def __init__(self, client: GraceMomentumClient) -> None:
        self.client = client

    def snapshot(self, *, objective_id: str = "objective-demo", directive_id: str | None = "gmd-demo", cursor: int = 0, conversation_id: str | None = None) -> dict[str, Any]:
        queries = {name: self.client.query(name, objective_id=objective_id, directive_id=directive_id) for name in QUERY_NAMES}
        # The v1 client does not expose a subscription method.  The lifecycle
        # query is therefore the only permitted event projection until that
        # client method is published; do not reach through to service storage.
        lifecycle = queries["lifecycle.timeline"].get("result") or {}
        all_events = list(lifecycle.get("events") or [])
        events = [event for event in all_events if int(event.get("position", 0)) > cursor]
        next_cursor = events[-1].get("position", cursor) if events else cursor
        blockers = [event for event in events if event.get("event_type") == "blocker.raised"]
        return {
            "contract": "estate.grace-momentum-client.v1", "transport_binding": "deferred",
            "objective_id": objective_id, "directive_id": directive_id, "cursor": next_cursor,
            "queries": queries, "events": events, "blockers": blockers,
            "links": canonical_links(objective_id, directive_id, next_cursor, conversation_id),
            "controls": [{"action": action, "availability": "server_authority_checked_on_submit"} for action in LAWFUL_ACTIONS],
            "recovery": {"query": "replay.state", "lawful_action": "progression.inspect", "arbitrary_rerun": False},
        }

    def command(self, action: str, *, objective_id: str, directive_id: str | None = None, idempotency_key: str | None = None, **fields: Any) -> dict[str, Any]:
        if action not in LAWFUL_ACTIONS:
            return {"disposition": "blocked", "error": {"code": "unsupported_control", "retryable": False}}
        key = idempotency_key or f"estate-ui-{uuid4().hex}"
        command = reference_command(action, objective_id=objective_id, directive_id=directive_id, idempotency_key=key)
        command.update(fields)
        return self.client.send(command)


def fixture_surface(root: str, identity: OfficeIdentity | None = None) -> GraceMomentumEstateUI:
    """Temporary client binding for local/browser tests; no network transport."""
    return GraceMomentumEstateUI(GraceMomentumClient(FakeGraceMomentumService(root), identity or TEST_IDENTITIES["grace"]))


def build_grace_momentum_surface(root: str) -> dict[str, Any]:
    return fixture_surface(root).snapshot()
