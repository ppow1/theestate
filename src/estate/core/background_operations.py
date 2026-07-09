"""Models for the Estate background operations event runtime.

The models in this module are deliberately provider-neutral.  They describe
observed events, standing watches, and governed requests; they do not execute
providers, approve movement, or create institutional truth.
"""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

ALLOWED_CLASSIFICATIONS = {"Public", "Estate Internal", "Restricted", "Steward Only", "Local Only", "Sensitive", "Private"}
ALLOWED_EVENT_TYPES = {
    "time_tick", "artifact_changed", "recommendation_created", "movement_decision_needed",
    "validation_stale", "ring2_review_needed", "provider_capacity_warning",
    "assignment_gap_detected", "background_request_created", "background_request_completed",
    "background_request_blocked",
    "operational_target_watch_needed", "git_hygiene_review_needed", "post_merge_audit_needed",
    "validation_evidence_root_drift", "steward_acceptance_needed",
}
ALLOWED_REQUEST_TYPES = {
    "staff_update_request", "validation_review_request", "traffic_controller_review_request",
    "routing_review_request", "provider_capacity_review_request", "worker_assignment_review_request",
    "steward_attention_request", "post_merge_audit_request",
}
SENSITIVE_TERMS = ("resident", "character", "persona", "identity", "continuity", "private", "sensitive")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def validate_iso_timestamp(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} is required")
    datetime.fromisoformat(value.replace("Z", "+00:00"))


def _require_str(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} is required")
    return value


def is_sensitive_subject(*values: Any) -> bool:
    text = " ".join(str(v or "") for v in values).lower()
    return any(term in text for term in SENSITIVE_TERMS)


@dataclass
class BackgroundOperationEvent:
    event_id: str
    event_type: str
    source: str
    source_artifact: str | None
    subject_type: str
    subject_id: str
    classification: str
    created_at: str
    summary: str
    payload: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(cls, *, event_type: str, source: str, subject_type: str, subject_id: str, classification: str, summary: str, source_artifact: str | None = None, payload: dict[str, Any] | None = None, metadata: dict[str, Any] | None = None) -> "BackgroundOperationEvent":
        return cls(f"boe-{uuid4().hex}", event_type, source, source_artifact, subject_type, subject_id, classification, utc_now_iso(), summary, payload or {}, metadata or {})

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BackgroundOperationEvent":
        ev = cls(**{k: data.get(k) for k in cls.__dataclass_fields__})  # type: ignore[attr-defined]
        ev.validate(); return ev

    def validate(self) -> None:
        for key in ["event_id", "event_type", "source", "subject_type", "subject_id", "classification", "created_at", "summary"]:
            _require_str(getattr(self, key), key)
        if self.event_type not in ALLOWED_EVENT_TYPES:
            raise ValueError(f"unknown event_type '{self.event_type}'")
        if self.classification not in ALLOWED_CLASSIFICATIONS:
            raise ValueError(f"unknown classification '{self.classification}'")
        validate_iso_timestamp(self.created_at, "created_at")
        if not isinstance(self.payload, dict) or not isinstance(self.metadata, dict):
            raise ValueError("payload and metadata must be objects")

    def to_dict(self) -> dict[str, Any]:
        self.validate(); return asdict(self)


@dataclass
class BackgroundOperationWatch:
    watch_id: str
    name: str
    enabled: bool
    trigger_type: str
    source_paths: list[str]
    conditions: dict[str, Any]
    action_type: str
    cooldown_seconds: int
    classification: str
    last_triggered_at: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BackgroundOperationWatch":
        watch = cls(**{k: data.get(k) for k in cls.__dataclass_fields__})  # type: ignore[attr-defined]
        watch.validate(); return watch

    def validate(self) -> None:
        for key in ["watch_id", "name", "trigger_type", "action_type", "classification"]:
            _require_str(getattr(self, key), key)
        if not isinstance(self.enabled, bool): raise ValueError("enabled must be boolean")
        if not isinstance(self.source_paths, list): raise ValueError("source_paths must be a list")
        if not isinstance(self.conditions, dict) or not isinstance(self.metadata, dict): raise ValueError("conditions and metadata must be objects")
        if int(self.cooldown_seconds) < 0: raise ValueError("cooldown_seconds must be non-negative")
        if self.classification not in ALLOWED_CLASSIFICATIONS: raise ValueError(f"unknown classification '{self.classification}'")
        if self.last_triggered_at: validate_iso_timestamp(self.last_triggered_at, "last_triggered_at")

    def to_dict(self) -> dict[str, Any]:
        self.validate(); return asdict(self)


