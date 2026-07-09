"""Deterministic provider routing recommendations.

Recommendations are evidence for Traffic Controller / Operations Manager decisions.
They do not schedule, dispatch, assign, or execute providers.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
from typing import Any, Iterable

ALLOWED_PROVIDERS = (
    "deterministic_local_tooling",
    "local_ollama_gpu",
    "chatgpt_planning",
    "codex_cloud_web",
    "codex_cli",
    "human_review",
)

VALIDATION_RINGS = {
    "deterministic_local_tooling": ["ring_0_static_structural", "ring_1_deterministic_tests"],
    "local_ollama_gpu": ["ring_2_local_gpu_reasoning_review"],
    "chatgpt_planning": ["planning_review"],
    "codex_cloud_web": ["ring_0_static_structural", "ring_1_deterministic_tests", "ring_2_local_gpu_reasoning_review"],
    "codex_cli": ["ring_0_static_structural", "ring_1_deterministic_tests", "ring_2_local_gpu_reasoning_review", "ring_3_cli_escalation_validation"],
    "human_review": ["ring_4_institutional_acceptance"],
}

@dataclass(frozen=True)
class ProviderRoutingRecommendationRequest:
    routing_request_id: str
    source_artifact: str = ""
    work_package_id: str = ""
    mission_summary: str = ""
    work_type: str = ""
    requires_repo_write: bool = False
    requires_local_runtime: bool = False
    requires_gpu: bool = False
    requires_network: bool = False
    requires_large_context: bool = False
    requires_human_authority: bool = False
    requires_boundary_review: bool = False
    classification: str = "Estate Internal"
    estimated_complexity: str = "normal"
    estimated_context_size: str = "bounded"
    expected_artifacts: list[str] = field(default_factory=list)
    allowed_paths: list[str] = field(default_factory=list)
    blocked_paths: list[str] = field(default_factory=list)
    validation_required: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ProviderRoutingRecommendationRequest":
        data = dict(payload)
        if not data.get("routing_request_id"):
            raise ValueError("routing_request_id is required")
        for key in ("expected_artifacts", "allowed_paths", "blocked_paths"):
            value = data.get(key) or []
            data[key] = list(value) if isinstance(value, (list, tuple)) else [str(value)]
        data["metadata"] = dict(data.get("metadata") or {})
        allowed = {f.name for f in cls.__dataclass_fields__.values()}
        return cls(**{k: v for k, v in data.items() if k in allowed})

    def to_dict(self) -> dict[str, Any]:
        return {field_name: getattr(self, field_name) for field_name in self.__dataclass_fields__}

@dataclass(frozen=True)
class ProviderRoutingRecommendationResult:
    routing_request_id: str
    recommendation_id: str
    recommended_provider: str
    alternate_providers: list[str]
    provider_rationale: str
    capacity_note: str
    local_runtime_required: bool
    human_review_required: bool
    boundary_review_required: bool
    validation_rings_required: list[str]
    not_recommended: dict[str, str]
    created_at: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {field_name: getattr(self, field_name) for field_name in self.__dataclass_fields__}

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ProviderRoutingRecommendationResult":
        return cls(**payload)


def _contains_any(values: Iterable[str], needles: Iterable[str]) -> bool:
    text = " ".join(str(v).lower() for v in values)
    return any(needle in text for needle in needles)


def _stable_recommendation_id(request: ProviderRoutingRecommendationRequest, provider: str) -> str:
    digest = hashlib.sha256(f"{request.routing_request_id}:{provider}".encode("utf-8")).hexdigest()[:12]
    return f"prr-{digest}"


def evaluate_provider_routing_recommendation(request: ProviderRoutingRecommendationRequest | dict[str, Any]) -> ProviderRoutingRecommendationResult:
    if isinstance(request, dict):
        request = ProviderRoutingRecommendationRequest.from_dict(request)
    work_type = request.work_type.lower()
    summary = request.mission_summary.lower()
    artifacts = [*request.expected_artifacts, *request.allowed_paths]
    decision_terms = ("authority", "policy decision", "boundary", "classification decision", "resident identity", "acceptance", "steward acceptance")
    validation_terms = ("test", "pytest", "schema", "receipt", "validation", "file check", "static", "compile")
    review_terms = ("bounded reasoning", "decomposition review", "classification review", "evidence review", "review")
    planning_terms = ("planning", "architecture", "decomposition", "governance", "work-package", "work package", "prose")
    implementation_terms = ("implementation", "repository", "code", "contract", "feature", "bugfix")

    human = request.requires_human_authority or request.requires_boundary_review or _contains_any([work_type, summary, request.classification], decision_terms)
    if human:
        provider = "human_review"
        rationale = "Human review is required because the request touches authority, policy, boundary, classification, resident identity, or institutional acceptance."
    elif _contains_any([work_type, summary, *artifacts], validation_terms) and not request.requires_repo_write:
        provider = "deterministic_local_tooling"
        rationale = "Deterministic local tooling is the best fit for tests, file checks, schemas, receipts, and static validation without live provider execution."
    elif request.requires_gpu or _contains_any([work_type, summary], review_terms):
        provider = "local_ollama_gpu"
        rationale = "Local RTX 4090/Ollama is the best fit for bounded reasoning, decomposition, classification, or validation evidence review."
    elif _contains_any([work_type, summary], planning_terms) and not request.requires_repo_write:
        provider = "chatgpt_planning"
        rationale = "ChatGPT planning is the best fit for architectural planning, decomposition, governance prose, and provider-neutral package design."
    elif request.requires_repo_write and request.requires_local_runtime:
        provider = "codex_cli"
        rationale = "Codex CLI may be appropriate because implementation materially requires local runtime context; use cautiously and only after approved escalation."
    elif request.requires_repo_write or _contains_any([work_type, summary], implementation_terms):
        provider = "codex_cloud_web"
        rationale = "Codex Cloud/Web is preferred for broad repository implementation when local runtime is not required."
    else:
        provider = "deterministic_local_tooling"
        rationale = "Deterministic local tooling is the conservative default for bounded local checks and validation evidence."

    alternates = [p for p in ALLOWED_PROVIDERS if p != provider]
    not_rec = {}
    if provider != "codex_cli":
        not_rec["codex_cli"] = "Protected for local-runtime-required implementation or approved escalation to avoid accidental premium CLI capacity burn."
    if provider != "human_review" and human is False:
        not_rec["human_review"] = "Not required unless authority, boundary, classification, identity, or acceptance decisions are present."
    if request.requires_network:
        not_rec["live_network_provider_calls"] = "Network access requirement is recorded, but this evaluator does not call live network services."

    rings = list(VALIDATION_RINGS[provider])
    if request.validation_required and "ring_1_deterministic_tests" not in rings:
        rings.append("ring_1_deterministic_tests")
    result = ProviderRoutingRecommendationResult(
        routing_request_id=request.routing_request_id,
        recommendation_id=_stable_recommendation_id(request, provider),
        recommended_provider=provider,
        alternate_providers=alternates,
        provider_rationale=rationale,
        capacity_note="Recommendation only: Traffic Controller / Operations Manager decides movement; no scheduling, dispatch, assignment, provider execution, live network, GPU, Ollama, ChatGPT, or Codex CLI call occurred.",
        local_runtime_required=request.requires_local_runtime,
        human_review_required=provider == "human_review" or request.requires_human_authority,
        boundary_review_required=request.requires_boundary_review,
        validation_rings_required=rings,
        not_recommended=not_rec,
        created_at=datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        metadata={"allowed_providers": list(ALLOWED_PROVIDERS), "recommendation_only": True, "dispatch_mutated": False, "orchestrator_mutated": False, **request.metadata},
    )
    return result


def explain_provider_routing_recommendation(result: ProviderRoutingRecommendationResult | dict[str, Any]) -> str:
    if isinstance(result, dict):
        result = ProviderRoutingRecommendationResult.from_dict(result)
    lines = [
        f"# Provider Routing Recommendation {result.recommendation_id}",
        "",
        f"Recommended provider: `{result.recommended_provider}`",
        "",
        result.provider_rationale,
        "",
        f"Capacity note: {result.capacity_note}",
        "",
        "This recommendation is evidence for a decision. It is not the decision.",
    ]
    return "\n".join(lines) + "\n"
