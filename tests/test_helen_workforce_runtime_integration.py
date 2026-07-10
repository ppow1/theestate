import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from estate.core.helen_workforce import HelenWorkforceStore, WorkforceAssessment, WorkforceRequest
from estate.core.steward_presence import generate_steward_presence_state


def test_duplicate_request_idempotent_and_conflict_rejected(tmp_path: Path):
    store = HelenWorkforceStore(tmp_path)
    req = WorkforceRequest.create(request_type="coaching_request", subject_id="worker-a", subject_type="worker", requesting_office="Engineering", summary="Coach worker.", requested_outcome="Improve retrieval.")
    store.save_request(req)
    store.save_request(req)
    changed = WorkforceRequest.from_dict(req.to_dict())
    changed.summary = "Different"
    with pytest.raises(ValueError, match="duplicate request identifier"):
        store.save_request(changed)


def test_missing_request_assessment_rejected(tmp_path: Path):
    assessment = WorkforceAssessment.create(request_id="wfr-missing", subject_id="worker-a", rationale="No request exists.")
    with pytest.raises(ValueError, match="workforce request not found"):
        HelenWorkforceStore(tmp_path).save_assessment(assessment)


def test_malformed_artifacts_are_ignored_in_status(tmp_path: Path):
    req_dir = tmp_path / "runtime/workforce_development/requests"
    req_dir.mkdir(parents=True)
    (req_dir / "bad.json").write_text("not json", encoding="utf-8")
    status = HelenWorkforceStore(tmp_path).write_status()
    assert status["summary"]["open_requests"] == 0
    assert status["summary"]["latest_request_id"] is None


def test_event_bridge_for_request_and_escalated_assessment(tmp_path: Path):
    store = HelenWorkforceStore(tmp_path)
    req = WorkforceRequest.create(request_type="continuity_review", subject_id="resident-x", subject_type="resident", requesting_office="Office of the Steward", summary="Resident continuity review.", requested_outcome="Determine boundary-safe next step.", requires_steward_attention=True)
    store.save_request(req)
    assessment = WorkforceAssessment.create(request_id=req.request_id, subject_id="resident-x", recommendations=["temporary_stand_down"], rationale="Attention required.")
    store.save_assessment(assessment)
    events = "\n".join(p.read_text(encoding="utf-8") for p in (tmp_path / "runtime/operations/events").glob("*.jsonl"))
    assert req.request_id in events
    assert assessment.assessment_id in events
    assert "provider_execution_performed" in events
    assert "operational_queue_control_performed" in events
    assert "constitutional_authority_granted" in events


def test_steward_presence_absorbs_workforce_status(tmp_path: Path):
    store = HelenWorkforceStore(tmp_path)
    req = WorkforceRequest.create(request_type="coaching_request", subject_id="worker-a", subject_type="worker", requesting_office="Engineering", summary="Coach worker.", requested_outcome="Improve retrieval.")
    store.save_request(req)
    state = generate_steward_presence_state(root=tmp_path, write=False)
    assert state["summary"]["helen_workforce"]["open_requests"] == 1
    assert state["summary"]["provider_execution_performed"] is False


def test_main_estate_cli_helen_workforce(tmp_path: Path):
    req = WorkforceRequest.create(request_type="coaching_request", subject_id="worker-main", subject_type="worker", requesting_office="Engineering", summary="Coach worker.", requested_outcome="Improve retrieval.")
    f = tmp_path / "request.json"
    f.write_text(json.dumps(req.to_dict()), encoding="utf-8")
    env = {**os.environ, "PYTHONPATH": str(Path.cwd() / "src")}
    result = subprocess.run([sys.executable, "-m", "estate.cli.main", "helen-workforce", "request-create", "--root", str(tmp_path), "--file", str(f), "--json"], text=True, capture_output=True, check=True, env=env)
    assert json.loads(result.stdout)["request"]["request_id"] == req.request_id
    status = subprocess.run([sys.executable, "-m", "estate.cli.main", "helen-workforce", "status", "--root", str(tmp_path), "--json"], text=True, capture_output=True, check=True, env=env)
    payload = json.loads(status.stdout)
    assert payload["status"]["summary"]["open_requests"] == 1
    assert payload["status"]["provider_execution_performed"] is False


def test_json_schemas_examples_are_valid():
    for path in Path("docs/schemas/workforce_development").glob("*.schema.json"):
        schema = json.loads(path.read_text(encoding="utf-8"))
        assert schema["$schema"].endswith("2020-12/schema")
        required = set(schema.get("required", []))
        for example in schema.get("examples", []):
            assert required <= set(example)
            for key, spec in schema.get("properties", {}).items():
                if key in example and "const" in spec:
                    assert example[key] == spec["const"]
            assert "journal_body" not in example
