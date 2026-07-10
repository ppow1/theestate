from pathlib import Path

import pytest

from estate.core.helen_workforce import HelenWorkforceStore, WorkforceAssessment, WorkforceRequest


def _request(kind="overload_review"):
    return WorkforceRequest.create(
        request_type=kind,
        subject_id="worker-cog",
        subject_type="worker",
        requesting_office="Human Resources / Helen",
        summary="Evidence-based review of overload and repeated errors.",
        requested_outcome="Governed intervention recommendation without diagnosis.",
        source_artifacts=["runtime/workers/worker-cog/status.json", "runtime/operations/events/example.jsonl"],
    )


def test_cognitive_health_intervention_requires_minimum_evidence(tmp_path: Path):
    store = HelenWorkforceStore(tmp_path)
    req = _request()
    req.source_artifacts = ["one-artifact.json"]
    store.save_request(req)
    assessment = WorkforceAssessment.create(
        request_id=req.request_id,
        subject_id=req.subject_id,
        worker_factors=["context strain observed in repeated handoff misses"],
        institutional_factors=["unclear documentation path"],
        recommendations=["coaching"],
        rationale="Evidence supports a bounded coaching intervention.",
    )
    with pytest.raises(ValueError, match="minimum evidence"):
        store.save_assessment(assessment)


def test_institutional_causes_required_alongside_worker_factors(tmp_path: Path):
    store = HelenWorkforceStore(tmp_path)
    req = _request("repeated_error_review")
    store.save_request(req)
    assessment = WorkforceAssessment.create(
        request_id=req.request_id,
        subject_id=req.subject_id,
        worker_factors=["repeated checklist misses"],
        institutional_factors=[],
        recommendations=["targeted_reread"],
        rationale="Bounded reread requested.",
    )
    with pytest.raises(ValueError, match="institutional causes"):
        store.save_assessment(assessment)


def test_material_intervention_requires_follow_up_and_exposes_summaries(tmp_path: Path):
    store = HelenWorkforceStore(tmp_path)
    req = _request("context_strain_review")
    store.save_request(req)
    blocked = WorkforceAssessment.create(
        request_id=req.request_id,
        subject_id=req.subject_id,
        worker_factors=["context strain after long queue exposure"],
        institutional_factors=["retrieval index did not surface current runbook"],
        recommendations=["workload_adjustment"],
        rationale="Temporary workload adjustment is proportional to the observed evidence.",
    )
    with pytest.raises(ValueError, match="follow-up checkpoints"):
        store.save_assessment(blocked)

    assessment = WorkforceAssessment.create(
        request_id=req.request_id,
        subject_id=req.subject_id,
        worker_factors=["context strain after long queue exposure"],
        institutional_factors=["retrieval index did not surface current runbook"],
        recommendations=["workload_adjustment", "retrieval_repair"],
        evidence_artifacts=["runtime/workers/worker-cog/error-window.json"],
        follow_up_checkpoints=["review after next operating cycle"],
        rationale="Bounded workload adjustment and retrieval repair are proportional.",
        alfred_exception_summary="Worker has a bounded availability exception pending follow-up.",
        grace_operational_constraint_summary="Do not schedule this worker for parallel urgent queues this cycle.",
    )
    store.save_assessment(assessment)
    status = store.write_status()
    assert status["grace_operational_constraints"][0]["raw_private_records_included"] is False
    assert status["grace_operational_constraints"][0]["prescribes_intervention"] is False
    assert status["alfred_exceptions"][0]["raw_private_records_included"] is False


def test_private_journals_and_false_diagnosis_are_rejected(tmp_path: Path):
    store = HelenWorkforceStore(tmp_path)
    req = _request("worker_health_review")
    store.save_request(req)
    journal = WorkforceAssessment.create(
        request_id=req.request_id,
        subject_id=req.subject_id,
        worker_factors=["reported fatigue"],
        institutional_factors=["unclear shift handoff"],
        recommendations=["coaching"],
        evidence_artifacts=["private/journal/body.md"],
        protected_evidence_used=True,
        classification="Restricted",
        rationale="Private evidence should not be routine.",
    )
    with pytest.raises(ValueError, match="private journals"):
        store.save_assessment(journal)

    diagnosing = WorkforceAssessment.create(
        request_id=req.request_id,
        subject_id=req.subject_id,
        worker_factors=["diagnosis of burnout disorder"],
        institutional_factors=["unclear operating expectations"],
        recommendations=["coaching"],
        rationale="This attempts a diagnosis.",
    )
    with pytest.raises(ValueError, match="do not diagnose"):
        store.save_assessment(diagnosing)
