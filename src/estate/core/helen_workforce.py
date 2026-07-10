"""Governed workforce contracts and local artifact store for Helen.

This module gives Helen a deterministic implementation surface for workforce
intake and assessment without granting operational queue control, provider
execution, constitutional authority, or unrestricted access to private worker
records.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any
from uuid import uuid4

from estate.core.background_operations import (
    ALLOWED_CLASSIFICATIONS,
    is_sensitive_subject,
    utc_now_iso,
    validate_iso_timestamp,
)
from estate.core.paths import ESTATE_ROOT
from estate.core.operational_events import OperationalEvent, append_event_artifact

WORKFORCE_BASE = Path("runtime/workforce_development")
REQUESTS = WORKFORCE_BASE / "requests"
ASSESSMENTS = WORKFORCE_BASE / "assessments"
STATUS = WORKFORCE_BASE / "status"

ALLOWED_REQUEST_TYPES = {
    "staffing_request",
    "onboarding_request",
    "role_fit_review",
    "worker_health_review",
    "coaching_request",
    "reflection_cycle_request",
    "continuity_review",
    "stand_down_review",
    "reassignment_review",
    "lessons_learned_intake",
    "institutional_improvement_review",
}

ALLOWED_STATUSES = {
    "open",
    "blocked",
    "in_review",
    "ready_for_action",
    "closed",
    "declined",
}

ALLOWED_RECOMMENDATIONS = {
    "no_action",
    "request_more_evidence",
    "targeted_reread",
    "coaching",
    "mentoring",
    "workload_adjustment",
    "reflection_cycle",
    "continuity_artifact",
    "fresh_operational_cycle",
    "temporary_stand_down",
    "reassignment",
    "succession_review",
    "onboarding_repair",
    "documentation_repair",
    "retrieval_repair",
    "governance_review",
    "staffing_action",
}


def _root(root: Path | None = None) -> Path:
    return root or (ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd())


def _require_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} is required")
    return value


def _require_string_list(value: Any, field_name: str) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise ValueError(f"{field_name} must be a list of strings")
    return value


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def _read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"expected JSON object in {path}")
    return data


@dataclass
class WorkforceRequest:
    request_id: str
    request_type: str
    subject_id: str
    subject_type: str
    requesting_office: str
    summary: str
    requested_outcome: str
    classification: str
    source_artifacts: list[str]
    requires_steward_attention: bool
    requires_boundary_review: bool
    created_at: str
    status: str = "open"
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        *,
        request_type: str,
        subject_id: str,
        subject_type: str,
        requesting_office: str,
        summary: str,
        requested_outcome: str,
        classification: str = "Estate Internal",
        source_artifacts: list[str] | None = None,
        requires_steward_attention: bool = False,
        requires_boundary_review: bool = False,
        metadata: dict[str, Any] | None = None,
    ) -> "WorkforceRequest":
        sensitive = is_sensitive_subject(
            request_type,
            subject_type,
            summary,
            requested_outcome,
            metadata,
        )
        return cls(
            request_id=f"wfr-{uuid4().hex}",
            request_type=request_type,
            subject_id=subject_id,
            subject_type=subject_type,
            requesting_office=requesting_office,
            summary=summary,
            requested_outcome=requested_outcome,
            classification=classification,
            source_artifacts=source_artifacts or [],
            requires_steward_attention=bool(requires_steward_attention),
            requires_boundary_review=bool(requires_boundary_review or sensitive),
            created_at=utc_now_iso(),
            status="open",
            metadata=metadata or {},
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WorkforceRequest":
        request = cls(**{key: data.get(key) for key in cls.__dataclass_fields__})
        request.validate()
        return request

    def validate(self) -> None:
        for field_name in [
            "request_id",
            "request_type",
            "subject_id",
            "subject_type",
            "requesting_office",
            "summary",
            "requested_outcome",
            "classification",
            "created_at",
            "status",
        ]:
            _require_text(getattr(self, field_name), field_name)
        if self.request_type not in ALLOWED_REQUEST_TYPES:
            raise ValueError(f"unknown request_type '{self.request_type}'")
        if self.classification not in ALLOWED_CLASSIFICATIONS:
            raise ValueError(f"unknown classification '{self.classification}'")
        if self.status not in ALLOWED_STATUSES:
            raise ValueError(f"unknown status '{self.status}'")
        validate_iso_timestamp(self.created_at, "created_at")
        _require_string_list(self.source_artifacts, "source_artifacts")
        if not isinstance(self.requires_steward_attention, bool):
            raise ValueError("requires_steward_attention must be boolean")
        if not isinstance(self.requires_boundary_review, bool):
            raise ValueError("requires_boundary_review must be boolean")
        if not isinstance(self.metadata, dict):
            raise ValueError("metadata must be object")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)


@dataclass
class WorkforceAssessment:
    assessment_id: str
    request_id: str
    assessor: str
    subject_id: str
    classification: str
    worker_factors: list[str]
    institutional_factors: list[str]
    missing_evidence: list[str]
    recommendations: list[str]
    rationale: str
    private_detail_included: bool
    created_at: str
    status: str = "ready_for_action"
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        *,
        request_id: str,
        subject_id: str,
        worker_factors: list[str] | None = None,
        institutional_factors: list[str] | None = None,
        missing_evidence: list[str] | None = None,
        recommendations: list[str] | None = None,
        rationale: str,
        classification: str = "Estate Internal",
        private_detail_included: bool = False,
        metadata: dict[str, Any] | None = None,
    ) -> "WorkforceAssessment":
        return cls(
            assessment_id=f"wfa-{uuid4().hex}",
            request_id=request_id,
            assessor="Helen",
            subject_id=subject_id,
            classification=classification,
            worker_factors=worker_factors or [],
            institutional_factors=institutional_factors or [],
            missing_evidence=missing_evidence or [],
            recommendations=recommendations or [],
            rationale=rationale,
            private_detail_included=bool(private_detail_included),
            created_at=utc_now_iso(),
            status="ready_for_action",
            metadata=metadata or {},
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WorkforceAssessment":
        assessment = cls(**{key: data.get(key) for key in cls.__dataclass_fields__})
        assessment.validate()
        return assessment

    def validate(self) -> None:
        for field_name in [
            "assessment_id",
            "request_id",
            "assessor",
            "subject_id",
            "classification",
            "rationale",
            "created_at",
            "status",
        ]:
            _require_text(getattr(self, field_name), field_name)
        if self.assessor != "Helen":
            raise ValueError("assessor must be Helen")
        if self.classification not in ALLOWED_CLASSIFICATIONS:
            raise ValueError(f"unknown classification '{self.classification}'")
        if self.status not in ALLOWED_STATUSES:
            raise ValueError(f"unknown status '{self.status}'")
        validate_iso_timestamp(self.created_at, "created_at")
        for field_name in [
            "worker_factors",
            "institutional_factors",
            "missing_evidence",
            "recommendations",
        ]:
            _require_string_list(getattr(self, field_name), field_name)
        unknown = set(self.recommendations) - ALLOWED_RECOMMENDATIONS
        if unknown:
            raise ValueError(f"unknown recommendations: {sorted(unknown)}")
        if not isinstance(self.private_detail_included, bool):
            raise ValueError("private_detail_included must be boolean")
        if self.private_detail_included and self.classification not in {
            "Restricted",
            "Steward Only",
            "Sensitive",
            "Private",
            "Local Only",
        }:
            raise ValueError("private detail requires a restricted classification")
        if not isinstance(self.metadata, dict):
            raise ValueError("metadata must be object")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)


class HelenWorkforceStore:
    """Local artifact store for governed Helen workforce records."""

    def __init__(self, root: Path | None = None) -> None:
        self.root = _root(root)

    def ensure_dirs(self) -> None:
        for relative in [REQUESTS, ASSESSMENTS, STATUS]:
            (self.root / relative).mkdir(parents=True, exist_ok=True)

    def save_request(self, request: WorkforceRequest, *, emit_event: bool = True) -> Path:
        self.ensure_dirs()
        payload = request.to_dict()
        path = self.root / REQUESTS / f"{request.request_id}.json"
        wrote = self._write_new_or_idempotent(path, payload, "request")
        if emit_event and wrote:
            self.emit_request_event(request, path)
        self.write_status()
        return path

    def load_request(self, request_id: str) -> WorkforceRequest:
        path = self.root / REQUESTS / f"{request_id}.json"
        if not path.exists():
            raise ValueError(f"workforce request not found: {request_id}")
        return WorkforceRequest.from_dict(_read_json(path))

    def save_assessment(self, assessment: WorkforceAssessment, *, emit_event: bool = True) -> Path:
        self.ensure_dirs()
        request = self.load_request(assessment.request_id)
        if request.subject_id != assessment.subject_id:
            raise ValueError("assessment subject must match workforce request subject")
        payload = assessment.to_dict()
        path = self.root / ASSESSMENTS / f"{assessment.assessment_id}.json"
        wrote = self._write_new_or_idempotent(path, payload, "assessment")
        request.status = "in_review" if assessment.missing_evidence else "ready_for_action"
        _write_json(self.root / REQUESTS / f"{request.request_id}.json", request.to_dict())
        if emit_event and wrote and self.assessment_requires_attention(assessment, request):
            self.emit_assessment_attention_event(assessment, request, path)
        self.write_status()
        return path

    def list_requests(self) -> list[WorkforceRequest]:
        directory = self.root / REQUESTS
        if not directory.exists():
            return []
        requests: list[WorkforceRequest] = []
        for path in sorted(directory.glob("*.json")):
            try:
                requests.append(WorkforceRequest.from_dict(_read_json(path)))
            except (OSError, ValueError, json.JSONDecodeError):
                continue
        return requests

    def list_assessments(self) -> list[WorkforceAssessment]:
        directory = self.root / ASSESSMENTS
        if not directory.exists():
            return []
        assessments: list[WorkforceAssessment] = []
        for path in sorted(directory.glob("*.json")):
            try:
                assessments.append(WorkforceAssessment.from_dict(_read_json(path)))
            except (OSError, ValueError, json.JSONDecodeError):
                continue
        return assessments

    def build_status(self) -> dict[str, Any]:
        requests = self.list_requests()
        assessments = self.list_assessments()
        return {
            "available": True,
            "generated_at": utc_now_iso(),
            "summary": {
                "schema_version": "workforce_status_summary.v1",
                "open_requests": sum(request.status == "open" for request in requests),
                "blocked_requests": sum(request.status == "blocked" for request in requests),
                "in_review_requests": sum(request.status == "in_review" for request in requests),
                "ready_for_action_requests": sum(request.status == "ready_for_action" for request in requests),
                "assessment_count": len(assessments),
                "steward_attention_count": sum(request.requires_steward_attention for request in requests),
                "boundary_review_count": sum(request.requires_boundary_review for request in requests),
                "private_assessment_count": sum(assessment.private_detail_included for assessment in assessments),
                "latest_request_id": requests[-1].request_id if requests else None,
                "latest_assessment_id": assessments[-1].assessment_id if assessments else None,
            },
            "requests": [request.to_dict() for request in requests],
            "assessments": [assessment.to_dict() for assessment in assessments],
            "operational_queue_control_performed": False,
            "provider_execution_performed": False,
            "constitutional_authority_granted": False,
            "grace_appointed_or_activated": False,
        }


    def _write_new_or_idempotent(self, path: Path, payload: dict[str, Any], kind: str) -> bool:
        if path.exists():
            existing = _read_json(path)
            if existing != payload:
                raise ValueError(f"duplicate {kind} identifier with different payload: {path.stem}")
            return False
        _write_json(path, payload)
        return True

    def _rel(self, path: Path) -> str:
        try:
            return str(path.relative_to(self.root)).replace("\\", "/")
        except ValueError:
            return str(path).replace("\\", "/")

    def emit_request_event(self, request: WorkforceRequest, path: Path) -> Path:
        event = OperationalEvent.create(
            event_type="Checkpoint Reached", state="Waiting", classification="Estate Internal",
            message=f"Helen workforce request exists: {request.request_id}", request_id=request.request_id,
            requires_attention=request.requires_steward_attention or request.requires_boundary_review,
            artifact_paths=[self._rel(path)],
            metadata={"source":"helen_workforce", "subject_id": request.subject_id, "subject_type": request.subject_type, "requires_boundary_review": request.requires_boundary_review, "provider_execution_performed": False, "operational_queue_control_performed": False, "constitutional_authority_granted": False},
        )
        return append_event_artifact(event, root=self.root)

    def assessment_requires_attention(self, assessment: WorkforceAssessment, request: WorkforceRequest) -> bool:
        return bool(request.requires_steward_attention or request.requires_boundary_review or assessment.private_detail_included or set(assessment.recommendations) & {"temporary_stand_down", "succession_review", "governance_review"})

    def emit_assessment_attention_event(self, assessment: WorkforceAssessment, request: WorkforceRequest, path: Path) -> Path:
        event = OperationalEvent.create(
            event_type="Boundary Review Required" if request.requires_boundary_review or assessment.private_detail_included else "Waiting for Approval",
            state="Awaiting Approval", classification="Estate Internal",
            message=f"Helen workforce assessment requires governed attention: {assessment.assessment_id}",
            request_id=request.request_id, requires_attention=True, artifact_paths=[self._rel(path)],
            metadata={"source":"helen_workforce", "assessment_id": assessment.assessment_id, "subject_id": assessment.subject_id, "recommendations": assessment.recommendations, "requires_boundary_review": request.requires_boundary_review or assessment.private_detail_included, "requires_steward_attention": request.requires_steward_attention, "provider_execution_performed": False, "operational_queue_control_performed": False, "constitutional_authority_granted": False},
        )
        return append_event_artifact(event, root=self.root)

    def write_status(self) -> dict[str, Any]:
        self.ensure_dirs()
        status = self.build_status()
        _write_json(self.root / STATUS / "latest.json", status)
        _write_json(self.root / STATUS / "summary.json", status["summary"])
        return status
