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
DISPOSITIONS = WORKFORCE_BASE / "operational_dispositions"

OPERATIONAL_NEED_KINDS = {"staffing", "capability", "provider", "environment"}
OPERATIONAL_DISPOSITIONS = {
    "fulfilled", "partially_fulfilled", "refused", "deferred", "expired", "protected_review_required"
}
PROTECTED_OPERATIONAL_CONSTRAINTS = {"budget", "privacy", "protected_policy", "provider_suitability_unresolved"}

ALLOWED_REQUEST_TYPES = {
    "staffing_request",
    "onboarding_request",
    "role_fit_review",
    "worker_health_review",
    "coaching_request",
    "reflection_cycle_request",
    "continuity_review",
    "stand_down_review",
    "overload_review",
    "repeated_error_review",
    "context_strain_review",
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

COGNITIVE_HEALTH_REQUEST_TYPES = {
    "overload_review",
    "repeated_error_review",
    "context_strain_review",
    "role_fit_review",
    "worker_health_review",
    "coaching_request",
    "reflection_cycle_request",
    "stand_down_review",
    "reassignment_review",
    "continuity_review",
}

PROPORTIONAL_RECOMMENDATIONS = {
    "no_action": 0,
    "request_more_evidence": 0,
    "targeted_reread": 1,
    "coaching": 1,
    "mentoring": 1,
    "reflection_cycle": 2,
    "workload_adjustment": 2,
    "temporary_stand_down": 3,
    "reassignment": 3,
    "succession_review": 3,
}

INSTITUTIONAL_REPAIR_RECOMMENDATIONS = {
    "onboarding_repair",
    "documentation_repair",
    "retrieval_repair",
    "governance_review",
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
    evidence_artifacts: list[str] = field(default_factory=list)
    follow_up_checkpoints: list[str] = field(default_factory=list)
    outcome_review: str = "pending"
    protected_evidence_used: bool = False
    alfred_exception_summary: str = ""
    grace_operational_constraint_summary: str = ""
    ingrid_boundary_enforcement: str = "private records are not routine evidence"
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
        evidence_artifacts: list[str] | None = None,
        follow_up_checkpoints: list[str] | None = None,
        outcome_review: str = "pending",
        protected_evidence_used: bool = False,
        alfred_exception_summary: str = "",
        grace_operational_constraint_summary: str = "",
        ingrid_boundary_enforcement: str = "private records are not routine evidence",
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
            evidence_artifacts=evidence_artifacts or [],
            follow_up_checkpoints=follow_up_checkpoints or [],
            outcome_review=outcome_review,
            protected_evidence_used=bool(protected_evidence_used),
            alfred_exception_summary=alfred_exception_summary,
            grace_operational_constraint_summary=grace_operational_constraint_summary,
            ingrid_boundary_enforcement=ingrid_boundary_enforcement,
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
            "evidence_artifacts",
            "follow_up_checkpoints",
        ]:
            _require_string_list(getattr(self, field_name), field_name)
        unknown = set(self.recommendations) - ALLOWED_RECOMMENDATIONS
        if unknown:
            raise ValueError(f"unknown recommendations: {sorted(unknown)}")
        if not isinstance(self.private_detail_included, bool):
            raise ValueError("private_detail_included must be boolean")
        if not isinstance(self.protected_evidence_used, bool):
            raise ValueError("protected_evidence_used must be boolean")
        if self.outcome_review not in {"pending", "scheduled", "completed", "not_required"}:
            raise ValueError("unknown outcome_review state")
        for field_name in ["outcome_review", "alfred_exception_summary", "grace_operational_constraint_summary", "ingrid_boundary_enforcement"]:
            if not isinstance(getattr(self, field_name), str):
                raise ValueError(f"{field_name} must be string")
        if (self.private_detail_included or self.protected_evidence_used) and self.classification not in {
            "Restricted",
            "Steward Only",
            "Sensitive",
            "Private",
            "Local Only",
        }:
            raise ValueError("private detail requires a restricted classification")
        if self.protected_evidence_used and any("journal" in item.lower() for item in self.evidence_artifacts):
            raise ValueError("private journals may not be routine evidence artifacts")
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
        for relative in [REQUESTS, ASSESSMENTS, DISPOSITIONS, STATUS]:
            (self.root / relative).mkdir(parents=True, exist_ok=True)

    def create_operational_request(
        self,
        blocker: dict[str, Any],
        *,
        campaign_id: str,
        package_id: str,
        need_kind: str,
        required_role: str,
        required_capabilities: list[str],
        urgency: str,
        duration: str,
        constraints: list[str] | None = None,
        requesting_office: str = "Office of Operations",
    ) -> tuple[WorkforceRequest, Path]:
        """Translate a qualifying operational blocker into Helen's workforce lane."""
        blocker_class = str(blocker.get("blocker_class") or "")
        if blocker_class not in {"staffing_or_capability_blocker", "provider_or_environment_blocker"}:
            raise ValueError("blocker is not a staffing, capability, provider, or environment need")
        if need_kind not in OPERATIONAL_NEED_KINDS:
            raise ValueError(f"unknown operational need kind: {need_kind}")
        for value, name in [
            (campaign_id, "campaign_id"), (package_id, "package_id"),
            (required_role, "required_role"), (urgency, "urgency"), (duration, "duration"),
        ]:
            _require_text(value, name)
        _require_string_list(required_capabilities, "required_capabilities")
        if not required_capabilities:
            raise ValueError("required_capabilities must not be empty")
        evidence = blocker.get("canonical_evidence_references") or []
        _require_string_list(evidence, "canonical_evidence_references")
        if not evidence:
            raise ValueError("canonical blocker evidence is required")
        limitations = sorted(set(constraints or []))
        protected = sorted(set(limitations) & PROTECTED_OPERATIONAL_CONSTRAINTS)
        if blocker.get("protected_decision"):
            protected.append("blocker_requires_protected_decision")
        request = WorkforceRequest.create(
            request_type="staffing_request",
            subject_id=f"{campaign_id}:{package_id}:{required_role}",
            subject_type=f"operational_{need_kind}_need",
            requesting_office=requesting_office,
            summary=f"{package_id} requires {required_role} for a governed {need_kind} need.",
            requested_outcome="Helen records an evidence-backed workforce or capability disposition without changing Engineering priority or acceptance.",
            source_artifacts=list(evidence),
            requires_steward_attention=bool(protected),
            requires_boundary_review=bool(set(limitations) & {"privacy", "provider_suitability_unresolved"}),
            metadata={
                "schema_version": "estate.operational-staffing-request.v1",
                "campaign_id": campaign_id,
                "package_id": package_id,
                "blocker_class": blocker_class,
                "need_kind": need_kind,
                "required_role": required_role,
                "required_capabilities": sorted(set(required_capabilities)),
                "urgency": urgency,
                "duration": duration,
                "constraints": limitations,
                "protected_constraints": sorted(set(protected)),
                "request_is_fulfillment": False,
                "engineering_priority_authority_granted": False,
                "architecture_authority_granted": False,
                "acceptance_authority_granted": False,
                "provider_execution_performed": False,
            },
        )
        if protected:
            request.status = "blocked"
        return request, self.save_request(request)

    def record_operational_disposition(
        self,
        request_id: str,
        *,
        disposition: str,
        decided_by: str,
        evidence_references: list[str],
        fulfilled_capabilities: list[str] | None = None,
        reason: str,
        expires_at: str | None = None,
        authority_evidence: list[str] | None = None,
    ) -> tuple[dict[str, Any], Path]:
        """Correlate Helen's disposition without assigning, dispatching, or accepting work."""
        if disposition not in OPERATIONAL_DISPOSITIONS:
            raise ValueError(f"unknown operational disposition: {disposition}")
        _require_text(decided_by, "decided_by")
        _require_text(reason, "reason")
        _require_string_list(evidence_references, "evidence_references")
        if not evidence_references:
            raise ValueError("disposition evidence is required")
        authority = authority_evidence or []
        _require_string_list(authority, "authority_evidence")
        capabilities = fulfilled_capabilities or []
        _require_string_list(capabilities, "fulfilled_capabilities")
        if expires_at:
            validate_iso_timestamp(expires_at, "expires_at")

        request = self.load_request(request_id)
        protected = list(request.metadata.get("protected_constraints") or [])
        if disposition in {"fulfilled", "partially_fulfilled"}:
            if decided_by != "Helen":
                raise ValueError("only Helen may record workforce fulfillment in this lane")
            if not authority:
                raise ValueError("fulfillment requires authority evidence")
            if protected:
                raise ValueError("protected constraints must be resolved by their authority before fulfillment")
            if not capabilities:
                raise ValueError("fulfilled capabilities are required")
        if disposition == "expired" and not expires_at:
            raise ValueError("expired disposition requires expires_at")

        required_capabilities = list(request.metadata.get("required_capabilities") or [])
        remaining_need = (
            sorted(set(required_capabilities) - set(capabilities))
            if disposition in {"fulfilled", "partially_fulfilled"}
            else required_capabilities
        )
        disposition_id = f"wfd-{uuid4().hex}"
        payload = {
            "schema_version": "estate.operational-staffing-disposition.v1",
            "disposition_id": disposition_id,
            "request_id": request_id,
            "campaign_id": request.metadata.get("campaign_id"),
            "package_id": request.metadata.get("package_id"),
            "need_kind": request.metadata.get("need_kind"),
            "disposition": disposition,
            "decided_by": decided_by,
            "reason": reason,
            "evidence_references": sorted(set(evidence_references)),
            "authority_evidence": sorted(set(authority)),
            "fulfilled_capabilities": sorted(set(capabilities)),
            "partial_fulfillment": disposition == "partially_fulfilled",
            "expires_at": expires_at,
            "created_at": utc_now_iso(),
            "request_was_fulfillment": False,
            "staff_assignment_performed": False,
            "provider_execution_performed": False,
            "engineering_priority_authority_granted": False,
            "architecture_authority_granted": False,
            "acceptance_authority_granted": False,
            "requires_protected_review": disposition == "protected_review_required" or bool(protected),
            "remaining_need": remaining_need,
        }
        path = self.root / DISPOSITIONS / f"{disposition_id}.json"
        self._write_new_or_idempotent(path, payload, "operational disposition")
        request.status = {
            "fulfilled": "closed",
            "partially_fulfilled": "ready_for_action",
            "refused": "declined",
            "deferred": "blocked",
            "expired": "blocked",
            "protected_review_required": "blocked",
        }[disposition]
        _write_json(self.root / REQUESTS / f"{request.request_id}.json", request.to_dict())
        self.write_status()
        return payload, path

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
        self.validate_intervention_assessment(request, assessment)
        payload = assessment.to_dict()
        path = self.root / ASSESSMENTS / f"{assessment.assessment_id}.json"
        wrote = self._write_new_or_idempotent(path, payload, "assessment")
        request.status = "in_review" if assessment.missing_evidence else "ready_for_action"
        _write_json(self.root / REQUESTS / f"{request.request_id}.json", request.to_dict())
        if emit_event and wrote and self.assessment_requires_attention(assessment, request):
            self.emit_assessment_attention_event(assessment, request, path)
        self.write_status()
        return path

    def validate_intervention_assessment(self, request: WorkforceRequest, assessment: WorkforceAssessment) -> None:
        if request.request_type not in COGNITIVE_HEALTH_REQUEST_TYPES:
            return
        evidence_count = len(request.source_artifacts) + len(assessment.evidence_artifacts)
        substantive = [r for r in assessment.recommendations if r != "request_more_evidence"]
        if assessment.missing_evidence and substantive:
            raise ValueError("interventions cannot proceed while evidence is missing")
        if substantive and evidence_count < 2:
            raise ValueError("minimum evidence requirements not met")
        if substantive and not assessment.institutional_factors:
            raise ValueError("institutional causes must be evaluated alongside worker factors")
        max_level = max((PROPORTIONAL_RECOMMENDATIONS.get(r, 1) for r in substantive), default=0)
        if max_level >= 2 and len(assessment.follow_up_checkpoints) < 1:
            raise ValueError("follow-up checkpoints are required for material interventions")
        if max_level >= 3 and evidence_count < 3:
            raise ValueError("high-impact interventions require stronger evidence")
        if any(r in INSTITUTIONAL_REPAIR_RECOMMENDATIONS for r in assessment.recommendations) and not assessment.institutional_factors:
            raise ValueError("institutional repairs require institutional factors")
        medical_terms = ["diagnosis", "depression", "anxiety disorder", "adhd", "burnout disorder", "psychological condition"]
        text = " ".join([assessment.rationale, *assessment.worker_factors]).lower()
        if any(term in text for term in medical_terms):
            raise ValueError("false-diagnosis prevention: do not diagnose medical or psychological conditions")

    def grace_constraint_summary(self, assessment: WorkforceAssessment) -> dict[str, Any]:
        return {"assessment_id": assessment.assessment_id, "subject_id": assessment.subject_id, "availability_constraint": assessment.grace_operational_constraint_summary, "allowed_for_grace": True, "raw_private_records_included": False, "prescribes_intervention": False}

    def alfred_exception_summary(self, assessment: WorkforceAssessment) -> dict[str, Any]:
        return {"assessment_id": assessment.assessment_id, "subject_id": assessment.subject_id, "exception_summary": assessment.alfred_exception_summary, "raw_private_records_included": False}

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

    def list_operational_dispositions(self) -> list[dict[str, Any]]:
        directory = self.root / DISPOSITIONS
        if not directory.exists():
            return []
        dispositions: list[dict[str, Any]] = []
        for path in sorted(directory.glob("*.json")):
            try:
                dispositions.append(_read_json(path))
            except (OSError, ValueError, json.JSONDecodeError):
                continue
        return dispositions

    def build_status(self) -> dict[str, Any]:
        requests = self.list_requests()
        assessments = self.list_assessments()
        dispositions = self.list_operational_dispositions()
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
                "cognitive_health_request_count": sum(request.request_type in COGNITIVE_HEALTH_REQUEST_TYPES for request in requests),
                "missing_evidence_assessment_count": sum(bool(assessment.missing_evidence) for assessment in assessments),
                "latest_request_id": requests[-1].request_id if requests else None,
                "latest_assessment_id": assessments[-1].assessment_id if assessments else None,
                "operational_disposition_count": len(dispositions),
            },
            "requests": [request.to_dict() for request in requests],
            "assessments": [assessment.to_dict() for assessment in assessments],
            "operational_dispositions": dispositions,
            "operational_queue_control_performed": False,
            "provider_execution_performed": False,
            "constitutional_authority_granted": False,
            "grace_appointed_or_activated": False,
            "grace_operational_constraints": [self.grace_constraint_summary(a) for a in assessments if a.grace_operational_constraint_summary],
            "alfred_exceptions": [self.alfred_exception_summary(a) for a in assessments if a.alfred_exception_summary],
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
