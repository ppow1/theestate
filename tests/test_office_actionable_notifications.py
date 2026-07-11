from __future__ import annotations

import json
from pathlib import Path

from estate.core.office_actionable_notifications import (
    ActionableNotification,
    AUTHORITATIVE_CLOSED,
    BLOCKED,
    LOCAL_ACKNOWLEDGED,
    NotificationEvidence,
    acknowledge,
    assign,
    attention_indicators,
    build_center,
    close_authoritatively,
    open_source,
    refresh,
    route,
    schedule_follow_up,
    snooze,
)


def evidence(**overrides):
    data = {
        "id": "N-1",
        "title": "Delivery failed",
        "source_uri": "collaboration/messages/inbox/N-1.json",
        "created_at": "2026-07-01T00:00:00+00:00",
        "severity": "warning",
        "delivery_status": "failed",
        "delivery_error": "mailbox unavailable",
    }
    data.update(overrides)
    return NotificationEvidence(**data)


def test_build_center_is_deterministic_and_opens_source():
    center = build_center([evidence(id="N-2", created_at="2026-07-02T00:00:00+00:00"), evidence(id="N-1")])
    assert list(center) == ["N-1", "N-2"]
    assert open_source(center["N-1"])["source_uri"] == "collaboration/messages/inbox/N-1.json"


def test_acknowledgement_is_not_authoritative_closure():
    notification = ActionableNotification(evidence=evidence())
    result = acknowledge(notification, steward="Grace")
    assert result["state"] == LOCAL_ACKNOWLEDGED
    assert result["authoritative_closed"] is False
    assert notification.evidence.authoritative_status != AUTHORITATIVE_CLOSED
    assert "not authoritative closure" in result["warning"]


def test_authoritative_closure_requires_source_receipt():
    notification = ActionableNotification(evidence=evidence())
    blocked = close_authoritatively(notification, source_receipt="")
    assert blocked == {"state": BLOCKED, "closed": False, "reason": "missing source receipt"}
    closed = close_authoritatively(notification, source_receipt="source-system:closed:N-1")
    assert closed["closed"] is True
    assert notification.evidence.authoritative_status == AUTHORITATIVE_CLOSED


def test_snooze_assignment_follow_up_and_route_controls():
    notification = ActionableNotification(evidence=evidence())
    assert snooze(notification, "2026-07-20T00:00:00+00:00", "wait for mailbox repair")["snoozed"] is True
    assert assign(notification, "Alfred")["assigned"] is True
    assert schedule_follow_up(notification, "2026-07-21T00:00:00+00:00")["scheduled"] is True
    assert route(notification, "mailbox:0002", "needs owner response")["routed"] is True
    assert notification.assignee == "Alfred"
    assert notification.follow_up_at == "2026-07-21T00:00:00+00:00"
    assert notification.routed_to == "mailbox:0002"


def test_truthful_blocked_states_for_invalid_actions():
    notification = ActionableNotification(evidence=evidence())
    assert assign(notification, " ")["state"] == BLOCKED
    assert snooze(notification, "2026-07-01T00:00:00+00:00", "past")["state"] == BLOCKED
    assert schedule_follow_up(notification, "2026-07-01T00:00:00+00:00")["state"] == BLOCKED
    assert route(notification, "", "missing")["state"] == BLOCKED


def test_aging_delivery_failure_escalation_and_persistence_round_trip(tmp_path: Path):
    notification = ActionableNotification(evidence=evidence())
    indicators = attention_indicators(notification, "2026-07-05T00:00:00+00:00")
    assert indicators["aged"] is True
    assert indicators["escalated"] is True
    assert indicators["delivery_failed"] is True
    assert indicators["delivery_error"] == "mailbox unavailable"

    acknowledge(notification, steward="Grace")
    snapshot_path = tmp_path / "notification.json"
    snapshot_path.write_text(json.dumps(notification.to_snapshot(), sort_keys=True), encoding="utf-8")
    restored = ActionableNotification.from_snapshot(json.loads(snapshot_path.read_text(encoding="utf-8")))
    assert restored.to_snapshot() == notification.to_snapshot()
    assert restored.to_snapshot()["installed_by_wp_0531"] is True


def test_refresh_preserves_local_state_and_updates_evidence():
    notification = ActionableNotification(evidence=evidence(title="Original"))
    assign(notification, "Ingrid")
    refreshed = refresh({"N-1": notification}, [evidence(title="Updated", delivery_status="delivered", delivery_error=None)])
    assert refreshed["N-1"].assignee == "Ingrid"
    assert refreshed["N-1"].evidence.title == "Updated"
    assert refreshed["N-1"].evidence.delivery_status == "delivered"
