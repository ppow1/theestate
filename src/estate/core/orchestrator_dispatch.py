from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any
from uuid import uuid4

from estate.core.operational_events import utc_now_iso, validate_iso_timestamp
from estate.core.orchestrator_intake import ALLOWED_CLASSIFICATIONS, ALLOWED_PRIORITIES

ALLOWED_DISPATCH_STATES = {"pending_dispatch", "blocked", "deferred", "cancelled"}
SENSITIVE_CLASSIFICATIONS = {"Restricted", "Steward Only", "Local Only"}


def _require_str(data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} is required")
    return value


def _optional_str(data: dict[str, Any], key: str) -> str | None:
    value = data.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{key} must be a string")
    return value


def _list_value(data: dict[str, Any], key: str) -> list[str]:
    value = data.get(key) or []
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"{key} must be a list of strings")
    return value


@dataclass
class DispatchRecord:
    dispatch_id: str
    created_at: str
    cycle_id: str
    state: str
    classification: str
    mission: str
    summary: str
    created_by: str = "estate.orchestrator.local"
    intake_id: str | None = None
    schedule_id: str | None = None
    assignment_id: str | None = None
    work_package_id: str | None = None
    work_package_path: str | None = None
    provider_id: str | None = None
    provider_type: str | None = None
    required_capabilities: list[str] = field(default_factory=list)
    priority: str = "normal"
    allowed_paths: list[str] = field(default_factory=list)
    forbidden_paths: list[str] = field(default_factory=list)
    expected_outputs: list[str] = field(default_factory=list)
    validation_required: bool = True
    boundary_review_reference: str | None = None
    decision_reference: str | None = None
    blocked_reason: str | None = None
    deferred_reason: str | None = None
    artifact_paths: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(cls, *, cycle_id: str, state: str, schedule: dict[str, Any], reason: str | None = None, created_by: str = "estate.orchestrator.local") -> "DispatchRecord":
        metadata = dict(schedule.get("metadata") or {})
        summary = schedule.get("summary") or metadata.get("summary") or schedule.get("intake_id") or schedule.get("schedule_id") or "Scheduled orchestration item"
        rec = cls(
            dispatch_id=f"disp-{uuid4().hex}", created_at=utc_now_iso(), created_by=created_by, cycle_id=cycle_id, state=state,
            intake_id=schedule.get("intake_id"), schedule_id=schedule.get("schedule_id"), assignment_id=schedule.get("assignment_id"),
            work_package_id=schedule.get("work_package_id"), work_package_path=schedule.get("work_package_path"), provider_id=schedule.get("provider_id"), provider_type=schedule.get("provider_type"),
            required_capabilities=list(schedule.get("required_capabilities") or []), classification=schedule.get("classification") or "Estate Internal", priority=schedule.get("priority") or "normal",
            mission=schedule.get("mission") or metadata.get("mission") or "Dispatch scheduled Estate work", summary=summary,
            allowed_paths=list(schedule.get("allowed_paths") or []), forbidden_paths=list(schedule.get("forbidden_paths") or []), expected_outputs=list(schedule.get("expected_outputs") or []),
            validation_required=bool(schedule.get("validation_required", True)), boundary_review_reference=metadata.get("boundary_review_reference"), decision_reference=schedule.get("decision_reference"),
            blocked_reason=reason if state == "blocked" else schedule.get("blocked_reason"), deferred_reason=reason if state == "deferred" else metadata.get("deferred_reason"), metadata=metadata,
        )
        rec.validate(); return rec

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DispatchRecord":
        rec = cls(dispatch_id=_require_str(data, "dispatch_id"), created_at=_require_str(data, "created_at"), created_by=data.get("created_by") or "estate.orchestrator.local", cycle_id=_require_str(data, "cycle_id"), state=_require_str(data, "state"), intake_id=_optional_str(data, "intake_id"), schedule_id=_optional_str(data, "schedule_id"), assignment_id=_optional_str(data, "assignment_id"), work_package_id=_optional_str(data, "work_package_id"), work_package_path=_optional_str(data, "work_package_path"), provider_id=_optional_str(data, "provider_id"), provider_type=_optional_str(data, "provider_type"), required_capabilities=_list_value(data, "required_capabilities"), classification=_require_str(data, "classification"), priority=data.get("priority") or "normal", mission=_require_str(data, "mission"), summary=_require_str(data, "summary"), allowed_paths=_list_value(data, "allowed_paths"), forbidden_paths=_list_value(data, "forbidden_paths"), expected_outputs=_list_value(data, "expected_outputs"), validation_required=bool(data.get("validation_required", True)), boundary_review_reference=_optional_str(data, "boundary_review_reference"), decision_reference=_optional_str(data, "decision_reference"), blocked_reason=_optional_str(data, "blocked_reason"), deferred_reason=_optional_str(data, "deferred_reason"), artifact_paths=_list_value(data, "artifact_paths"), metadata=data.get("metadata") or {})
        rec.validate(); return rec

    def validate(self) -> None:
        validate_iso_timestamp(self.created_at, "created_at")
        if self.state not in ALLOWED_DISPATCH_STATES: raise ValueError(f"unknown dispatch state '{self.state}'")
        if self.classification not in ALLOWED_CLASSIFICATIONS: raise ValueError(f"unknown classification '{self.classification}'")
        if self.priority not in ALLOWED_PRIORITIES: raise ValueError(f"unknown priority '{self.priority}'")
        if self.state == "blocked" and not self.blocked_reason: raise ValueError("blocked dispatch requires blocked_reason")
        if self.state == "deferred" and not self.deferred_reason: raise ValueError("deferred dispatch requires deferred_reason")
        if not isinstance(self.metadata, dict): raise ValueError("metadata must be an object")

    def to_dict(self) -> dict[str, Any]:
        self.validate(); return asdict(self)


def safe_dispatch_summary(record: dict[str, Any]) -> str:
    if record.get("classification") in SENSITIVE_CLASSIFICATIONS and not (record.get("metadata") or {}).get("summary_safe"):
        return "Sensitive summary redacted."
    return record.get("summary") or ""
