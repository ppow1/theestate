"""Durable governed reflection workflow records."""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from estate.core.paths import ESTATE_ROOT

SCHEMA_VERSION = "reflection_workflow.v1"
WORKFLOW_DIR = Path("runtime/reflection/workflows")
STATES = {
    "evaluation_requested", "assessment_in_progress", "reflection_recommended",
    "reflection_authorized", "package_building", "package_validation_failed",
    "package_ready_for_review", "helen_review_required", "approved_for_onboarding",
    "onboarding_in_progress", "first_assignment_in_progress", "renewal_confirmed",
    "previous_implementation_retired", "manual_fallback_active", "renewal_blocked",
}
PROTECTED_STATES = {
    "reflection_authorized": {"steward"},
    "approved_for_onboarding": {"helen", "steward"},
    "renewal_confirmed": {"helen", "steward"},
    "previous_implementation_retired": {"steward"},
}
ALLOWED_TRANSITIONS = {
    "evaluation_requested": {"assessment_in_progress", "renewal_blocked"},
    "assessment_in_progress": {"reflection_recommended", "renewal_blocked"},
    "reflection_recommended": {"reflection_authorized", "renewal_blocked"},
    "reflection_authorized": {"package_building", "manual_fallback_active", "renewal_blocked"},
    "package_building": {"package_validation_failed", "package_ready_for_review", "manual_fallback_active", "renewal_blocked"},
    "package_validation_failed": {"package_building", "manual_fallback_active", "renewal_blocked"},
    "package_ready_for_review": {"helen_review_required", "renewal_blocked"},
    "helen_review_required": {"approved_for_onboarding", "package_building", "renewal_blocked"},
    "approved_for_onboarding": {"onboarding_in_progress", "renewal_blocked"},
    "onboarding_in_progress": {"first_assignment_in_progress", "renewal_blocked"},
    "first_assignment_in_progress": {"renewal_confirmed", "renewal_blocked"},
    "renewal_confirmed": {"previous_implementation_retired", "renewal_blocked"},
    "previous_implementation_retired": set(),
    "manual_fallback_active": {"package_building", "package_validation_failed", "package_ready_for_review", "renewal_blocked"},
    "renewal_blocked": {"assessment_in_progress", "reflection_authorized", "package_building", "manual_fallback_active", "helen_review_required", "onboarding_in_progress", "first_assignment_in_progress"},
}

def _root(root: str | Path | None) -> Path:
    return Path(root) if root is not None else ESTATE_ROOT

def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

def _slug(value: str) -> str:
    text = "".join(ch.lower() if ch.isalnum() else "_" for ch in str(value))
    return "_".join(x for x in text.split("_") if x) or "workflow"

def _clean(values: Iterable[str] | None) -> list[str]:
    return [str(v).strip() for v in (values or []) if str(v).strip()]

def workflow_path(run_id: str, root: str | Path | None = None) -> Path:
    return _root(root) / WORKFLOW_DIR / f"{_slug(run_id)}.json"

def load_reflection_workflow(run_id: str, root: str | Path | None = None) -> dict[str, Any] | None:
    path = workflow_path(run_id, root)
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None

def _write(record: dict[str, Any], root: str | Path | None) -> dict[str, Any]:
    path = workflow_path(record["run_id"], root)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temp.replace(path)
    return record

