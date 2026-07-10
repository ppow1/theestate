from pathlib import Path

import pytest

from estate.core.helen_workforce import (
    HelenWorkforceStore,
    WorkforceAssessment,
    WorkforceRequest,
)


def test_sensitive_workforce_request_requires_boundary_review():
    request = WorkforceRequest.create(
        request_type="continuity_review",
        subject_id="resident-helen",
        subject_type="resident",
        requesting_office="Human Resources / Workforce Development",
        summary="Review resident continuity and private reflection handling.",
        requested_outcome="Determine whether a new operational cycle is required.",
    )

    assert request.requires_boundary_review is True
    assert request.status == "open"
    assert request.request_id.startswith("wfr-")


def test_unknown_request_type_is_rejected():
    request = WorkforceRequest.create(
        request_type="take_over_operations",
        subject_id="worker-1",
        subject_type="worker",
        requesting_office="Office of Operations",
        summary="Take over the operational queue.",
        requested_outcome="Move all work directly.",
    )

    with pytest.raises(ValueError, match="unknown request_type"):
        request.to_dict()


def test_private_assessment_requires_restricted_classification():
    assessment = WorkforceAssessment.create(
        request_id="wfr-example",
        subject_id="worker-1",
        rationale="Private journal details were used in the assessment.",
        private_detail_included=True,
        classification="Estate Internal",
    )

    with pytest.raises(ValueError, match="private detail requires"):
        assessment.to_dict()


def test_unknown_recommendation_is_rejected():
    assessment = WorkforceAssessment.create(
        request_id="wfr-example",
        subject_id="worker-1",
        rationale="Recommendation is outside Helen's contract.",
        recommendations=["seize_operational_control"],
    )

    with pytest.raises(ValueError, match="unknown recommendations"):
        assessment.to_dict()


def test_store_writes_request_assessment_and_status(tmp_path: Path):
    store = HelenWorkforceStore(tmp_path)
    request = WorkforceRequest.create(
        request_type="worker_health_review",
        subject_id="worker-42",
        subject_type="worker",
        requesting_office="Engineering",
        summary="Worker has repeated mistakes and visible context strain.",
        requested_outcome="Assess worker and institutional causes.",
        source_artifacts=["runtime/workers/worker-42/status.json", "runtime/operations/events/worker-42.jsonl"],
    )

    request_path = store.save_request(request)
    assert request_path.is_file()

    assessment = WorkforceAssessment.create(
        request_id=request.request_id,
        subject_id="worker-42",
        worker_factors=["context strain"],
        institutional_factors=["unclear onboarding guidance", "poor retrieval indexing"],
        missing_evidence=[],
        recommendations=["targeted_reread", "onboarding_repair", "retrieval_repair"],
        rationale="The evidence supports both worker-level and institutional intervention.",
        follow_up_checkpoints=["review after the next operating cycle"],
    )

    assessment_path = store.save_assessment(assessment)
    assert assessment_path.is_file()

    loaded = store.load_request(request.request_id)
    assert loaded.status == "ready_for_action"

    status = store.write_status()
    assert status["summary"]["ready_for_action_requests"] == 1
    assert status["summary"]["assessment_count"] == 1
    assert status["operational_queue_control_performed"] is False
    assert status["provider_execution_performed"] is False
    assert status["constitutional_authority_granted"] is False

    assert (tmp_path / "runtime/workforce_development/status/latest.json").is_file()
    assert (tmp_path / "runtime/workforce_development/status/summary.json").is_file()


def test_missing_evidence_keeps_request_in_review(tmp_path: Path):
    store = HelenWorkforceStore(tmp_path)
    request = WorkforceRequest.create(
        request_type="role_fit_review",
        subject_id="candidate-grace",
        subject_type="resident candidate",
        requesting_office="Office of the Steward",
        summary="Assess Grace for the approved Director of Operations role.",
        requested_outcome="Produce a readiness recommendation without appointing her.",
        requires_steward_attention=True,
    )
    store.save_request(request)

    assessment = WorkforceAssessment.create(
        request_id=request.request_id,
        subject_id="candidate-grace",
        missing_evidence=[
            "approved constitutional office artifact",
            "deterministic resident validation",
            "runtime registration capability",
        ],
        recommendations=["request_more_evidence"],
        rationale="Grace cannot be marked ready until the required evidence exists.",
    )
    store.save_assessment(assessment)

    loaded = store.load_request(request.request_id)
    assert loaded.status == "in_review"
    assert store.write_status()["summary"]["steward_attention_count"] == 1


def test_assessment_subject_must_match_request_subject(tmp_path: Path):
    store = HelenWorkforceStore(tmp_path)
    request = WorkforceRequest.create(
        request_type="coaching_request",
        subject_id="worker-a",
        subject_type="worker",
        requesting_office="Engineering",
        summary="Provide targeted coaching.",
        requested_outcome="Improve policy retrieval behavior.",
    )
    store.save_request(request)

    assessment = WorkforceAssessment.create(
        request_id=request.request_id,
        subject_id="worker-b",
        recommendations=["coaching"],
        rationale="Wrong subject on purpose.",
    )

    with pytest.raises(ValueError, match="assessment subject must match"):
        store.save_assessment(assessment)
