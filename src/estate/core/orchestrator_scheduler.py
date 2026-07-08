from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any
from uuid import uuid4

from estate.core.operational_events import utc_now_iso, validate_iso_timestamp
from estate.core.orchestrator_intake import ALLOWED_CLASSIFICATIONS, ALLOWED_PRIORITIES

ALLOWED_SCHEDULE_STATES = {"scheduled", "deferred", "blocked", "cancelled"}
CLASSIFICATION_RANK = {"Public": 0, "Estate Internal": 1, "Restricted": 2, "Steward Only": 3, "Local Only": 4}
BLOCKING_INTAKE_STATES = {"rejected", "needs_revision", "blocked"}
APPROVED_INTAKE_STATES = {"approved"}


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
class OrchestratorScheduleRecord:
    schedule_id: str
    intake_id: str
    created_at: str
    updated_at: str
    scheduled_by: str
    state: str
    priority: str
    classification: str
    work_package_id: str | None = None
    work_package_path: str | None = None
    assignment_id: str | None = None
    provider_type: str | None = None
    provider_id: str | None = None
    required_capabilities: list[str] = field(default_factory=list)
    allowed_paths: list[str] = field(default_factory=list)
    forbidden_paths: list[str] = field(default_factory=list)
    expected_outputs: list[str] = field(default_factory=list)
    validation_required: bool = True
    boundary_review_required: bool = False
    approval_reference: str | None = None
    decision_reference: str | None = None
    blocked_reason: str | None = None
    deferred_until: str | None = None
    artifact_paths: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(cls, *, intake: dict[str, Any], state: str, scheduled_by: str, blocked_reason: str | None = None, deferred_until: str | None = None, metadata: dict[str, Any] | None = None) -> "OrchestratorScheduleRecord":
        now = utc_now_iso()
        latest_decision = intake.get("latest_decision") if isinstance(intake.get("latest_decision"), dict) else {}
        return cls(
            schedule_id=f"sch-{uuid4().hex}", intake_id=_require_str(intake, "intake_id"), created_at=now, updated_at=now,
            scheduled_by=scheduled_by, state=state, priority=intake.get("priority") or "normal", classification=_require_str(intake, "classification"),
            work_package_id=intake.get("work_package_id"), work_package_path=intake.get("work_package_path"), assignment_id=intake.get("assignment_id"),
            provider_type=intake.get("requested_provider_type"), provider_id=intake.get("requested_provider_id"),
            required_capabilities=list(intake.get("required_capabilities") or []), allowed_paths=list(intake.get("allowed_paths") or []), forbidden_paths=list(intake.get("forbidden_paths") or []), expected_outputs=list(intake.get("expected_outputs") or []),
            validation_required=bool(intake.get("validation_required", True)), boundary_review_required=bool(intake.get("boundary_review_required", False)),
            approval_reference=(latest_decision or {}).get("decision_id") if latest_decision else (intake.get("metadata") or {}).get("approval_reference"),
            decision_reference=(latest_decision or {}).get("decision_id") if latest_decision else None,
            blocked_reason=blocked_reason, deferred_until=deferred_until, metadata={**(intake.get("metadata") or {}), **(metadata or {})},
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "OrchestratorScheduleRecord":
        record = cls(schedule_id=_require_str(data, "schedule_id"), intake_id=_require_str(data, "intake_id"), created_at=_require_str(data, "created_at"), updated_at=_require_str(data, "updated_at"), scheduled_by=_require_str(data, "scheduled_by"), state=_require_str(data, "state"), priority=_require_str(data, "priority"), classification=_require_str(data, "classification"), work_package_id=_optional_str(data, "work_package_id"), work_package_path=_optional_str(data, "work_package_path"), assignment_id=_optional_str(data, "assignment_id"), provider_type=_optional_str(data, "provider_type"), provider_id=_optional_str(data, "provider_id"), required_capabilities=_list_value(data, "required_capabilities"), allowed_paths=_list_value(data, "allowed_paths"), forbidden_paths=_list_value(data, "forbidden_paths"), expected_outputs=_list_value(data, "expected_outputs"), validation_required=bool(data.get("validation_required", True)), boundary_review_required=bool(data.get("boundary_review_required", False)), approval_reference=_optional_str(data, "approval_reference"), decision_reference=_optional_str(data, "decision_reference"), blocked_reason=_optional_str(data, "blocked_reason"), deferred_until=_optional_str(data, "deferred_until"), artifact_paths=_list_value(data, "artifact_paths"), metadata=data.get("metadata") or {})
        record.validate(); return record

    def validate(self) -> None:
        validate_iso_timestamp(self.created_at, "created_at"); validate_iso_timestamp(self.updated_at, "updated_at")
        if self.deferred_until: validate_iso_timestamp(self.deferred_until, "deferred_until")
        if self.state not in ALLOWED_SCHEDULE_STATES: raise ValueError(f"unknown state '{self.state}'")
        if self.priority not in ALLOWED_PRIORITIES: raise ValueError(f"unknown priority '{self.priority}'")
        if self.classification not in ALLOWED_CLASSIFICATIONS: raise ValueError(f"unknown classification '{self.classification}'")
        for key in ["required_capabilities", "allowed_paths", "forbidden_paths", "expected_outputs", "artifact_paths"]:
            if not isinstance(getattr(self, key), list) or not all(isinstance(item, str) for item in getattr(self, key)):
                raise ValueError(f"{key} must be a list of strings")
        if not isinstance(self.metadata, dict): raise ValueError("metadata must be an object")

    def to_dict(self) -> dict[str, Any]:
        self.validate(); return asdict(self)


def is_intake_approved(intake: dict[str, Any]) -> bool:
    if intake.get("state") in APPROVED_INTAKE_STATES: return True
    decision = intake.get("latest_decision") if isinstance(intake.get("latest_decision"), dict) else {}
    metadata = intake.get("metadata") if isinstance(intake.get("metadata"), dict) else {}
    return decision.get("decision") == "approve" or metadata.get("schedule_eligible") is True or metadata.get("approval") is True or bool(metadata.get("steward_approval"))


def obvious_path_conflict(intake: dict[str, Any]) -> str | None:
    allowed = set(intake.get("allowed_paths") or [])
    forbidden = set(intake.get("forbidden_paths") or [])
    overlap = sorted(allowed & forbidden)
    return f"Forbidden path conflicts with allowed path: {overlap[0]}" if overlap else None


def provider_issue(intake: dict[str, Any], catalog: Any | None) -> tuple[str | None, bool]:
    provider_id, provider_type = intake.get("requested_provider_id"), intake.get("requested_provider_type")
    required = set(intake.get("required_capabilities") or [])
    if not provider_id and not provider_type:
        return None, False
    if catalog is None:
        return "Provider catalog unavailable; provider availability cannot be determined.", True
    candidates = []
    if provider_id:
        try: candidates = [catalog.get_provider(provider_id)]
        except KeyError: return f"Requested provider_id '{provider_id}' is not registered.", True
    elif provider_type:
        candidates = catalog.providers_by_type(provider_type)
        if not candidates: return f"No registered providers for provider_type '{provider_type}'.", True
    compatible = []
    for provider in candidates:
        if provider.status in {"deprecated", "blocked"}: continue
        if provider_type and provider.provider_type != provider_type: continue
        if required and not required.issubset(set(provider.capabilities)): continue
        if CLASSIFICATION_RANK[intake.get("classification", "Public")] > CLASSIFICATION_RANK[provider.classification_ceiling]: continue
        compatible.append(provider)
    if compatible: return None, False
    return "Provider requirements conflict with available provider catalog evidence.", False


def determine_schedule_outcome(intake: dict[str, Any] | None, *, catalog: Any | None = None, defer_if_provider_unavailable: bool = True, explicit_defer: bool = False) -> tuple[str, str | None]:
    if intake is None: return "blocked", "Intake is missing."
    state = intake.get("state")
    if state in BLOCKING_INTAKE_STATES: return "blocked", f"Intake state '{state}' is not eligible for scheduling."
    if not is_intake_approved(intake): return "blocked", "Approval is required but not recorded."
    if intake.get("classification") not in ALLOWED_CLASSIFICATIONS: return "blocked", "Classification is invalid."
    if intake.get("boundary_review_required") and not ((intake.get("metadata") or {}).get("boundary_review_completed") or (intake.get("latest_decision") or {}).get("metadata", {}).get("boundary_review_completed")):
        return "blocked", "Boundary review is required but not completed."
    if intake.get("source") == "work_package" and not intake.get("work_package_path"):
        return "blocked", "Work package path is missing for work-package-based execution."
    conflict = obvious_path_conflict(intake)
    if conflict: return "blocked", conflict
    issue, may_defer = provider_issue(intake, catalog)
    if issue: return ("deferred" if may_defer and defer_if_provider_unavailable else "blocked"), issue
    if explicit_defer: return "deferred", "Deferred scheduling was explicitly requested."
    return "scheduled", None
