"""Deterministic Alfred standalone runtime foundations.

This module intentionally performs no model calls, no watching, and no event
execution. It only builds governed intake records and renders briefings.
"""
from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from estate.core.mailbox_index import (
    generate_mailbox_index,
    load_functional_mailbox_registry,
    load_personnel_registry,
    resolve_destination,
)

EVENT_TYPES = {
    "work_package_completed",
    "validation_failed",
    "validation_passed",
    "pull_request_merged",
    "local_runtime_error",
    "provider_unavailable",
    "queue_blocked",
    "resident_health_observation",
    "manual_steward_note",
}
SEVERITIES = {"info", "notice", "warning", "error", "critical"}
VERBOSITY_LEVELS = {"brief", "standard", "mid", "detailed", "forensic"}
INTERFACE_ADAPTERS = {"textgen", "text generation webui", "open webui", "sillytavern", "ollama"}
AUTHORITY_BOUNDARY = {
    "resident": "Alfred",
    "role": "Chief of Staff of the Estate",
    "may": ["summarize", "route", "brief", "recommend_escalation"],
    "must_not": ["execute_events", "approve_work", "merge_pull_requests", "validate_work", "spend", "hire", "modify_governance", "bypass_offices"],
    "live_access": "not_implied",
}

OPERATIONAL_MESSAGE_TYPES = {
    "notification", "coordination_request", "staffing_request", "execution_request",
    "blocker_escalation", "acceptance_request", "protected_decision_request",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _parse_time(value: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("created_at is required")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("created_at must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def evaluate_operational_route(
    message: dict[str, Any],
    *,
    root: str | Path,
    now: str | None = None,
    stale_after_seconds: int = 86400,
) -> dict[str, Any]:
    """Resolve one operational message against canonical registries without writing it."""
    root_path = Path(root)
    payload = deepcopy(message)
    message_id = str(payload.get("message_id") or payload.get("id") or "").strip()
    message_type = str(payload.get("message_type") or "").strip()
    reasons: list[str] = []
    if not message_id:
        reasons.append("message_id is required")
    if message_type not in OPERATIONAL_MESSAGE_TYPES:
        reasons.append(f"unsupported operational message type: {message_type or '(missing)'}")
    if not str(payload.get("source") or "").strip():
        reasons.append("source is required")
    if not isinstance(payload.get("payload"), dict):
        reasons.append("payload object is required")
    elif not str(payload["payload"].get("title") or "").strip():
        reasons.append("payload title is required")
    if payload.get("operational_context", {}).get("authorizes_action") is not False:
        reasons.append("operational message must explicitly authorize no action")

    personnel = load_personnel_registry(root_path)
    mailboxes = load_functional_mailbox_registry(root_path)
    employee_id, mailbox_id, warning = resolve_destination(payload, personnel, mailboxes)
    if warning:
        reasons.append(warning)
    if employee_id is None and mailbox_id is None:
        reasons.append("canonical destination could not be resolved")

    explicit_employee = payload.get("destination_employee_id")
    explicit_mailbox = payload.get("destination_mailbox_id")
    if explicit_employee is None and explicit_mailbox is None:
        reasons.append("explicit canonical destination ID is required; Alfred may not guess from a title")
    if explicit_employee is not None and employee_id is not None and int(explicit_employee) != int(employee_id):
        reasons.append("destination employee ID conflicts with canonical resolution")
    if explicit_mailbox is not None and mailbox_id is not None and int(explicit_mailbox) != int(mailbox_id):
        reasons.append("destination mailbox ID conflicts with canonical resolution")
    if explicit_employee is not None and explicit_mailbox is not None:
        entry = next((item for item in personnel if int(item.get("employee_id", -1)) == int(explicit_employee)), None)
        if entry and int(entry.get("mailbox_id", -1)) != int(explicit_mailbox):
            reasons.append("destination employee and mailbox IDs are misrouted")

    try:
        created_at = _parse_time(str(payload.get("created_at") or ""))
        observed_at = _parse_time(now) if now else datetime.now(timezone.utc)
        if (observed_at - created_at).total_seconds() > stale_after_seconds:
            reasons.append("message is stale and requires refreshed evidence")
        if created_at > observed_at:
            reasons.append("message timestamp is in the future")
    except ValueError as exc:
        reasons.append(str(exc))

    messages_dir = root_path / "collaboration" / "messages"
    existing_path = messages_dir / f"{message_id}.json"
    duplicate = False
    conflicting_duplicate = False
    if existing_path.exists():
        try:
            existing = json.loads(existing_path.read_text(encoding="utf-8"))
            duplicate = existing == payload
            conflicting_duplicate = not duplicate
            if conflicting_duplicate:
                reasons.append("message ID already exists with different content")
        except (OSError, json.JSONDecodeError):
            conflicting_duplicate = True
            reasons.append("message ID already exists as unreadable evidence")

    return {
        "schema_version": "estate.alfred-operational-route.v1",
        "message_id": message_id,
        "message_type": message_type,
        "canonical_destination": {
            "name": payload.get("destination"),
            "employee_id": employee_id,
            "mailbox_id": mailbox_id,
        },
        "routable": not reasons,
        "duplicate": duplicate,
        "conflicting_duplicate": conflicting_duplicate,
        "reasons": sorted(set(reasons)),
        "requires_ack": payload.get("requires_ack") is True,
        "ack_status": payload.get("ack_status"),
        "repository_message_path": f"collaboration/messages/{message_id}.json" if message_id else None,
        "mailbox_index_path": "collaboration/mailboxes/index.json",
        "routing_is_execution": False,
        "underlying_work_complete": False,
        "acceptance_granted": False,
        "authorizes_action": False,
    }


def route_operational_message(
    message: dict[str, Any],
    *,
    root: str | Path,
    now: str | None = None,
    stale_after_seconds: int = 86400,
) -> dict[str, Any]:
    """Write a routable message to the existing source-of-truth and rebuild discovery."""
    root_path = Path(root)
    decision = evaluate_operational_route(
        message, root=root_path, now=now, stale_after_seconds=stale_after_seconds
    )
    if not decision["routable"]:
        raise ValueError("operational message is not routable: " + "; ".join(decision["reasons"]))
    path = root_path / str(decision["repository_message_path"])
    if not decision["duplicate"]:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(message, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    index = generate_mailbox_index(root_path, write=True)
    indexed = next((item for item in index["messages"] if item.get("message_id") == decision["message_id"]), None)
    if not indexed or indexed.get("warning"):
        raise ValueError("routed message is not discoverable without warning in the canonical mailbox index")
    return {
        **decision,
        "recorded": True,
        "mailbox_index_message_count": index["message_count"],
        "indexed_destination_employee_id": indexed.get("destination_employee_id"),
        "indexed_destination_mailbox_id": indexed.get("destination_mailbox_id"),
    }


def correlate_operational_response(original: dict[str, Any], response: dict[str, Any]) -> dict[str, Any]:
    """Correlate acknowledgement/reply evidence without changing underlying work status."""
    original_id = str(original.get("message_id") or original.get("id") or "").strip()
    response_id = str(response.get("message_id") or response.get("id") or "").strip()
    thread_id = str(original.get("thread_id") or original_id)
    correlated = bool(
        original_id
        and response_id
        and (
            response.get("reply_to") == original_id
            or response.get("acknowledges") == original_id
            or response.get("thread_id") == thread_id
        )
    )
    return {
        "original_message_id": original_id,
        "response_message_id": response_id,
        "correlated": correlated,
        "acknowledged": correlated and response.get("message_type") == "acknowledgement",
        "underlying_work_complete": False,
        "decision_authority_exercised": False,
        "acceptance_granted": False,
        "authorizes_action": False,
    }


def classify_alfred_event(event_type: str, source: str | None = None, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """Classify event intake without executing or implying live access."""
    normalized_type = str(event_type).strip().lower()
    normalized_source = str(source or "manual").strip().lower()
    payload = payload or {}
    source_kind = "interface_adapter" if normalized_source in INTERFACE_ADAPTERS else "estate_runtime_source"
    if normalized_type not in EVENT_TYPES:
        source_kind = "unknown_event_type"
    requires_attention = normalized_type in {"validation_failed", "local_runtime_error", "provider_unavailable", "queue_blocked"}
    severity = {
        "validation_failed": "error",
        "local_runtime_error": "error",
        "provider_unavailable": "warning",
        "queue_blocked": "warning",
        "resident_health_observation": "notice",
    }.get(normalized_type, "info")
    return {
        "event_type": normalized_type,
        "recognized": normalized_type in EVENT_TYPES,
        "source_kind": source_kind,
        "textgen_runtime_role": "adapter_interface_not_home" if normalized_source in {"textgen", "text generation webui"} else None,
        "severity": payload.get("severity") or severity,
        "recommended_verbosity": payload.get("recommended_verbosity") or ("mid" if requires_attention else "standard"),
        "steward_attention_required": bool(payload.get("steward_attention_required", requires_attention)),
        "execution_authorized": False,
        "live_access_implied": False,
    }


def build_alfred_event(
    event_type: str,
    source: str,
    *,
    event_id: str | None = None,
    timestamp: str | None = None,
    severity: str | None = None,
    recommended_verbosity: str | None = None,
    source_artifacts: list[str] | None = None,
    required_action: str = "brief_only",
    authority_boundary: dict[str, Any] | None = None,
    payload: dict[str, Any] | None = None,
    steward_attention_required: bool | None = None,
) -> dict[str, Any]:
    classification = classify_alfred_event(event_type, source, payload)
    level = severity or classification["severity"]
    verbosity = recommended_verbosity or classification["recommended_verbosity"]
    if level not in SEVERITIES:
        raise ValueError(f"unsupported severity: {level}")
    if verbosity not in VERBOSITY_LEVELS:
        raise ValueError(f"unsupported verbosity: {verbosity}")
    if classification["recognized"] is False:
        raise ValueError(f"unsupported Alfred event type: {event_type}")
    boundary = dict(AUTHORITY_BOUNDARY)
    boundary.update(authority_boundary or {})
    boundary["execution_authorized"] = False
    boundary["live_access_implied"] = False
    return {
        "event_id": event_id or f"alfred_evt_{uuid4().hex[:12]}",
        "event_type": classification["event_type"],
        "source": source,
        "timestamp": timestamp or _now(),
        "severity": level,
        "recommended_verbosity": verbosity,
        "source_artifacts": _as_list(source_artifacts),
        "required_action": required_action,
        "authority_boundary": boundary,
        "payload": payload or {},
        "steward_attention_required": classification["steward_attention_required"] if steward_attention_required is None else bool(steward_attention_required),
        "classification": classification,
    }


def render_alfred_briefing(event: dict[str, Any], verbosity: str = "standard") -> dict[str, Any]:
    """Render presentation-depth variants while preserving the same facts."""
    if verbosity not in VERBOSITY_LEVELS:
        raise ValueError(f"unsupported verbosity: {verbosity}")
    facts = {
        "event_id": event["event_id"],
        "event_type": event["event_type"],
        "source": event["source"],
        "severity": event["severity"],
        "required_action": event["required_action"],
        "execution_authorized": False,
        "live_access_implied": False,
        "steward_attention_required": bool(event.get("steward_attention_required")),
    }
    lines = [f"Alfred runtime briefing: {facts['event_type']} from {facts['source']} ({facts['severity']})."]
    if verbosity in {"standard", "mid", "detailed", "forensic"}:
        lines.append(f"Required action: {facts['required_action']}; Alfred may brief or route, not execute or approve.")
    if verbosity in {"mid", "detailed", "forensic"}:
        lines.append(f"Source artifacts: {', '.join(event.get('source_artifacts') or ['none'])}.")
    if verbosity in {"detailed", "forensic"}:
        lines.append("Boundary: no live Estate access is implied by intake; interface providers are adapters.")
    if verbosity == "forensic":
        lines.append(f"Payload keys: {', '.join(sorted((event.get('payload') or {}).keys())) or 'none'}.")
    return {"resident": "Alfred", "verbosity": verbosity, "facts": facts, "briefing": "\n".join(lines)}


def record_alfred_health_observation(identity_status: str, conversation_status: str, governance_status: str, *, source: str = "manual", notes: str | None = None) -> dict[str, Any]:
    payload = {
        "identity_status": identity_status,
        "conversation_status": conversation_status,
        "governance_status": governance_status,
        "notes": notes or "",
    }
    return build_alfred_event(
        "resident_health_observation",
        source,
        severity="notice",
        recommended_verbosity="mid",
        required_action="observe_and_brief_only",
        payload=payload,
        steward_attention_required=False,
    )
