"""Engineering provider routing runtime.

Uses Engineering Capacity Runtime evidence to recommend local RTX 4090/Ollama
execution or cloud Codex escalation. Recommendation only; never dispatches.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from estate.core.paths import ESTATE_ROOT
from estate.core.engineering_capacity_runtime import generate_engineering_capacity_dashboard
from estate.core.provider_routing_recommendations import ProviderRoutingRecommendationRequest, evaluate_provider_routing_recommendation
from estate.core.provider_health import _write_json, utc_now_iso
from estate.core.engineering_provider_health_runtime import load_current_provider_health

RUNTIME_JSON = Path("runtime/engineering_provider_routing/latest.json")
RUNTIME_MD = Path("runtime/engineering_provider_routing/latest.md")
OFFICE_HANDOFF_MD = Path("operations/engineering_capacity/provider_routing.md")


def _root(root: str | Path | None = None) -> Path:
    return Path(root) if root is not None else (ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd())


def _local_available(dashboard: dict[str, Any]) -> bool:
    providers = dashboard.get("local_worker_providers") or []
    workers = dashboard.get("workers") or []
    return any((p.get("health_status") in {"available", "degraded", "unknown"}) and p.get("capacity_state") in {"idle", "available", "unknown"} for p in providers) or any(w.get("status") == "idle" and not w.get("stale") for w in workers)


def _cloud_constrained(dashboard: dict[str, Any]) -> bool:
    return (dashboard.get("summary") or {}).get("constrained_cloud_codex_seat_count", 0) > 0


def recommend_engineering_provider(request_payload: dict[str, Any] | ProviderRoutingRecommendationRequest, *, root: str | Path | None = None, stale_after_minutes: int = 30, write: bool = True) -> dict[str, Any]:
    root_path = _root(root)
    request = request_payload if isinstance(request_payload, ProviderRoutingRecommendationRequest) else ProviderRoutingRecommendationRequest.from_dict(request_payload)
    dashboard = generate_engineering_capacity_dashboard(root=root_path, stale_after_minutes=stale_after_minutes, write=True)
    health = load_current_provider_health(root=root_path)
    health_by_id = {p.get("provider_id"): p for p in health.get("providers", [])}
    base = evaluate_provider_routing_recommendation(request).to_dict()
    local_available = _local_available(dashboard)
    cloud_constrained = _cloud_constrained(dashboard)

    if request.requires_human_authority or request.requires_boundary_review:
        final_provider = "human_review"
        reason = "Authority or boundary review required before any provider movement."
    elif request.requires_local_runtime or request.requires_gpu:
        final_provider = "local_ollama_gpu" if local_available else "human_review"
        reason = "Request requires local runtime/GPU evidence; local RTX 4090 lane is preferred when available."
    elif request.requires_repo_write and not cloud_constrained:
        candidate = health_by_id.get("codex_cloud_web", {})
        if candidate.get("health_state") in {"offline", "maintenance"} or candidate.get("authentication_state") in {"invalid", "missing", "unauthenticated"}:
            final_provider = "human_review"
            reason = "Cloud Codex is excluded by health evidence: " + "; ".join(candidate.get("health_reasons") or ["missing health evidence"])
        else:
            final_provider = "codex_cloud_web"
            reason = "Repository write is requested and cloud Codex capacity/health evidence does not block recommendation."
    elif request.requires_repo_write and local_available:
        final_provider = "local_ollama_gpu"
        reason = "Cloud Codex capacity is constrained; use local RTX 4090 lane for bounded decomposition/review before escalation."
    else:
        final_provider = base["recommended_provider"]
        reason = "Base provider-routing recommendation is consistent with current capacity evidence."

    selected_health = health_by_id.get(final_provider, {}) if final_provider not in {"human_review", "deterministic_local_tooling", "chatgpt_planning"} else {}
    if selected_health and ((selected_health.get("health_state") == "maintenance" or (selected_health.get("health_state") == "offline" and "runtime/providers/health/records" in (selected_health.get("evidence_refs") or [])) or selected_health.get("authentication_state") in {"invalid", "missing", "unauthenticated"})):
        reason = f"{final_provider} is excluded by health evidence: " + "; ".join(selected_health.get("health_reasons") or ["unhealthy provider"])
        final_provider = "human_review"

    payload = {
        "version": 1,
        "generated_at": utc_now_iso(),
        "routing_request_id": request.routing_request_id,
        "recommended_provider": final_provider,
        "base_recommended_provider": base["recommended_provider"],
        "capacity_reason": reason,
        "engineering_capacity_summary": dashboard.get("summary"),
        "engineering_provider_health": {"providers": health_by_id, "source_artifact": "runtime/provider_health/current.json"},
        "constraints": {"advisory_only": True, "does_not_dispatch": True, "traffic_controller_decides_movement": True},
        "source_artifacts": ["runtime/engineering_capacity/dashboard.json"],
    }
    if write:
        _write_json(root_path / RUNTIME_JSON, payload)
        text = format_engineering_provider_routing(payload)
        for rel in (RUNTIME_MD, OFFICE_HANDOFF_MD):
            path = root_path / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
    return payload


def format_engineering_provider_routing(payload: dict[str, Any]) -> str:
    s = payload.get("engineering_capacity_summary") or {}
    return (
        "# Engineering Provider Routing Recommendation\n\n"
        f"Generated: {payload.get('generated_at')}\n\n"
        "Advisory only: Traffic Controller / Operations Manager decides movement; this runtime does not dispatch.\n\n"
        f"- Routing request: {payload.get('routing_request_id')}\n"
        f"- Recommended provider: {payload.get('recommended_provider')}\n"
        f"- Base recommendation: {payload.get('base_recommended_provider')}\n"
        f"- Capacity reason: {payload.get('capacity_reason')}\n"
        f"- Cloud Codex seats: {s.get('cloud_codex_seat_count', 0)}\n"
        f"- Constrained Cloud Codex seats: {s.get('constrained_cloud_codex_seat_count', 0)}\n"
        f"- Idle workers: {s.get('idle_worker_count', 0)}\n"
    )
