from __future__ import annotations

from estate.core.office_resident_presence import (
    ATTENTION_REQUIRED,
    BLOCKED,
    EvidenceReference,
    ResidentPresenceInput,
    build_presence_card,
    build_presence_surface,
    filter_presence,
    open_drill_down,
)


def evidence(**overrides):
    data = {
        "id": "EV-1",
        "title": "Duty log",
        "uri": "operations/alfred/duty_summary.md",
        "observed_at": "2026-07-10T09:00:00+00:00",
        "supports": "active assignment and last completed duty",
    }
    data.update(overrides)
    return EvidenceReference(**data)


def resident(**overrides):
    data = {
        "resident_id": "alfred",
        "resident_name": "Alfred",
        "office": "Estate Engineering",
        "duty_state": "on_duty",
        "status": "active",
        "updated_at": "2026-07-10T09:30:00+00:00",
        "active_assignment": "Repair mailbox adapter",
        "last_completed_duty": "Validated conversation routing",
        "blocker": None,
        "attention_required": False,
        "assignment_uri": "operations/boards/active_work.md#mailbox-adapter",
        "conversation_uri": "operations/alfred/operational_briefing.md",
        "mailbox_uri": "operations/mailboxes/synchronization_duty.md",
        "work_package_uri": "collaboration/work_packages/pending/WP-0525_PARALLEL_STAGED_Resident_Presence_and_Operational_Activity.md",
        "evidence": (evidence(),),
    }
    data.update(overrides)
    return ResidentPresenceInput(**data)


def test_truthful_presence_card_uses_only_supplied_activity_and_evidence():
    card = build_presence_card(resident(), as_of="2026-07-10T10:00:00+00:00")
    assert card["active_assignment"] == "Repair mailbox adapter"
    assert card["last_completed_duty"] == "Validated conversation routing"
    assert card["evidence"][0]["uri"] == "operations/alfred/duty_summary.md"
    assert card["truthfulness_guardrails"]["fabricated_activity"] is False
    assert card["truthfulness_guardrails"]["hidden_monitoring"] is False
    assert card["truthfulness_guardrails"]["authority_expansion"] is False


def test_stale_data_sets_freshness_and_attention_indicator():
    card = build_presence_card(resident(updated_at="2026-07-10T07:00:00+00:00"), as_of="2026-07-10T10:00:00+00:00", stale_after_minutes=60)
    assert card["freshness"]["stale"] is True
    assert card["attention_required"] is True
    assert "presence stale" in card["attention_reasons"]


def test_drill_down_links_cover_assignments_conversations_mailboxes_work_packages_and_missing_links():
    card = build_presence_card(resident(), as_of="2026-07-10T10:00:00+00:00")
    assert open_drill_down(card, "assignment")["uri"] == "operations/boards/active_work.md#mailbox-adapter"
    assert open_drill_down(card, "conversation")["openable"] is True
    assert open_drill_down(card, "mailbox")["openable"] is True
    assert open_drill_down(card, "work_package")["openable"] is True
    assert open_drill_down(card, "evidence")["openable"] is False


def test_filter_by_resident_office_status_and_attention_state():
    records = [
        resident(),
        resident(resident_id="helen", resident_name="Helen", office="Household", status="available", active_assignment=None),
        resident(resident_id="ingrid", resident_name="Ingrid", office="Estate Engineering", blocker="Waiting for source receipt"),
    ]
    cards = build_presence_surface(records, as_of="2026-07-10T10:00:00+00:00")
    assert [card["resident_id"] for card in filter_presence(cards, resident="hel")] == ["helen"]
    assert {card["resident_id"] for card in filter_presence(cards, office="Estate Engineering")} == {"alfred", "ingrid"}
    assert [card["resident_id"] for card in filter_presence(cards, status=BLOCKED)] == ["ingrid"]
    assert [card["resident_id"] for card in filter_presence(cards, attention_state=True)] == ["ingrid"]


def test_missing_evidence_is_visible_and_never_filled_with_fake_activity():
    card = build_presence_card(resident(evidence=(), active_assignment=None, last_completed_duty=None, attention_required=True), as_of="2026-07-10T10:00:00+00:00")
    assert card["missing_evidence"] is True
    assert "missing supporting evidence" in card["attention_reasons"]
    assert card["active_assignment"] is None
    assert card["last_completed_duty"] is None
    assert card["status"] == ATTENTION_REQUIRED


def test_blocker_takes_precedence_over_attention_status():
    card = build_presence_card(resident(blocker="Mailbox source unreachable", attention_required=True), as_of="2026-07-10T10:00:00+00:00")
    assert card["status"] == BLOCKED
    assert "blocker present" in card["attention_reasons"]
