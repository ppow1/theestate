"""Staged resident delegation and handoff runtime for WP-4023.

This module is intentionally isolated under collaboration/workstreams/WP-4023.
It models deterministic local contracts for future integration with the active
assignment, Traffic Controller, work-package, Dispatch, mailbox, and audit
mechanisms. It does not create a queue, registry, Dispatch path, or authority
layer; callers must supply source authority and approval metadata.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Iterable

REQUESTED = "requested"
ACCEPTED = "accepted"
DECLINED = "declined"
TRANSFERRED = "transferred"
STALLED = "stalled"
REJECTED = "rejected"
RETURNED = "returned"
COMPLETED = "completed"

TERMINAL_STATES = frozenset({DECLINED, REJECTED, RETURNED, COMPLETED})
VISIBLE_UNRESOLVED_STATES = frozenset({REQUESTED, ACCEPTED, TRANSFERRED, STALLED, REJECTED})


@dataclass(frozen=True)
class AuthorityMetadata:
    """Caller-provided authority and approval context.

    The presence of a delegation message is not authority. Integration code must
    derive these fields from the active authority, assignment, Dispatch, and
    approval systems before requesting ownership transfer.
    """

    source_authority: str
    approved_by: str | None = None
    approval_reference: str | None = None
    can_request: bool = False
    can_accept: bool = False
    can_transfer_ownership: bool = False
    can_complete: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "source_authority": self.source_authority,
            "approved_by": self.approved_by,
            "approval_reference": self.approval_reference,
            "can_request": self.can_request,
            "can_accept": self.can_accept,
            "can_transfer_ownership": self.can_transfer_ownership,
            "can_complete": self.can_complete,
        }


@dataclass(frozen=True)
class EvidenceItem:
    kind: str
    reference: str
    summary: str = ""
    provenance: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "reference": self.reference,
            "summary": self.summary,
            "provenance": dict(self.provenance),
        }


@dataclass(frozen=True)
class TransitionRecord:
    sequence: int
    state: str
    actor: str
    reason: str
    occurred_at: str
    idempotency_key: str
    authority: dict[str, Any]
    evidence: tuple[dict[str, Any], ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class DelegationRecord:
    delegation_id: str
    work_item_id: str
    requester: str
    recipient: str
    owner: str
    state: str
    prerequisites: tuple[str, ...]
    completion_criteria: tuple[str, ...]
    evidence: tuple[dict[str, Any], ...]
    receipts: tuple[dict[str, Any], ...]
    history: tuple[TransitionRecord, ...]
    idempotency_keys: frozenset[str]

    def as_dict(self) -> dict[str, Any]:
        return {
            "delegation_id": self.delegation_id,
            "work_item_id": self.work_item_id,
            "requester": self.requester,
            "recipient": self.recipient,
            "owner": self.owner,
            "state": self.state,
            "visible": self.state in VISIBLE_UNRESOLVED_STATES,
            "prerequisites": list(self.prerequisites),
            "completion_criteria": list(self.completion_criteria),
            "evidence": list(self.evidence),
            "receipts": list(self.receipts),
            "history": [record.__dict__ for record in self.history],
        }


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _evidence(items: Iterable[EvidenceItem | dict[str, Any]]) -> tuple[dict[str, Any], ...]:
    normalized = []
    for item in items:
        normalized.append(item.as_dict() if isinstance(item, EvidenceItem) else dict(item))
    return tuple(normalized)


def request_delegation(
    *,
    delegation_id: str,
    work_item_id: str,
    requester: str,
    recipient: str,
    prerequisites: Iterable[str],
    completion_criteria: Iterable[str],
    authority: AuthorityMetadata,
    evidence: Iterable[EvidenceItem | dict[str, Any]] = (),
    idempotency_key: str,
) -> DelegationRecord:
    """Create a staged delegation request without changing ownership."""

    _require(authority.can_request, "delegation request is not authorized")
    _require(bool(tuple(completion_criteria)), "completion criteria are required")
    ev = _evidence(evidence)
    transition = TransitionRecord(1, REQUESTED, requester, "delegation requested", _now(), idempotency_key, authority.as_dict(), ev)
    return DelegationRecord(
        delegation_id=delegation_id,
        work_item_id=work_item_id,
        requester=requester,
        recipient=recipient,
        owner=requester,
        state=REQUESTED,
        prerequisites=tuple(prerequisites),
        completion_criteria=tuple(completion_criteria),
        evidence=ev,
        receipts=(),
        history=(transition,),
        idempotency_keys=frozenset({idempotency_key}),
    )


def transition_delegation(
    record: DelegationRecord,
    *,
    target_state: str,
    actor: str,
    authority: AuthorityMetadata,
    reason: str,
    evidence: Iterable[EvidenceItem | dict[str, Any]] = (),
    idempotency_key: str,
) -> DelegationRecord:
    """Apply an authorized deterministic transition with idempotent retry."""

    if idempotency_key in record.idempotency_keys:
        return record
    _require(record.state not in TERMINAL_STATES, f"cannot transition terminal state {record.state}")
    allowed = {
        REQUESTED: {ACCEPTED, DECLINED, REJECTED, STALLED},
        ACCEPTED: {TRANSFERRED, RETURNED, STALLED, REJECTED},
        TRANSFERRED: {COMPLETED, RETURNED, STALLED, REJECTED},
        STALLED: {ACCEPTED, TRANSFERRED, RETURNED, REJECTED},
    }
    _require(target_state in allowed.get(record.state, set()), f"invalid transition {record.state}->{target_state}")
    if target_state in {ACCEPTED, DECLINED}:
        _require(actor == record.recipient and authority.can_accept, "recipient acceptance or decline is not authorized")
    if target_state == TRANSFERRED:
        _require(authority.can_transfer_ownership, "ownership transfer is not authorized")
    if target_state == COMPLETED:
        _require(actor == record.owner and authority.can_complete, "completion is not authorized")
    ev = _evidence(evidence)
    owner = record.recipient if target_state == TRANSFERRED else record.owner
    receipts = record.receipts
    if target_state == COMPLETED:
        receipts = receipts + ({
            "handoff_receipt_id": f"{record.delegation_id}:receipt:{len(receipts) + 1}",
            "received_by": record.requester,
            "completed_by": actor,
            "work_item_id": record.work_item_id,
            "evidence": list(record.evidence + ev),
            "provenance": {"delegation_id": record.delegation_id, "source_authority": authority.source_authority},
        },)
    transition = TransitionRecord(len(record.history) + 1, target_state, actor, reason, _now(), idempotency_key, authority.as_dict(), ev)
    return DelegationRecord(
        delegation_id=record.delegation_id,
        work_item_id=record.work_item_id,
        requester=record.requester,
        recipient=record.recipient,
        owner=owner,
        state=target_state,
        prerequisites=record.prerequisites,
        completion_criteria=record.completion_criteria,
        evidence=record.evidence + ev,
        receipts=receipts,
        history=record.history + (transition,),
        idempotency_keys=record.idempotency_keys | {idempotency_key},
    )
