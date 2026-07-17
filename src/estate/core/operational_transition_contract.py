"""Rebuildable, non-authoritative operational transition contract.

The contract normalizes references to canonical Estate records.  It does not
replace domain state, append events, dispatch work, or grant authority.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Iterable

SCHEMA_VERSION = "estate.operational.v1"

ENTITY_TYPES = {
    "campaign", "work_package", "resident", "service", "office", "worker",
    "provider", "validation_run", "evidence_package", "staffing_request",
    "message", "escalation", "protected_decision",
}

OPERATIONAL_STATES = {
    "observed", "pending", "not_ready", "ready", "eligible", "coordinating",
    "executing", "waiting_for_evidence", "waiting_for_authority", "blocked",
    "degraded", "failed", "paused", "recovering", "review_required", "complete",
    "accepted", "cancelled", "superseded",
}

AUTHORITY_CLASSIFICATIONS = {
    "observation", "recommendation", "coordination", "execution_request",
    "delegated_mechanical", "office_decision", "protected_decision", "acceptance",
}

SEVERITIES = {"info", "warning", "error", "critical"}
HEALTH_STATES = {"healthy", "degraded", "unavailable", "stale", "unknown"}

TRANSITIONS = {
    "observed": {"pending", "not_ready", "ready", "blocked", "degraded", "failed", "cancelled", "superseded"},
    "pending": {"not_ready", "ready", "blocked", "paused", "cancelled", "superseded"},
    "not_ready": {"pending", "ready", "blocked", "waiting_for_authority", "cancelled", "superseded"},
    "ready": {"eligible", "not_ready", "blocked", "degraded", "paused", "cancelled", "superseded"},
    "eligible": {"coordinating", "executing", "waiting_for_authority", "blocked", "paused", "cancelled", "superseded"},
    "coordinating": {"executing", "waiting_for_evidence", "waiting_for_authority", "blocked", "degraded", "paused", "failed", "cancelled"},
    "executing": {"waiting_for_evidence", "waiting_for_authority", "blocked", "degraded", "failed", "paused", "complete", "cancelled"},
    "waiting_for_evidence": {"coordinating", "executing", "blocked", "failed", "review_required", "complete", "cancelled"},
    "waiting_for_authority": {"coordinating", "executing", "review_required", "blocked", "cancelled", "superseded"},
    "blocked": {"pending", "ready", "coordinating", "recovering", "failed", "cancelled", "superseded"},
    "degraded": {"coordinating", "executing", "blocked", "recovering", "failed", "paused", "complete", "cancelled"},
    "failed": {"recovering", "review_required", "cancelled", "superseded"},
    "paused": {"recovering", "cancelled", "superseded"},
    "recovering": {"pending", "ready", "coordinating", "executing", "blocked", "degraded", "failed", "paused"},
    "review_required": {"complete", "accepted", "blocked", "cancelled", "superseded"},
    "complete": {"review_required", "accepted", "superseded"},
    "accepted": set(),
    "cancelled": set(),
    "superseded": set(),
}


class ContractViolation(ValueError):
    """Raised when normalized evidence cannot safely support a transition."""


def _timestamp(value: str, field_name: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ContractViolation(f"{field_name} is required")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ContractViolation(f"{field_name} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise ContractViolation(f"{field_name} must include a timezone")
    return parsed


def _required_text(value: Any, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ContractViolation(f"{field_name} is required")


@dataclass(frozen=True)
class CanonicalSubjectRef:
    subject_type: str
    subject_id: str
    canonical_path: str

    def validate(self) -> None:
        if self.subject_type not in ENTITY_TYPES:
            raise ContractViolation(f"unknown subject_type '{self.subject_type}'")
        _required_text(self.subject_id, "subject_id")
        _required_text(self.canonical_path, "canonical_path")
        if self.canonical_path.startswith(("runtime/operations/projections/", "http://", "https://")):
            raise ContractViolation("canonical_path must reference an in-repository domain source, not a projection or URL")


@dataclass(frozen=True)
class NormalizedOperationalEvent:
    event_id: str
    event_type: str
    source_system: str
    source_record: str
    subject: CanonicalSubjectRef
    observed_at: str
    effective_at: str
    prior_state: str
    new_state: str
    emitter: str
    authority_classification: str
    evidence_refs: tuple[str, ...]
    correlation_id: str
    causation_id: str | None
    severity: str
    idempotency_key: str
    schema_version: str = SCHEMA_VERSION
    metadata: dict[str, Any] = field(default_factory=dict, compare=False)

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "NormalizedOperationalEvent":
        payload = dict(value)
        subject = payload.get("subject")
        if not isinstance(subject, dict):
            raise ContractViolation("subject must be an object")
        payload["subject"] = CanonicalSubjectRef(**subject)
        evidence_refs = payload.get("evidence_refs")
        if not isinstance(evidence_refs, (list, tuple)):
            raise ContractViolation("evidence_refs must be an array")
        payload["evidence_refs"] = tuple(evidence_refs)
        try:
            event = cls(**payload)
        except TypeError as exc:
            raise ContractViolation(f"invalid event envelope: {exc}") from exc
        event.validate()
        return event

    def validate(self) -> None:
        for name in ("event_id", "event_type", "source_system", "source_record", "emitter", "correlation_id", "idempotency_key"):
            _required_text(getattr(self, name), name)
        self.subject.validate()
        observed = _timestamp(self.observed_at, "observed_at")
        effective = _timestamp(self.effective_at, "effective_at")
        if effective > observed:
            raise ContractViolation("effective_at cannot be later than observed_at")
        if self.prior_state not in OPERATIONAL_STATES or self.new_state not in OPERATIONAL_STATES:
            raise ContractViolation("prior_state and new_state must use the operational vocabulary")
        if self.authority_classification not in AUTHORITY_CLASSIFICATIONS:
            raise ContractViolation(f"unknown authority_classification '{self.authority_classification}'")
        if self.severity not in SEVERITIES:
            raise ContractViolation(f"unknown severity '{self.severity}'")
        if self.schema_version != SCHEMA_VERSION:
            raise ContractViolation(f"unsupported schema_version '{self.schema_version}'")
        if not self.evidence_refs or not all(isinstance(ref, str) and ref.strip() for ref in self.evidence_refs):
            raise ContractViolation("at least one non-empty evidence reference is required")
        if not isinstance(self.metadata, dict):
            raise ContractViolation("metadata must be an object")


@dataclass(frozen=True)
class TransitionContext:
    dependencies_ready: bool = False
    readiness_confirmed: bool = False
    staffing_confirmed: bool = False
    evidence_complete: bool = False
    health_status: str = "unknown"
    authority_refs: tuple[str, ...] = ()
    protected_approval_refs: tuple[str, ...] = ()
    canonical_acceptance_ref: str | None = None
    evidence_observed_at: str | None = None
    max_evidence_age_seconds: int | None = None
    conflicting_evidence: bool = False

    def validate(self, event: NormalizedOperationalEvent) -> None:
        if self.health_status not in HEALTH_STATES:
            raise ContractViolation(f"unknown health_status '{self.health_status}'")
        if self.conflicting_evidence:
            raise ContractViolation("conflicting evidence requires review")
        if self.max_evidence_age_seconds is not None:
            if self.max_evidence_age_seconds < 0 or self.evidence_observed_at is None:
                raise ContractViolation("freshness policy requires non-negative age and evidence_observed_at")
            age = (_timestamp(event.observed_at, "observed_at") - _timestamp(self.evidence_observed_at, "evidence_observed_at")).total_seconds()
            if age < 0 or age > self.max_evidence_age_seconds:
                raise ContractViolation("stale or future-dated prerequisite evidence")


def validate_transition(current_state: str, event: NormalizedOperationalEvent, context: TransitionContext) -> None:
    """Validate one derived transition without mutating a canonical record."""
    event.validate()
    context.validate(event)
    if current_state != event.prior_state:
        raise ContractViolation(f"prior_state '{event.prior_state}' does not match projected state '{current_state}'")
    if event.new_state == current_state:
        if event.authority_classification not in {"observation", "recommendation", "execution_request"}:
            raise ContractViolation("a no-op event must be observational, advisory, or a request")
        return
    if event.new_state not in TRANSITIONS[current_state]:
        raise ContractViolation(f"transition {current_state} -> {event.new_state} is not allowed")
    if event.authority_classification in {"recommendation", "execution_request"}:
        raise ContractViolation(f"{event.authority_classification} cannot change operational state")
    if event.authority_classification == "protected_decision" and not context.protected_approval_refs:
        raise ContractViolation("protected transition requires explicit protected approval evidence")

    if event.new_state in {"ready", "eligible", "coordinating", "executing"}:
        missing = []
        if not context.dependencies_ready:
            missing.append("dependencies")
        if not context.readiness_confirmed:
            missing.append("readiness")
        if not context.staffing_confirmed:
            missing.append("staffing")
        if context.health_status in {"unavailable", "stale", "unknown"}:
            missing.append("health")
        if missing:
            raise ContractViolation(f"transition prerequisites are incomplete: {', '.join(missing)}")

    if event.new_state == "eligible" and not context.evidence_complete:
        raise ContractViolation("eligibility requires complete evidence")
    if event.new_state == "executing":
        if event.authority_classification not in {"delegated_mechanical", "office_decision", "protected_decision"}:
            raise ContractViolation("execution requires an authorized action classification")
        if not context.authority_refs:
            raise ContractViolation("execution requires explicit authority evidence")
    if event.new_state == "complete" and not context.evidence_complete:
        raise ContractViolation("completion requires evidence; execution success alone is insufficient")
    if event.new_state == "accepted":
        if event.authority_classification != "acceptance":
            raise ContractViolation("acceptance requires a distinct acceptance event")
        if not context.canonical_acceptance_ref or not context.authority_refs:
            raise ContractViolation("acceptance requires canonical acceptance and authority evidence")


@dataclass(frozen=True)
class OperationalProjection:
    subject: CanonicalSubjectRef
    state: str
    applied_event_ids: tuple[str, ...]
    duplicate_event_ids: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    authoritative: bool = False
    rebuildable: bool = True
    schema_version: str = SCHEMA_VERSION


def replay_projection(
    events: Iterable[NormalizedOperationalEvent],
    contexts: dict[str, TransitionContext],
    *,
    initial_state: str = "observed",
) -> OperationalProjection:
    """Replay events in supplied canonical order, rejecting unsafe ambiguity."""
    if initial_state not in OPERATIONAL_STATES:
        raise ContractViolation(f"unknown initial_state '{initial_state}'")
    state = initial_state
    subject: CanonicalSubjectRef | None = None
    last_effective: datetime | None = None
    seen_ids: dict[str, NormalizedOperationalEvent] = {}
    seen_keys: dict[str, NormalizedOperationalEvent] = {}
    applied: list[str] = []
    duplicates: list[str] = []
    evidence: list[str] = []

    for event in events:
        event.validate()
        if subject is None:
            subject = event.subject
        elif event.subject != subject:
            raise ContractViolation("one projection replay may reference only one canonical subject")
        prior_id = seen_ids.get(event.event_id)
        prior_key = seen_keys.get(event.idempotency_key)
        duplicate = prior_id or prior_key
        if duplicate:
            if duplicate == event:
                duplicates.append(event.event_id)
                continue
            raise ContractViolation("duplicate event identity or idempotency key has conflicting content")
        effective = _timestamp(event.effective_at, "effective_at")
        if last_effective is not None and effective < last_effective:
            raise ContractViolation("out-of-order effective time requires reconciliation before replay")
        context = contexts.get(event.event_id)
        if context is None:
            raise ContractViolation(f"transition context is missing for {event.event_id}")
        validate_transition(state, event, context)
        state = event.new_state
        last_effective = effective
        seen_ids[event.event_id] = event
        seen_keys[event.idempotency_key] = event
        applied.append(event.event_id)
        for ref in event.evidence_refs:
            if ref not in evidence:
                evidence.append(ref)

    if subject is None:
        raise ContractViolation("at least one event is required to build a projection")
    return OperationalProjection(subject, state, tuple(applied), tuple(duplicates), tuple(evidence))
