"""Message acknowledgement and reply helpers for the Communication Bus."""

import json
from datetime import datetime, timezone
from pathlib import Path

from estate.core.collaboration_events import append_event
from estate.core.paths import ESTATE_ROOT


def _root(root=None):
    return Path(root) if root else ESTATE_ROOT


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def messages_dir(root=None):
    return _root(root) / "collaboration" / "messages"


def message_path(message_id, root=None):
    base = messages_dir(root)
    direct = base / f"{message_id}.json"
    if direct.exists():
        return direct
    matches = sorted(base.glob(f"*{message_id}*.json"))
    if len(matches) == 1:
        return matches[0]
    if not matches:
        raise FileNotFoundError(f"message not found: {message_id}")
    raise ValueError(f"message id is ambiguous: {message_id}")


def load_message(message_id, root=None):
    path = message_path(message_id, root)
    message = _read_json(path)
    if not isinstance(message, dict):
        raise ValueError(f"message JSON must be an object: {path}")
    return path, message


def _message_id(message):
    return message.get("id") or message.get("message_id")


def _slug(value):
    chars = []
    previous_sep = False
    for char in str(value or "").strip().lower():
        if char.isalnum():
            chars.append(char)
            previous_sep = False
        elif not previous_sep:
            chars.append("_")
            previous_sep = True
    return "".join(chars).strip("_") or "message"


def _next_id(prefix, root=None):
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    candidate = f"msg_{stamp}_{prefix}"
    path = messages_dir(root) / f"{candidate}.json"
    counter = 1
    while path.exists():
        candidate = f"msg_{stamp}_{prefix}_{counter:02d}"
        path = messages_dir(root) / f"{candidate}.json"
        counter += 1
    return candidate


def _source_for_reply(original, actor):
    return actor or original.get("destination") or original.get("destination_employee_id") or "unknown"


def _destination_for_reply(original):
    return original.get("source") or original.get("source_employee_id") or "unknown"


def acknowledge_message(message_id, actor="Alfred", note="Acknowledged.", root=None):
    """Mark a message acknowledged and create a durable acknowledgement reply."""
    base = _root(root)
    original_path, original = load_message(message_id, base)
    original_id = _message_id(original) or original_path.stem
    created_at = _now()

    original["ack_status"] = "acknowledged"
    original["acknowledged_at"] = created_at
    original["acknowledged_by"] = actor
    if str(original.get("status", "")).lower() in {"open", "new", "queued", "ready"}:
        original["status"] = "acknowledged"
    _write_json(original_path, original)

    ack_id = _next_id(f"ack_{_slug(original_id)}", base)
    ack = {
        "id": ack_id,
        "version": original.get("version", 1),
        "created_at": created_at,
        "created_by": actor,
        "source": _source_for_reply(original, actor),
        "destination": _destination_for_reply(original),
        "classification": original.get("classification", "Estate Internal"),
        "message_type": "acknowledgement",
        "priority": original.get("priority", "normal"),
        "status": "closed",
        "requires_ack": False,
        "ack_status": "not_required",
        "acknowledges": original_id,
        "reply_to": original_id,
        "thread_id": original.get("thread_id") or original_id,
        "payload": {
            "title": f"Acknowledgement: {original_id}",
            "summary": note,
            "instructions": "",
            "artifact_refs": [],
        },
    }
    ack_path = messages_dir(base) / f"{ack_id}.json"
    _write_json(ack_path, ack)
    _event("message.acknowledged", actor, original_id, ack_id, base)
    return {"message": original, "message_path": str(original_path.relative_to(base)), "acknowledgement": ack, "acknowledgement_path": str(ack_path.relative_to(base))}


def create_reply(message_id, actor="Alfred", body="", title=None, root=None):
    """Create a reply message that references an existing message/thread."""
    base = _root(root)
    original_path, original = load_message(message_id, base)
    original_id = _message_id(original) or original_path.stem
    reply_id = _next_id(f"reply_{_slug(original_id)}", base)
    reply = {
        "id": reply_id,
        "version": original.get("version", 1),
        "created_at": _now(),
        "created_by": actor,
        "source": _source_for_reply(original, actor),
        "destination": _destination_for_reply(original),
        "classification": original.get("classification", "Estate Internal"),
        "message_type": "reply",
        "priority": original.get("priority", "normal"),
        "status": "open",
        "requires_ack": False,
        "ack_status": "not_required",
        "reply_to": original_id,
        "thread_id": original.get("thread_id") or original_id,
        "payload": {"title": title or f"Reply: {original_id}", "summary": body, "instructions": "", "artifact_refs": []},
    }
    reply_path = messages_dir(base) / f"{reply_id}.json"
    _write_json(reply_path, reply)
    _event("message.replied", actor, original_id, reply_id, base)
    return {"reply": reply, "reply_path": str(reply_path.relative_to(base))}


def group_threads(root=None):
    base = _root(root)
    threads = {}
    for path in sorted(messages_dir(base).glob("*.json")):
        try:
            message = _read_json(path)
        except Exception:
            continue
        if not isinstance(message, dict):
            continue
        mid = _message_id(message) or path.stem
        tid = message.get("thread_id") or message.get("reply_to") or message.get("acknowledges") or mid
        threads.setdefault(tid, []).append(mid)
    return threads


def _event(event_type, actor, original_id, generated_id, root):
    try:
        append_event(event_type, actor, {"message_id": original_id, "generated_message_id": generated_id}, subject_id=original_id, root=root)
    except Exception:
        pass
