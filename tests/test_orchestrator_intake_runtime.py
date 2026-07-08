import json
import os
import subprocess
import sys
from pathlib import Path

from estate.core.orchestrator_intake import OrchestratorIntakeRequest
from estate.core.orchestrator_intake_runtime import OrchestratorIntakeRuntime


def payload(intake_id="intake-1", **overrides):
    data = {
        "intake_id": intake_id,
        "created_at": "2026-07-08T00:00:00Z",
        "requested_by": "tests",
        "source": "manual",
        "classification": "Estate Internal",
        "mission": "Plan documentation",
        "summary": "Create intake docs.",
        "metadata": {"summary_safe": True},
    }
    data.update(overrides)
    return data


def test_pending_intake_artifact_latest_and_queue_written(tmp_path):
    runtime = OrchestratorIntakeRuntime(root=tmp_path)
    status, paths = runtime.submit(OrchestratorIntakeRequest.from_dict(payload()))
    assert status.state == "pending"
    assert Path(paths["artifact"]).exists()
    assert Path(paths["latest"]).exists()
    assert Path(paths["queue"]).exists()
    queue = json.loads(Path(paths["queue"]).read_text())
    assert queue["pending"][0]["intake_id"] == "intake-1"


def test_blocked_intake_artifact_written(tmp_path):
    runtime = OrchestratorIntakeRuntime(root=tmp_path)
    status, paths = runtime.submit(OrchestratorIntakeRequest.from_dict(payload(classification="Restricted")))
    assert status.state == "blocked"
    assert "Restricted" in status.blocked_reason
    assert "/blocked/" in paths["artifact"].replace("\\", "/")
    assert Path(paths["artifact"]).exists()


def run_cli(args, cwd):
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[1] / "src")
    return subprocess.run([sys.executable, "-m", "estate.cli.main", *args], cwd=cwd, text=True, capture_output=True, env=env)


def test_cli_submit_succeeds_for_valid_intake(tmp_path):
    request = tmp_path / "request.json"
    request.write_text(json.dumps(payload("cli-valid")), encoding="utf-8")
    result = run_cli(["orchestrator-intake-submit", "--request", str(request)], Path.cwd())
    assert result.returncode == 0, result.stderr + result.stdout
    assert "PENDING" in result.stdout


def test_cli_submit_fails_for_invalid_intake(tmp_path):
    request = tmp_path / "invalid.json"
    request.write_text(json.dumps({"intake_id": "missing"}), encoding="utf-8")
    result = run_cli(["orchestrator-intake-submit", "--request", str(request)], Path.cwd())
    assert result.returncode == 1
    assert "failed" in result.stdout


def test_cli_submit_reports_blocked_intake(tmp_path):
    request = tmp_path / "blocked.json"
    request.write_text(json.dumps(payload("cli-blocked", classification="Restricted")), encoding="utf-8")
    result = run_cli(["orchestrator-intake-submit", "--request", str(request)], Path.cwd())
    assert result.returncode == 0
    assert "BLOCKED" in result.stdout


def test_cli_list_succeeds_with_empty_queue(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = run_cli(["orchestrator-intake-list"], Path.cwd())
    assert result.returncode == 0
    assert "Orchestrator Intake Queue" in result.stdout


def test_cli_list_reports_pending_and_blocked_items(tmp_path):
    valid = tmp_path / "valid.json"
    blocked = tmp_path / "blocked.json"
    valid.write_text(json.dumps(payload("cli-list-pending")), encoding="utf-8")
    blocked.write_text(json.dumps(payload("cli-list-blocked", classification="Restricted")), encoding="utf-8")
    run_cli(["orchestrator-intake-submit", "--request", str(valid)], Path.cwd())
    run_cli(["orchestrator-intake-submit", "--request", str(blocked)], Path.cwd())
    result = run_cli(["orchestrator-intake-list"], Path.cwd())
    assert result.returncode == 0
    assert "cli-list-pending" in result.stdout
    assert "cli-list-blocked" in result.stdout
