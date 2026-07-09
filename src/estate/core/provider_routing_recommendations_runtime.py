"""Runtime artifact helpers for provider routing recommendations."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any
from estate.core.paths import ESTATE_ROOT
from estate.core.provider_routing_recommendations import ProviderRoutingRecommendationRequest, evaluate_provider_routing_recommendation, explain_provider_routing_recommendation

ROOT = ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd()
BASE = ROOT / "runtime" / "provider_routing"
RECOMMENDATIONS = BASE / "recommendations"
STATUS = BASE / "status"
REPORTS = BASE / "reports"


def _write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def load_recommendation_request(path: str | Path) -> ProviderRoutingRecommendationRequest:
    return ProviderRoutingRecommendationRequest.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))


def evaluate_recommendation_file(path: str | Path, *, write: bool = True) -> dict[str, Any]:
    request = load_recommendation_request(path)
    return write_recommendation(request) if write else evaluate_provider_routing_recommendation(request).to_dict()


def write_recommendation(request: ProviderRoutingRecommendationRequest) -> dict[str, Any]:
    result = evaluate_provider_routing_recommendation(request)
    payload = result.to_dict()
    recommendation_path = _write_json(RECOMMENDATIONS / f"{result.recommendation_id}.json", payload)
    latest_path = _write_json(STATUS / "latest.json", payload)
    summary = {
        "latest_recommendation_id": result.recommendation_id,
        "latest_routing_request_id": result.routing_request_id,
        "recommended_provider": result.recommended_provider,
        "human_review_required": result.human_review_required,
        "boundary_review_required": result.boundary_review_required,
        "recommendation_only": True,
        "dispatch_mutated": False,
        "orchestrator_mutated": False,
    }
    summary_path = _write_json(STATUS / "summary.json", summary)
    report_path = REPORTS / f"{result.recommendation_id}.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(explain_provider_routing_recommendation(result), encoding="utf-8")
    payload.update({
        "recommendation_path": str(recommendation_path.relative_to(ROOT)),
        "latest_status_path": str(latest_path.relative_to(ROOT)),
        "summary_path": str(summary_path.relative_to(ROOT)),
        "report_path": str(report_path.relative_to(ROOT)),
    })
    return payload
