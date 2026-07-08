import pytest

from estate.core.planning_provider import PlanningProviderRequest, StubPlanningProvider


def request_payload(**overrides):
    payload = {
        "request_id": "req-1",
        "provider_id": "stub.planning.echo",
        "requested_by": "pytest",
        "classification": "Estate Internal",
        "planning_intent": "Draft a plan",
        "prompt": "Plan this safely.",
        "created_at": "2026-07-08T00:00:00Z",
    }
    payload.update(overrides)
    return payload


def test_valid_request_model():
    request = PlanningProviderRequest.from_dict(request_payload())
    assert request.context_paths == []
    assert request.allowed_output_paths == []
    assert request.metadata == {}


def test_invalid_classification_rejected():
    with pytest.raises(ValueError, match="unknown classification"):
        PlanningProviderRequest.from_dict(request_payload(classification="Secret"))


def test_stub_provider_completes_allowed_request():
    request = PlanningProviderRequest.from_dict(request_payload())
    response = StubPlanningProvider().run(request)
    assert response.status == "completed"
    assert "Draft a plan" in response.summary
    assert response.events[-1]["event_type"] == "Planning Complete"


def test_stub_provider_blocks_restricted_request_without_approval():
    request = PlanningProviderRequest.from_dict(request_payload(classification="Restricted"))
    response = StubPlanningProvider().run(request)
    assert response.status == "blocked"
    assert response.requires_review is True
    assert "boundary_approved" in response.errors[0]


def test_stub_provider_allows_restricted_request_with_approval_metadata():
    request = PlanningProviderRequest.from_dict(request_payload(classification="Restricted", metadata={"boundary_approved": True}))
    response = StubPlanningProvider().run(request)
    assert response.status == "completed"
