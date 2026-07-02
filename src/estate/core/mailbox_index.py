"""Mailbox discovery index generation for Estate collaboration messages.

Messages under collaboration/messages remain the source of truth. This module
builds a generated index so external workers can discover mailbox contents from
a single known file without requiring directory enumeration.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

from estate.core.paths import ESTATE_ROOT

INDEX_VERSION = 1
ALLOWED_MAILBOX_TYPES = {"personnel", "office", "service", "queue", "work_package", "temporary"}
LEGACY_DESTINATIONS = {
    "office.chief_architect_2": {"employee_id": 3, "mailbox_id": 3},
    "office.chief_architect_3": {"employee_id": 4, "mailbox_id": 4},
}


def _root(root=None):
    if root:
        return Path(root)
    return ESTATE_ROOT if (ESTATE_ROOT / "README.md").exists() else Path.cwd()


def _read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def mailbox_directory_name(mailbox_id):
    mailbox_id = int(mailbox_id)
    return f"{mailbox_id:04d}" if mailbox_id < 10000 else str(mailbox_id)


def registry_paths(root=None):
    base = _root(root)
    return {
        "personnel": base / "data" / "registry" / "personnel.json",
        "mailboxes": base / "data" / "registry" / "mailboxes.json",
        "residents": base / "data" / "registry" / "residents.json",
        "messages": base / "collaboration" / "messages",
        "mailboxes_root": base / "collaboration" / "mailboxes",
        "index": base / "collaboration" / "mailboxes" / "index.json",
    }


def load_personnel_registry(root=None):
    path = registry_paths(root)["personnel"]
    if not path.exists():
        return []
    entries = _read_json(path)
    if not isinstance(entries, list):
        raise ValueError("personnel registry must be a JSON list")
    return entries


def load_functional_mailbox_registry(root=None):
    path = registry_paths(root)["mailboxes"]
    if not path.exists():
        return []
    entries = _read_json(path)
    if not isinstance(entries, list):
        raise ValueError("functional mailbox registry must be a JSON list")
    for entry in entries:
        mailbox_type = entry.get("mailbox_type")
        if mailbox_type not in ALLOWED_MAILBOX_TYPES:
            raise ValueError(f"unsupported mailbox_type: {mailbox_type}")
    return entries


def personnel_by_employee_id(personnel):
    return {int(entry["employee_id"]): entry for entry in personnel if "employee_id" in entry}


def personnel_by_mailbox_id(personnel):
    return {int(entry["mailbox_id"]): entry for entry in personnel if "mailbox_id" in entry}


def functional_by_mailbox_id(mailboxes):
    return {int(entry["mailbox_id"]): entry for entry in mailboxes if "mailbox_id" in entry}


def _slug(value):
    text = str(value or "").strip().lower().replace("#", " ")
    chars = []
    previous_sep = False
    for char in text:
        if char.isalnum():
            chars.append(char)
            previous_sep = False
        elif not previous_sep:
            chars.append("_")
            previous_sep = True
    return "".join(chars).strip("_")


def _mailbox_destination_aliases(personnel, functional_mailboxes):
    aliases = {}

    def add(alias, employee_id, mailbox_id):
        if alias:
            aliases.setdefault(alias, (employee_id, mailbox_id))

    for entry in personnel:
        employee_id = entry.get("employee_id")
        mailbox_id = entry.get("mailbox_id", employee_id)
        if employee_id is None or mailbox_id is None:
            continue
        employee_id = int(employee_id)
        mailbox_id = int(mailbox_id)
        add(str(mailbox_id), employee_id, mailbox_id)
        add(mailbox_directory_name(mailbox_id), employee_id, mailbox_id)
        add(f"employee.{employee_id}", employee_id, mailbox_id)
        add(f"mailbox.{mailbox_id}", employee_id, mailbox_id)
        add(f"mailbox.{mailbox_directory_name(mailbox_id)}", employee_id, mailbox_id)
        for field in ("display_name", "current_title"):
            slug = _slug(entry.get(field))
            add(f"employee.{slug}", employee_id, mailbox_id)
            add(f"office.{slug}", employee_id, mailbox_id)
        office_slug = _slug(entry.get("current_office"))
        add(f"office.{office_slug}", employee_id, mailbox_id)

    for entry in functional_mailboxes:
        mailbox_id = entry.get("mailbox_id")
        if mailbox_id is None:
            continue
        mailbox_id = int(mailbox_id)
        responsible = entry.get("responsible_employee_id")
        employee_id = int(responsible) if responsible is not None else None
        add(str(mailbox_id), employee_id, mailbox_id)
        add(f"mailbox.{mailbox_id}", employee_id, mailbox_id)
        for field in ("display_name", "owning_office"):
            slug = _slug(entry.get(field))
            add(f"mailbox.{slug}", employee_id, mailbox_id)
            if entry.get("mailbox_type") == "office":
                add(f"office.{slug}", employee_id, mailbox_id)

    for alias, mapped in LEGACY_DESTINATIONS.items():
        aliases[alias] = (mapped["employee_id"], mapped["mailbox_id"])
    return aliases


def ensure_mailbox_directories(root=None):
    paths = registry_paths(root)
    personnel = load_personnel_registry(root)
    functional = load_functional_mailbox_registry(root)
    mailbox_ids = [entry.get("mailbox_id") for entry in personnel + functional if entry.get("mailbox_id") is not None]
    created = []
    for mailbox_id in sorted({int(item) for item in mailbox_ids}):
        for child in ("inbox", "sent", "archive"):
            directory = paths["mailboxes_root"] / mailbox_directory_name(mailbox_id) / child
            directory.mkdir(parents=True, exist_ok=True)
            created.append(str(directory.relative_to(paths["mailboxes_root"].parent.parent)))
    return created


def resolve_destination(message, personnel=None, functional_mailboxes=None):
    personnel = personnel or []
    functional_mailboxes = functional_mailboxes or []
    by_employee = personnel_by_employee_id(personnel)
    by_personnel_mailbox = personnel_by_mailbox_id(personnel)
    by_functional_mailbox = functional_by_mailbox_id(functional_mailboxes)

    warning = None
    destination_employee_id = message.get("destination_employee_id")
    destination_mailbox_id = message.get("destination_mailbox_id")

    if destination_employee_id is not None:
        try:
            employee_id = int(destination_employee_id)
            entry = by_employee.get(employee_id)
            mailbox_id = int(entry.get("mailbox_id", employee_id)) if entry else employee_id
            if not entry:
                warning = f"destination_employee_id {employee_id} is not in personnel registry"
            return employee_id, mailbox_id, warning
        except (TypeError, ValueError):
            return None, None, f"invalid destination_employee_id: {destination_employee_id}"

    if destination_mailbox_id is not None:
        try:
            mailbox_id = int(destination_mailbox_id)
            entry = by_personnel_mailbox.get(mailbox_id)
            employee_id = int(entry["employee_id"]) if entry else None
            if entry is None and mailbox_id not in by_functional_mailbox:
                warning = f"destination_mailbox_id {mailbox_id} is not in mailbox registries"
            return employee_id, mailbox_id, warning
        except (TypeError, ValueError):
            return None, None, f"invalid destination_mailbox_id: {destination_mailbox_id}"

    destination = message.get("destination")
    normalized_destination = str(destination or "").strip().lower()
    if normalized_destination.startswith("worker."):
        return None, None, None

    aliases = _mailbox_destination_aliases(personnel, functional_mailboxes)
    if normalized_destination in aliases:
        employee_id, mailbox_id = aliases[normalized_destination]
        return employee_id, mailbox_id, None

    if normalized_destination.startswith(("employee.", "mailbox.", "office.")):
        return None, None, f"unresolved destination: {destination}"

    return None, None, f"unresolved destination: {destination}"


def _message_title(message):
    payload = message.get("payload") if isinstance(message.get("payload"), dict) else {}
    return message.get("title") or payload.get("title") or payload.get("summary") or ""


def index_message(path, message, root, personnel, functional_mailboxes):
    employee_id, mailbox_id, warning = resolve_destination(message, personnel, functional_mailboxes)
    item = {
        "message_id": message.get("message_id") or message.get("id") or path.stem,
        "path": str(path.relative_to(root)).replace("\\", "/"),
        "source": message.get("source"),
        "source_employee_id": message.get("source_employee_id"),
        "destination": message.get("destination"),
        "destination_employee_id": employee_id,
        "destination_mailbox_id": mailbox_id,
        "title": _message_title(message),
        "message_type": message.get("message_type"),
        "priority": message.get("priority", "normal"),
        "status": message.get("status"),
        "requires_ack": message.get("requires_ack", False),
        "ack_status": message.get("ack_status"),
        "thread_id": message.get("thread_id"),
        "reply_to": message.get("reply_to"),
        "acknowledges": message.get("acknowledges"),
        "created_at": message.get("created_at"),
    }
    if warning:
        item["warning"] = warning
    return item


def generate_mailbox_index(root=None, write=True):
    base = _root(root)
    paths = registry_paths(base)
    personnel = load_personnel_registry(base)
    functional_mailboxes = load_functional_mailbox_registry(base)
    ensure_mailbox_directories(base)
    paths["messages"].mkdir(parents=True, exist_ok=True)

    messages = []
    warnings = []
    for path in sorted(paths["messages"].glob("*.json")):
        try:
            message = _read_json(path)
            if not isinstance(message, dict):
                raise ValueError("message JSON must be an object")
            item = index_message(path, message, base, personnel, functional_mailboxes)
        except Exception as exc:
            item = {
                "message_id": path.stem,
                "path": str(path.relative_to(base)).replace("\\", "/"),
                "destination_employee_id": None,
                "destination_mailbox_id": None,
                "warning": f"malformed message: {exc}",
            }
        if item.get("warning"):
            warnings.append({"path": item["path"], "warning": item["warning"]})
        messages.append(item)

    index = {
        "index_version": INDEX_VERSION,
        "generated_at": _now(),
        "source": "generated",
        "personnel_registry_path": str(paths["personnel"].relative_to(base)).replace("\\", "/"),
        "functional_mailbox_registry_path": str(paths["mailboxes"].relative_to(base)).replace("\\", "/"),
        "message_source_of_truth": "collaboration/messages/*.json",
        "message_count": len(messages),
        "warning_count": len(warnings),
        "warnings": warnings,
        "messages": messages,
    }
    if write:
        _write_json(paths["index"], index)
    return index


def mailbox_index_summary(index):
    open_ca2 = [m for m in index.get("messages", []) if m.get("destination_employee_id") == 3 and str(m.get("status", "")).lower() == "open"]
    open_ca3 = [m for m in index.get("messages", []) if m.get("destination_employee_id") == 4 and str(m.get("status", "")).lower() == "open"]
    open_ca4 = [m for m in index.get("messages", []) if m.get("destination_employee_id") == 5 and str(m.get("status", "")).lower() == "open"]
    ack_required = [
        m for m in index.get("messages", [])
        if m.get("requires_ack") is True and str(m.get("ack_status", "pending")).lower() not in {"acknowledged", "not_required"}
    ]
    threads = sorted({m.get("thread_id") for m in index.get("messages", []) if m.get("thread_id")})
    return {
        "index_version": index.get("index_version"),
        "message_count": index.get("message_count", len(index.get("messages", []))),
        "warning_count": index.get("warning_count", len(index.get("warnings", []))),
        "open_ca2_message_count": len(open_ca2),
        "open_ca3_message_count": len(open_ca3),
        "open_ca4_message_count": len(open_ca4),
        "ack_required_message_count": len(ack_required),
        "thread_count": len(threads),
        "index_path": "collaboration/mailboxes/index.json",
    }
