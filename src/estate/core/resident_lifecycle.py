"""Governed resident lifecycle state machine.

The lifecycle composes existing Estate resident/personnel/mailbox/continuity
artifacts without creating replacement registries. Local lifecycle files are a
versioned runtime projection and audit history for transition governance.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from estate.core.character_continuity import status as continuity_status
from estate.core.paths import ESTATE_ROOT
from estate.core.resident_authority import check_authority

SCHEMA_VERSION = "resident_lifecycle.v1"
LIFECYCLE_DIR = Path("runtime/residents/lifecycle")
REQUIRED_STATES = [
    "candidate", "under_review", "approved_for_hire", "onboarding", "ready_for_service", "active",
    "reflection_due", "in_reflection", "stand_down", "reassignment_review", "retirement_review",
    "retired", "archived", "successor_review",
]

TRANSITIONS: dict[str, dict[str, Any]] = {
    "intake_candidate": {"from": None, "to": "candidate", "actor": "Helen", "authority": "HR intake with Steward-reserved appointment protection", "prerequisites": ["candidate evidence", "privacy classification"], "evidence": ["candidate_packet"], "output": "local lifecycle record only", "rollback": "archive erroneous candidate lifecycle record; do not delete identity registries"},
    "begin_review": {"from": "candidate", "to": "under_review", "actor": "Helen", "authority": "workforce review", "prerequisites": ["candidate exists"], "evidence": ["review_request"], "output": "pending review gate", "rollback": "return to candidate with correction note"},
    "approve_for_hire": {"from": "under_review", "to": "approved_for_hire", "actor": "Steward", "authority": "constitutional personnel approval", "prerequisites": ["review complete", "no Ingrid privacy block"], "evidence": ["steward_approval"], "output": "approved hiring gate", "rollback": "correction returns to under_review; no auto-appointment"},
    "start_onboarding": {"from": "approved_for_hire", "to": "onboarding", "actor": "Helen", "authority": "Helen onboarding workflow", "prerequisites": ["steward approval", "employee/mailbox plan"], "evidence": ["onboarding_receipt"], "output": "onboarding in progress", "rollback": "pause onboarding and retain approved_for_hire gate"},
    "mark_ready": {"from": "onboarding", "to": "ready_for_service", "actor": "Helen", "authority": "workforce readiness", "prerequisites": ["mailbox identity", "personnel identity", "continuity seed"], "evidence": ["readiness_report"], "output": "ready service gate", "rollback": "return to onboarding for correction"},
    "activate": {"from": "ready_for_service", "to": "active", "actor": "Steward", "authority": "constitutional appointment", "prerequisites": ["ready gate", "reserved appointment check"], "evidence": ["appointment_record"], "output": "active resident status", "rollback": "stand_down with correction record; identity remains stable"},
    "schedule_reflection": {"from": "active", "to": "reflection_due", "actor": "Helen", "authority": "cognitive-health cadence", "prerequisites": ["active service"], "evidence": ["health_signal"], "output": "pending reflection gate", "rollback": "return active if scheduled in error"},
    "start_reflection": {"from": "reflection_due", "to": "in_reflection", "actor": "Helen", "authority": "continuity reflection workflow", "prerequisites": ["continuity evidence prepared"], "evidence": ["reflection_evidence"], "output": "reflection in progress", "rollback": "return to reflection_due; do not replace identity"},
    "complete_refresh": {"from": "in_reflection", "to": "active", "actor": "Helen", "authority": "continuity refresh, not succession", "prerequisites": ["continuity artifact"], "evidence": ["continuity_artifact"], "output": "refreshed resident, same resident_id", "rollback": "resume in_reflection with correction"},
    "stand_down": {"from": "active", "to": "stand_down", "actor": "Steward", "authority": "Steward operational safety", "prerequisites": ["stand-down reason"], "evidence": ["stand_down_order"], "output": "not active for service", "rollback": "reactivate only via ready_for_service/active correction"},
    "review_reassignment": {"from": "stand_down", "to": "reassignment_review", "actor": "Helen", "authority": "workforce reassignment review", "prerequisites": ["stand-down record"], "evidence": ["fit_review"], "output": "reassignment gate", "rollback": "return stand_down"},
    "review_retirement": {"from": "stand_down", "to": "retirement_review", "actor": "Steward", "authority": "retirement approval review", "prerequisites": ["stand-down record"], "evidence": ["retirement_recommendation"], "output": "retirement gate", "rollback": "return stand_down"},
    "retire": {"from": "retirement_review", "to": "retired", "actor": "Steward", "authority": "constitutional retirement approval", "prerequisites": ["retirement gate"], "evidence": ["retirement_approval"], "output": "retired resident distinct from successor", "rollback": "correction opens retirement_review; do not reactivate automatically"},
    "archive": {"from": "retired", "to": "archived", "actor": "Eleanor", "authority": "archives provenance", "prerequisites": ["retired record"], "evidence": ["archive_manifest"], "output": "archived lifecycle", "rollback": "restore retired archival pending gate"},
    "open_successor_review": {"from": "retired", "to": "successor_review", "actor": "Steward", "authority": "succession review, not continuity refresh", "prerequisites": ["retired predecessor"], "evidence": ["succession_request"], "output": "successor candidate gate", "rollback": "return retired; no successor created"},
}


def _root(root=None) -> Path: return Path(root) if root is not None else ESTATE_ROOT
def _now() -> str: return datetime.now(timezone.utc).isoformat(timespec="seconds")
def record_path(resident_id: str, root=None) -> Path: return _root(root) / LIFECYCLE_DIR / f"{resident_id}.json"

def load_record(resident_id: str, root=None) -> dict[str, Any] | None:
    p = record_path(resident_id, root)
    return json.loads(p.read_text()) if p.exists() else None

def _write(record: dict[str, Any], root=None) -> dict[str, Any]:
    p = record_path(record["resident_id"], root); p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return record

def _pending_for(state: str) -> str:
    return {"candidate":"begin_review","under_review":"approve_for_hire","approved_for_hire":"start_onboarding","onboarding":"mark_ready","ready_for_service":"activate","active":"schedule_reflection","reflection_due":"start_reflection","in_reflection":"complete_refresh","stand_down":"review_reassignment or review_retirement","retirement_review":"retire","retired":"archive or open_successor_review","successor_review":"intake successor candidate"}.get(state, "none")

def transition(resident_id: str, transition_name: str, *, actor: str, evidence: dict[str, Any] | None = None, root=None, resident_name: str | None = None, classification: str = "Estate Internal", resume_token: str | None = None) -> dict[str, Any]:
    if transition_name not in TRANSITIONS: raise ValueError(f"unknown transition: {transition_name}")
    spec = TRANSITIONS[transition_name]; record = load_record(resident_id, root)
    current = record.get("status") if record else None
    event_id = resume_token or f"{transition_name}:{len(record.get('history', [])) if record else 0}"
    if record and any(e.get("event_id") == event_id for e in record.get("history", [])): return record
    if current != spec["from"]: raise ValueError(f"invalid transition {transition_name}: expected {spec['from']}, found {current}")
    if evidence is None: raise ValueError("evidence is required")
    auth = check_authority(actor, "modify-personnel-identity" if transition_name in {"approve_for_hire","activate","retire","open_successor_review"} else "update-resident-runtime-state", target=resident_id, root=root, audit=False)
    if spec["actor"] == "Steward" and actor.lower() != "steward": raise PermissionError("Steward-reserved transition requires actor=Steward")
    if spec["actor"] != "Steward" and auth["decision"] == "denied" and actor.lower() not in {spec["actor"].lower(), "steward"}: raise PermissionError(auth["reason"])
    if record is None:
        record = {"schema_version": SCHEMA_VERSION, "resident_id": resident_id, "resident_name": resident_name or resident_id, "classification": classification, "identity_lineage": {"kind": "resident", "resident_id": resident_id, "predecessor_resident_id": None, "successor_resident_id": None}, "history": []}
    if transition_name == "complete_refresh": record.setdefault("identity_lineage", {})["kind"] = "refreshed_resident"
    if transition_name == "retire": record.setdefault("identity_lineage", {})["kind"] = "retired_resident"
    record.update({"status": spec["to"], "pending_gate": None if spec["to"] in {"active","archived"} else _pending_for(spec["to"]), "next_action": _pending_for(spec["to"]), "updated_at": _now()})
    record["history"].append({"event_id": event_id, "transition": transition_name, "from": spec["from"], "to": spec["to"], "actor": actor, "authority": spec["authority"], "prerequisites": spec["prerequisites"], "evidence": evidence, "output": spec["output"], "rollback_or_correction": spec["rollback"], "at": record["updated_at"]})
    return _write(record, root)

def status(resident_id: str, root=None) -> dict[str, Any]:
    rec = load_record(resident_id, root)
    if not rec: raise FileNotFoundError(resident_id)
    try: rec["continuity"] = continuity_status(resident_id, root=root)
    except Exception: rec["continuity"] = {"available": False}
    return rec

def office_lifecycle_summary(root=None) -> dict[str, Any]:
    base = _root(root) / LIFECYCLE_DIR
    records = [json.loads(p.read_text()) for p in sorted(base.glob("*.json"))] if base.exists() else []
    return {"schema_version": SCHEMA_VERSION, "source": str(LIFECYCLE_DIR), "records": [{"resident_id": r.get("resident_id"), "status": r.get("status"), "pending_gate": r.get("pending_gate"), "next_action": r.get("next_action"), "updated_at": r.get("updated_at")} for r in records]}
