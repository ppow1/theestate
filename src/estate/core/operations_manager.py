from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any
from uuid import uuid4

from estate.core.operational_events import utc_now_iso, validate_iso_timestamp
from estate.core.traffic_controller import ALLOWED_TARGET_TYPES
from estate.core.worker_assignments import ALLOWED_CLASSIFICATIONS, ALLOWED_PRIORITIES

ALLOWED_DECISION_TYPES = {"assign", "reprioritize", "hold", "release", "defer", "cancel", "escalate", "request_boundary_review", "request_revision", "request_validation", "authorize_dispatch"}


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
    schema_version: str = "estate.operations-control.decision.v1"
    decision_state: str = "recorded"
    institutional_acceptance_state: str = "not_granted"
    technical_execution: bool = False
    grace_objective_id: str | None = None
    grace_action_id: str | None = None
    helen_determination_id: str | None = None
    ptm_readiness: dict[str, Any] | None = None
    engineering_commission_id: str | None = None
    engineering_authorization_id: str | None = None
    dispatch_id: str | None = None
    selected_provider_id: str | None = None
    selected_adapter_reference: str | None = None
    authorization_reference: str | None = None
    decision_reference: str | None = None
    prompt_source: str | None = None
    prompt_source_digest: str | None = None
    allowed_read_paths: list[str] | None = None
    allowed_write_paths: list[str] | None = None
    expected_outputs: list[str] | None = None
    authorized_at: str | None = None
    expires_at: str | None = None
    idempotency_key: str | None = None
    record_digest: str | None = None
    parent_operations_decision_id: str | None = None
    provider_extension: dict[str, Any] | None = None

    @classmethod
    def create(cls, *, decided_by: str, decision_type: str, target_type: str, reason: str, classification: str = "Estate Internal", **kwargs: Any) -> "OperationsDecision":
        return cls(decision_id=f"opdec-{uuid4().hex}", created_at=utc_now_iso(), decided_by=decided_by, decision_type=decision_type, target_type=target_type, classification=classification, reason=reason, **kwargs)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "OperationsDecision":
        decision = cls(decision_id=_require_str(data, "decision_id"), created_at=_require_str(data, "created_at"), decided_by=_require_str(data, "decided_by"), decision_type=_require_str(data, "decision_type"), target_type=_require_str(data, "target_type"), target_id=_optional_str(data, "target_id"), classification=_require_str(data, "classification"), priority=data.get("priority") or "normal", reason=_require_str(data, "reason"), next_state=_optional_str(data, "next_state"), assignment_label=_optional_str(data, "assignment_label"), provider_id=_optional_str(data, "provider_id"), worker_id=_optional_str(data, "worker_id"), seat_id=_optional_str(data, "seat_id"), requires_boundary_review=bool(data.get("requires_boundary_review", False)), requires_steward_attention=bool(data.get("requires_steward_attention", False)), summary_safe=bool(data.get("summary_safe", False)), metadata=data.get("metadata") or {}, schema_version=data.get("schema_version") or "estate.operations-control.decision.v1", decision_state=data.get("decision_state") or "recorded", institutional_acceptance_state=data.get("institutional_acceptance_state") or "not_granted", technical_execution=bool(data.get("technical_execution", False)), grace_objective_id=_optional_str(data, "grace_objective_id"), grace_action_id=_optional_str(data, "grace_action_id"), helen_determination_id=_optional_str(data, "helen_determination_id"), ptm_readiness=data.get("ptm_readiness"), engineering_commission_id=_optional_str(data, "engineering_commission_id"), engineering_authorization_id=_optional_str(data, "engineering_authorization_id"), dispatch_id=_optional_str(data, "dispatch_id"), selected_provider_id=_optional_str(data, "selected_provider_id"), selected_adapter_reference=_optional_str(data, "selected_adapter_reference"), authorization_reference=_optional_str(data, "authorization_reference"), decision_reference=_optional_str(data, "decision_reference"), prompt_source=_optional_str(data, "prompt_source"), prompt_source_digest=_optional_str(data, "prompt_source_digest"), allowed_read_paths=data.get("allowed_read_paths"), allowed_write_paths=data.get("allowed_write_paths"), expected_outputs=data.get("expected_outputs"), authorized_at=_optional_str(data, "authorized_at"), expires_at=_optional_str(data, "expires_at"), idempotency_key=_optional_str(data, "idempotency_key"), record_digest=_optional_str(data, "record_digest"), parent_operations_decision_id=_optional_str(data, "parent_operations_decision_id"), provider_extension=data.get("provider_extension"))
        decision.validate(); return decision

    def validate(self) -> None:
        validate_iso_timestamp(self.created_at, "created_at")
        if self.decision_type not in ALLOWED_DECISION_TYPES: raise ValueError(f"unknown decision type '{self.decision_type}'")
        if self.target_type not in ALLOWED_TARGET_TYPES: raise ValueError(f"unknown target type '{self.target_type}'")
        if self.classification not in ALLOWED_CLASSIFICATIONS: raise ValueError(f"unknown classification '{self.classification}'")
        if self.priority not in ALLOWED_PRIORITIES: raise ValueError(f"unknown priority '{self.priority}'")
        if not isinstance(self.metadata, dict): raise ValueError("metadata must be an object")
        if self.schema_version != "estate.operations-control.decision.v1": raise ValueError("unsupported Operations decision schema")
        if self.institutional_acceptance_state != "not_granted": raise ValueError("institutional acceptance must remain not_granted")
        if self.decision_state not in {"recorded", "authorized_for_dispatch", "expired", "rejected", "cancelled"}: raise ValueError("unknown decision state")
        if self.technical_execution and not isinstance(self.provider_extension, dict): raise ValueError("technical execution requires provider extension")

    def to_dict(self) -> dict[str, Any]:
        self.validate(); return asdict(self)
