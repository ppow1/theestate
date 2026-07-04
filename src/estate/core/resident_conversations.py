"""Resident conversation workspace data model for the Operations Center.

The workspace is an interface surface only: it summarizes local resident,
mailbox, message, and artifact context, but it does not treat chat or voice
conversation as an authoritative institutional record.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

from estate.core.paths import ESTATE_ROOT
from estate.core.resident_cards import PLACEHOLDER, build_resident_card
from estate.core.resident_conversation_sessions import session_summaries_for_workspace

DEFAULT_RESIDENT_NAMES = ("Alfred", "Helen")


def _root(root=None):
    if root is not None:
        return Path(root)
    if ESTATE_ROOT.exists():
        return ESTATE_ROOT
    return Path.cwd()


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _slug(value):
    return "".join(ch.lower() for ch in str(value or "") if ch.isalnum())


def _rel(path, root):
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def _read_json(path, warnings, required=False, root=None):
    if not path.exists():
        warnings.append({"type": "missing_artifact", "path": _rel(path, root or path.parent), "required": required})
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        warnings.append({"type": "malformed_json", "path": str(path), "message": str(exc), "required": required})
        return None


def _read_registry(root, name, warnings):
    data = _read_json(root / "data" / "registry" / f"{name}.json", warnings, root=root)
    return data if isinstance(data, list) else []


def _message_title(message):
    payload = message.get("payload") if isinstance(message.get("payload"), dict) else {}
    return message.get("title") or payload.get("title") or message.get("message_id") or message.get("id") or "Untitled message"


def _message_summary(message):
    payload = message.get("payload") if isinstance(message.get("payload"), dict) else {}
    artifact_refs = []
    for key in ("related_artifact", "related_work_package", "audit_ref", "promotion_ref"):
        value = message.get(key)
        if value:
            artifact_refs.append(str(value))
    for ref in payload.get("artifact_refs") or []:
        artifact_refs.append(str(ref))
    return {
        "id": message.get("message_id") or message.get("id") or "unknown",
        "title": _message_title(message),
        "summary": payload.get("summary") or message.get("summary") or PLACEHOLDER,
        "created_at": message.get("created_at"),
        "source": message.get("source") or message.get("created_by") or PLACEHOLDER,
        "destination": message.get("destination") or (f"mailbox.{message.get('destination_mailbox_id')}" if message.get("destination_mailbox_id") is not None else PLACEHOLDER),
        "status": message.get("status") or "open",
        "priority": message.get("priority") or "normal",
        "path": message.get("path"),
        "source_artifacts": [ref for ref in artifact_refs if ref],
    }


def _load_messages(root, warnings):
    messages = []
    msg_dir = root / "collaboration" / "messages"
    if not msg_dir.exists():
        warnings.append({"type": "missing_artifact", "path": "collaboration/messages", "required": False})
        return messages
    for path in sorted(msg_dir.glob("*")):
        if path.suffix == ".json":
            data = _read_json(path, warnings, root=root)
            if isinstance(data, dict):
                data = dict(data)
                data.setdefault("path", _rel(path, root))
                messages.append(data)
        elif path.suffix in {".md", ".txt"}:
            text = path.read_text(encoding="utf-8", errors="replace")
            messages.append({"id": path.stem, "title": path.stem.replace("_", " "), "summary": text[:240], "path": _rel(path, root), "source": "markdown_message"})
    return messages


def _matches_resident(message, card, resident):
    name = str(card.get("name") or resident.get("name") or "")
    slug = _slug(name)
    mailbox_id = (card.get("mailbox") or {}).get("mailbox_id")
    text = " ".join(str(message.get(key) or "") for key in ("id", "message_id", "title", "created_by", "source", "destination", "path", "related_work_package", "related_artifact"))
    payload = message.get("payload") if isinstance(message.get("payload"), dict) else {}
    text += " " + " ".join(str(payload.get(key) or "") for key in ("title", "summary", "instructions"))
    if slug and slug in _slug(text):
        return True
    if mailbox_id is not None and message.get("destination_mailbox_id") == mailbox_id:
        return True
    if resident.get("id") and str(resident.get("id")) in text:
        return True
    return False


def _conversation_for(root, resident, card, messages):
    related = [_message_summary(m) for m in messages if isinstance(m, dict) and _matches_resident(m, card, resident)]
    related = sorted(related, key=lambda item: str(item.get("created_at") or item.get("path") or ""), reverse=True)[:8]
    sources = [card.get("details_link")] if card.get("details_link") and card.get("details_link") != PLACEHOLDER else []
    mailbox_source = (card.get("mailbox") or {}).get("source")
    if mailbox_source:
        sources.append(mailbox_source)
    for message in related:
        if message.get("path"):
            sources.append(message["path"])
        sources.extend(message.get("source_artifacts") or [])
    sessions = session_summaries_for_workspace(root, resident=card.get("name") or resident.get("name"))
    for session in sessions:
        if session.get("path"):
            sources.append(session["path"])
        sources.extend(session.get("source_artifacts") or [])
    return {
        "resident_id": resident.get("id"),
        "resident_name": card.get("name") or resident.get("name") or PLACEHOLDER,
        "role": card.get("role") or PLACEHOLDER,
        "status": card.get("operational_status") or PLACEHOLDER,
        "available": bool(card.get("available")),
        "mailbox": card.get("mailbox") or {"mailbox_id": None, "display_name": PLACEHOLDER, "source": None},
        "recent_messages": related,
        "recent_sessions": sessions,
        "conversation_placeholder": "Local conversation surface placeholder. Draft interaction can be displayed here, but durable actions must link to institutional artifacts.",
        "transcript_audit_placeholder": "No authoritative voice/chat transcript is recorded by this workspace. Future transcripts must be promoted into audit, message, work-package, or artifact records before becoming institutional records.",
        "source_artifacts": sorted({str(source) for source in sources if source}),
    }


def build_resident_conversations_workspace(root=None, names=None):
    root = _root(root)
    warnings = []
    residents = _read_registry(root, "residents", warnings)
    personnel = _read_registry(root, "personnel", warnings)
    mailboxes = _read_registry(root, "mailboxes", warnings)
    runtime = _read_json(root / "runtime" / "residents" / "status.json", warnings, root=root) or {}
    requested = list(names or DEFAULT_RESIDENT_NAMES)
    by_name = {_slug(r.get("name")): r for r in residents if isinstance(r, dict)}
    resident_records = []
    for name in requested:
        resident_records.append(by_name.get(_slug(name), {"name": name}))
    if names is None:
        for resident in residents:
            if isinstance(resident, dict) and _slug(resident.get("name")) not in {_slug(n) for n in requested}:
                resident_records.append(resident)
    messages = _load_messages(root, warnings)
    conversations = []
    for resident in resident_records:
        card = build_resident_card(root, resident, personnel=personnel, mailboxes=mailboxes, runtime=runtime)
        conversations.append(_conversation_for(root, resident, card, messages))
    return {
        "version": 1,
        "generated_at": _now(),
        "available": True,
        "kind": "resident_conversations_workspace",
        "path": "data/registry/residents.json; collaboration/messages; data/registry/mailboxes.json",
        "data": {
            "resident_selection": [item["resident_name"] for item in conversations],
            "conversations": conversations,
            "record_policy": "Conversation is an interface surface only; institutional truth remains in linked artifacts, messages, work packages, and audit records.",
        },
        "warnings": warnings,
    }
