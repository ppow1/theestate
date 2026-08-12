import json

import pytest

from estate.core.autonomous_reason_execute_loop import classify_reasoning_response
from estate.core.consultation_store import ConsultationStore


def evidence_response(consultation_id="1.00"):
    return {
        "content": json.dumps({
            "reasoning": "Specific repository evidence is missing.",
            "decision": {
                "classification": "MORE_REASONING_REQUIRED",
                "evidence_request": {
                    "objective": "Read the bounded README.",
                    "evidence_type": "repository_read",
                    "target": "tests/fixtures/ptm_read_only_adapters/README.md",
                    "required_capability": "repository_read",
                    "allowed_scope": ["tests/fixtures/ptm_read_only_adapters"],
                    "prohibited_scope": ["src", "runtime", ".git"],
                    "evidence_requirements": ["README facts"],
                    "consultation_correlation": consultation_id,
                },
            },
        })
    }


def test_structured_evidence_request_validates():
    decision = classify_reasoning_response(evidence_response())
    assert decision.classification == "MORE_REASONING_REQUIRED"
    assert decision.evidence_request["consultation_id"] == "1.00"


@pytest.mark.parametrize("field", ["allowed_scope", "prohibited_scope", "evidence_requirements"])
def test_evidence_request_missing_bounded_field_fails_closed(field):
    response = evidence_response()
    parsed = json.loads(response["content"])
    parsed["decision"]["evidence_request"].pop(field)
    response["content"] = json.dumps(parsed)
    with pytest.raises(ValueError, match="evidence_request_missing"):
        classify_reasoning_response(response)


def test_evidence_request_rejects_provider_specific_capability():
    response = evidence_response()
    parsed = json.loads(response["content"])
    parsed["decision"]["evidence_request"]["required_capability"] = "codex_read"
    response["content"] = json.dumps(parsed)
    with pytest.raises(ValueError, match="provider_neutral"):
        classify_reasoning_response(response)


def test_evidence_reservation_is_idempotent_and_bounded(tmp_path):
    store = ConsultationStore(tmp_path / "consultations.db")
    store.allocate_root(status="awaiting_reasoning", objective="evidence", question="evidence")
    first = store.reserve_evidence_acquisition("1.00", "read|README|1.00")
    again = store.reserve_evidence_acquisition("1.00", "read|README|1.00")
    assert first["slot"] == again["slot"] == 1
    store.reserve_evidence_acquisition("1.00", "read|A|1.00")
    store.reserve_evidence_acquisition("1.00", "read|B|1.00")
    with pytest.raises(ValueError, match="EVIDENCE_ACQUISITION_LIMIT_REACHED"):
        store.reserve_evidence_acquisition("1.00", "read|C|1.00")
