from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any
from uuid import uuid4

from estate.core.operational_events import utc_now_iso, validate_iso_timestamp
from estate.core.worker_assignments import ALLOWED_CLASSIFICATIONS, ALLOWED_PRIORITIES

ALLOWED_ACTION_TYPES = {"assign", "reprioritize", "hold", "release", "defer", "cancel", "escalate", "request_boundary_review", "request_revision", "request_validation", "no_action"}
ALLOWED_TARGET_TYPES = {"intake", "schedule", "dispatch", "assignment", "provider", "work_package", "system"}
SENSITIVE_CLASSIFICATIONS = {"Restricted", "Steward Only", "Local Only"}


def _require_str(data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} is required")
    return value


def _optional_str(data: dict[str, Any], key: str) -> str | None:
    value = data.get(key)
    if value in (None, ""):
        return None
    if not isinstance(value, str):
        raise ValueError(f"{key} must be a string")
    return value


@dataclass
class RecommendedAction:
    action_id: str
    action_type: str
    target_type: str
    reason: str
    safe_summary: str
    target_id: str | None = None
    priority: str = "normal"
    requires_steward_approval: bool = False
    requires_boundary_review: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(cls, *, action_type: str, target_type: str, reason: str, safe_summary: str, **kwargs: Any) -> "RecommendedAction":
        return cls(action_id=f"opact-{uuid4().hex}", action_type=action_type, target_type=target_type, reason=reason, safe_summary=safe_summary, **kwargs)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RecommendedAction":
        action = cls(action_id=_require_str(data, "action_id"), action_type=_require_str(data, "action_type"), target_type=_require_str(data, "target_type"), target_id=_optional_str(data, "target_id"), priority=data.get("priority") or "normal", reason=_require_str(data, "reason"), requires_steward_approval=bool(data.get("requires_steward_approval", False)), requires_boundary_review=bool(data.get("requires_boundary_review", False)), safe_summary=_require_str(data, "safe_summary"), metadata=data.get("metadata") or {})
        action.validate(); return action

    def validate(self) -> None:
        if self.action_type not in ALLOWED_ACTION_TYPES: raise ValueError(f"unknown action type '{self.action_type}'")
        if self.target_type not in ALLOWED_TARGET_TYPES: raise ValueError(f"unknown target type '{self.target_type}'")
        if self.priority not in ALLOWED_PRIORITIES: raise ValueError(f"unknown priority '{self.priority}'")
        if not isinstance(self.metadata, dict): raise ValueError("metadata must be an object")

    def to_dict(self) -> dict[str, Any]:
        self.validate(); return asdict(self)


@dataclass
class OperationsReview:
    review_id: str
    created_at: str
    classification: str
    created_by: str = "traffic_controller.operations_manager"
    source_artifacts: list[str] = field(default_factory=list)
    pending_intake_count: int = 0
    blocked_intake_count: int = 0
    scheduled_count: int = 0
    dispatch_pending_count: int = 0
    assignment_active_count: int = 0
    assignment_blocked_count: int = 0
    provider_available_count: int = 0
    provider_blocked_count: int = 0
    provider_saturated_count: int = 0
    requires_steward_attention: bool = False
    requires_boundary_review: bool = False
    recommended_actions: list[RecommendedAction] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(cls, *, classification: str = "Estate Internal", **kwargs: Any) -> "OperationsReview":
        return cls(review_id=f"oprev-{uuid4().hex}", created_at=utc_now_iso(), classification=classification, **kwargs)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "OperationsReview":
        review = cls(review_id=_require_str(data, "review_id"), created_at=_require_str(data, "created_at"), created_by=data.get("created_by") or "traffic_controller.operations_manager", classification=_require_str(data, "classification"), source_artifacts=list(data.get("source_artifacts") or []), pending_intake_count=int(data.get("pending_intake_count", 0)), blocked_intake_count=int(data.get("blocked_intake_count", 0)), scheduled_count=int(data.get("scheduled_count", 0)), dispatch_pending_count=int(data.get("dispatch_pending_count", 0)), assignment_active_count=int(data.get("assignment_active_count", 0)), assignment_blocked_count=int(data.get("assignment_blocked_count", 0)), provider_available_count=int(data.get("provider_available_count", 0)), provider_blocked_count=int(data.get("provider_blocked_count", 0)), provider_saturated_count=int(data.get("provider_saturated_count", 0)), requires_steward_attention=bool(data.get("requires_steward_attention", False)), requires_boundary_review=bool(data.get("requires_boundary_review", False)), recommended_actions=[RecommendedAction.from_dict(x) for x in data.get("recommended_actions", [])], warnings=list(data.get("warnings") or []), errors=list(data.get("errors") or []), metadata=data.get("metadata") or {})
        review.validate(); return review

    def validate(self) -> None:
        validate_iso_timestamp(self.created_at, "created_at")
        if self.classification not in ALLOWED_CLASSIFICATIONS: raise ValueError(f"unknown classification '{self.classification}'")
        for action in self.recommended_actions: action.validate()
        if not isinstance(self.metadata, dict): raise ValueError("metadata must be an object")

    def to_dict(self) -> dict[str, Any]:
        self.validate(); data = asdict(self); data["recommended_actions"] = [a.to_dict() for a in self.recommended_actions]; return data


def redact_summary(classification: str, text: str, metadata: dict[str, Any] | None = None) -> str:
    if classification in SENSITIVE_CLASSIFICATIONS and not ((metadata or {}).get("summary_safe") is True):
        return "Sensitive operations summary redacted."
    return text
