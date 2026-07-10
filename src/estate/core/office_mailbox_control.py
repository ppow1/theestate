"""Office mailbox, notification, and attention control handlers for WP-0519.

This module composes the existing collaboration message bus, mailbox index,
notification center, personnel directory, and local attention acknowledgement
artifacts.  It intentionally does not create a second mailbox, notification bus,
attention registry, or delivery queue.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from estate.core.collaboration_messages import acknowledge_message, create_reply, load_message
from estate.core.mailbox_index import generate_mailbox_index
from estate.core.operations_notification_center import acknowledge_operations_notification, generate_operations_notification_center
from estate.core.office_personnel_directory import open_employee_detail

MAILBOX_FILTER_OUTPUT = "runtime/steward/mailbox_filter_result.json"
MESSAGE_READ_STATE_OUTPUT = "runtime/steward/mailbox_message_read_state.json"
ATTENTION_ACK_OUTPUT = "runtime/steward/local_attention_acknowledgements.json"
DELIVERY_FAILURE_OUTPUT = "runtime/steward/delivery_failure_inspection.json"
MESSAGE_ROUTE_OUTPUT = "runtime/steward/mailbox_message_routes.jsonl"
MAILBOX_PAYLOAD_OUTPUT = "runtime/steward/mailbox_control_center.json"


def _root(root: Path | str | None) -> Path:
    return Path(root) if root is not None else Path.cwd()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _read_json(path: Path, default: Any):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _write_json(root: Path, rel: str, payload: Any) -> str:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return rel


def _append_jsonl(root: Path, rel: str, payload: Any) -> str:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload, sort_keys=True) + "\n")
    return rel


def refresh_mailbox_control_center(root=None, *, query: str = "", status: str = "", mailbox_id: str = "", sort: str = "created_at", write: bool = True) -> dict[str, Any]:
    base = _root(root)
    index = generate_mailbox_index(root=base, write=True)
    notes = generate_operations_notification_center(root=base, write=True)
    read_state = _read_json(base / MESSAGE_READ_STATE_OUTPUT, {"messages": {}}).get("messages", {})
    messages = list(index.get("messages") or [])
    for message in messages:
        state = read_state.get(str(message.get("message_id"))) or {}
        message["read_state"] = state.get("state") or ("read" if str(message.get("status", "")).lower() in {"closed", "acknowledged"} else "unread")
    def ok(message: dict[str, Any]) -> bool:
        hay = " ".join(str(message.get(k, "")) for k in ("message_id", "title", "source", "destination", "status", "priority")).lower()
        return (not query or query.lower() in hay) and (not status or str(message.get("status", "")).lower() == status.lower()) and (not mailbox_id or str(message.get("destination_mailbox_id")) == str(mailbox_id))
    filtered = [m for m in messages if ok(m)]
    reverse = sort.startswith("-")
    key = sort[1:] if reverse else sort
    filtered.sort(key=lambda m: str(m.get(key) or ""), reverse=reverse)
    payload = {
        "version": 1,
        "generated_at": _now(),
        "authority": "existing_mailbox_and_notification_mechanisms_only",
        "filters": {"query": query, "status": status, "mailbox_id": mailbox_id, "sort": sort},
        "summary": {"message_count": len(messages), "filtered_message_count": len(filtered), "notification_count": (notes.get("summary") or {}).get("filtered_notification_count", 0)},
        "messages": filtered,
        "notifications": notes.get("notifications") or [],
        "sources": {"mailbox_index": "collaboration/mailboxes/index.json", "notification_center": "runtime/notifications/operations_notification_center.json", "read_state": MESSAGE_READ_STATE_OUTPUT},
    }
    if write:
        _write_json(base, MAILBOX_PAYLOAD_OUTPUT, payload)
    return payload


def open_message_detail(message_id: str, root=None) -> dict[str, Any]:
    base = _root(root)
    path, message = load_message(message_id, base)
    payload = {"outcome": "completed", "message_id": message.get("id") or message.get("message_id") or path.stem, "path": str(path.relative_to(base)).replace("\\", "/"), "message": message}
    refresh_mailbox_control_center(base)
    return payload


def mark_message_read_state(message_id: str, state: str, root=None, actor: str = "Office") -> dict[str, Any]:
    if state not in {"read", "unread"}:
        raise ValueError("state must be read or unread")
    base = _root(root)
    path, _ = load_message(message_id, base)
    data = _read_json(base / MESSAGE_READ_STATE_OUTPUT, {"version": 1, "messages": {}})
    data.setdefault("messages", {})[str(message_id)] = {"state": state, "actor": actor, "updated_at": _now(), "source_message_path": str(path.relative_to(base)).replace("\\", "/")}
    _write_json(base, MESSAGE_READ_STATE_OUTPUT, data)
    refresh_mailbox_control_center(base)
    return data["messages"][str(message_id)]


def route_message(message_id: str, route_target: str, root=None, actor: str = "Office", note: str = "") -> dict[str, Any]:
    base = _root(root)
    path, message = load_message(message_id, base)
    record = {"message_id": message.get("id") or message.get("message_id") or path.stem, "source_message_path": str(path.relative_to(base)).replace("\\", "/"), "route_target": route_target, "actor": actor, "note": note, "routed_at": _now(), "canonical_mechanism": "collaboration_message_bus_route_evidence"}
    _append_jsonl(base, MESSAGE_ROUTE_OUTPUT, record)
    refresh_mailbox_control_center(base)
    return record


def local_attention_acknowledge(attention_id: str, root=None, actor: str = "Office", reason: str = "resolved locally") -> dict[str, Any]:
    base = _root(root)
    record = {"attention_id": attention_id, "actor": actor, "reason": reason, "acknowledged_at": _now(), "scope": "local_attention_only_not_authoritative_source_closure"}
    data = _read_json(base / ATTENTION_ACK_OUTPUT, {"version": 1, "acknowledgements": {}})
    data.setdefault("acknowledgements", {})[attention_id] = record
    _write_json(base, ATTENTION_ACK_OUTPUT, data)
    if str(attention_id).startswith("notification:"):
        acknowledge_operations_notification(str(attention_id).split(":", 1)[1], root=base, actor=actor)
    refresh_mailbox_control_center(base)
    return record


def inspect_delivery_failures(root=None) -> dict[str, Any]:
    base = _root(root)
    candidates = ["runtime/notifications/gotify_delivery_report.json", "runtime/audit/recall_audit_log.json", "runtime/notifications/notification_router_report.json"]
    failures = []
    for rel in candidates:
        path = base / rel
        if not path.exists():
            continue
        data = _read_json(path, {})
        text = json.dumps(data, sort_keys=True).lower()
        if any(word in text for word in ("fail", "error", "undelivered", "blocked")):
            failures.append({"path": rel, "summary": str(data.get("status") or data.get("summary") or "failure evidence found")[:500]})
    payload = {"generated_at": _now(), "failure_count": len(failures), "failures": failures, "actionable": bool(failures), "sources": candidates}
    _write_json(base, DELIVERY_FAILURE_OUTPUT, payload)
    return payload
