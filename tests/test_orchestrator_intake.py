import pytest

from estate.core.orchestrator_intake import OrchestratorIntakeRequest, determine_block_reason


def valid_payload(**overrides):
    payload = {
        "intake_id": "intake-1",
        "created_at": "2026-07-08T00:00:00Z",
        "requested_by": "tests",
        "source": "manual",
        "classification": "Estate Internal",
        "mission": "Document intake contract",
        "summary": "Create a governed intake artifact.",
    }
    payload.update(overrides)
    return payload


def test_valid_intake_request_accepted():
    request = OrchestratorIntakeRequest.from_dict(valid_payload())
    assert request.priority == "normal"
    assert request.state == "pending"
    assert determine_block_reason(request) is None


def test_missing_required_field_fails():
    payload = valid_payload()
    payload.pop("intake_id")
    with pytest.raises(ValueError, match="intake_id is required"):
        OrchestratorIntakeRequest.from_dict(payload)


def test_unknown_classification_fails():
    with pytest.raises(ValueError, match="unknown classification"):
        OrchestratorIntakeRequest.from_dict(valid_payload(classification="Secret"))


def test_unknown_priority_fails():
    with pytest.raises(ValueError, match="unknown priority"):
        OrchestratorIntakeRequest.from_dict(valid_payload(priority="later"))


def test_restricted_without_boundary_review_is_blocked():
    request = OrchestratorIntakeRequest.from_dict(valid_payload(classification="Restricted"))
    assert determine_block_reason(request) == "Restricted intake requires boundary_review_required=true."


def test_steward_only_without_approval_metadata_is_blocked():
    request = OrchestratorIntakeRequest.from_dict(valid_payload(classification="Steward Only"))
    assert determine_block_reason(request) == "Steward Only intake requires explicit approval metadata."
