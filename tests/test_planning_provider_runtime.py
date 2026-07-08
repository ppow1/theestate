import json
import os
import subprocess
import sys
from pathlib import Path

from estate.core.planning_provider import PlanningProviderRequest, StubPlanningProvider
from estate.core.planning_provider_runtime import PlanningProviderRuntimeWriter


def payload(request_id="req-runtime", classification="Estate Internal", metadata=None):
    return {
        "request_id": request_id,
        "provider_id": "stub.planning.echo",
        "requested_by": "pytest",
        "classification": classification,
        "planning_intent": "Runtime artifact test",
        "prompt": "Write artifacts.",
        "created_at": "2026-07-08T00:00:00Z",
        "metadata": metadata or {},
    }


def test_runtime_artifacts_emitted(tmp_path):
    request = PlanningProviderRequest.from_dict(payload())
    response = StubPlanningProvider().run(request)
    paths = PlanningProviderRuntimeWriter(root=tmp_path).write_all(request, response)
    assert (tmp_path / "runtime/planning_provider/events/req-runtime.jsonl").exists()
    assert (tmp_path / "runtime/planning_provider/results/req-runtime.json").exists()
    latest = json.loads((tmp_path / "runtime/planning_provider/status/latest.json").read_text())
    assert latest["request_id"] == "req-runtime"
    assert latest["status"] == "completed"
    assert paths["latest_status"].endswith("latest.json")


def test_cli_succeeds_for_valid_request(tmp_path):
    request_path = tmp_path / "request.json"
    request_path.write_text(json.dumps(payload("req-cli")), encoding="utf-8")
    env = {**os.environ, "PYTHONPATH": str(Path.cwd() / "src")}
    result = subprocess.run([sys.executable, "-m", "estate.cli.main", "planning-provider-run", "--request", str(request_path)], cwd=tmp_path, text=True, capture_output=True, env=env)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "Status: completed" in result.stdout
    assert (tmp_path / "runtime/planning_provider/results/req-cli.json").exists()


def test_cli_exits_nonzero_for_blocked_request(tmp_path):
    request_path = tmp_path / "request.json"
    request_path.write_text(json.dumps(payload("req-blocked", classification="Restricted")), encoding="utf-8")
    env = {**os.environ, "PYTHONPATH": str(Path.cwd() / "src")}
    result = subprocess.run([sys.executable, "-m", "estate.cli.main", "planning-provider-run", "--request", str(request_path)], cwd=tmp_path, text=True, capture_output=True, env=env)
    assert result.returncode != 0
    assert "Status: blocked" in result.stdout
