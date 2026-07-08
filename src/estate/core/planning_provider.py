from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from typing import Any

from estate.core.planning_provider_events import PlanningProviderEvent, validate_classification, validate_iso_timestamp, utc_now_iso

ALLOWED_STATUSES = {"completed", "queued", "blocked", "failed"}
ALLOWED_VALIDATION_STATUSES = {"not_validated", "validation_required", "validation_started", "validated", "validation_failed"}


def _require_str(data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} is required")
    return value


@dataclass
class PlanningProviderRequest:
    request_id: str
    provider_id: str
    requested_by: str
    classification: str
    planning_intent: str
    prompt: str
    created_at: str
    worker_id: str | None = None
    mailbox_id: str | None = None
    work_package_id: str | None = None
    context_paths: list[str] = field(default_factory=list)
    allowed_output_paths: list[str] = field(default_factory=list)
    budget_source: str | None = None
    requires_boundary_review: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PlanningProviderRequest":
        if not isinstance(data, dict):
            raise ValueError("request must be a JSON object")
        payload = {
            "request_id": _require_str(data, "request_id"),
            "provider_id": _require_str(data, "provider_id"),
            "requested_by": _require_str(data, "requested_by"),
            "classification": _require_str(data, "classification"),
            "planning_intent": _require_str(data, "planning_intent"),
            "prompt": _require_str(data, "prompt"),
            "created_at": _require_str(data, "created_at"),
            "worker_id": data.get("worker_id"),
            "mailbox_id": data.get("mailbox_id"),
            "work_package_id": data.get("work_package_id"),
            "context_paths": data.get("context_paths") or [],
            "allowed_output_paths": data.get("allowed_output_paths") or [],
            "budget_source": data.get("budget_source"),
            "requires_boundary_review": bool(data.get("requires_boundary_review", False)),
            "metadata": data.get("metadata") or {},
        }
        req = cls(**payload)
        req.validate()
        return req

    def validate(self) -> None:
        for key in ["request_id", "provider_id", "requested_by", "classification", "planning_intent", "prompt", "created_at"]:
            if not isinstance(getattr(self, key), str) or not getattr(self, key).strip():
                raise ValueError(f"{key} is required")
        validate_classification(self.classification)
        validate_iso_timestamp(self.created_at, "created_at")
        for key in ["context_paths", "allowed_output_paths"]:
            if not isinstance(getattr(self, key), list):
                raise ValueError(f"{key} must be a list")
        if not isinstance(self.metadata, dict):
            raise ValueError("metadata must be an object")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)


@dataclass
class PlanningProviderResponse:
    request_id: str
    provider_id: str
    status: str
    started_at: str
    finished_at: str
    summary: str
    classification: str
    output_text: str | None = None
    artifacts: list[str] = field(default_factory=list)
    events: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    requires_review: bool = False
    validation_status: str = "not_validated"
    metadata: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        for key in ["request_id", "provider_id", "status", "started_at", "finished_at", "summary", "classification"]:
            if not isinstance(getattr(self, key), str) or not getattr(self, key).strip():
                raise ValueError(f"{key} is required")
        if self.status not in ALLOWED_STATUSES:
            raise ValueError(f"unknown status '{self.status}'")
        if self.validation_status not in ALLOWED_VALIDATION_STATUSES:
            raise ValueError(f"unknown validation_status '{self.validation_status}'")
        validate_classification(self.classification)
        validate_iso_timestamp(self.started_at, "started_at")
        validate_iso_timestamp(self.finished_at, "finished_at")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)


class PlanningProvider(ABC):
    provider_id: str
    display_name: str

    @abstractmethod
    def capabilities(self) -> list[str]: ...
    @abstractmethod
    def can_handle(self, request: PlanningProviderRequest) -> bool: ...
    @abstractmethod
    def run(self, request: PlanningProviderRequest) -> PlanningProviderResponse: ...


class StubPlanningProvider(PlanningProvider):
    provider_id = "stub.planning.echo"
    display_name = "Deterministic Planning Echo Stub"

    def capabilities(self) -> list[str]:
        return ["planning", "architecture", "governance_draft", "work_package_draft", "documentation_draft"]

    def can_handle(self, request: PlanningProviderRequest) -> bool:
        return request.provider_id == self.provider_id

    def run(self, request: PlanningProviderRequest) -> PlanningProviderResponse:
        started = utc_now_iso()
        events: list[PlanningProviderEvent] = [PlanningProviderEvent.create(request_id=request.request_id, provider_id=self.provider_id, worker_id=request.worker_id, event_type="Job Accepted", state="Planning", message="Planning provider request accepted.", classification=request.classification)]
        boundary_needed = request.classification in {"Restricted", "Steward Only"} and not request.metadata.get("boundary_approved")
        if boundary_needed:
            events.append(PlanningProviderEvent.create(request_id=request.request_id, provider_id=self.provider_id, worker_id=request.worker_id, event_type="Boundary Review Required", state="Blocked", message=f"{request.classification} planning requests require boundary_approved metadata.", classification=request.classification))
            finished = utc_now_iso()
            return PlanningProviderResponse(request_id=request.request_id, provider_id=self.provider_id, status="blocked", started_at=started, finished_at=finished, summary="Planning request blocked pending boundary approval.", output_text=None, events=[e.to_dict() for e in events], errors=[f"{request.classification} request blocked: metadata.boundary_approved must be true."], classification=request.classification, requires_review=True, validation_status="not_validated")
        events.append(PlanningProviderEvent.create(request_id=request.request_id, provider_id=self.provider_id, worker_id=request.worker_id, event_type="Planning Started", state="Running", message="Deterministic stub planning started.", classification=request.classification))
        events.append(PlanningProviderEvent.create(request_id=request.request_id, provider_id=self.provider_id, worker_id=request.worker_id, event_type="Checkpoint Reached", state="Running", message="Request envelope parsed and deterministic response prepared.", classification=request.classification))
        output = f"Planning intent: {request.planning_intent}\nSummary: Deterministic stub response for request {request.request_id}.\nPrompt received: {request.prompt}"
        events.append(PlanningProviderEvent.create(request_id=request.request_id, provider_id=self.provider_id, worker_id=request.worker_id, event_type="Result Returned", state="Completed", message="Deterministic planning result returned.", classification=request.classification))
        events.append(PlanningProviderEvent.create(request_id=request.request_id, provider_id=self.provider_id, worker_id=request.worker_id, event_type="Planning Complete", state="Completed", message="Planning provider run completed.", classification=request.classification))
        finished = utc_now_iso()
        return PlanningProviderResponse(request_id=request.request_id, provider_id=self.provider_id, status="completed", started_at=started, finished_at=finished, summary=f"Deterministic planning complete for intent: {request.planning_intent}", output_text=output, events=[e.to_dict() for e in events], classification=request.classification)
