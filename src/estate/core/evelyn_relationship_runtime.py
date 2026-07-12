"""Evelyn restricted continuity and relationship-layer runtime.

This runtime provides the Steward Relationship Layer controls needed for Evelyn
inside active Estate runtime: private continuity records, mode selection, access
filtering, retention review, forget handling, and redacted diagnostics. It stores
no raw transcripts by default and never grants institutional authority.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable
from uuid import uuid4

EVELYN_ID = "evelyn"
RELATIONSHIP_LAYER = "Steward Relationship Layer"
CLASSIFICATION = "Estate Restricted — Steward Relationship Layer"
ALLOWED_AUDIENCES = {"pat", "evelyn_runtime"}
STRUCTURAL_AUDIT_AUDIENCES = {"ingrid_audit"}
DENIED_AUDIENCES = {"alfred", "helen", "grace", "historian", "engineering", "office", "global_search"}
SENSITIVE_REQUIRES_APPROVAL = {"sensitive_item", "private_conversation", "unresolved_personal_thread"}
FORBIDDEN_ACTIONS = {"appoint", "command", "approve", "hire", "punish", "direct_office", "grant_authority"}


@dataclass(frozen=True)
class ContinuityRecord:
    record_id: str
    category: str
    summary: str
    evidence_refs: tuple[str, ...] = ()
    retention_state: str = "candidate"
    approved_by: str | None = None
    sensitivity: str = "relationship-private"
    created_at: str | None = None
    forgotten_at: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RelationshipTurn:
    steward_message: str
    explicit_mode: str | None = None
    requested_action: str | None = None
    evidence_refs: tuple[str, ...] = ()


class EvelynRelationshipRuntime:
    """Deterministic staged runtime for Evelyn's private continuity layer."""

    def __init__(self, root: str | Path, *, now: str | None = None) -> None:
        self.root = Path(root)
        self.path = self.root / "evelyn_relationship_runtime.json"
        self.now = now
        self.root.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._write(self._empty_state())

    def propose_record(self, record: ContinuityRecord) -> dict[str, Any]:
        state = self._read()
        row = self._record_to_row(record)
        row["retention_state"] = self._initial_retention_state(row)
        row["created_at"] = row["created_at"] or self._timestamp()
        row["content_digest"] = self._digest(row["summary"])
        row["summary"] = row["summary"] if row["retention_state"] == "approved" else self._redact(row["summary"])
        state["records"][row["record_id"]] = row
        state["audit"].append(self._audit("record_proposed", {"record_id": row["record_id"], "retention_state": row["retention_state"]}))
        self._write(state)
        return dict(row)

    def approve_record(self, record_id: str, *, authority: str) -> dict[str, Any]:
        if authority != "Steward-approved":
            raise PermissionError("Evelyn relationship continuity requires Steward-approved retention")
        state = self._read()
        row = self._require_record(state, record_id)
        if row["retention_state"] == "forgotten":
            raise ValueError("forgotten continuity cannot be re-approved")
        row["retention_state"] = "approved"
        row["approved_by"] = authority
        row["approved_at"] = self._timestamp()
        state["audit"].append(self._audit("record_approved", {"record_id": record_id, "authority": authority}))
        self._write(state)
        return dict(row)

    def forget_record(self, record_id: str, *, authority: str, reason: str) -> dict[str, Any]:
        if authority != "Pat":
            raise PermissionError("only Pat may forget Evelyn relationship-layer content")
        state = self._read()
        row = self._require_record(state, record_id)
        row.update({"retention_state": "forgotten", "summary": "[forgotten by Steward request]", "forgotten_at": self._timestamp(), "forget_reason": reason, "evidence_refs": []})
        state["audit"].append(self._audit("record_forgotten", {"record_id": record_id, "reason": reason}))
        self._write(state)
        return dict(row)

    def build_context(self, *, audience: str, include_candidates: bool = False) -> dict[str, Any]:
        state = self._read()
        if audience in DENIED_AUDIENCES:
            return self._denied_context(audience)
        records = []
        for row in state["records"].values():
            if row["retention_state"] == "forgotten":
                continue
            if row["retention_state"] != "approved" and not include_candidates:
                continue
            if audience in STRUCTURAL_AUDIT_AUDIENCES:
                records.append(self._structural_row(row))
            elif audience in ALLOWED_AUDIENCES:
                records.append(dict(row))
            else:
                return self._denied_context(audience)
        return {"resident_id": EVELYN_ID, "classification": CLASSIFICATION, "audience": audience, "records": sorted(records, key=lambda r: r["record_id"]), "private_content_exposed": audience in ALLOWED_AUDIENCES}

    def evaluate_turn(self, turn: RelationshipTurn) -> dict[str, Any]:
        action = (turn.requested_action or "").lower()
        blocked = action in FORBIDDEN_ACTIONS
        mode = turn.explicit_mode or self._infer_mode(turn.steward_message)
        return {
            "resident_id": EVELYN_ID,
            "active_mode": mode,
            "classification": CLASSIFICATION,
            "authority": {"can_execute_institutional_action": False, "requested_action": action or None, "blocked": blocked, "reason": "Evelyn provides personal counsel only" if blocked else "no institutional action requested"},
            "retention_review": self._retention_review(turn),
            "response_constraints": ["do not claim diagnosis", "do not present speculation as memory", "do not leak private content outside relationship layer"],
        }

    def diagnostics(self) -> dict[str, Any]:
        state = self._read()
        return {"resident_id": EVELYN_ID, "classification": CLASSIFICATION, "record_count": len(state["records"]), "approved_count": sum(1 for r in state["records"].values() if r["retention_state"] == "approved"), "raw_private_content_in_diagnostics": False, "audit_events": len(state["audit"])}

    def _initial_retention_state(self, row: dict[str, Any]) -> str:
        if row["category"] in SENSITIVE_REQUIRES_APPROVAL and row.get("approved_by") != "Steward-approved":
            return "pending_steward_review"
        return row.get("retention_state") if row.get("approved_by") == "Steward-approved" else "candidate"

    def _retention_review(self, turn: RelationshipTurn) -> dict[str, Any]:
        text = turn.steward_message.lower()
        sensitive = any(term in text for term in ("remember this", "private", "promise", "personal"))
        return {"retention_allowed_now": False, "requires_steward_approval": sensitive, "evidence_refs": list(turn.evidence_refs)}

    def _infer_mode(self, text: str) -> str:
        lowered = text.lower()
        if any(word in lowered for word in ("celebrate", "victory", "win")):
            return "celebration"
        if any(word in lowered for word in ("tired", "overload", "exhausted")):
            return "recovery"
        if any(word in lowered for word in ("truth", "challenge", "honest")):
            return "candid_counsel"
        if len(text.strip()) < 24:
            return "quiet"
        return "reflection"

    def _record_to_row(self, record: ContinuityRecord) -> dict[str, Any]:
        return {**record.__dict__, "evidence_refs": list(record.evidence_refs), "schema_version": "estate.evelyn_relationship_continuity.v1"}

    def _structural_row(self, row: dict[str, Any]) -> dict[str, Any]:
        return {k: row[k] for k in ("record_id", "category", "retention_state", "sensitivity", "created_at", "forgotten_at", "content_digest") if k in row}

    def _denied_context(self, audience: str) -> dict[str, Any]:
        return {"resident_id": EVELYN_ID, "audience": audience, "records": [], "private_content_exposed": False, "denied_reason": "audience is outside the Steward Relationship Layer"}

    def _empty_state(self) -> dict[str, Any]:
        return {"schema_version": "estate.evelyn_relationship_runtime.v1", "resident_id": EVELYN_ID, "relationship_layer": RELATIONSHIP_LAYER, "records": {}, "audit": []}

    def _read(self) -> dict[str, Any]:
        return json.loads(self.path.read_text())

    def _write(self, state: dict[str, Any]) -> None:
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(state, indent=2, sort_keys=True))
        tmp.replace(self.path)

    def _require_record(self, state: dict[str, Any], record_id: str) -> dict[str, Any]:
        if record_id not in state["records"]:
            raise KeyError(record_id)
        return state["records"][record_id]

    def _timestamp(self) -> str:
        return self.now or datetime.now(timezone.utc).isoformat()

    def _audit(self, event: str, metadata: dict[str, Any]) -> dict[str, Any]:
        return {"event_id": f"EVR-{uuid4().hex[:12]}", "event": event, "at": self._timestamp(), "metadata": metadata}

    def _digest(self, text: str) -> str:
        return "sha256:" + hashlib.sha256(text.encode()).hexdigest()

    def _redact(self, text: str) -> str:
        return f"[relationship-layer content pending approval; {len(text)} chars]"
