import json
import os
import subprocess
import sys
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from estate.core.provider_routing_recommendations_runtime import evaluate_recommendation_file


def test_runtime_artifacts_are_written(tmp_path):
    request = tmp_path / "request.json"
    request.write_text(json.dumps({"routing_request_id": "route-runtime", "work_type": "repository implementation", "requires_repo_write": True}), encoding="utf-8")
    payload = evaluate_recommendation_file(request, write=True)
    assert payload["recommended_provider"] == "codex_cloud_web"
    for key in ["recommendation_path", "latest_status_path", "summary_path", "report_path"]:
        assert Path(payload[key]).is_file()


def test_cli_evaluate_writes_runtime_artifacts_without_dispatch_or_orchestrator_mutation(tmp_path):
    request = tmp_path / "request.json"
    request.write_text(json.dumps({"routing_request_id": "route-cli-runtime", "work_type": "classification review", "requires_gpu": True}), encoding="utf-8")
    proc = subprocess.run([sys.executable, "-m", "estate.cli.main", "provider-routing-recommendation", "evaluate", "--request", str(request), "--json"], text=True, capture_output=True, check=False, env={**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src")})
    assert proc.returncode == 0, proc.stderr or proc.stdout
    data = json.loads(proc.stdout)
    assert data["recommended_provider"] == "local_ollama_gpu"
    assert data["metadata"]["dispatch_mutated"] is False
    assert data["metadata"]["orchestrator_mutated"] is False
    assert Path(data["recommendation_path"]).is_file()
