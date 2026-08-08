import pytest

from estate.core.consultation_escalation import (
    build_escalation_package,
    propose_reframe,
    resume_after_steward,
)
from estate.core.consultation_store import ConsultationStore


def test_budget_exhaustion_creates_bounded_steward_package_without_closure(tmp_path):
    store = ConsultationStore(tmp_path / "consultations.db")
    root = store.allocate_root(status="awaiting_reasoning", objective="Validate a bounded assumption")
    current = store.allocate_continuation(root.logical_consultation_id, status="continuation_required", question="What remains unknown?")
    store.append_response(current.logical_consultation_id, {
        "content": "I still need bounded evidence.",
        "structured_decision": {
            "classification": "MORE_REASONING_REQUIRED",
            "evidence_request": {
                "objective": "Confirm the documented constraint",
                "target": "README.md",
                "required_capability": "repository_read",
                "evidence_requirements": ["relevant section"],
            },
        },
    })
    store.append_validation(current.logical_consultation_id, observed_result="EVIDENCE_ACQUISITION_LIMIT_REACHED", evidence={"acquisition_count": 3}, status="continuation_required")

    package = build_escalation_package(store, current.logical_consultation_id)
    stored_root = store.get(root.logical_consultation_id)
    stored_current = store.get(current.logical_consultation_id)

    assert package["status"] == "STEWARD_DECISION_REQUIRED"
    assert package["acquisition_count"] == 0  # no provider rows in this focused fixture
    assert len(package["current_understanding"]) <= 4000
    assert stored_root.status == "steward_decision_required"
    assert stored_current.status == "steward_decision_required"
    assert stored_current.observed_result == "STEWARD_DECISION_REQUIRED"
    assert stored_current.status != "resolved"


def test_reframe_is_only_a_proposal_and_resume_preserves_lineage(tmp_path):
    store = ConsultationStore(tmp_path / "consultations.db")
    root = store.allocate_root(status="steward_decision_required", objective="Original")
    store.set_escalation_package(root.logical_consultation_id, {"status": "STEWARD_DECISION_REQUIRED"})

    proposal = propose_reframe(store, root.logical_consultation_id)
    assert proposal["status"] == "REFRAME_AS_NEW_CONSULTATION"
    assert proposal["created"] is False
    assert len(store.get_turn_range(root.root_logical_id)) == 1

    resumed = resume_after_steward(store, root.logical_consultation_id, question="Use the Steward evidence.", evidence={"fact": "provided"})
    assert resumed.logical_consultation_id == "1.01"
    assert resumed.root_logical_id == "1.00"
    assert resumed.parent_logical_id == "1.00"
    assert resumed.status == "awaiting_reasoning"


def test_escalation_does_not_change_evidence_budget_or_create_requests(tmp_path):
    store = ConsultationStore(tmp_path / "consultations.db")
    root = store.allocate_root(objective="Evidence")
    build_escalation_package(store, root.logical_consultation_id)
    assert store.execution_requests(root.logical_consultation_id) == []
    with pytest.raises(ValueError, match="EVIDENCE_ACQUISITION_LIMIT_REACHED"):
        for name in ("a", "b", "c", "d"):
            store.reserve_evidence_acquisition(root.logical_consultation_id, name)
