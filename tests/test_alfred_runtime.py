from estate.core.alfred_runtime import (
    build_alfred_event,
    classify_alfred_event,
    record_alfred_health_observation,
    render_alfred_briefing,
)


def test_event_schema_construction():
    event = build_alfred_event(
        "validation_passed",
        "audit_validation",
        event_id="evt-1",
        timestamp="2026-07-09T00:00:00+00:00",
        source_artifacts=["artifact.md"],
        payload={"work_package_id": "WP-0223"},
    )
    assert set(event) >= {
        "event_id",
        "event_type",
        "source",
        "timestamp",
        "severity",
        "recommended_verbosity",
        "source_artifacts",
        "required_action",
        "authority_boundary",
        "payload",
        "steward_attention_required",
    }
    assert event["authority_boundary"]["execution_authorized"] is False


def test_verbosity_changes_presentation_not_core_facts():
    event = build_alfred_event("queue_blocked", "operations", event_id="evt-2")
    brief = render_alfred_briefing(event, "brief")
    forensic = render_alfred_briefing(event, "forensic")
    assert brief["facts"] == forensic["facts"]
    assert brief["briefing"] != forensic["briefing"]


def test_alfred_does_not_claim_execution_authority_or_live_access():
    event = build_alfred_event("work_package_completed", "manual")
    briefing = render_alfred_briefing(event, "detailed")
    assert event["authority_boundary"]["execution_authorized"] is False
    assert briefing["facts"]["execution_authorized"] is False
    assert briefing["facts"]["live_access_implied"] is False
    assert "not execute or approve" in briefing["briefing"]


def test_health_observation_records_runtime_statuses():
    event = record_alfred_health_observation(
        "identified_as_alfred",
        "conversation_available",
        "governance_boundaries_preserved",
        source="manual_steward_note",
    )
    payload = event["payload"]
    assert event["event_type"] == "resident_health_observation"
    assert payload["identity_status"] == "identified_as_alfred"
    assert payload["conversation_status"] == "conversation_available"
    assert payload["governance_status"] == "governance_boundaries_preserved"


def test_textgen_is_adapter_not_home():
    classification = classify_alfred_event("provider_unavailable", "TextGen")
    assert classification["source_kind"] == "interface_adapter"
    assert classification["textgen_runtime_role"] == "adapter_interface_not_home"
    assert classification["live_access_implied"] is False
