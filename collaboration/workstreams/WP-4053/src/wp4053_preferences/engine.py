"""Staged deterministic resident preference evolution engine for WP-4053.

Isolated under collaboration/workstreams/WP-4053; it does not install into active
runtime paths. The engine stores compact, source-linked conclusions rather than
raw transcripts and requires explicit authority for durable identity changes.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any

PREFERENCE_STATES = {"seeded","emerging","established","contextual","experimenting","changed","retired","disputed","unknown"}
ORIGIN_TYPES = {"seeded","resident-stated","interaction-derived","Steward-approved","imported-continuity"}
SENSITIVITY_PUBLIC = "public"
SENSITIVITY_OFFICE = "office"
SENSITIVITY_PRIVATE = "private"
SENSITIVITY_RELATIONSHIP = "relationship-private"
DURABLE_AUTHORITIES = {"Steward-approved", "accepted-continuity-review", "resident-proposal-approved"}
IDENTITY_ANCHOR_DOMAINS = {"core_identity", "constitutional_role", "authority", "appointment_status", "protected_history", "relationship_boundary"}
PRIVATE_AUDIENCES = {"steward", "self", "approved_relationship_party"}

@dataclass
class Evidence:
    ref: str
    summary: str
    timestamp: str
    accepted: bool = True
    actor: str = "system"
    model_generated: bool = False

@dataclass
class PreferenceRecord:
    resident_id: str
    domain: str
    item: str
    value: Any = None
    state: str = "unknown"
    confidence: float = 0.0
    first_observed: str | None = None
    last_reinforced: str | None = None
    evidence_refs: list[str] = field(default_factory=list)
    context_scope: dict[str, str] = field(default_factory=dict)
    sensitivity: str = SENSITIVITY_OFFICE
    origin_type: str = "interaction-derived"
    prior_value_lineage: list[dict[str, Any]] = field(default_factory=list)
    reason_for_change: str | None = None
    promotion_authority: str | None = None
    contradiction_notes: list[str] = field(default_factory=list)
    forget_retire_markers: dict[str, Any] = field(default_factory=dict)
    version: int = 1

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

class PreferenceStore:
    def __init__(self, records: list[PreferenceRecord] | None = None):
        self.records: dict[tuple[str,str,str,tuple[tuple[str,str],...]], PreferenceRecord] = {}
        for record in records or []:
            self.records[self._key(record.resident_id, record.domain, record.item, record.context_scope)] = deepcopy(record)

    @staticmethod
    def _key(resident_id: str, domain: str, item: str, context: dict[str,str] | None = None):
        return (resident_id, domain, item, tuple(sorted((context or {}).items())))

    def get(self, resident_id: str, domain: str, item: str, context_scope: dict[str,str] | None = None) -> PreferenceRecord:
        return deepcopy(self.records.get(self._key(resident_id, domain, item, context_scope), PreferenceRecord(resident_id, domain, item)))

    def upsert(self, record: PreferenceRecord) -> PreferenceRecord:
        if record.domain in IDENTITY_ANCHOR_DOMAINS and record.promotion_authority not in DURABLE_AUTHORITIES:
            raise ValueError("Preference evolution cannot rewrite governed identity anchors without review authority.")
        self.records[self._key(record.resident_id, record.domain, record.item, record.context_scope)] = deepcopy(record)
        return deepcopy(record)

    def observe(self, resident_id: str, domain: str, item: str, value: Any, evidence: Evidence, *, context_scope: dict[str,str] | None = None, sensitivity: str = SENSITIVITY_OFFICE, origin_type: str = "interaction-derived") -> PreferenceRecord:
        if evidence.model_generated and origin_type == "interaction-derived":
            raise ValueError("Ordinary model output may not self-authorize durable preference observations.")
        rec = self.get(resident_id, domain, item, context_scope)
        if rec.state == "unknown":
            rec.value = value; rec.state = "emerging"; rec.confidence = 0.25
            rec.first_observed = evidence.timestamp; rec.context_scope = context_scope or {}; rec.sensitivity = sensitivity; rec.origin_type = origin_type
        elif rec.value != value and rec.state in {"seeded","established","changed","contextual"}:
            rec.state = "disputed"; rec.contradiction_notes.append(f"{evidence.ref}: observed {value!r} conflicts with {rec.value!r}")
        elif rec.value == value:
            rec.confidence = min(1.0, rec.confidence + 0.2); rec.last_reinforced = evidence.timestamp
        rec.evidence_refs.append(evidence.ref)
        return self.upsert(rec)

    def reinforce(self, resident_id: str, domain: str, item: str, evidence: Evidence, *, context_scope: dict[str,str] | None = None) -> PreferenceRecord:
        rec = self.get(resident_id, domain, item, context_scope)
        rec.confidence = min(1.0, rec.confidence + 0.2); rec.last_reinforced = evidence.timestamp; rec.evidence_refs.append(evidence.ref)
        return self.upsert(rec)

    def promote(self, resident_id: str, domain: str, item: str, *, authority: str, context_scope: dict[str,str] | None = None, min_evidence: int = 3) -> PreferenceRecord:
        rec = self.get(resident_id, domain, item, context_scope)
        if authority not in DURABLE_AUTHORITIES: raise ValueError("Durable promotion requires approved authority.")
        if rec.state != "emerging" or len(set(rec.evidence_refs)) < min_evidence: raise ValueError("Insufficient accepted evidence for promotion.")
        rec.state = "established"; rec.confidence = max(rec.confidence, 0.75); rec.promotion_authority = authority
        return self.upsert(rec)

    def experiment(self, resident_id: str, domain: str, item: str, value: Any, evidence: Evidence, *, context_scope: dict[str,str] | None = None) -> PreferenceRecord:
        rec = PreferenceRecord(resident_id, domain, item, value, "experimenting", 0.1, evidence.timestamp, evidence.timestamp, [evidence.ref], context_scope or {}, SENSITIVITY_OFFICE, "resident-stated")
        return self.upsert(rec)

    def change(self, resident_id: str, domain: str, item: str, new_value: Any, *, reason: str, authority: str, evidence: Evidence, context_scope: dict[str,str] | None = None) -> PreferenceRecord:
        if authority not in DURABLE_AUTHORITIES: raise ValueError("Changing established preferences requires review authority.")
        rec = self.get(resident_id, domain, item, context_scope)
        rec.prior_value_lineage.append({"value": deepcopy(rec.value), "state": rec.state, "changed_at": evidence.timestamp, "reason": reason, "evidence_ref": evidence.ref})
        rec.value = new_value; rec.state = "changed"; rec.reason_for_change = reason; rec.promotion_authority = authority; rec.last_reinforced = evidence.timestamp; rec.evidence_refs.append(evidence.ref)
        return self.upsert(rec)

    def retire(self, resident_id: str, domain: str, item: str, *, reason: str, authority: str, evidence_ref: str, context_scope: dict[str,str] | None = None, forget: bool = False) -> PreferenceRecord:
        if authority not in DURABLE_AUTHORITIES: raise ValueError("Retirement/forget requires approved authority.")
        rec = self.get(resident_id, domain, item, context_scope)
        if forget:
            rec.value = None; rec.evidence_refs = []
        rec.state = "retired"; rec.forget_retire_markers = {"reason": reason, "authority": authority, "evidence_ref": evidence_ref, "minimal_audit_only": forget}
        return self.upsert(rec)

    def visible_records(self, requester: str, *, resident_id: str | None = None, office_payload: bool = False) -> list[dict[str, Any]]:
        out = []
        for rec in self.records.values():
            if resident_id and rec.resident_id != resident_id: continue
            if rec.sensitivity in {SENSITIVITY_PRIVATE, SENSITIVITY_RELATIONSHIP} and requester.lower() not in PRIVATE_AUDIENCES:
                continue
            if office_payload and rec.sensitivity in {SENSITIVITY_PRIVATE, SENSITIVITY_RELATIONSHIP}:
                continue
            out.append(deepcopy(rec).to_dict())
        return out

def utc(ts: str = "2026-07-12T00:00:00Z") -> str:
    if ts == "now": return datetime.now(timezone.utc).isoformat(timespec="seconds")
    return ts