@dataclass
class BackgroundOperationRequest:
    request_id: str
    request_type: str
    source_event_id: str
    watch_id: str
    target_role: str
    target_subsystem: str
    recommended_provider: str | None
    requires_human_review: bool
    requires_boundary_review: bool
    priority: str
    classification: str
    summary: str
    requested_action: str
    source_artifacts: list[str]
    created_at: str
    status: str
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(cls, *, request_type: str, source_event_id: str, watch_id: str, target_role: str, target_subsystem: str, priority: str, classification: str, summary: str, requested_action: str, source_artifacts: list[str] | None = None, recommended_provider: str | None = None, requires_human_review: bool = True, requires_boundary_review: bool = False, metadata: dict[str, Any] | None = None) -> "BackgroundOperationRequest":
        sensitive = is_sensitive_subject(summary, requested_action, target_role, target_subsystem, metadata)
        return cls(f"bor-{uuid4().hex}", request_type, source_event_id, watch_id, target_role, target_subsystem, recommended_provider, bool(requires_human_review or sensitive), bool(requires_boundary_review or sensitive), priority, classification, summary, requested_action, source_artifacts or [], utc_now_iso(), "open", metadata or {})

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BackgroundOperationRequest":
        req = cls(**{k: data.get(k) for k in cls.__dataclass_fields__})  # type: ignore[attr-defined]
        req.validate(); return req

    def validate(self) -> None:
        for key in ["request_id", "request_type", "source_event_id", "watch_id", "target_role", "target_subsystem", "priority", "classification", "summary", "requested_action", "created_at", "status"]:
            _require_str(getattr(self, key), key)
        if self.request_type not in ALLOWED_REQUEST_TYPES: raise ValueError(f"unknown request_type '{self.request_type}'")
        if self.classification not in ALLOWED_CLASSIFICATIONS: raise ValueError(f"unknown classification '{self.classification}'")
        validate_iso_timestamp(self.created_at, "created_at")
        if not isinstance(self.source_artifacts, list): raise ValueError("source_artifacts must be list")
        if not isinstance(self.metadata, dict): raise ValueError("metadata must be object")

    def to_dict(self) -> dict[str, Any]:
        self.validate(); return asdict(self)


def default_background_operation_watches() -> list[BackgroundOperationWatch]:
    base = dict(enabled=True, cooldown_seconds=3600, classification="Estate Internal", last_triggered_at=None, metadata={})
    specs = [
        ("pending_routing_recommendation_watch", "Pending routing recommendation", "artifact_status", ["runtime/provider_routing/status/summary.json", "runtime/provider_routing/status/latest.json"], {"watch_kind": "pending_routing_recommendation"}, "routing_review_request"),
        ("missing_ring2_review_watch", "Missing Ring 2 review", "artifact_status", ["runtime/validation/work_packages", "runtime/validation/reviews"], {"watch_kind": "missing_ring2_review"}, "validation_review_request"),
        ("stale_validation_artifact_watch", "Stale validation artifact", "time_tick", ["runtime/validation/work_packages"], {"watch_kind": "stale_validation_artifact", "stale_after_seconds": 86400}, "validation_review_request"),
        ("provider_capacity_warning_watch", "Provider capacity warning", "artifact_status", ["runtime/providers/health/status/summary.json", "runtime/providers/health/status/latest_capacity.json"], {"watch_kind": "provider_capacity_warning"}, "provider_capacity_review_request"),
        ("worker_assignment_gap_watch", "Worker assignment gap", "artifact_status", ["runtime/workers/assignments/status/board.json", "collaboration/work_packages/pending"], {"watch_kind": "worker_assignment_gap"}, "worker_assignment_review_request"),
        ("pending_movement_decision_watch", "Pending movement decision", "artifact_status", ["runtime/provider_routing/status/summary.json", "runtime/traffic_controller/movement/status/summary.json"], {"watch_kind": "pending_movement_decision"}, "traffic_controller_review_request"),
        ("operational_target_watch", "Operational target watch", "artifact_status", ["runtime/operational_targets/registry.json"], {"watch_kind": "operational_target_watch_needed"}, "post_merge_audit_request"),
    ]
    return [BackgroundOperationWatch(wid, name, **base, trigger_type=trig, source_paths=paths, conditions=conds, action_type=action) for wid, name, trig, paths, conds, action in specs]
