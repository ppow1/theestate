import pytest

from estate.core.consultation_escalation import grace_decision_packet, instrument_escalation
from estate.core.consultation_store import ConsultationStore


def make_escalation(store):
    root = store.allocate_root(status="steward_decision_required", objective="Bounded objective", ptm_project_id="PROJ-1", tags=("reasoning",))
    store.append_response(root.logical_consultation_id, {"content": "Insufficient evidence.", "structured_decision": {"classification": "MORE_REASONING_REQUIRED", "evidence_request": {"objective": "Need the policy fact"}}})
    store.append_validation(root.logical_consultation_id, observed_result="EVIDENCE_ACQUISITION_LIMIT_REACHED", evidence={"count": 3}, status="steward_decision_required")
    return root


def test_escalation_has_stable_id_and_itemized_provenance(tmp_path):
    store = ConsultationStore(tmp_path / "consultations.db")
    root = make_escalation(store)
    first = instrument_escalation(store, root.logical_consultation_id)
    second = instrument_escalation(store, root.logical_consultation_id)
    record = store.escalation(first["escalation_id"])

    assert first["escalation_id"] == second["escalation_id"]
    assert record.snapshot["known_facts"]
    assert all(item["basis"] and isinstance(item["confidence"], float) for item in record.snapshot["known_facts"])
    assert all("confidence" in item and "reason_for_uncertainty" in item for item in record.snapshot["working_interpretations"])
    assert record.snapshot["unknowns"][0]["impact"] == "high"
    assert record.snapshot["recommendation_confidence"] is None


def test_snapshot_is_immutable_and_grace_packet_is_bounded(tmp_path):
    store = ConsultationStore(tmp_path / "consultations.db")
    root = make_escalation(store)
    first = instrument_escalation(store, root.logical_consultation_id)
    original = store.escalation(first["escalation_id"]).snapshot
    store.set_escalation_package(root.logical_consultation_id, {"status": "STEWARD_DECISION_REQUIRED", "changed": True})
    assert store.escalation(first["escalation_id"]).snapshot == original
    packet = grace_decision_packet(store, first["escalation_id"])
    assert packet["escalation_id"] == first["escalation_id"]
    assert set(packet) >= {"known_facts", "working_interpretations", "unknowns", "options"}


def test_steward_decision_evidence_and_outcome_are_separate(tmp_path):
    store = ConsultationStore(tmp_path / "consultations.db")
    root = make_escalation(store)
    escalation = instrument_escalation(store, root.logical_consultation_id)
    decision = store.record_steward_decision(
        escalation["escalation_id"], selected_option="steward_direction",
        decision_text="Supply the missing policy fact.", rationale=None,
        steward_evidence=[{"content": {"policy": "bounded"}, "provenance": "Steward statement", "impact": "resolves unknown"}],
    )
    assert decision.rationale is None
    outcome = store.record_escalation_outcome(
        decision.decision_id, observed_result="bounded evidence supplied",
        validation_result="validated", classification="SUCCESS",
        consultation_status="closed", new_evidence={"policy": "bounded"},
    )
    assert outcome.decision_id == decision.decision_id
    assert outcome.classification == "SUCCESS"
    assert store.escalation(escalation["escalation_id"]).snapshot["status"] == "STEWARD_DECISION_REQUIRED"


def test_invalid_outcome_and_decision_fail_closed(tmp_path):
    store = ConsultationStore(tmp_path / "consultations.db")
    root = make_escalation(store)
    escalation = instrument_escalation(store, root.logical_consultation_id)
    with pytest.raises(ValueError):
        store.record_steward_decision(escalation["escalation_id"], selected_option=None, decision_text="", decision_actor="Grace")


def test_escalations_are_queryable_by_project_tag_reason_and_confidence(tmp_path):
    store = ConsultationStore(tmp_path / "consultations.db")
    root = make_escalation(store)
    store.add_tags(root.logical_consultation_id, ["bounded-review"])
    escalation = instrument_escalation(store, root.logical_consultation_id)
    assert [item.escalation_id for item in store.escalations(ptm_project_id="PROJ-1")] == [escalation["escalation_id"]]
    assert [item.escalation_id for item in store.escalations(tag="bounded-review")] == [escalation["escalation_id"]]
    assert [item.escalation_id for item in store.escalations(reason="bounded_autonomous_evidence_exhausted")] == [escalation["escalation_id"]]
    assert [item.escalation_id for item in store.escalations(confidence_band="high")] == [escalation["escalation_id"]]
