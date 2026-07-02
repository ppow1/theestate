from estate.core.notification_router import route_notification_events


def _event(**overrides):
    event = {
        "id": "evt-1",
        "source": "alfred",
        "event_type": "recall_candidate",
        "requested_by": "alfred",
        "alfred_validated": True,
        "triggering_artifact": "docs/example.md",
        "blocked_decision": "Steward-only decision required.",
        "steward_only_rationale": "Existing authority is insufficient.",
        "options_or_recommended_next_action": "Recall Steward for decision.",
        "consequence_of_waiting": "Affected decision path remains paused.",
        "continuity_assessment": "Unrelated work may continue.",
        "supporting_references": ["docs/example.md"],
    }
    event.update(overrides)
    return event


def _route_one(event):
    return route_notification_events([event], write=False)["notifications"][0]


def test_constitutional_recall_event_routes_as_recall():
    notification = _route_one(_event(recall_reason="constitutional"))

    assert notification["class"] == "recall"
    assert notification["eligible_for_immediate_delivery"] is True
    assert notification["audit"]["primary_recall_reason"] == "constitutional"


def test_architectural_decision_request_routes_as_recall_when_policy_indicates_it():
    notification = _route_one(_event(recall_reason="architectural", event_type="architectural_decision_request"))

    assert notification["class"] == "recall"
    assert notification["action"] == "prepare_recall_delivery"


def test_successful_codex_run_routes_as_informational():
    notification = _route_one(_event(event_type="successful_codex_run", status="success", recall_reason="operational"))

    assert notification["class"] == "informational"
    assert notification["eligible_for_immediate_delivery"] is False
    assert notification["action"] == "defer_to_briefing"


def test_normal_mailbox_update_routes_as_informational():
    notification = _route_one(_event(event_type="normal_mailbox_update", recall_reason=None, requested_by="ca3"))

    assert notification["class"] == "informational"
    assert notification["priority"] == "normal"


def test_router_output_does_not_contain_gotify_specific_fields():
    report = route_notification_events([
        _event(recall_reason="security", evidence={"gotify_token": "secret", "supporting_references": ["audit.json"]})
    ], write=False)

    serialized = str(report).lower()
    assert "gotify" not in serialized
