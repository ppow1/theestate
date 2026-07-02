"""Local-first Check for Updates briefing generation.

This module is a pointer mechanism for role-aware synchronization. It does not
create governance, security clearance policy, lifecycle states, offices, or a
new mailbox identity system.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from estate.core.mailbox_index import generate_mailbox_index
from estate.core.paths import ESTATE_ROOT
from estate.core.personnel_identity import resolve_personnel_identity

UPDATE_KEYS = [
    "governance_updates",
    "architecture_updates",
    "collaboration_updates",
    "operations_updates",
    "capability_updates",
    "audit_updates",
    "assigned_messages",
    "institutional_memory_updates",
]

VISIBILITY_ORDER = {"public": 0, "estate_internal": 1, "restricted": 2}

ACTOR_VISIBILITY = {
    "general": "public",
    "worker.implementation": "estate_internal",
    "worker.documentation": "estate_internal",
    "worker.audit": "estate_internal",
    "worker.discovery": "estate_internal",
    "alfred": "estate_internal",
    "office.chief_architect": "estate_internal",
    "office.chief_architect_1": "estate_internal",
    "office.chief_architect_2": "estate_internal",
    "office.chief_architect_3": "estate_internal",
    "office.chief_architect_4": "estate_internal",
    "helen": "estate_internal",
    "steward": "restricted",
}

ALIASES = {
    "": "general",
    "general": "general",
    "chief_architect": "office.chief_architect",
    "ca": "office.chief_architect",
    "chief_architect_1": "office.chief_architect_1",
    "ca1": "office.chief_architect_1",
    "chief_architect_2": "office.chief_architect_2",
    "ca2": "office.chief_architect_2",
    "chief_architect_3": "office.chief_architect_3",
    "ca3": "office.chief_architect_3",
    "chief_architect_4": "office.chief_architect_4",
    "ca4": "office.chief_architect_4",
    "office.chief_architect_4": "office.chief_architect_4",
    "helen": "helen",
    "alfred": "alfred",
    "audit": "worker.audit",
    "worker.audit": "worker.audit",
    "implementation": "worker.implementation",
    "codex": "worker.implementation",
    "worker.implementation": "worker.implementation",
    "documentation": "worker.documentation",
    "worker.documentation": "worker.documentation",
    "discovery": "worker.discovery",
    "worker.discovery": "worker.discovery",
    "steward": "steward",
}

CATEGORY_INTERESTS = {
    "general": {"operations_updates"},
    "office.chief_architect": set(UPDATE_KEYS) - {"audit_updates"},
    "alfred": {"operations_updates", "collaboration_updates", "assigned_messages"},
    "helen": {"operations_updates", "collaboration_updates", "assigned_messages"},
    "worker.audit": {"audit_updates", "operations_updates", "assigned_messages"},
    "worker.implementation": {"collaboration_updates", "operations_updates", "capability_updates", "assigned_messages"},
    "worker.documentation": {"governance_updates", "collaboration_updates", "operations_updates", "assigned_messages"},
    "worker.discovery": {"collaboration_updates", "operations_updates", "assigned_messages"},
    "steward": set(UPDATE_KEYS),
}

SOURCE_GROUPS = {
    "architecture_updates": ["Architecture/ADR/**/*.md"],
    "governance_updates": ["docs/governance/**/*.md"],
    "collaboration_updates": ["docs/collaboration/**/*.md", "collaboration/status/*.json", "runtime/collaboration/events/events.jsonl"],
    "operations_updates": ["docs/operations/**/*.md", "operations/**/*.md", "runtime/operations/operations_board.json", "runtime/validation/operational_validation_report.json"],
    "capability_updates": ["runtime/capabilities/capability_lifecycle_report.json", "runtime/dependencies/dependency_graph.json"],
    "audit_updates": ["runtime/validation/operational_validation_report.json", "collaboration/messages/*.json"],
    "institutional_memory_updates": ["archive/institutional_memory/**/*.md"],
}

EXPECTED_INPUTS = [
    "Architecture/ADR/**/*.md", "docs/governance/**/*.md", "docs/collaboration/**/*.md",
    "docs/operations/**/*.md", "operations/**/*.md", "collaboration/messages/*.json",
    "collaboration/status/*.json", "runtime/collaboration/events/events.jsonl",
    "runtime/operations/operations_board.json", "runtime/capabilities/capability_lifecycle_report.json",
    "runtime/dependencies/dependency_graph.json", "runtime/validation/operational_validation_report.json",
    "archive/institutional_memory/**/*.md",
]


def estate_root(root: str | Path | None = None) -> Path:
    if root is not None:
        return Path(root)
    return ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def normalize_actor(actor: str | None) -> str:
    key = (actor or "general").strip().lower().replace(" ", "_")
    return ALIASES.get(key, key if key in ACTOR_VISIBILITY else "general")


def actor_category(actor: str) -> str:
    if actor.startswith("office.chief_architect"):
        return "office.chief_architect"
    return actor


def _classification_visibility(text: str) -> str:
    low = text.lower()
    if "restricted" in low or "local only" in low:
        return "restricted"
    if "estate internal" in low or "classification:" in low:
        return "estate_internal"
    return "public"


def _allowed(item_visibility: str, actor_visibility: str) -> bool:
    return VISIBILITY_ORDER[item_visibility] <= VISIBILITY_ORDER[actor_visibility]


def _summarize_markdown(path: Path, root: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace")[:4096]
    title = next((line.lstrip("# ").strip() for line in text.splitlines() if line.strip().startswith("#")), path.name)
    return {"path": _rel(path, root), "title": title, "visibility": _classification_visibility(text), "kind": "markdown"}


def _summarize_json(path: Path, root: Path, warnings: list[dict[str, Any]]) -> dict[str, Any] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        warnings.append({"type": "malformed_json", "path": _rel(path, root), "message": str(exc)})
        return None
    title = data.get("title") or data.get("id") or data.get("name") or data.get("type") or path.name if isinstance(data, dict) else path.name
    return {"path": _rel(path, root), "title": str(title), "visibility": "estate_internal", "kind": "json"}


def _summarize_jsonl(path: Path, root: Path, warnings: list[dict[str, Any]]) -> dict[str, Any] | None:
    count = malformed = 0
    for i, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        if not line.strip():
            continue
        try:
            json.loads(line)
            count += 1
        except Exception as exc:
            malformed += 1
            warnings.append({"type": "malformed_jsonl", "path": _rel(path, root), "line": i, "message": str(exc)})
    return {"path": _rel(path, root), "title": f"Collaboration event log ({count} valid records)", "visibility": "estate_internal", "kind": "jsonl", "malformed_count": malformed}


def _is_generated_update_output(path: Path, root: Path) -> bool:
    return _rel(path, root) in {
        "runtime/updates/check_updates_latest.json",
        "operations/updates/check_updates_latest.md",
    }


def _iter_matches(root: Path, pattern: str) -> list[Path]:
    return sorted(p for p in root.glob(pattern) if p.is_file() and not _is_generated_update_output(p, root))


def _message_destination(message: dict[str, Any]) -> str:
    for key in ("destination", "to", "recipient", "target"):
        if message.get(key):
            return str(message[key])
    return ""


def _destination_matches(dest: str, actor: str, family: str) -> bool:
    d = dest.strip().lower()
    if d == actor or d == family:
        return True
    if family.startswith("worker.") and d == family.split(".", 1)[1]:
        return True
    if family == "office.chief_architect" and d in {"chief_architect", "ca"}:
        return True
    return False


def _message_title(data: dict[str, Any], fallback: str) -> str:
    payload = data.get("payload") if isinstance(data.get("payload"), dict) else {}
    return str(data.get("subject") or data.get("title") or payload.get("title") or payload.get("summary") or data.get("id") or fallback)


def _actor_destinations(actor: str, family: str, identity: dict[str, Any]) -> set[str]:
    destinations = {actor, family}
    canonical = identity.get("canonical_destination")
    if canonical:
        destinations.add(str(canonical).lower())
    if identity.get("employee_id") is not None:
        destinations.add(f"employee.{identity['employee_id']}")
        destinations.add(str(identity["employee_id"]))
    if identity.get("mailbox_id") is not None:
        destinations.add(f"mailbox.{identity['mailbox_id']}")
        destinations.add(str(identity["mailbox_id"]))
        try:
            destinations.add(f"mailbox.{int(identity['mailbox_id']):04d}")
            destinations.add(f"{int(identity['mailbox_id']):04d}")
        except (TypeError, ValueError):
            pass
    if identity.get("worker"):
        destinations.add(str(identity["worker"]).lower())
    if family.startswith("worker."):
        destinations.add(family.split(".", 1)[1])
    if family == "office.chief_architect":
        destinations.update({"chief_architect", "ca"})
    return {item.strip().lower() for item in destinations if item}


def _message_matches_actor(item: dict[str, Any], destinations: set[str], identity: dict[str, Any]) -> bool:
    destination = str(item.get("destination") or "").strip().lower()
    if destination in destinations:
        return True
    if identity.get("employee_id") is not None and item.get("destination_employee_id") == identity.get("employee_id"):
        return True
    if identity.get("mailbox_id") is not None and item.get("destination_mailbox_id") == identity.get("mailbox_id"):
        return True
    return False


def _collect_messages(root: Path, actor: str, family: str, identity: dict[str, Any], warnings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    destinations = _actor_destinations(actor, family, identity)
    messages_by_path: dict[str, dict[str, Any]] = {}
    try:
        index = generate_mailbox_index(root, write=False)
    except Exception as exc:
        warnings.append({"type": "mailbox_index_unavailable", "message": str(exc)})
        index = {"messages": []}
    for index_warning in index.get("warnings", []):
        warnings.append({"type": "mailbox_index_warning", "path": index_warning.get("path"), "message": index_warning.get("warning", "")})
    for item in index.get("messages", []):
        if not _message_matches_actor(item, destinations, identity):
            continue
        message = dict(item)
        message["title"] = str(message.get("title") or message.get("message_id") or Path(str(message.get("path", "message"))).stem)
        message["visibility"] = "estate_internal"
        messages_by_path[str(message.get("path") or message.get("message_id"))] = message

    for path in _iter_matches(root, "collaboration/messages/*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            warnings.append({"type": "malformed_json", "path": _rel(path, root), "message": str(exc)})
            continue
        if not isinstance(data, dict):
            continue
        rel = _rel(path, root)
        if rel in messages_by_path:
            messages_by_path[rel]["title"] = _message_title(data, path.stem)
            continue
        dest = _message_destination(data)
        if _destination_matches(dest, actor, family):
            messages_by_path[rel] = {
                "message_id": data.get("message_id") or data.get("id") or path.stem,
                "path": rel,
                "title": _message_title(data, path.stem),
                "destination": dest,
                "requires_ack": data.get("requires_ack", False),
                "ack_status": data.get("ack_status"),
                "thread_id": data.get("thread_id"),
                "reply_to": data.get("reply_to"),
                "acknowledges": data.get("acknowledges"),
                "visibility": "estate_internal",
            }
    return sorted(messages_by_path.values(), key=lambda item: (str(item.get("created_at") or ""), str(item.get("message_id") or "")))


def generate_check_updates(actor: str | None = None, root: str | Path | None = None) -> dict[str, Any]:
    root_path = estate_root(root)
    normalized = normalize_actor(actor)
    family = actor_category(normalized)
    identity = resolve_personnel_identity(actor or normalized, root_path)
    visibility = ACTOR_VISIBILITY.get(normalized, "public")
    interests = CATEGORY_INTERESTS.get(family, CATEGORY_INTERESTS["general"])
    warnings: list[dict[str, Any]] = []
    used, missing = [], []
    updates = {key: [] for key in UPDATE_KEYS}

    if actor and normalize_actor(actor) == "general" and actor.strip().lower() not in ALIASES:
        warnings.append({"type": "unknown_actor", "actor": actor, "message": "Actor was not recognized; generated general briefing."})

    for resolver_warning in identity.get("warnings", []):
        warnings.append({"type": "identity_resolution", "actor": actor or normalized, "message": resolver_warning})
    if actor and not identity.get("resolved") and normalized != "general":
        warnings.append({"type": "unresolved_identity", "actor": actor, "message": "Actor identity could not be resolved to a mailbox or worker."})

    for pattern in EXPECTED_INPUTS:
        matches = _iter_matches(root_path, pattern)
        if matches:
            used.extend(_rel(p, root_path) for p in matches)
        else:
            missing.append(pattern)
            warnings.append({"type": "missing_input", "path": pattern, "message": "Optional update source not present."})

    for category, patterns in SOURCE_GROUPS.items():
        if category not in interests:
            continue
        for pattern in patterns:
            for path in _iter_matches(root_path, pattern):
                if path.suffix.lower() == ".md":
                    item = _summarize_markdown(path, root_path)
                elif path.suffix.lower() == ".jsonl":
                    item = _summarize_jsonl(path, root_path, warnings)
                elif path.suffix.lower() == ".json":
                    item = _summarize_json(path, root_path, warnings)
                else:
                    item = None
                if item and _allowed(item["visibility"], visibility):
                    updates[category].append(item)

    updates["assigned_messages"] = [m for m in _collect_messages(root_path, normalized, family, identity, warnings) if _allowed(m["visibility"], visibility)]
    ack_required = [m for m in updates["assigned_messages"] if m.get("requires_ack") is True and str(m.get("ack_status", "pending")).lower() not in {"acknowledged", "not_required"}]
    update_count = sum(len(v) for k, v in updates.items() if k != "assigned_messages")
    report = {
        "version": 1,
        "generated_at": _now(),
        "actor": normalized,
        "actor_category": family,
        "visibility_level": visibility,
        "identity": identity,
        "mailbox": {"canonical_actor": identity.get("canonical_destination") or normalized, "employee_id": identity.get("employee_id"), "mailbox_id": identity.get("mailbox_id")},
        "summary": {"update_count": update_count, "assigned_message_count": len(updates["assigned_messages"]), "ack_required_message_count": len(ack_required), "warning_count": len(warnings)},
        "updates": updates,
        "mailbox_obligations": {"messages_requiring_ack": ack_required},
        "inputs": {"used": sorted(set(used)), "missing": missing},
        "warnings": warnings,
    }
    write_reports(report, root_path)
    return report


def write_reports(report: dict[str, Any], root: Path) -> None:
    json_path = root / "runtime" / "updates" / "check_updates_latest.json"
    md_path = root / "operations" / "updates" / "check_updates_latest.md"
    json_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(format_check_updates(report) + "\n", encoding="utf-8")


def _section(title: str, items: list[dict[str, Any]]) -> list[str]:
    lines = [f"## {title}", ""]
    if not items:
        return lines + ["No relevant updates found.", ""]
    for item in items:
        detail = f" — {item.get('path')}" if item.get("path") else ""
        lines.append(f"- {item.get('title', '(untitled)')}{detail}")
    return lines + [""]


def format_check_updates(report: dict[str, Any]) -> str:
    lines = [
        "# Check for Updates", "",
        f"Actor: {report['actor']}", f"Actor Category: {report['actor_category']}",
        f"Visibility: {report['visibility_level']}", f"Generated: {report['generated_at']}", "",
        "## Actor Identity", "",
        f"- Canonical actor: {report.get('mailbox', {}).get('canonical_actor') or report['actor']}",
        f"- Employee ID: {report.get('mailbox', {}).get('employee_id') or 'unresolved'}",
        f"- Mailbox ID: {report.get('mailbox', {}).get('mailbox_id') or 'unresolved'}", "",
        "## Summary", "",
        f"- Updates: {report['summary']['update_count']}",
        f"- Assigned messages: {report['summary']['assigned_message_count']}",
        f"- Messages requiring acknowledgement: {report['summary'].get('ack_required_message_count', 0)}",
        f"- Warnings: {report['summary']['warning_count']}", "",
    ]
    names = [("Assigned Messages", "assigned_messages"), ("Governance Updates", "governance_updates"), ("Architecture Updates", "architecture_updates"), ("Collaboration Updates", "collaboration_updates"), ("Operations Updates", "operations_updates"), ("Capability Updates", "capability_updates"), ("Audit Updates", "audit_updates"), ("Institutional Memory Updates", "institutional_memory_updates")]
    for title, key in names:
        lines.extend(_section(title, report["updates"].get(key, [])))
    lines.extend(_section("Messages Requiring Acknowledgement", report.get("mailbox_obligations", {}).get("messages_requiring_ack", [])))
    lines.append("## Warnings")
    lines.append("")
    if report["warnings"]:
        for warning in report["warnings"]:
            lines.append(f"- {warning.get('type')}: {warning.get('path') or warning.get('actor') or ''} {warning.get('message', '')}".strip())
    else:
        lines.append("No warnings.")
    return "\n".join(lines)
