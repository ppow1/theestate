import pytest

from estate.core.orchestrator_scheduler import OrchestratorScheduleRecord, determine_schedule_outcome


def intake(**overrides):
    data = {
        "intake_id": "intake-1",
        "state": "approved",
        "classification": "Estate Internal",
        "priority": "normal",
        "source": "manual",
        "summary": "Safe schedule summary.",
        "metadata": {"summary_safe": True},
        "validation_required": True,
    }
    data.update(overrides)
    return data


def test_schedule_record_model_validates_required_fields():
    record = OrchestratorScheduleRecord.create(intake=intake(), state="scheduled", scheduled_by="tests")
    data = record.to_dict()
    assert data["schedule_id"].startswith("sch-")
    assert data["state"] == "scheduled"
    assert data["validation_required"] is True


def test_missing_intake_blocks():
    state, reason = determine_schedule_outcome(None)
    assert state == "blocked"
    assert "missing" in reason


@pytest.mark.parametrize("bad_state", ["rejected", "needs_revision"])
def test_rejected_or_needs_revision_intake_blocks(bad_state):
    state, reason = determine_schedule_outcome(intake(state=bad_state))
    assert state == "blocked"
    assert bad_state in reason


def test_approval_required_when_not_approved():
    state, reason = determine_schedule_outcome(intake(state="pending", metadata={}))
    assert state == "blocked"
    assert "Approval" in reason


def test_restricted_without_boundary_review_blocks():
    state, reason = determine_schedule_outcome(intake(classification="Restricted", boundary_review_required=True))
    assert state == "blocked"
    assert "Boundary review" in reason


def test_explicit_defer_creates_deferred_outcome():
    state, reason = determine_schedule_outcome(intake(), explicit_defer=True)
    assert state == "deferred"
    assert "explicitly" in reason


def test_invalid_classification_blocks_when_eligible_marker_present():
    state, reason = determine_schedule_outcome(intake(classification="Secret", metadata={"schedule_eligible": True}))
    assert state == "blocked"
    assert "Classification" in reason


def test_work_package_missing_path_blocks():
    state, reason = determine_schedule_outcome(intake(source="work_package", work_package_path=None))
    assert state == "blocked"
    assert "Work package path" in reason


def test_obvious_path_conflict_blocks():
    state, reason = determine_schedule_outcome(intake(allowed_paths=["src"], forbidden_paths=["src"]))
    assert state == "blocked"
    assert "Forbidden path" in reason
