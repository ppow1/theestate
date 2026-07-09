"""Deterministic Alfred standalone runtime foundations.

This module intentionally performs no model calls, no watching, and no event
execution. It only builds governed intake records and renders briefings.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

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


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


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
