from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any
from uuid import uuid4

from estate.core.operational_events import utc_now_iso, validate_iso_timestamp
from estate.core.traffic_controller import ALLOWED_TARGET_TYPES
from estate.core.worker_assignments import ALLOWED_CLASSIFICATIONS, ALLOWED_PRIORITIES

ALLOWED_DECISION_TYPES = {"assign", "reprioritize", "hold", "release", "defer", "cancel", "escalate", "request_boundary_review", "request_revision", "request_validation"}


def _require_str(data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip(): raise ValueError(f"{key} is required")
    return value


def _optional_str(data: dict[str, Any], key: str) -> str | None:
    value = data.get(key)
    if value in (None, ""): return None
    if not isinstance(value, str): raise ValueError(f"{key} must be a string")
    return value


@dataclass
class OperationsDecision:
    decision_id: str
    created_at: str
    decided_by: str
    decision_type: str
    target_type: str
    classification: str
    reason: str
    target_id: str | None = None
    priority: str = "normal"
    next_state: str | None = None
    assignment_label: str | None = None
    provider_id: str | None = None
    worker_id: str | None = None
    seat_id: str | None = None
    requires_boundary_review: bool = False
    requires_steward_attention: bool = False
    summary_safe: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(cls, *, decided_by: str, decision_type: str, target_type: str, reason: str, classification: str = "Estate Internal", **kwargs: Any) -> "OperationsDecision":
        return cls(decision_id=f"opdec-{uuid4().hex}", created_at=utc_now_iso(), decided_by=decided_by, decision_type=decision_type, target_type=target_type, classification=classification, reason=reason, **kwargs)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "OperationsDecision":
        decision = cls(decision_id=_require_str(data, "decision_id"), created_at=_require_str(data, "created_at"), decided_by=_require_str(data, "decided_by"), decision_type=_require_str(data, "decision_type"), target_type=_require_str(data, "target_type"), target_id=_optional_str(data, "target_id"), classification=_require_str(data, "classification"), priority=data.get("priority") or "normal", reason=_require_str(data, "reason"), next_state=_optional_str(data, "next_state"), assignment_label=_optional_str(data, "assignment_label"), provider_id=_optional_str(data, "provider_id"), worker_id=_optional_str(data, "worker_id"), seat_id=_optional_str(data, "seat_id"), requires_boundary_review=bool(data.get("requires_boundary_review", False)), requires_steward_attention=bool(data.get("requires_steward_attention", False)), summary_safe=bool(data.get("summary_safe", False)), metadata=data.get("metadata") or {})
        decision.validate(); return decision

    def validate(self) -> None:
        validate_iso_timestamp(self.created_at, "created_at")
        if self.decision_type not in ALLOWED_DECISION_TYPES: raise ValueError(f"unknown decision type '{self.decision_type}'")
        if self.target_type not in ALLOWED_TARGET_TYPES: raise ValueError(f"unknown target type '{self.target_type}'")
        if self.classification not in ALLOWED_CLASSIFICATIONS: raise ValueError(f"unknown classification '{self.classification}'")
        if self.priority not in ALLOWED_PRIORITIES: raise ValueError(f"unknown priority '{self.priority}'")
        if not isinstance(self.metadata, dict): raise ValueError("metadata must be an object")

    def to_dict(self) -> dict[str, Any]:
        self.validate(); return asdict(self)
