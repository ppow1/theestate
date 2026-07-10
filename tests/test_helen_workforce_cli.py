import json
from pathlib import Path

from estate.cli.helen_workforce import run
from estate.core.helen_workforce import WorkforceAssessment, WorkforceRequest


def _write(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def test_cli_creates_request_and_status(tmp_path: Path, capsys):
    request = WorkforceRequest.create(
        request_type="worker_health_review",
        subject_id="worker-7",
        subject_type="worker",
        requesting_office="Engineering",
        summary="Repeated mistakes and context strain require review.",
        requested_outcome="Assess worker and institutional causes.",
    )
    request_path = _write(tmp_path / "request.json", request.to_dict())

    payload = run([
        "--root",
        str(tmp_path),
        "request-create",
        "--file",
        str(request_path),
    ])

    output = capsys.readouterr().out
    assert "Helen workforce request created" in output
    assert payload["request"]["request_id"] == request.request_id
    assert payload["operational_queue_control_performed"] is False
    assert (tmp_path / "runtime/workforce_development/requests" / f"{request.request_id}.json").is_file()

    status = run(["--root", str(tmp_path), "--json", "status"])
    status_output = capsys.readouterr().out
    assert json.loads(status_output)["status"]["summary"]["open_requests"] == 1
    assert status["status"]["provider_execution_performed"] is False


def test_cli_creates_assessment_and_advances_request(tmp_path: Path, capsys):
    request = WorkforceRequest.create(
        request_type="role_fit_review",
        subject_id="candidate-grace",
        subject_type="resident candidate",
        requesting_office="Office of the Steward",
        summary="Assess Grace for Director of Operations.",
        requested_outcome="Produce readiness assessment without appointment.",
        requires_steward_attention=True,
    )
    request_path = _write(tmp_path / "request.json", request.to_dict())
    run(["--root", str(tmp_path), "request-create", "--file", str(request_path)])
    capsys.readouterr()

    assessment = WorkforceAssessment.create(
        request_id=request.request_id,
        subject_id="candidate-grace",
        missing_evidence=["constitutional office artifact"],
        recommendations=["request_more_evidence"],
        rationale="Grace remains in review until required evidence exists.",
    )
    assessment_path = _write(tmp_path / "assessment.json", assessment.to_dict())

    payload = run([
        "--root",
        str(tmp_path),
        "assessment-create",
        "--file",
        str(assessment_path),
    ])

    output = capsys.readouterr().out
    assert "Helen workforce assessment created" in output
    assert payload["request_status"] == "in_review"
    assert payload["constitutional_authority_granted"] is False

    shown = run([
        "--root",
        str(tmp_path),
        "--json",
        "request-show",
        "--request-id",
        request.request_id,
    ])
    shown_output = capsys.readouterr().out
    assert json.loads(shown_output)["request"]["status"] == "in_review"
    assert shown["request"]["subject_id"] == "candidate-grace"


def test_cli_lists_requests_and_assessments(tmp_path: Path, capsys):
    request = WorkforceRequest.create(
        request_type="coaching_request",
        subject_id="worker-9",
        subject_type="worker",
        requesting_office="Engineering",
        summary="Targeted coaching requested.",
        requested_outcome="Improve policy retrieval behavior.",
        source_artifacts=["runtime/workers/worker-9/status.json", "runtime/operations/events/worker-9.jsonl"],
    )
    request_path = _write(tmp_path / "request.json", request.to_dict())
    run(["--root", str(tmp_path), "request-create", "--file", str(request_path)])
    capsys.readouterr()

    assessment = WorkforceAssessment.create(
        request_id=request.request_id,
        subject_id="worker-9",
        worker_factors=["policy retrieval misses"],
        institutional_factors=["unclear policy index"],
        recommendations=["coaching"],
        rationale="A focused coaching intervention is proportionate.",
    )
    assessment_path = _write(tmp_path / "assessment.json", assessment.to_dict())
    run(["--root", str(tmp_path), "assessment-create", "--file", str(assessment_path)])
    capsys.readouterr()

    requests = run(["--root", str(tmp_path), "--json", "requests-list"])
    requests_output = capsys.readouterr().out
    assert len(json.loads(requests_output)["requests"]) == 1
    assert requests["requests"][0]["request_id"] == request.request_id

    assessments = run(["--root", str(tmp_path), "--json", "assessments-list"])
    assessments_output = capsys.readouterr().out
    assert len(json.loads(assessments_output)["assessments"]) == 1
    assert assessments["assessments"][0]["assessment_id"] == assessment.assessment_id
