from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any

ALLOWED_CLASSIFICATIONS = {"Public", "Estate Internal", "Restricted", "Steward Only", "Local Only"}
ALLOWED_PRIORITIES = {"low", "normal", "high", "urgent"}
ALLOWED_INITIAL_STATES = {"pending", "accepted", "blocked", "rejected"}
EXECUTION_HINTS = {"execution", "implementation", "validation", "codex", "worker", "local", "python", "powershell"}


def validate_iso_timestamp(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} is required")
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an ISO timestamp") from exc


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
class OrchestratorIntakeRequest:
    intake_id: str
    created_at: str
    requested_by: str
    source: str
    classification: str
    mission: str
    summary: str
    source_artifact: str | None = None
    work_package_id: str | None = None
    work_package_path: str | None = None
    assignment_id: str | None = None
    requested_worker_id: str | None = None
    requested_provider_type: str | None = None
    requested_provider_id: str | None = None
    priority: str = "normal"
    state: str = "pending"
    required_capabilities: list[str] = field(default_factory=list)
    allowed_paths: list[str] = field(default_factory=list)
    forbidden_paths: list[str] = field(default_factory=list)
    expected_outputs: list[str] = field(default_factory=list)
    validation_required: bool = True
    approval_required: bool = False
    boundary_review_required: bool = False
    budget_source: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "OrchestratorIntakeRequest":
        if not isinstance(data, dict):
            raise ValueError("intake request must be a JSON object")
        request = cls(
            intake_id=_require_str(data, "intake_id"),
            created_at=_require_str(data, "created_at"),
            requested_by=_require_str(data, "requested_by"),
            source=_require_str(data, "source"),
            classification=_require_str(data, "classification"),
            mission=_require_str(data, "mission"),
            summary=_require_str(data, "summary"),
            source_artifact=_optional_str(data, "source_artifact"),
            work_package_id=_optional_str(data, "work_package_id"),
            work_package_path=_optional_str(data, "work_package_path"),
            assignment_id=_optional_str(data, "assignment_id"),
            requested_worker_id=_optional_str(data, "requested_worker_id"),
            requested_provider_type=_optional_str(data, "requested_provider_type"),
            requested_provider_id=_optional_str(data, "requested_provider_id"),
            priority=data.get("priority") or "normal",
            state=data.get("state") or "pending",
            required_capabilities=_list_value(data, "required_capabilities"),
            allowed_paths=_list_value(data, "allowed_paths"),
            forbidden_paths=_list_value(data, "forbidden_paths"),
            expected_outputs=_list_value(data, "expected_outputs"),
            validation_required=bool(data.get("validation_required", True)),
            approval_required=bool(data.get("approval_required", False)),
            boundary_review_required=bool(data.get("boundary_review_required", False)),
            budget_source=_optional_str(data, "budget_source"),
            metadata=data.get("metadata") or {},
        )
        request.validate()
        return request

    def validate(self) -> None:
        for key in ["intake_id", "created_at", "requested_by", "source", "classification", "mission", "summary"]:
            if not isinstance(getattr(self, key), str) or not getattr(self, key).strip():
                raise ValueError(f"{key} is required")
        validate_iso_timestamp(self.created_at, "created_at")
        if self.classification not in ALLOWED_CLASSIFICATIONS:
            raise ValueError(f"unknown classification '{self.classification}'")
        if self.priority not in ALLOWED_PRIORITIES:
            raise ValueError(f"unknown priority '{self.priority}'")
        if self.state not in ALLOWED_INITIAL_STATES:
            raise ValueError(f"invalid initial state '{self.state}'")
        for key in ["required_capabilities", "allowed_paths", "forbidden_paths", "expected_outputs"]:
            if not isinstance(getattr(self, key), list) or not all(isinstance(item, str) for item in getattr(self, key)):
                raise ValueError(f"{key} must be a list of strings")
        if not isinstance(self.metadata, dict):
            raise ValueError("metadata must be an object")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)


def determine_block_reason(request: OrchestratorIntakeRequest) -> str | None:
    if request.classification == "Restricted" and not request.boundary_review_required:
        return "Restricted intake requires boundary_review_required=true."
    if request.classification == "Steward Only" and not request.metadata.get("approval") and not request.metadata.get("steward_approval"):
        return "Steward Only intake requires explicit approval metadata."
    execution_text = " ".join([request.source, request.mission, request.summary, *request.required_capabilities]).lower()
    clearly_execution = any(hint in execution_text for hint in EXECUTION_HINTS) or bool(request.requested_worker_id)
    if clearly_execution and not request.requested_provider_type:
        return "Execution-oriented intake requires requested_provider_type."
    if request.source == "work_package" and not request.work_package_path:
        return "work_package source requires work_package_path."
    return None


@dataclass
class OrchestratorIntakeStatus:
    intake_id: str
    state: str
    created_at: str
    updated_at: str
    requested_by: str
    source: str
    work_package_id: str | None
    work_package_path: str | None
    requested_provider_type: str | None
    requested_provider_id: str | None
    classification: str
    priority: str
    mission: str
    summary: str
    validation_required: bool
    approval_required: bool
    boundary_review_required: bool
    blocked_reason: str | None = None
    artifact_paths: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_request(cls, request: OrchestratorIntakeRequest, *, state: str, updated_at: str, blocked_reason: str | None = None, artifact_paths: list[str] | None = None) -> "OrchestratorIntakeStatus":
        return cls(request.intake_id, state, request.created_at, updated_at, request.requested_by, request.source, request.work_package_id, request.work_package_path, request.requested_provider_type, request.requested_provider_id, request.classification, request.priority, request.mission, request.summary, request.validation_required, request.approval_required, request.boundary_review_required, blocked_reason, artifact_paths or [], request.metadata)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
