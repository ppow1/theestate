import json
import os
import subprocess
import sys
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from estate.core.provider_routing_recommendations import ProviderRoutingRecommendationRequest, evaluate_provider_routing_recommendation


def req(**overrides):
    data = {"routing_request_id": "route-test", "mission_summary": "", "work_type": "", "metadata": {}}
    data.update(overrides)
    return ProviderRoutingRecommendationRequest.from_dict(data)


def provider(**overrides):
    return evaluate_provider_routing_recommendation(req(**overrides))


def test_deterministic_validation_work_recommends_local_tooling():
    r = provider(work_type="pytest schema validation", validation_required=True)
    assert r.recommended_provider == "deterministic_local_tooling"
    assert "ring_1_deterministic_tests" in r.validation_rings_required


def test_bounded_review_work_recommends_local_ollama_gpu():
    r = provider(work_type="bounded reasoning review", requires_gpu=True)
    assert r.recommended_provider == "local_ollama_gpu"


def test_planning_work_recommends_chatgpt_planning():
    r = provider(work_type="architectural planning", mission_summary="governance prose")
    assert r.recommended_provider == "chatgpt_planning"


def test_broad_repo_implementation_recommends_codex_cloud_web():
    r = provider(work_type="repository implementation", requires_repo_write=True, requires_local_runtime=False)
    assert r.recommended_provider == "codex_cloud_web"


def test_local_runtime_required_implementation_can_recommend_codex_cli_with_caution():
    r = provider(work_type="repository implementation", requires_repo_write=True, requires_local_runtime=True)
    assert r.recommended_provider == "codex_cli"
    assert "cautiously" in r.provider_rationale.lower() or "approved escalation" in r.provider_rationale.lower()


def test_boundary_or_classification_decision_recommends_human_review():
    r = provider(work_type="classification decision", requires_boundary_review=True)
    assert r.recommended_provider == "human_review"
    assert r.human_review_required is True
    assert r.boundary_review_required is True


def test_recommendations_include_rationale_capacity_and_no_mutation_metadata():
    r = provider(work_type="repository implementation", requires_repo_write=True)
    assert r.provider_rationale
    assert "Recommendation only" in r.capacity_note
    assert r.metadata["dispatch_mutated"] is False
    assert r.metadata["orchestrator_mutated"] is False


def test_cli_json_output_is_stable_and_no_live_calls(tmp_path):
    request = tmp_path / "request.json"
    request.write_text(json.dumps({"routing_request_id": "route-cli", "work_type": "pytest validation"}), encoding="utf-8")
    proc = subprocess.run([sys.executable, "-m", "estate.cli.main", "provider-routing-recommendation", "explain", "--request", str(request), "--json"], text=True, capture_output=True, check=False, env={**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src")})
    assert proc.returncode == 0, proc.stderr or proc.stdout
    data = json.loads(proc.stdout)
    assert data["routing_request_id"] == "route-cli"
    assert data["recommended_provider"] == "deterministic_local_tooling"
    assert data["metadata"]["recommendation_only"] is True