def create_reflection_workflow(*, run_id: str, office: str, officeholder: str,
    current_implementation: str, mailbox_id: str, initiation_type: str,
    authority_reference: str, actor: str, reason: str = "", repository: str = "",
    branch: str = "", blockers: Iterable[str] | None = None,
    root: str | Path | None = None) -> dict[str, Any]:
    fields = {"run_id": run_id, "office": office, "officeholder": officeholder,
        "current_implementation": current_implementation, "mailbox_id": mailbox_id,
        "initiation_type": initiation_type, "authority_reference": authority_reference,
        "actor": actor}
    missing = [k for k, v in fields.items() if not str(v or "").strip()]
    if missing:
        raise ValueError(f"missing required input(s): {', '.join(missing)}")
    kind = str(initiation_type).strip().lower()
    if kind not in {"evaluation", "direct_reflection"}:
        raise ValueError("initiation_type must be evaluation or direct_reflection")
    state = "evaluation_requested" if kind == "evaluation" else "reflection_authorized"
    if state == "reflection_authorized" and str(actor).strip().lower() != "steward":
        raise PermissionError("direct reflection requires actor=Steward")
    at = _now()
    record = {"schema_version": SCHEMA_VERSION, "run_id": str(run_id).strip(),
        "office": str(office).strip(), "officeholder": str(officeholder).strip(),
        "current_implementation": str(current_implementation).strip(),
        "renewed_implementation": None, "mailbox_id": str(mailbox_id).strip(),
        "initiation_type": kind, "authority_reference": str(authority_reference).strip(),
        "reason": str(reason).strip(), "repository": str(repository).strip(),
        "branch": str(branch).strip(), "state": state,
        "last_successful_action": "workflow_created",
        "next_action": "request_worker_assessment" if state == "evaluation_requested" else "begin_package_building",
        "blockers": _clean(blockers), "warnings": [], "artifacts": {}, "receipts": {},
        "created_at": at, "updated_at": at,
        "history": [{"event_id": "workflow_created", "from": None, "to": state,
            "actor": str(actor).strip(), "authority_reference": str(authority_reference).strip(),
            "evidence": {}, "at": at}]}
    existing = load_reflection_workflow(run_id, root)
    if existing is None:
        return _write(record, root)
    left, right = dict(existing), dict(record)
    for item in (left, right):
        for key in ("created_at", "updated_at", "history"):
            item.pop(key, None)
    if left == right:
        return existing
    raise ValueError(f"conflicting workflow already exists: {workflow_path(run_id, root)}")

def transition_reflection_workflow(run_id: str, to_state: str, *, actor: str,
    evidence: dict[str, Any], event_id: str, next_action: str,
    last_successful_action: str | None = None, blockers: Iterable[str] | None = None,
    warnings: Iterable[str] | None = None, artifacts: dict[str, str] | None = None,
    receipts: dict[str, str] | None = None, renewed_implementation: str | None = None,
    root: str | Path | None = None) -> dict[str, Any]:
    if to_state not in STATES:
        raise ValueError(f"unknown reflection workflow state: {to_state}")
    if not str(actor or "").strip() or not str(event_id or "").strip():
        raise ValueError("actor and event_id are required")
    if not isinstance(evidence, dict) or not evidence:
        raise ValueError("non-empty evidence is required")
    if not str(next_action or "").strip():
        raise ValueError("next_action is required")
    record = load_reflection_workflow(run_id, root)
    if record is None:
        raise FileNotFoundError(run_id)
    matches = [e for e in record.get("history", []) if e.get("event_id") == event_id]
    if matches:
        prior = matches[0]
        if prior.get("to") == to_state and prior.get("actor") == str(actor).strip() and prior.get("evidence") == evidence:
            return record
        raise ValueError(f"conflicting event_id reuse: {event_id}")
    current = record["state"]
    if to_state not in ALLOWED_TRANSITIONS[current]:
        raise ValueError(f"invalid reflection transition: {current} -> {to_state}")
    allowed = PROTECTED_STATES.get(to_state)
    if allowed and str(actor).strip().lower() not in allowed:
        raise PermissionError(f"{to_state} requires authorized actor")
    at = _now()
    record["history"].append({"event_id": str(event_id).strip(), "from": current,
        "to": to_state, "actor": str(actor).strip(), "evidence": evidence, "at": at})
    record.update({"state": to_state, "updated_at": at,
        "next_action": str(next_action).strip(),
        "last_successful_action": str(last_successful_action or event_id).strip()})
    if blockers is not None: record["blockers"] = _clean(blockers)
    if warnings is not None: record["warnings"] = _clean(warnings)
    if artifacts: record.setdefault("artifacts", {}).update({str(k): str(v) for k, v in artifacts.items()})
    if receipts: record.setdefault("receipts", {}).update({str(k): str(v) for k, v in receipts.items()})
    if renewed_implementation is not None:
        record["renewed_implementation"] = str(renewed_implementation).strip() or None
    return _write(record, root)

def reflection_workflow_status(run_id: str, root: str | Path | None = None) -> dict[str, Any]:
    record = load_reflection_workflow(run_id, root)
    if record is None:
        raise FileNotFoundError(run_id)
    return record
