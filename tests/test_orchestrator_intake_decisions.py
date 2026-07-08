import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from estate.core.orchestrator_intake import OrchestratorIntakeRequest
from estate.core.orchestrator_intake_decisions import OrchestratorIntakeDecision, OrchestratorIntakeDecisionRuntime, load_office_intake_decision_surface
from estate.core.orchestrator_intake_runtime import OrchestratorIntakeRuntime


def payload(intake_id="intake-1", **overrides):
    data = {
        "intake_id": intake_id,
        "created_at": "2026-07-08T00:00:00Z",
        "requested_by": "tests",
        "source": "work_package",
        "classification": "Estate Internal",
        "mission": "Review intake item",
        "summary": "Safe summary for review.",
        "work_package_id": "WP-TEST",
        "work_package_path": "collaboration/work_packages/pending/WP-TEST.md",
        "requested_provider_type": "codex",
        "metadata": {"summary_safe": True},
    }
    data.update(overrides)
    return data


def submit(root, intake_id="intake-1", **overrides):
    return OrchestratorIntakeRuntime(root).submit(OrchestratorIntakeRequest.from_dict(payload(intake_id, **overrides)))


def test_valid_decision_artifact_accepted():
    artifact = OrchestratorIntakeDecision.from_dict({
        "decision_id": "oid-1",
        "intake_id": "intake-1",
        "decision": "approve",
        "decided_by": "Steward",
        "decided_at": "2026-07-08T00:00:00Z",
        "classification": "Estate Internal",
        "next_state": "approved",
    })
    assert artifact.summary_safe is False
    assert artifact.metadata == {}


def test_unknown_decision_rejected():
    with pytest.raises(ValueError, match="unknown decision"):
        OrchestratorIntakeDecision.create(intake_id="i", decision="execute", decided_by="Steward", classification="Estate Internal")


def test_unknown_classification_rejected():
    with pytest.raises(ValueError, match="unknown classification"):
        OrchestratorIntakeDecision.create(intake_id="i", decision="approve", decided_by="Steward", classification="Secret").to_dict()


@pytest.mark.parametrize("decision,next_state", [
    ("approve", "approved"),
    ("reject", "rejected"),
    ("defer", "deferred"),
    ("request_boundary_review", "blocked"),
    ("mark_needs_revision", "needs_revision"),
])
def test_decision_writes_artifact(tmp_path, decision, next_state):
    submit(tmp_path, f"intake-{decision}")
    artifact, paths = OrchestratorIntakeDecisionRuntime(tmp_path).decide(intake_id=f"intake-{decision}", decision=decision, decided_by="Steward", reason="Because")
    assert artifact.next_state == next_state
    assert Path(paths["decision"]).exists()
    data = json.loads(Path(paths["decision"]).read_text())
    assert data["decision"] == decision


def test_intake_queue_status_updates_after_decision(tmp_path):
    submit(tmp_path, "intake-approve")
    artifact, paths = OrchestratorIntakeDecisionRuntime(tmp_path).decide(intake_id="intake-approve", decision="approve", decided_by="Steward")
    queue = json.loads(Path(paths["queue"]).read_text())
    assert queue["pending"] == []
    latest = json.loads(Path(paths["latest"]).read_text())
    assert latest["state"] == "approved"
    assert latest["latest_decision"]["decision_id"] == artifact.decision_id


def test_sensitive_summaries_redacted_by_default(tmp_path):
    submit(tmp_path, "intake-private", classification="Restricted", boundary_review_required=True, metadata={})
    surface = load_office_intake_decision_surface(tmp_path)
    item = surface["items"][0]
    assert item["safe_summary"] == "Sensitive summary redacted."
    assert item["summary_redacted"] is True


def test_office_rendering_shows_available_decisions(tmp_path):
    submit(tmp_path, "intake-boundary", classification="Restricted", boundary_review_required=True, metadata={"summary_safe": True})
    surface = load_office_intake_decision_surface(tmp_path)
    item = surface["items"][0]
    assert item["intake_id"] == "intake-boundary"
    assert "request_boundary_review" in item["available_decisions"]
    assert "mark_needs_revision" in item["available_decisions"]


def run_cli(args, cwd):
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[1] / "src")
    return subprocess.run([sys.executable, "-m", "estate.cli.main", *args], cwd=cwd, text=True, capture_output=True, env=env)


def test_cli_fallback_records_real_decision(tmp_path):
    request = tmp_path / "request.json"
    request.write_text(json.dumps(payload("cli-decision")), encoding="utf-8")
    assert run_cli(["orchestrator-intake-submit", "--request", str(request)], Path.cwd()).returncode == 0
    result = run_cli(["orchestrator-intake-decide", "--intake-id", "cli-decision", "--decision", "defer", "--decided-by", "Steward", "--reason", "Wait"], Path.cwd())
    assert result.returncode == 0, result.stdout + result.stderr
    assert "Decision: defer" in result.stdout


def test_invalid_cli_decision_exits_nonzero():
    result = run_cli(["orchestrator-intake-decide", "--intake-id", "missing", "--decision", "execute", "--decided-by", "Steward"], Path.cwd())
    assert result.returncode != 0
