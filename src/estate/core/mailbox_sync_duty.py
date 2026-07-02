"""Mailbox synchronization duty reporting.

This module provides lightweight operational mailbox duty checks. It reports
current mailbox obligations without defining polling cadence, HR authority, or
security clearance policy.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from estate.core.check_updates import actor_category, normalize_actor
from estate.core.mailbox_index import generate_mailbox_index
from estate.core.paths import ESTATE_ROOT
from estate.core.personnel_identity import resolve_personnel_identity


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


def _read_json(path: Path, warnings: list[dict[str, Any]]) -> Any | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        warnings.append({"type": "malformed_json", "path": str(path), "message": str(exc)})
        return None


def _actor_destinations(actor: str, family: str, identity: dict[str, Any]) -> set[str]:
    destinations = {actor, family}
    canonical = identity.get("canonical_destination")
    if canonical:
        destinations.add(str(canonical).lower())
    if identity.get("employee_id") is not None:
        destinations.update({f"employee.{identity['employee_id']}", str(identity["employee_id"])})
    if identity.get("mailbox_id") is not None:
        destinations.update({f"mailbox.{identity['mailbox_id']}", str(identity["mailbox_id"])})
        try:
            mailbox_id = int(identity["mailbox_id"])
            destinations.update({f"mailbox.{mailbox_id:04d}", f"{mailbox_id:04d}"})
        except (TypeError, ValueError):
            pass
    if identity.get("worker"):
        destinations.add(str(identity["worker"]).lower())
    if family.startswith("worker."):
        destinations.add(family.split(".", 1)[1])
    if family == "office.chief_architect":
        destinations.update({"chief_architect", "ca"})
    return {item.strip().lower() for item in destinations if item}


def _matches_actor(item: dict[str, Any], destinations: set[str], identity: dict[str, Any]) -> bool:
    destination = str(item.get("destination") or "").strip().lower()
    if destination in destinations:
        return True
    if identity.get("employee_id") is not None and item.get("destination_employee_id") == identity.get("employee_id"):
        return True
    if identity.get("mailbox_id") is not None and item.get("destination_mailbox_id") == identity.get("mailbox_id"):
        return True
    return False


def _is_open_or_unread(message: dict[str, Any]) -> bool:
    status = str(message.get("status") or "").strip().lower()
    read_status = str(message.get("read_status") or message.get("read") or "").strip().lower()
    return status in {"open", "new", "pending", "unread"} or read_status in {"unread", "false", "no"}


def _needs_ack(message: dict[str, Any]) -> bool:
    return message.get("requires_ack") is True and str(message.get("ack_status") or "pending").strip().lower() not in {"acknowledged", "not_required"}


def _message_summary(message: dict[str, Any]) -> dict[str, Any]:
    return {
        "message_id": message.get("message_id") or message.get("id"),
        "path": message.get("path"),
        "title": message.get("title") or message.get("message_id") or message.get("id") or "(untitled)",
        "destination": message.get("destination"),
        "destination_employee_id": message.get("destination_employee_id"),
        "destination_mailbox_id": message.get("destination_mailbox_id"),
        "status": message.get("status"),
        "requires_ack": message.get("requires_ack", False),
        "ack_status": message.get("ack_status"),
        "thread_id": message.get("thread_id"),
        "reply_to": message.get("reply_to"),
        "created_at": message.get("created_at"),
    }


def _load_latest_check_updates(root: Path, actor: str) -> dict[str, Any] | None:
    path = root / "runtime" / "updates" / "check_updates_latest.json"
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    if isinstance(data, dict) and data.get("actor") == actor:
        return data
    return None


def generate_mailbox_sync_duty(actor: str | None = None, root: str | Path | None = None, write: bool = True) -> dict[str, Any]:
    root_path = estate_root(root)
    normalized = normalize_actor(actor)
    family = actor_category(normalized)
    identity = resolve_personnel_identity(actor or normalized, root_path)
    warnings: list[dict[str, Any]] = []
    for resolver_warning in identity.get("warnings", []):
        warnings.append({"type": "identity_resolution", "actor": actor or normalized, "message": resolver_warning})
    if actor and not identity.get("resolved"):
        warnings.append({"type": "unresolved_identity", "actor": actor, "message": "Actor identity could not be resolved to a mailbox or worker."})

    try:
        index = generate_mailbox_index(root_path, write=False)
    except Exception as exc:
        index = {"messages": [], "warnings": []}
        warnings.append({"type": "mailbox_index_unavailable", "message": str(exc)})
    for warning in index.get("warnings", []):
        warnings.append({"type": "mailbox_index_warning", "path": warning.get("path"), "message": warning.get("warning", "")})

    destinations = _actor_destinations(normalized, family, identity)
    assigned = [_message_summary(item) for item in index.get("messages", []) if _matches_actor(item, destinations, identity)]
    open_or_unread = [item for item in assigned if _is_open_or_unread(item)]
    ack_required = [item for item in assigned if _needs_ack(item)]
    replies_waiting = [item for item in assigned if item.get("reply_to") or item.get("thread_id")]
    latest_updates = _load_latest_check_updates(root_path, normalized)

    report = {
        "version": 1,
        "generated_at": _now(),
        "actor": normalized,
        "actor_category": family,
        "identity": identity,
        "mailbox": {"canonical_actor": identity.get("canonical_destination") or normalized, "employee_id": identity.get("employee_id"), "mailbox_id": identity.get("mailbox_id")},
        "summary": {
            "has_obligations": bool(open_or_unread or ack_required or replies_waiting or any(w.get("type") == "unresolved_identity" for w in warnings)),
            "assigned_message_count": len(assigned),
            "open_or_unread_message_count": len(open_or_unread),
            "ack_required_message_count": len(ack_required),
            "reply_attention_message_count": len(replies_waiting),
            "warning_count": len(warnings),
        },
        "obligations": {"assigned_messages": assigned, "open_or_unread_messages": open_or_unread, "messages_requiring_ack": ack_required, "replies_waiting_for_attention": replies_waiting},
        "inputs": {"mailbox_index": "collaboration/mailboxes/index.json", "messages": "collaboration/messages/*.json", "check_updates_latest_used": latest_updates is not None},
        "warnings": warnings,
    }
    if latest_updates:
        report["check_updates_summary"] = latest_updates.get("summary", {})
    if write:
        write_reports(report, root_path)
    return report


def write_reports(report: dict[str, Any], root: Path) -> None:
    json_path = root / "runtime" / "mailboxes" / "synchronization_duty.json"
    md_path = root / "operations" / "mailboxes" / "synchronization_duty.md"
    json_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(format_mailbox_sync_duty(report) + "\n", encoding="utf-8")


def _section(title: str, items: list[dict[str, Any]]) -> list[str]:
    lines = [f"## {title}", ""]
    if not items:
        return lines + ["None.", ""]
    for item in items:
        detail = f" — {item.get('path')}" if item.get("path") else ""
        lines.append(f"- {item.get('title') or item.get('message_id')}{detail}")
    return lines + [""]


def format_mailbox_sync_duty(report: dict[str, Any]) -> str:
    summary = report.get("summary", {})
    mailbox = report.get("mailbox", {})
    lines = [
        "# Mailbox Synchronization Duty", "",
        f"Actor: {report.get('actor')}",
        f"Actor Category: {report.get('actor_category')}",
        f"Generated: {report.get('generated_at')}", "",
        "## Identity", "",
        f"- Canonical actor: {mailbox.get('canonical_actor') or report.get('actor')}",
        f"- Employee ID: {mailbox.get('employee_id') or 'unresolved'}",
        f"- Mailbox ID: {mailbox.get('mailbox_id') or 'unresolved'}", "",
        "## Summary", "",
        f"- Has obligations: {summary.get('has_obligations')}",
        f"- Assigned messages: {summary.get('assigned_message_count', 0)}",
        f"- Open or unread messages: {summary.get('open_or_unread_message_count', 0)}",
        f"- Messages requiring acknowledgement: {summary.get('ack_required_message_count', 0)}",
        f"- Replies waiting for attention: {summary.get('reply_attention_message_count', 0)}",
        f"- Warnings: {summary.get('warning_count', 0)}", "",
    ]
    obligations = report.get("obligations", {})
    lines.extend(_section("Open or Unread Messages", obligations.get("open_or_unread_messages", [])))
    lines.extend(_section("Messages Requiring Acknowledgement", obligations.get("messages_requiring_ack", [])))
    lines.extend(_section("Replies Waiting for Attention", obligations.get("replies_waiting_for_attention", [])))
    lines.append("## Warnings")
    lines.append("")
    if report.get("warnings"):
        lines.extend(f"- {w.get('type')}: {w.get('actor') or w.get('path') or ''} {w.get('message', '')}".strip() for w in report["warnings"])
    else:
        lines.append("No warnings.")
    return "\n".join(lines)
