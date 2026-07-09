import pytest
from estate.core.background_operations import BackgroundOperationEvent, BackgroundOperationRequest, default_background_operation_watches


def test_default_watches_include_required_ids():
    ids = {w.watch_id for w in default_background_operation_watches()}
    assert {
        "pending_routing_recommendation_watch",
        "missing_ring2_review_watch",
        "stale_validation_artifact_watch",
        "provider_capacity_warning_watch",
        "worker_assignment_gap_watch",
        "pending_movement_decision_watch",
    } <= ids


def test_event_model_validates_event_type():
    ev = BackgroundOperationEvent.create(event_type="time_tick", source="test", subject_type="system", subject_id="tick", classification="Estate Internal", summary="Tick")
    assert ev.to_dict()["event_type"] == "time_tick"
    ev.event_type = "provider_execution"
    with pytest.raises(ValueError):
        ev.to_dict()


def test_resident_sensitive_request_is_flagged_for_review():
    req = BackgroundOperationRequest.create(
        request_type="staff_update_request",
        source_event_id="boe-test",
        watch_id="watch-test",
        target_role="resident identity reviewer",
        target_subsystem="resident_identity",
        priority="normal",
        classification="Estate Internal",
        summary="Resident persona continuity requires attention",
        requested_action="Review only; do not act autonomously.",
    )
    assert req.requires_human_review is True
    assert req.requires_boundary_review is True
