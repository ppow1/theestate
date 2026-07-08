from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any
from uuid import uuid4

from estate.core.operational_events import validate_iso_timestamp
from estate.core.provider_health import utc_now_iso

ALLOWED_CLASSIFICATIONS = {"Public", "Estate Internal", "Restricted", "Steward Only", "Local Only"}
ALLOWED_PRIORITIES = {"low", "normal", "high", "urgent"}
ALLOWED_ASSIGNMENT_STATES = {"assigned", "accepted", "running", "blocked", "awaiting_approval", "reviewing", "validation", "completed", "failed", "cancelled", "deferred"}
SENSITIVE_CLASSIFICATIONS = {"Restricted", "Steward Only", "Local Only"}
ACTIVE_STATES = {"assigned", "accepted", "running", "reviewing", "validation"}


def _require_str(data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} is required")
    return value


def _optional_str(data: dict[str, Any], key: str) -> str | None:
    value = data.get(key)
    if value is None or value == "":
        return None
    if not isinstance(value, str):
        raise ValueError(f"{key} must be a string")
    return value


def _string_list(data: dict[str, Any], key: str) -> list[str]:
    value = data.get(key) or []
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"{key} must be a list of strings")
    return value


@dataclass
class WorkerAssignmentRecord:
    assignment_id: str
    created_at: str
    updated_at: str
    assigned_by: str
    assigned_to: str
    classification: str
    state: str
    mission: str
    summary: str
    assignment_label: str | None = None
    worker_id: str | None = None
    worker_role: str | None = None
    provider_id: str | None = None
    provider_type: str | None = None
    seat_id: str | None = None
    profile_id: str | None = None
    work_package_id: str | None = None
    work_package_path: str | None = None
    intake_id: str | None = None
    schedule_id: str | None = None
    priority: str = "normal"
    expected_outputs: list[str] = field(default_factory=list)
    validation_required: bool = True
    requires_attention: bool = False
    blocked_reason: str | None = None
    artifact_paths: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(cls, *, assigned_by: str, assigned_to: str, mission: str, summary: str, classification: str = "Estate Internal", state: str = "assigned", assignment_id: str | None = None, **kwargs: Any) -> "WorkerAssignmentRecord":
        now = utc_now_iso()
        return cls(assignment_id=assignment_id or f"wa-{uuid4().hex}", created_at=now, updated_at=now, assigned_by=assigned_by, assigned_to=assigned_to, classification=classification, state=state, mission=mission, summary=summary, **kwargs)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WorkerAssignmentRecord":
        if not isinstance(data, dict):
            raise ValueError("assignment record must be an object")
        rec = cls(
            assignment_id=_require_str(data, "assignment_id"), created_at=_require_str(data, "created_at"), updated_at=_require_str(data, "updated_at"),
            assigned_by=_require_str(data, "assigned_by"), assigned_to=_require_str(data, "assigned_to"), classification=_require_str(data, "classification"),
            state=_require_str(data, "state"), mission=_require_str(data, "mission"), summary=_require_str(data, "summary"),
            assignment_label=_optional_str(data, "assignment_label"), worker_id=_optional_str(data, "worker_id"), worker_role=_optional_str(data, "worker_role"),
            provider_id=_optional_str(data, "provider_id"), provider_type=_optional_str(data, "provider_type"), seat_id=_optional_str(data, "seat_id"), profile_id=_optional_str(data, "profile_id"),
            work_package_id=_optional_str(data, "work_package_id"), work_package_path=_optional_str(data, "work_package_path"), intake_id=_optional_str(data, "intake_id"), schedule_id=_optional_str(data, "schedule_id"),
            priority=data.get("priority") or "normal", expected_outputs=_string_list(data, "expected_outputs"), validation_required=bool(data.get("validation_required", True)),
            requires_attention=bool(data.get("requires_attention", False)), blocked_reason=_optional_str(data, "blocked_reason"), artifact_paths=_string_list(data, "artifact_paths"), metadata=data.get("metadata") or {},
        )
        rec.validate()
        return rec

    def validate(self) -> None:
        for key in ["assignment_id", "created_at", "updated_at", "assigned_by", "assigned_to", "classification", "state", "mission", "summary"]:
            if not isinstance(getattr(self, key), str) or not getattr(self, key).strip():
                raise ValueError(f"{key} is required")
        validate_iso_timestamp(self.created_at, "created_at")
        validate_iso_timestamp(self.updated_at, "updated_at")
        if self.classification not in ALLOWED_CLASSIFICATIONS:
            raise ValueError(f"unknown classification '{self.classification}'")
        if self.priority not in ALLOWED_PRIORITIES:
            raise ValueError(f"unknown priority '{self.priority}'")
        if self.state not in ALLOWED_ASSIGNMENT_STATES:
            raise ValueError(f"unknown assignment state '{self.state}'")
        for key in ["expected_outputs", "artifact_paths"]:
            if not isinstance(getattr(self, key), list) or not all(isinstance(item, str) for item in getattr(self, key)):
                raise ValueError(f"{key} must be a list of strings")
        if not isinstance(self.validation_required, bool) or not isinstance(self.requires_attention, bool):
            raise ValueError("validation_required and requires_attention must be booleans")
        if not isinstance(self.metadata, dict):
            raise ValueError("metadata must be an object")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)


def safe_assignment_summary(record: WorkerAssignmentRecord | dict[str, Any]) -> str:
    data = record.to_dict() if isinstance(record, WorkerAssignmentRecord) else record
    if data.get("classification") in SENSITIVE_CLASSIFICATIONS and not (data.get("metadata") or {}).get("summary_safe"):
        return "Sensitive assignment summary redacted."
    return data.get("summary") or ""
