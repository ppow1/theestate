"""Institutional learning intake records for Helen's workforce loop.

The store turns repeated mistakes, friction, suggestions, onboarding gaps, and
ambiguities into durable evidence-linked lessons without exposing private HR
records or creating a parallel backlog.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any
from uuid import uuid4

from estate.core.background_operations import ALLOWED_CLASSIFICATIONS, utc_now_iso, validate_iso_timestamp
from estate.core.helen_workforce import HelenWorkforceStore, WorkforceRequest, _read_json, _require_string_list, _require_text, _root, _write_json

LEARNING_BASE = Path("runtime/workforce_development/institutional_learning")
LESSONS = LEARNING_BASE / "lessons"
STATUS = LEARNING_BASE / "status"
OFFICE_SURFACE = Path("runtime/office/institutional_learning_summary.json")

LESSON_TYPES = {
    "lesson_intake",
    "mistake_or_failure_pattern",
    "worker_suggestion",
    "onboarding_gap",
    "documentation_gap",
    "retrieval_gap",
    "policy_ambiguity",
    "governance_ambiguity",
    "repeated_cross_worker_pattern",
}
OWNER_BY_TYPE = {
    "worker_suggestion": "Engineering",
    "documentation_gap": "Engineering",
    "retrieval_gap": "Engineering",
    "onboarding_gap": "Human Resources",
    "mistake_or_failure_pattern": "Validation",
    "repeated_cross_worker_pattern": "Validation",
    "policy_ambiguity": "Ingrid",
    "governance_ambiguity": "Chief Architect",
    "lesson_intake": "Alfred",
}
ALLOWED_OWNERS = {"Engineering", "Validation", "Human Resources", "Ingrid", "Alfred", "Chief Architect"}
ALLOWED_SOURCES = {"worker", "office", "resident", "validation", "operations"}
ALLOWED_ATTRIBUTIONS = {"worker", "institution", "mixed", "undetermined"}
ALLOWED_STATUSES = {"new", "accepted", "routed", "in_follow_up", "closed", "declined", "duplicate"}


def _fingerprint(text: str) -> str:
    words = re.findall(r"[a-z0-9]+", text.lower())
    stop = {"the", "a", "an", "and", "or", "to", "of", "in", "for", "with", "from", "is", "are", "was", "were"}
    normalized = " ".join(w for w in words if w not in stop)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]


def _office_summary(text: str) -> str:
    redacted = re.sub(r"\b(worker|employee|person|resident)[-_ ]?[A-Za-z0-9]+\b", "[personnel-redacted]", text, flags=re.I)
    redacted = re.sub(r"\b[A-Z][a-z]+\s+[A-Z][a-z]+\b", "[name-redacted]", redacted)
    return redacted[:240]


@dataclass
class InstitutionalLesson:
    lesson_id: str
    schema_version: str
    lesson_type: str
    source_type: str
    source_office: str
    submitted_by: str
    summary: str
    evidence_artifacts: list[str]
    classification: str
    privacy_minimum_necessary: bool
    contains_private_personnel_detail: bool
    worker_involved: bool
    attribution_review: str
    pattern_key: str
    duplicate_of: str | None
    related_lessons: list[str]
    recommended_owner: str
    next_action: str
    follow_up_checkpoint: str
    disposition: str
    created_at: str
    updated_at: str
    status: str = "new"
    closure_summary: str = ""
    office_summary: str = ""
    workforce_request_id: str | None = None
    approval_required_for_policy_or_governance_change: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(cls, **kwargs: Any) -> "InstitutionalLesson":
        now = utc_now_iso()
        lesson_type = kwargs["lesson_type"]
        summary = kwargs["summary"]
        owner = kwargs.get("recommended_owner") or OWNER_BY_TYPE.get(lesson_type, "Alfred")
        pattern_key = kwargs.get("pattern_key") or _fingerprint(f"{lesson_type} {summary}")
        return cls(
            lesson_id=kwargs.get("lesson_id") or f"ilr-{uuid4().hex}",
            schema_version="institutional_learning_lesson.v1",
            lesson_type=lesson_type,
            source_type=kwargs.get("source_type", "worker"),
            source_office=kwargs.get("source_office", "Human Resources"),
            submitted_by=kwargs.get("submitted_by", "worker"),
            summary=summary,
            evidence_artifacts=kwargs.get("evidence_artifacts") or [],
            classification=kwargs.get("classification", "Estate Internal"),
            privacy_minimum_necessary=bool(kwargs.get("privacy_minimum_necessary", True)),
            contains_private_personnel_detail=bool(kwargs.get("contains_private_personnel_detail", False)),
            worker_involved=bool(kwargs.get("worker_involved", False)),
            attribution_review=kwargs.get("attribution_review", "undetermined"),
            pattern_key=pattern_key,
            duplicate_of=kwargs.get("duplicate_of"),
            related_lessons=kwargs.get("related_lessons") or [],
            recommended_owner=owner,
            next_action=kwargs.get("next_action", "review and route through existing owner"),
            follow_up_checkpoint=kwargs.get("follow_up_checkpoint", "review after next operating cycle"),
            disposition=kwargs.get("disposition", "pending_review"),
            created_at=kwargs.get("created_at", now),
            updated_at=kwargs.get("updated_at", now),
            status=kwargs.get("status", "new"),
            closure_summary=kwargs.get("closure_summary", ""),
            office_summary=kwargs.get("office_summary") or _office_summary(summary),
            workforce_request_id=kwargs.get("workforce_request_id"),
            approval_required_for_policy_or_governance_change=bool(kwargs.get("approval_required_for_policy_or_governance_change", lesson_type in {"policy_ambiguity", "governance_ambiguity"})),
            metadata=kwargs.get("metadata") or {},
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "InstitutionalLesson":
        lesson = cls(**{key: data.get(key) for key in cls.__dataclass_fields__})
        lesson.validate()
        return lesson

    def validate(self) -> None:
        for name in ["lesson_id", "schema_version", "lesson_type", "source_type", "source_office", "submitted_by", "summary", "classification", "attribution_review", "pattern_key", "recommended_owner", "next_action", "follow_up_checkpoint", "disposition", "created_at", "updated_at", "status"]:
            _require_text(getattr(self, name), name)
        if self.schema_version != "institutional_learning_lesson.v1":
            raise ValueError("unknown institutional learning schema_version")
        if self.lesson_type not in LESSON_TYPES:
            raise ValueError(f"unknown lesson_type '{self.lesson_type}'")
        if self.source_type not in ALLOWED_SOURCES:
            raise ValueError(f"unknown source_type '{self.source_type}'")
        if self.classification not in ALLOWED_CLASSIFICATIONS:
            raise ValueError(f"unknown classification '{self.classification}'")
        if self.recommended_owner not in ALLOWED_OWNERS:
            raise ValueError("recommended institutional owner must be existing owner")
        if self.attribution_review not in ALLOWED_ATTRIBUTIONS:
            raise ValueError("unknown attribution_review")
        if self.status not in ALLOWED_STATUSES:
            raise ValueError("unknown institutional learning status")
        for name in ["evidence_artifacts", "related_lessons"]:
            _require_string_list(getattr(self, name), name)
        for name in ["privacy_minimum_necessary", "contains_private_personnel_detail", "worker_involved", "approval_required_for_policy_or_governance_change"]:
            if not isinstance(getattr(self, name), bool):
                raise ValueError(f"{name} must be boolean")
        if self.contains_private_personnel_detail and self.classification == "Public":
            raise ValueError("private personnel detail cannot be Public")
        if self.contains_private_personnel_detail and not self.privacy_minimum_necessary:
            raise ValueError("private personnel detail requires minimum-necessary handling")
        if self.status in {"accepted", "routed", "in_follow_up"} and not (self.recommended_owner and self.next_action and self.follow_up_checkpoint):
            raise ValueError("accepted lessons require owner, next action, and checkpoint")
        if self.status == "closed" and not self.closure_summary:
            raise ValueError("closed lessons require closure_summary")
        validate_iso_timestamp(self.created_at, "created_at")
        validate_iso_timestamp(self.updated_at, "updated_at")
        if not isinstance(self.metadata, dict):
            raise ValueError("metadata must be object")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)


class InstitutionalLearningStore:
    def __init__(self, root: Path | None = None) -> None:
        self.root = _root(root)
        self.workforce = HelenWorkforceStore(self.root)

    def ensure_dirs(self) -> None:
        for relative in [LESSONS, STATUS, OFFICE_SURFACE.parent]:
            (self.root / relative).mkdir(parents=True, exist_ok=True)

    def list_lessons(self) -> list[InstitutionalLesson]:
        directory = self.root / LESSONS
        if not directory.exists():
            return []
        lessons = []
        for path in sorted(directory.glob("*.json")):
            try:
                lessons.append(InstitutionalLesson.from_dict(_read_json(path)))
            except (OSError, ValueError, json.JSONDecodeError):
                continue
        return lessons

    def detect_patterns(self, lesson: InstitutionalLesson) -> tuple[str | None, list[str]]:
        related = [item.lesson_id for item in self.list_lessons() if item.pattern_key == lesson.pattern_key and item.lesson_id != lesson.lesson_id]
        return (related[0] if related else None, related)

    def intake(self, lesson: InstitutionalLesson, *, integrate_workforce: bool = True) -> Path:
        self.ensure_dirs()
        duplicate, related = self.detect_patterns(lesson)
        if duplicate and not lesson.duplicate_of:
            lesson.duplicate_of = duplicate
            lesson.status = "duplicate"
            lesson.disposition = "duplicate_pattern_detected"
        lesson.related_lessons = sorted(set(lesson.related_lessons + related))
        if not duplicate and lesson.status == "new":
            lesson.status = "accepted"
            lesson.disposition = "accepted_for_owner_review"
        if integrate_workforce and not lesson.workforce_request_id:
            req = WorkforceRequest.create(request_type="lessons_learned_intake", subject_id=lesson.lesson_id, subject_type="institutional_lesson", requesting_office=lesson.source_office, summary=lesson.office_summary, requested_outcome=f"Route to {lesson.recommended_owner}: {lesson.next_action}", classification=lesson.classification, source_artifacts=lesson.evidence_artifacts, requires_boundary_review=lesson.contains_private_personnel_detail, metadata={"institutional_learning": True, "recommended_owner": lesson.recommended_owner})
            self.workforce.save_request(req, emit_event=False)
            lesson.workforce_request_id = req.request_id
        lesson.updated_at = utc_now_iso()
        payload = lesson.to_dict()
        path = self.root / LESSONS / f"{lesson.lesson_id}.json"
        _write_json(path, payload)
        self.write_status()
        return path

    def close(self, lesson_id: str, closure_summary: str) -> InstitutionalLesson:
        lesson = self.load(lesson_id)
        lesson.status = "closed"
        lesson.disposition = "closed"
        lesson.closure_summary = closure_summary
        lesson.updated_at = utc_now_iso()
        _write_json(self.root / LESSONS / f"{lesson.lesson_id}.json", lesson.to_dict())
        self.write_status()
        return lesson

    def load(self, lesson_id: str) -> InstitutionalLesson:
        path = self.root / LESSONS / f"{lesson_id}.json"
        if not path.exists():
            raise ValueError(f"institutional lesson not found: {lesson_id}")
        return InstitutionalLesson.from_dict(_read_json(path))

    def build_status(self) -> dict[str, Any]:
        lessons = self.list_lessons()
        summary = {
            "schema_version": "institutional_learning_status.v1",
            "lesson_count": len(lessons),
            "accepted_count": sum(l.status == "accepted" for l in lessons),
            "duplicate_count": sum(l.status == "duplicate" for l in lessons),
            "closed_count": sum(l.status == "closed" for l in lessons),
            "privacy_restricted_count": sum(l.contains_private_personnel_detail for l in lessons),
            "policy_or_governance_approval_required_count": sum(l.approval_required_for_policy_or_governance_change for l in lessons),
            "owner_counts": {owner: sum(l.recommended_owner == owner for l in lessons) for owner in sorted(ALLOWED_OWNERS)},
        }
        office = {"available": True, "generated_at": utc_now_iso(), "summary": summary, "lessons": [{"lesson_id": l.lesson_id, "type": l.lesson_type, "status": l.status, "owner": l.recommended_owner, "summary": l.office_summary, "checkpoint": l.follow_up_checkpoint} for l in lessons]}
        return {**office, "records": [l.to_dict() for l in lessons], "private_personnel_detail_exposed": False, "policy_or_governance_auto_rewritten": False}

    def write_status(self) -> dict[str, Any]:
        self.ensure_dirs()
        status = self.build_status()
        _write_json(self.root / STATUS / "latest.json", status)
        _write_json(self.root / STATUS / "summary.json", status["summary"])
        _write_json(self.root / OFFICE_SURFACE, {k: status[k] for k in ["available", "generated_at", "summary", "lessons", "private_personnel_detail_exposed", "policy_or_governance_auto_rewritten"]})
        return status
