from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from estate.core.paths import ESTATE_ROOT

ALLOWED_CLASSIFICATIONS = {"Public", "Estate Internal", "Restricted", "Steward Only", "Local Only"}
ALLOWED_STATES = {"Planning", "Waiting", "Running", "Reviewing", "Blocked", "Awaiting Approval", "Validation", "Completed", "Failed", "Cancelled", "Deferred"}
ALLOWED_EVENT_TYPES = {
    "Job Accepted", "Planning Started", "Execution Started", "Checkpoint Reached",
    "Waiting for Approval", "Boundary Review Required", "Validation Started",
    "Validation Passed", "Validation Failed", "Commit Created", "Result Returned",
    "Execution Complete", "Planning Complete", "Worker Blocked", "Worker Failed",
    "Worker Cancelled",
    "Operator Attention Required", "Operator Attention Resolved",
    "Operator Attention Timed Out", "Operator Attention Cancelled",
}
RUNTIME_EVENTS_RELATIVE_DIR = Path("runtime/operations/events")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def validate_iso_timestamp(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} is required and must be an ISO timestamp")
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an ISO timestamp") from exc


def validate_classification(value: str) -> None:
    if value not in ALLOWED_CLASSIFICATIONS:
        raise ValueError(f"unknown classification '{value}'")


@dataclass
class OperationalEvent:
    event_id: str
    event_type: str
    state: str
    created_at: str
    classification: str
    message: str
    updated_at: str | None = None
    worker_id: str | None = None
    worker_role: str | None = None
    provider_id: str | None = None
    provider_type: str | None = None
    assignment_id: str | None = None
    work_package_id: str | None = None
    request_id: str | None = None
    budget_source: str | None = None
    validation_status: str = "not_validated"
    requires_attention: bool = False
    artifact_paths: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(cls, *, event_type: str, state: str, classification: str, message: str, **kwargs: Any) -> "OperationalEvent":
        return cls(event_id=f"ope-{uuid4().hex}", event_type=event_type, state=state, created_at=utc_now_iso(), classification=classification, message=message, **kwargs)

    @classmethod
    def from_dict(cls, data: dict[str, Any], *, allow_extension_event_types: bool = False) -> "OperationalEvent":
        allowed = set(cls.__dataclass_fields__)  # type: ignore[attr-defined]
        event = cls(**{key: value for key, value in data.items() if key in allowed})
        event.validate(allow_extension_event_types=allow_extension_event_types)
        return event

    def validate(self, *, allow_extension_event_types: bool = False) -> None:
        for key in ["event_id", "event_type", "state", "created_at", "classification", "message"]:
            if not isinstance(getattr(self, key), str) or not getattr(self, key).strip():
                raise ValueError(f"{key} is required")
        if self.event_type not in ALLOWED_EVENT_TYPES and not allow_extension_event_types:
            raise ValueError(f"unknown event_type '{self.event_type}'")
        if self.state not in ALLOWED_STATES:
            raise ValueError(f"unknown state '{self.state}'")
        validate_classification(self.classification)
        validate_iso_timestamp(self.created_at, "created_at")
        if self.updated_at is not None:
            validate_iso_timestamp(self.updated_at, "updated_at")
        if not isinstance(self.requires_attention, bool):
            raise ValueError("requires_attention must be a boolean")
        if not isinstance(self.artifact_paths, list):
            raise ValueError("artifact_paths must be a list")
        if not all(isinstance(path, str) for path in self.artifact_paths):
            raise ValueError("artifact_paths must contain strings")
        if not isinstance(self.metadata, dict):
            raise ValueError("metadata must be an object")

    def to_dict(self, *, allow_extension_event_types: bool = False) -> dict[str, Any]:
        self.validate(allow_extension_event_types=allow_extension_event_types)
        return asdict(self)


def append_event_artifact(event: OperationalEvent, root: Path | None = None, *, allow_extension_event_types: bool = False) -> Path:
    event.validate(allow_extension_event_types=allow_extension_event_types)
    events_dir = (root or ESTATE_ROOT) / RUNTIME_EVENTS_RELATIVE_DIR
    events_dir.mkdir(parents=True, exist_ok=True)
    path = events_dir / f"{event.created_at[:10]}.jsonl"
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event.to_dict(allow_extension_event_types=allow_extension_event_types), sort_keys=True) + "\n")
    return path
