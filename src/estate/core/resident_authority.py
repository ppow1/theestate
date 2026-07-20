"""Resident action authority boundary.

This module records local operational permission checks for residents. It does
not grant governance, validation, merge, personnel, or Steward authority.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from estate.core.paths import ESTATE_ROOT

AUDIT_PATH = Path("runtime/residents/authority_decisions.jsonl")
SOURCE_REFERENCES = [
    "collaboration/work_packages/pending/WP-0110_SERIES_resident_action_authority_boundary.md",
    "src/estate/core/resident_authority.py",
]

ALLOWED = "allowed"
DENIED = "denied"
REQUIRES_STEWARD = "requires_steward_approval"
REQUIRES_ESCALATION = "requires_escalation"

RESPONSE_GUIDANCE = {
    ALLOWED: {"tone": "normal", "label": "Allowed", "operator_message": "This resident action is within the non-authoritative resident boundary."},
    DENIED: {"tone": "firm_boundary", "label": "Denied", "operator_message": "This resident action is outside delegated resident authority and must not proceed."},
    REQUIRES_STEWARD: {"tone": "approval_required", "label": "Requires Steward approval", "operator_message": "This resident action may only proceed after explicit Steward approval."},
    REQUIRES_ESCALATION: {"tone": "escalation_required", "label": "Requires escalation", "operator_message": "This resident action requires escalation before any external or consequential step occurs."},
}

ACTION_CATEGORIES: dict[str, dict[str, Any]] = {
    "conversation": {"classification": "conversation_only", "default": ALLOWED, "reason": "Conversation is informational and performs no privileged action."},
    "observe": {"classification": "non_authoritative", "default": ALLOWED, "reason": "Observation is read-only local awareness."},
    "summarize": {"classification": "non_authoritative", "default": ALLOWED, "reason": "Summaries are non-authoritative operational views."},
    "search": {"classification": "non_authoritative", "default": ALLOWED, "reason": "Local search is informational only."},
    "draft": {"classification": "proposal", "default": ALLOWED, "reason": "Drafts may be prepared but are not approvals."},
    "propose": {"classification": "proposal", "default": ALLOWED, "reason": "Proposals require later canonical Steward action to become authoritative."},
    "route": {"classification": "non_authoritative", "default": ALLOWED, "reason": "Routing local attention does not decide or execute."},
    "request-steward-decision": {"classification": "steward_request", "default": ALLOWED, "reason": "Residents may request Steward attention without deciding for the Steward."},
    "create-work-package-draft": {"classification": "draft", "default": REQUIRES_STEWARD, "reason": "Work-package drafts must remain non-authoritative until reviewed."},
    "update-resident-runtime-state": {"classification": "runtime", "default": ALLOWED, "reason": "Bounded duty runners may update resident runtime presence/state."},
    "send-mailbox-message-artifact": {"classification": "routing", "default": REQUIRES_STEWARD, "reason": "Message artifacts can affect workflows and require Steward approval unless separately delegated."},
    "run-validation-command": {"classification": "validation", "default": DENIED, "reason": "Residents may surface validation needs but cannot claim validation authority."},
    "execute-work-package": {"classification": "execution", "default": DENIED, "reason": "Residents do not execute work packages automatically."},
    "approve-merge-work": {"classification": "merge_authority", "default": DENIED, "reason": "Approval and merge authority remain outside resident authority."},
    "modify-personnel-identity": {"classification": "personnel_authority", "default": DENIED, "reason": "Residents cannot create, terminate, or modify personnel identities by default."},
    "modify-governance-artifact": {"classification": "governance_authority", "default": DENIED, "reason": "Residents cannot modify governance authority by default."},
    "external-notification-network-action": {"classification": "external_action", "default": REQUIRES_ESCALATION, "reason": "External or network actions require explicit escalation/approval."},
}

ALIASES = {
    "request Steward decision": "request-steward-decision",
    "modify-personnel": "modify-personnel-identity",
    "execute work package": "execute-work-package",
    "approve": "approve-merge-work",
    "merge": "approve-merge-work",
    "validate": "run-validation-command",
}

RESIDENT_RULES = {
    "alfred": {
        "resident": "Alfred",
        "allowed": ["conversation", "observe", "summarize", "search", "draft", "propose", "route", "request-steward-decision", "update-resident-runtime-state"],
        "approval_required": ["create-work-package-draft", "send-mailbox-message-artifact"],
        "escalation_required": ["external-notification-network-action"],
        "denied": ["run-validation-command", "execute-work-package", "approve-merge-work", "modify-personnel-identity", "modify-governance-artifact"],
    },
    "helen": {
        "resident": "Helen",
        "allowed": ["conversation", "observe", "summarize", "search", "draft", "propose", "route", "request-steward-decision", "update-resident-runtime-state"],
        "approval_required": ["create-work-package-draft", "send-mailbox-message-artifact"],
        "escalation_required": ["external-notification-network-action"],
        "denied": ["run-validation-command", "execute-work-package", "approve-merge-work", "modify-personnel-identity", "modify-governance-artifact"],
    },
    "grace": {
        "resident": "Grace",
        "allowed": ["conversation", "observe", "summarize", "propose", "route", "request-steward-decision", "update-resident-runtime-state"],
        "approval_required": ["create-work-package-draft", "send-mailbox-message-artifact", "external-notification-network-action"],
        "escalation_required": [],
        "denied": ["run-validation-command", "execute-work-package", "approve-merge-work", "modify-personnel-identity", "modify-governance-artifact"],
    },
}

for _resident in ("ingrid", "evelyn", "eleanor", "marie", "judy"):
    RESIDENT_RULES[_resident] = {
        "resident": _resident.title(),
        "allowed": ["conversation", "observe", "summarize", "search", "draft", "propose", "route", "request-steward-decision"],
        "approval_required": ["create-work-package-draft", "send-mailbox-message-artifact"],
        "escalation_required": ["external-notification-network-action"],
        "denied": ["run-validation-command", "execute-work-package", "approve-merge-work", "modify-personnel-identity", "modify-governance-artifact"],
    }


def _root(root: str | Path | None = None) -> Path:
    return Path(root) if root is not None else (ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd())


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def normalize_action(action: str) -> str:
    if action in ALIASES:
        return ALIASES[action]
    return re.sub(r"[^a-z0-9]+", "-", str(action or "").strip().lower()).strip("-")


def _resident_key(resident: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(resident or "").lower())


def list_authority(resident: str | None = None) -> dict[str, Any]:
    key = _resident_key(resident) if resident else None
    rules = {k: v for k, v in RESIDENT_RULES.items() if key is None or k == key}
    return {"version": 1, "kind": "resident_authority_boundary", "generated_at": _now(), "audit_path": str(AUDIT_PATH), "source_references": SOURCE_REFERENCES, "action_categories": ACTION_CATEGORIES, "resident_boundaries": rules, "default_unknown_action": DENIED}


def classification_driven_response(decision: str, classification: str, reason: str) -> dict[str, Any]:
    """Return operator-facing response guidance derived from authority classification.

    The guidance is intentionally descriptive only: it tells residents and
    operators how to respond to a boundary decision without granting any new
    authority or changing the decision itself.
    """

    guidance = RESPONSE_GUIDANCE.get(decision, RESPONSE_GUIDANCE[DENIED])
    blocked = decision in {DENIED, REQUIRES_STEWARD, REQUIRES_ESCALATION}
    return {
        "response_classification": classification,
        "boundary_response": guidance["label"],
        "response_tone": guidance["tone"],
        "operator_message": guidance["operator_message"],
        "resident_instruction": (
            "Provide only a non-authoritative explanation, cite the boundary reason, "
            "and route to the required authority; do not execute or imply approval."
            if blocked
            else "Proceed only as a non-authoritative resident action and preserve audit context."
        ),
        "must_not_execute": blocked,
        "reason": reason,
    }


def check_authority(resident: str, action: str, *, target: str | None = None, source_refs: list[str] | None = None, root: str | Path | None = None, audit: bool = True) -> dict[str, Any]:
    root_path = _root(root)
    normalized = normalize_action(action)
    resident_key = _resident_key(resident)
    rules = RESIDENT_RULES.get(resident_key)
    category = ACTION_CATEGORIES.get(normalized)
    if not rules:
        decision, reason, classification = DENIED, f"Unknown resident {resident!r}; no resident authority is implied.", "unknown_resident"
    elif not category:
        decision, reason, classification = DENIED, f"Unknown action category {action!r}; safe default denies resident action.", "unknown_action"
    elif normalized in rules.get("denied", []):
        decision, reason, classification = DENIED, category["reason"], category["classification"]
    elif normalized in rules.get("approval_required", []):
        decision, reason, classification = REQUIRES_STEWARD, category["reason"], category["classification"]
    elif normalized in rules.get("escalation_required", []):
        decision, reason, classification = REQUIRES_ESCALATION, category["reason"], category["classification"]
    elif normalized in rules.get("allowed", []):
        decision, reason, classification = ALLOWED, category["reason"], category["classification"]
    else:
        decision, reason, classification = REQUIRES_STEWARD, "Action is recognized but not explicitly allowed for this resident.", category["classification"]
    payload = {
        "version": 1,
        "kind": "resident_authority_decision",
        "checked_at": _now(),
        "resident": rules["resident"] if rules else str(resident),
        "requested_action": str(action),
        "normalized_action": normalized,
        "target": target,
        "authority_classification": classification,
        "decision": decision,
        "allowed": decision == ALLOWED,
        "requires_steward_approval": decision == REQUIRES_STEWARD,
        "requires_escalation": decision == REQUIRES_ESCALATION,
        "reason": reason,
        "classification_driven_response": classification_driven_response(decision, classification, reason),
        "source_artifact_references": [*SOURCE_REFERENCES, *(source_refs or [])],
        "audit_path": str(AUDIT_PATH),
        "source_of_truth_boundary": "Operational permission check only; does not change Estate constitutional, governance, validation, merge, personnel, or Steward authority.",
    }
    if audit:
        path = root_path / AUDIT_PATH
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, sort_keys=True) + "\n")
    return payload


def format_authority_decision(payload: dict[str, Any]) -> str:
    return f"{payload['resident']} {payload['normalized_action']}: {payload['decision']} — {payload['reason']}"
