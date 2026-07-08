from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

ALLOWED_CLASSIFICATIONS = {"Public", "Estate Internal", "Restricted", "Steward Only", "Local Only"}
ALLOWED_EVENT_TYPES = {"Job Accepted", "Planning Started", "Checkpoint Reached", "Waiting for Approval", "Boundary Review Required", "Result Returned", "Planning Complete", "Planning Failed", "Validation Required"}
ALLOWED_STATES = {"Planning", "Waiting", "Running", "Reviewing", "Blocked", "Awaiting Approval", "Validation", "Completed", "Failed"}


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
        allowed = ", ".join(sorted(ALLOWED_CLASSIFICATIONS))
        raise ValueError(f"unknown classification '{value}'; allowed classifications: {allowed}")


@dataclass
class PlanningProviderEvent:
    event_id: str
    request_id: str
    provider_id: str
    event_type: str
    state: str
    message: str
    created_at: str
    classification: str
    worker_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(cls, *, request_id: str, provider_id: str, event_type: str, state: str, message: str, classification: str, worker_id: str | None = None, metadata: dict[str, Any] | None = None) -> "PlanningProviderEvent":
        return cls(event_id=f"ppe-{uuid4().hex}", request_id=request_id, provider_id=provider_id, worker_id=worker_id, event_type=event_type, state=state, message=message, created_at=utc_now_iso(), classification=classification, metadata=metadata or {})

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PlanningProviderEvent":
        event = cls(**{**data, "metadata": data.get("metadata") or {}})
        event.validate()
        return event

    def validate(self) -> None:
        for key in ["event_id", "request_id", "provider_id", "event_type", "state", "message", "created_at", "classification"]:
            if not isinstance(getattr(self, key), str) or not getattr(self, key).strip():
                raise ValueError(f"{key} is required")
        if self.event_type not in ALLOWED_EVENT_TYPES:
            raise ValueError(f"unknown event_type '{self.event_type}'")
        if self.state not in ALLOWED_STATES:
            raise ValueError(f"unknown state '{self.state}'")
        validate_classification(self.classification)
        validate_iso_timestamp(self.created_at, "created_at")
        if not isinstance(self.metadata, dict):
            raise ValueError("metadata must be an object")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)
