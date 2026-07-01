"""Durable local event trail for the Estate Collaboration Layer.

The event trail is intentionally filesystem-local. It records operational facts
for Collaboration Layer tooling without replacing the Communication Bus or using
GitHub as an event bus.
"""

import json
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from estate.core.paths import ESTATE_ROOT

SUPPORTED_EVENT_TYPES = {
    "message.routed",
    "inbox.updated",
    "work.claimed",
    "work.completed",
    "work.blocked",
    "review.requested",
    "promotion.requested",
    "audit.result.created",
}

DEFAULT_RECENT_LIMIT = 25


def _estate_root(root=None):
    if root is not None:
        return Path(root)
    return ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd()


def event_paths(root=None):
    base = _estate_root(root)
    return {
        "root": base,
        "runtime_events": base / "runtime" / "collaboration" / "events",
        "events_log": base / "runtime" / "collaboration" / "events" / "events.jsonl",
        "latest": base / "runtime" / "collaboration" / "events" / "latest.json",
        "status": base / "collaboration" / "status",
        "summary": base / "collaboration" / "status" / "event_summary.json",
    }


def _now():
    return datetime.now().isoformat(timespec="seconds")


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def build_event(event_type, source, payload=None, *, subject_id=None, classification="Estate Internal", created_at=None):
    """Build a canonical collaboration event record."""
    if event_type not in SUPPORTED_EVENT_TYPES:
        raise ValueError(f"Unsupported collaboration event type: {event_type}")
    if payload is not None and not isinstance(payload, dict):
        raise ValueError("Collaboration event payload must be a dictionary")

    return {
        "id": f"evt_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:8]}",
        "version": 1,
        "type": event_type,
        "created_at": created_at or _now(),
        "source": source,
        "subject_id": subject_id,
        "classification": classification,
        "payload": payload or {},
    }


def validate_event(event):
    missing = []
    for field in ["id", "version", "type", "created_at", "source", "classification", "payload"]:
        if field not in event:
            missing.append(field)
    if event.get("type") not in SUPPORTED_EVENT_TYPES:
        missing.append("type.supported")
    if not isinstance(event.get("payload", {}), dict):
        missing.append("payload.object")
    return missing


def append_event(event_type, source, payload=None, *, subject_id=None, classification="Estate Internal", root=None):
    """Append one event to the local JSONL trail and refresh latest/summary files."""
    paths = event_paths(root)
    event = build_event(event_type, source, payload, subject_id=subject_id, classification=classification)
    missing = validate_event(event)
    if missing:
        raise ValueError(f"Invalid collaboration event: {', '.join(missing)}")

    paths["runtime_events"].mkdir(parents=True, exist_ok=True)
    with paths["events_log"].open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=True) + "\n")
    _write_json(paths["latest"], event)
    generate_event_summary(root=root)
    return event


def read_events(root=None, limit=None):
    """Read the event log, preserving malformed records as non-fatal errors."""
    paths = event_paths(root)
    events = []
    errors = []
    if not paths["events_log"].exists():
        return events, errors

    for line_number, line in enumerate(paths["events_log"].read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except Exception as exc:
            errors.append({"line": line_number, "error": str(exc), "raw": line[:200]})
            continue
        invalid = validate_event(event)
        if invalid:
            errors.append({"line": line_number, "error": "invalid_event", "missing_fields": invalid})
            continue
        events.append(event)

    if limit is not None:
        events = events[-int(limit):]
    return events, errors


def generate_event_summary(root=None, recent_limit=DEFAULT_RECENT_LIMIT):
    paths = event_paths(root)
    events, errors = read_events(root=root)
    counts = {}
    for event in events:
        counts[event["type"]] = counts.get(event["type"], 0) + 1

    latest = events[-1] if events else None
    summary = {
        "version": 1,
        "generated_at": _now(),
        "event_count": len(events),
        "malformed_record_count": len(errors),
        "event_types": sorted(SUPPORTED_EVENT_TYPES),
        "counts_by_type": counts,
        "latest_event": latest,
        "recent_events": events[-recent_limit:],
        "errors": errors,
        "generated_files": {
            "events_log": str(paths["events_log"].relative_to(paths["root"])),
            "latest": str(paths["latest"].relative_to(paths["root"])),
            "summary": str(paths["summary"].relative_to(paths["root"])),
        },
    }
    _write_json(paths["summary"], summary)
    if latest is not None:
        _write_json(paths["latest"], latest)
    return summary


def format_event_summary(summary):
    lines = [
        "Estate Collaboration Events",
        f"Events: {summary.get('event_count', 0)}",
        f"Malformed records: {summary.get('malformed_record_count', 0)}",
    ]
    for event_type, count in sorted(summary.get("counts_by_type", {}).items()):
        lines.append(f"- {event_type}: {count}")
    latest = summary.get("latest_event")
    if latest:
        lines.append(f"Latest: {latest.get('type')} ({latest.get('id')})")
    return "\n".join(lines)
