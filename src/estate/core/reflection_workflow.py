"""Durable lifecycle records for governed ChatGPT reflection workflows.

This module records deterministic workflow state and evidence. It does not assess
whether reflection is warranted, approve onboarding, confirm renewal, retire an
implementation, or create a conversation.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from estate.core.paths import ESTATE_ROOT

SCHEMA_VERSION = "reflection_workflow.v1"
WORKFLOW_DIR = Path("runtime/reflection/workflows")

STATES = (
    "evaluation_requested",
    "assessment_in_progress",
    "reflection_recommended",
    "reflection_authorized",
    "package_building",
    "package_validation_failed",
    "package_ready_for_review",
    "helen_review_required",
    "approved_for_onboarding",
    "onboarding_in_progress",
    "first_assignment_in_progress",
    "renewal_confirmed",
    "previous_implementation_retired",
    "manual_fallback_active",
    "renewal_blocked",
)

PROTECTED_STATES = {
    "reflection_authorized": {"Steward"},
    "approved_for_onboarding": {"Helen", "Steward"},
    "renewal_confirmed": {"Helen", "Steward"},
    "previous_implementation_retired": {"Steward"},
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
    "renewal_blocked": {
        "assessment_in_progress",
        "reflection_authorized",
        "package_building",
        "manual_fallback_active",
        "helen_review_required",
        "onboarding_in_progress",
        "first_assignment_in_progress",
    },
}


def _root(root: str | Path | None) -> Path:
    return Path(root) if root is not None else ESTATE_ROOT


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _slug(value: str) -> str:
    slug = "".join(ch.lower() if ch.isalnum() else "_" for ch in str(value))
    return "_".join(part for part in slug.split("_") if part) or "workflow"


def _clean_list(values: Iterable[str] | None) -> list[str]:
    return [str(value).strip() for value in (values or []) if str(value).strip()]


def workflow_path(run_id: str, root: str | Path | None = None) -> Path:
    return _root(root) / WORKFLOW_DIR / f"{_slug(run_id)}.json"


def load_reflection_workflow(run_id: str, root: str | Path | None = None) -> dict[str, Any] | None:
    path = workflow_path(run_id, root)
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def _write(record: dict[str, Any], root: str | Path | None = None) -> dict[str, Any]:
    path = workflow_path(record["run_id"], root)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)
    return record


def create_reflection_workflow(
    *,
    run_id: str,
    office: str,
    officeholder: str,
    current_implementation: str,
    mailbox_id: str,
    initiation_type: str,
    authority_reference: str,
    actor: str,
    reason: str = "",
    repository: str = "",
    branch: str = "",
    blockers: Iterable[str] | None = None,
    root: str | Path | None = None,
) -> dict[str, Any]:
    """Create an idempotent workflow record for evaluation or direct reflection."""

    required = {
        "run_id": run_id,
        "office": office,
        "officeholder": officeholder,
        "current_implementation": current_implementation,
        "mailbox_id": mailbox_id,
        "initiation_type": initiation_type,
        "authority_reference": authority_reference,
        "actor": actor,
    }
    missing = [name for name, value in required.items() if not str(value or "").strip()]
    if missing:
        raise ValueError(f"missing required input(s): {', '.join(missing)}")

    normalized_type = str(initiation_type).strip().lower()
    if normalized_type not in {"evaluation", "direct_reflection"}:
        raise ValueError("initiation_type must be evaluation or direct_reflection")

    initial_state = "evaluation_requested" if normalized_type == "evaluation" else "reflection_authorized"
    if initial_state == "reflection_authorized" and str(actor).strip().lower() != "steward":
        raise PermissionError("direct reflection requires actor=Steward")

    timestamp = _now()
    record = {
        "schema_version": SCHEMA_VERSION,
        "run_id": str(run_id).strip(),
        "office": str(office).strip(),
        "officeholder": str(officeholder).strip(),
        "current_implementation": str(current_implementation).strip(),
        "renewed_implementation": None,
        "mailbox_id": str(mailbox_id).strip(),
        "initiation_type": normalized_type,
        "authority_reference": str(authority_reference).strip(),
        "reason": str(reason).strip(),
        "repository": str(repository).strip(),
        "branch": str(branch).strip(),
        "state": initial_state,
        "last_successful_action": "workflow_created",
        "next_action": "request_worker_assessment" if initial_state == "evaluation_requested" else "begin_package_building",
        "blockers": _clean_list(blockers),
        "warnings": [],
        "artifacts": {},
        "receipts": {},
        "created_at": timestamp,
        "updated_at": timestamp,
        "history": [
            {
                "event_id": "workflow_created",
                "from": None,
                "to": initial_state,
                "actor": str(actor).strip(),
                "authority_reference": str(authority_reference).strip(),
                "evidence": {},
                "at": timestamp,
            }
        ],
    }

    existing = load_reflection_workflow(run_id, root)
    if existing is not None:
        comparable_existing = dict(existing)
        comparable_record = dict(record)
        for value in (comparable_existing, comparable_record):
            value.pop("created_at", None)
            value.pop("updated_at", None)
            value.pop("history", None)
        if comparable_existing == comparable_record:
            return existing
        raise ValueError(f"conflicting workflow already exists: {workflow_path(run_id, root)}")

    return _write(record, root)


def transition_reflection_workflow(
    run_id: str,
    to_state: str,
    *,
    actor: str,
    evidence: dict[str, Any],
    event_id: str,
    next_action: str,
    last_successful_action: str | None = None,
    blockers: Iterable[str] | None = None,
    warnings: Iterable[str] | None = None,
    artifacts: dict[str, str] | None = None,
    receipts: dict[str, str] | None = None,
    renewed_implementation: str | None = None,
    root: str | Path | None = None,
) -> dict[str, Any]:
    """Apply one validated, append-only and idempotent lifecycle transition."""

    if to_state not in STATES:
        raise ValueError(f"unknown reflection workflow state: {to_state}")
    if not str(actor or "").strip():
        raise ValueError("actor is required")
    if not str(event_id or "").strip():
        raise ValueError("event_id is required")
    if not isinstance(evidence, dict) or not evidence:
        raise ValueError("non-empty evidence is required")
    if not str(next_action or "").strip():
        raise ValueError("next_action is required")

    record = load_reflection_workflow(run_id, root)
    if record is None:
        raise FileNotFoundError(run_id)

    if any(event.get("event_id") == event_id for event in record.get("history", [])):
        return record

    current = record["state"]
    if to_state not in ALLOWED_TRANSITIONS[current]:
        raise ValueError(f"invalid reflection transition: {current} -> {to_state}")

    allowed_actors = PROTECTED_STATES.get(to_state)
    if allowed_actors and str(actor).strip().lower() not in {name.lower() for name in allowed_actors}:
        raise PermissionError(f"{to_state} requires actor in {sorted(allowed_actors)}")

    timestamp = _now()
    event = {
        "event_id": str(event_id).strip(),
        "from": current,
        "to": to_state,
        "actor": str(actor).strip(),
        "evidence": evidence,
        "at": timestamp,
    }
    record["history"].append(event)
    record["state"] = to_state
    record["updated_at"] = timestamp
    record["next_action"] = str(next_action).strip()
    record["last_successful_action"] = str(last_successful_action or event_id).strip()
    if blockers is not None:
        record["blockers"] = _clean_list(blockers)
    if warnings is not None:
        record["warnings"] = _clean_list(warnings)
    if artifacts:
        record.setdefault("artifacts", {}).update({str(key): str(value) for key, value in artifacts.items()})
    if receipts:
        record.setdefault("receipts", {}).update({str(key): str(value) for key, value in receipts.items()})
    if renewed_implementation is not None:
        record["renewed_implementation"] = str(renewed_implementation).strip() or None
    return _write(record, root)


def reflection_workflow_status(run_id: str, root: str | Path | None = None) -> dict[str, Any]:
    record = load_reflection_workflow(run_id, root)
    if record is None:
        raise FileNotFoundError(run_id)
    return record
