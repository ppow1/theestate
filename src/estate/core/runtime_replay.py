"""Idempotent replay support for durable Operations Runtime checkpoints."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from estate.core.runtime_recovery import EVENT_LOG, RuntimePersistenceStore, _root, utc_now_iso


@dataclass
class ReplayResult:
    checkpoint_cycle_id: str
    replay_started_at: str
    replayed_events: int = 0
    skipped_completed_side_effects: list[str] = field(default_factory=list)
    reconstructed_state: dict[str, Any] = field(default_factory=dict)
    last_replayed_position: int = -1

    def to_dict(self) -> dict[str, Any]:
        return {
            "checkpoint_cycle_id": self.checkpoint_cycle_id,
            "replay_started_at": self.replay_started_at,
            "replayed_events": self.replayed_events,
            "skipped_completed_side_effects": self.skipped_completed_side_effects,
            "reconstructed_state": self.reconstructed_state,
            "last_replayed_position": self.last_replayed_position,
        }


class RuntimeReplayEngine:
    """Rebuilds mutable runtime state from immutable event/evidence history."""

    def __init__(self, root: Path | None = None) -> None:
        self.root = _root(root)
        self.store = RuntimePersistenceStore(self.root)

    def replay_from_checkpoint(self, cycle_id: str) -> dict[str, Any]:
        checkpoint = self.store.load_checkpoint(cycle_id)
        state = checkpoint["state"]
        result = ReplayResult(checkpoint_cycle_id=cycle_id, replay_started_at=utc_now_iso(), reconstructed_state={k: v for k, v in state.items() if k != "metadata"})
        completed = set(state.get("completed_side_effects") or [])
        start_position = int(state.get("last_durable_event_position") or 0)
        for event in self._iter_events_after(start_position):
            payload = event.get("payload") or {}
            side_effect_id = payload.get("side_effect_id")
            if side_effect_id and side_effect_id in completed:
                result.skipped_completed_side_effects.append(side_effect_id)
                result.last_replayed_position = event.get("position", result.last_replayed_position)
                continue
            self._apply_event(result.reconstructed_state, event)
            result.replayed_events += 1
            result.last_replayed_position = event.get("position", result.last_replayed_position)
        self.store.append_event("checkpoint_replayed", {"cycle_id": cycle_id, "replayed_events": result.replayed_events, "last_replayed_position": result.last_replayed_position})
        return result.to_dict()

    def _iter_events_after(self, position: int):
        path = self.root / EVENT_LOG
        if not path.exists():
            return
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                event = json.loads(line)
                if int(event.get("position", -1)) > position:
                    yield event

    def _apply_event(self, state: dict[str, Any], event: dict[str, Any]) -> None:
        payload = event.get("payload") or {}
        event_type = event.get("event_type")
        if event_type == "lease_released":
            state.setdefault("leases", {}).pop(payload.get("lease_id"), None)
        elif event_type == "claim_requeued":
            claim_id = payload.get("claim_id")
            if claim_id:
                state.setdefault("claims", {}).setdefault(claim_id, {}).update({"status": "retryable"})
        elif event_type == "scheduler_state_updated":
            state["scheduler_state"] = payload.get("scheduler_state", state.get("scheduler_state", {}))
        elif event_type == "campaign_state_updated":
            state["campaign_state"] = payload.get("campaign_state", state.get("campaign_state", {}))
        elif event_type == "audit_state_updated":
            state["admitted_audit_state"] = payload.get("admitted_audit_state", state.get("admitted_audit_state", {}))
        state["last_durable_event_position"] = event.get("position", state.get("last_durable_event_position", 0))
