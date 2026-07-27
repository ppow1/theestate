"""Open WebUI consumer adapter for the published Grace Momentum contract.

This module owns only conversational correlation and delivery checkpoints.  It
never reads or writes Grace runtime persistence and never invokes a provider.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from estate.core.grace_momentum_service import GraceMomentumClient, reference_command

MUTATIONS = {
    "approve": "momentum.authorize",
    "pause": "directive.pause",
    "resume": "directive.resume",
    "stop": "directive.stop",
    "revoke": "directive.revoke",
}


@dataclass
class GraceConversationCorrelation:
    conversation_id: str
    message_id: str
    objective_id: str | None = None
    directive_id: str | None = None
    commission_id: str | None = None
    evaluation_id: str | None = None
    approval_state: str = "not_requested"
    completion_receipt_id: str | None = None

    def links(self) -> dict[str, str]:
        links = {
            "conversation": f"/open-webui/conversations/{self.conversation_id}?objective_id={self.objective_id or ''}&directive_id={self.directive_id or ''}"
        }
        if self.objective_id:
            links["objective"] = f"/estate/objectives/{self.objective_id}"
            links["lifecycle"] = f"/estate/objectives/{self.objective_id}/lifecycle?cursor=0"
        if self.directive_id:
            links["directive"] = f"/estate/directives/{self.directive_id}"
        return links


class _DeliveryCheckpoint:
    """Consumer-owned minimal replay state, separate from Grace persistence."""

    def __init__(self, root: str | Path, correlation: GraceConversationCorrelation) -> None:
        self.path = Path(root) / f"{correlation.conversation_id}.json"
        self.state = {"cursor": 0, "delivered_event_ids": [], "conversation_id": correlation.conversation_id,
                      "objective_id": correlation.objective_id, "directive_id": correlation.directive_id}
        if self.path.exists():
            try:
                loaded = json.loads(self.path.read_text(encoding="utf-8"))
                if isinstance(loaded, dict) and isinstance(loaded.get("delivered_event_ids", []), list):
                    self.state.update(loaded)
            except (OSError, ValueError, TypeError):
                # Corrupt consumer state must not manufacture progress.
                self.state["corrupt"] = True

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.state, indent=2, sort_keys=True) + "\n", encoding="utf-8")


class OpenWebUIGraceOperations:
    def __init__(self, client: GraceMomentumClient, *, state_root: str | Path | None = None) -> None:
        self.client = client
        self.state_root = Path(state_root) if state_root is not None else Path("runtime/openwebui/grace_momentum")
        self.delivered: set[str] = set()

    def route(self, text: str, correlation: GraceConversationCorrelation, *, approved: bool = False) -> dict[str, Any]:
        lower = text.lower().strip()
        action = next((value for key, value in MUTATIONS.items() if lower == key or lower.startswith(key + " ")), None)
        if not action:
            kind = "inspection" if "inspect" in lower else "discussion"
            return {"kind": kind, "correlation": asdict(correlation), "links": correlation.links(),
                    "message": "Discussion does not create operational work." if kind == "discussion" else "Inspection is read-only."}
        if not approved:
            return {"kind": "approval_required", "requested_action": action, "correlation": asdict(correlation), "links": correlation.links()}
        command = reference_command(action, objective_id=correlation.objective_id or "", directive_id=correlation.directive_id,
                                    idempotency_key=f"{correlation.conversation_id}:{correlation.message_id}:{action}")
        try:
            result = self.client.send(command)
        except Exception as exc:  # transport clients fail closed at this seam
            return {"kind": "unavailable", "error": {"code": "service_unavailable", "message": str(exc)}, "links": correlation.links()}
        return {"kind": "command", "action": action, "result": result, "correlation": asdict(correlation), "links": correlation.links()}

    def deliver(self, event: dict[str, Any], correlation: GraceConversationCorrelation) -> dict[str, Any] | None:
        if not isinstance(event, dict) or not {"event_id", "event_type", "payload", "position"} <= event.keys():
            return {"kind": "malformed_event", "links": correlation.links()}
        event_id = event["event_id"]
        if not isinstance(event_id, str) or event_id in self.delivered:
            return None
        if not isinstance(event["payload"], dict):
            return {"kind": "malformed_event", "links": correlation.links()}
        self.delivered.add(event_id)
        payload = event["payload"]
        if event["event_type"] == "grace.receipt.recorded":
            correlation.completion_receipt_id = payload.get("receipt_id")
        return {"kind": "canonical_progress", "event_type": event["event_type"], "payload": payload,
                "correlation": asdict(correlation), "links": correlation.links()}

    @staticmethod
    def _available(payload: Any) -> bool:
        if not isinstance(payload, dict):
            return False
        health, readiness = payload.get("health"), payload.get("readiness")
        if not (isinstance(health, dict) and health.get("healthy") is True and
                isinstance(readiness, dict) and readiness.get("ready") is True):
            return False
        if readiness.get("provider_effects_enabled") is True:
            return (readiness.get("governed_local_execution_enabled") is True and
                    readiness.get("local_only") is True and readiness.get("egress_disabled") is True and
                    readiness.get("spend_disabled") is True and readiness.get("mode") == "governed_local_test")
        return readiness.get("provider_effects_enabled") is False and readiness.get("mode") != "disabled"

    def refresh(self, correlation: GraceConversationCorrelation, cursor: int | None = None) -> dict[str, Any]:
        checkpoint = _DeliveryCheckpoint(self.state_root, correlation)
        if checkpoint.state.get("corrupt"):
            return {"kind": "unavailable", "reason": "consumer_checkpoint_malformed", "links": correlation.links()}
        self.delivered.update(item for item in checkpoint.state.get("delivered_event_ids", []) if isinstance(item, str))
        start = checkpoint.state["cursor"] if cursor is None else cursor
        try:
            availability = self.client.availability()
            if not self._available(availability):
                return {"kind": "unavailable", "availability": availability, "links": correlation.links()}
            projection = self.client.lifecycle_projection(correlation.objective_id or "")
            replay = self.client.replay(start)
        except Exception as exc:
            return {"kind": "unavailable", "error": {"code": "service_unavailable", "message": str(exc)}, "links": correlation.links()}
        if not isinstance(replay, dict) or not isinstance(replay.get("events"), list):
            return {"kind": "unavailable", "reason": "malformed_replay", "links": correlation.links()}
        delivered = [item for event in replay["events"] if (item := self.deliver(event, correlation))]
        next_cursor = replay.get("next_cursor", start)
        if not isinstance(next_cursor, int) or next_cursor < start:
            return {"kind": "unavailable", "reason": "malformed_replay_cursor", "links": correlation.links()}
        checkpoint.state.update({"cursor": next_cursor, "delivered_event_ids": sorted(self.delivered)})
        checkpoint.save()
        return {"kind": "refresh", "availability": availability, "projection": projection, "cursor": next_cursor,
                "events": delivered, "links": correlation.links()}
