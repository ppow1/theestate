"""Local Steward Decision Queue panel.

Builds a non-authoritative queue of items that appear to need Steward attention
from existing local Estate artifacts. It does not approve, notify, or create new
authority; it only summarizes already-recorded signals in one place.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from estate.core.paths import ESTATE_ROOT

JSON_OUTPUT = "runtime/steward/decision_queue.json"
MARKDOWN_OUTPUT = "operations/steward/decision_queue.md"

OPTIONAL_JSON_ARTIFACTS = {
    "recall_audit_log": "runtime/audit/recall_audit_log.json",
    "notification_router": "runtime/notifications/notification_router_report.json",
    "alfred_operational_briefing": "runtime/alfred/operational_briefing.json",
    "morning_briefing": "runtime/briefings/morning_briefing.json",
}

WORK_PACKAGE_DIRS = [
    "collaboration/work_packages/open",
    "collaboration/work_packages/pending",
]
MESSAGE_GLOB = "collaboration/messages/*.json"
ACK_DONE = {"acknowledged", "complete", "completed", "not_required"}


def estate_root(root: str | Path | None = None) -> Path:
    if root is not None:
        return Path(root)
    return ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _read_json(path: Path, rel: str, warnings: list[dict[str, Any]]) -> Any | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        warnings.append({"type": "malformed_source_artifact", "path": rel, "message": str(exc)})
        return None


def _item(title: str, reason: str, requested_by: str, source: str, urgency: str, action: str, status: str) -> dict[str, str]:
    return {
        "title": title or "Untitled decision item",
        "reason": reason or "Steward attention is indicated by the source artifact.",
        "requested_by": requested_by or "unknown",
        "source_artifact": source,
        "urgency": urgency or "normal",
        "recommended_action": action or "Review the source artifact and decide next steps.",
        "status": status or "pending",
    }


def _load_sources(root: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    warnings: list[dict[str, Any]] = []
    sources: dict[str, Any] = {}
    for key, rel in OPTIONAL_JSON_ARTIFACTS.items():
        path = root / rel
        if not path.exists():
            warnings.append({"type": "missing_source_artifact", "path": rel, "message": "Optional decision queue source artifact is unavailable."})
            sources[key] = None
        else:
            sources[key] = _read_json(path, rel, warnings)
    return sources, warnings


def _from_recall_audit(data: Any, source: str) -> list[dict[str, str]]:
    if not isinstance(data, dict):
        return []
    items = []
    for record in data.get("records", []):
        if not isinstance(record, dict) or str(record.get("acknowledgement_state", "pending")).lower() in ACK_DONE:
            continue
        items.append(_item(
            f"Recall acknowledgement pending: {record.get('record_id') or record.get('notification_id') or 'recall'}",
            record.get("recall_reason") or "Outstanding Steward recall acknowledgement.",
            record.get("requested_by") or record.get("source") or "alfred",
            source,
            record.get("priority") or "urgent",
            "Review and acknowledge the recall record if appropriate; do not auto-approve.",
            record.get("acknowledgement_state") or "pending",
        ))
    return items


def _from_notification_router(data: Any, source: str) -> list[dict[str, str]]:
    if not isinstance(data, dict):
        return []
    items = []
    for note in data.get("notifications", []):
        if not isinstance(note, dict) or note.get("class") != "recall":
            continue
        items.append(_item(
            note.get("summary") or note.get("id") or "Recall notification",
            note.get("reason") or note.get("audit", {}).get("primary_recall_reason") or "Recall notification requires Steward attention.",
            note.get("requested_by") or "alfred",
            source,
            note.get("priority") or "urgent",
            note.get("action") or "Review recall notification and determine next action.",
            "pending" if note.get("eligible_for_immediate_delivery") else "queued",
        ))
    return items


def _from_alfred(data: Any, source: str) -> list[dict[str, str]]:
    if not isinstance(data, dict):
        return []
    items = []
    for msg in data.get("messages_requiring_acknowledgement", []):
        if isinstance(msg, dict):
            items.append(_item(msg.get("title") or msg.get("id") or "Message acknowledgement required", "Mailbox message requires acknowledgement.", msg.get("created_by") or msg.get("source") or "unknown", source, "normal", "Acknowledge or route the message.", msg.get("ack_status") or "pending"))
    for wp in data.get("active_pending_work_packages", []):
        if isinstance(wp, dict) and wp.get("blockers"):
            items.append(_item(wp.get("title") or wp.get("id") or "Blocked work package", "; ".join(map(str, wp.get("blockers") or [])), wp.get("owner") or "work package", source, "high", wp.get("next_action") or "Resolve blocker or assign a human decision.", wp.get("status") or "blocked"))
    return items


def _from_morning(data: Any, source: str) -> list[dict[str, str]]:
    if not isinstance(data, dict):
        return []
    sections = data.get("sections", {}) if isinstance(data.get("sections"), dict) else {}
    items = []
    for approval in sections.get("pending_approvals", []) or []:
        if isinstance(approval, dict):
            items.append(_item(approval.get("title") or approval.get("id") or "Pending approval", "Morning Briefing lists this item under pending approvals.", "morning_briefing", approval.get("path") or source, "normal", "Review the pending approval; do not auto-approve.", "pending"))
    for recall in sections.get("outstanding_recalls", []) or []:
        if isinstance(recall, dict):
            items.append(_item(f"Outstanding recall: {recall.get('record_id') or recall.get('recall_reason') or 'recall'}", recall.get("recall_reason") or "Morning Briefing lists an outstanding recall.", "morning_briefing", source, "urgent", "Review outstanding recall acknowledgement.", recall.get("acknowledgement_state") or "pending"))
    return items


def _extract_heading(text: str, fallback: str) -> str:
    for line in text.splitlines():
        if line.startswith("#"):
            return line.lstrip("#").strip() or fallback
    return fallback


def _extract_blockers(text: str) -> list[str]:
    blockers: list[str] = []
    in_section = False
    for line in text.splitlines():
        stripped = line.strip()
        if re.match(r"^#+\s+(Blockers?|Blocked By)\b", stripped, re.I):
            in_section = True
            continue
        if in_section and stripped.startswith("#"):
            break
        if in_section and stripped.startswith(('-', '*')):
            value = stripped[1:].strip()
            if value and value.lower() not in {"none", "n/a", "not applicable"}:
                blockers.append(value)
        field = re.match(r"^(?:[-*]\s*)?(?:\*\*)?(Blockers?|Blocked By)(?:\*\*)?\s*:\s*(.+)$", stripped, re.I)
        if field and field.group(2).strip().lower() not in {"none", "n/a", "not applicable"}:
            blockers.append(field.group(2).strip())
    return blockers[:5]


def _from_work_packages(root: Path) -> list[dict[str, str]]:
    items = []
    for rel_dir in WORK_PACKAGE_DIRS:
        base = root / rel_dir
        if not base.exists():
            continue
        for path in sorted(base.glob("*.md")):
            rel = str(path.relative_to(root)).replace("\\", "/")
            text = path.read_text(encoding="utf-8")
            blockers = _extract_blockers(text)
            if blockers or rel_dir.endswith("open"):
                items.append(_item(_extract_heading(text, path.stem), "; ".join(blockers) if blockers else "Work package is in an open/blocking queue.", "work_package", rel, "high", "Review blocker and decide the next local action.", "blocked" if blockers else "open"))
    return items


def _from_messages(root: Path) -> list[dict[str, str]]:
    items = []
    for path in sorted(root.glob(MESSAGE_GLOB)):
        rel = str(path.relative_to(root)).replace("\\", "/")
        data = _read_json(path, rel, [])
        if not isinstance(data, dict) or data.get("requires_ack") is not True:
            continue
        if str(data.get("ack_status", "pending")).lower() in ACK_DONE:
            continue
        payload = data.get("payload") if isinstance(data.get("payload"), dict) else {}
        items.append(_item(payload.get("title") or data.get("id") or "Message acknowledgement required", "Mailbox message requires acknowledgement.", data.get("created_by") or data.get("source") or "unknown", rel, "normal", "Acknowledge the mailbox message or route it for follow-up.", data.get("ack_status") or "pending"))
    return items


def generate_decision_queue(root: str | Path | None = None, write: bool = True) -> dict[str, Any]:
    root = estate_root(root)
    sources, warnings = _load_sources(root)
    decisions = []
    decisions += _from_recall_audit(sources["recall_audit_log"], OPTIONAL_JSON_ARTIFACTS["recall_audit_log"])
    decisions += _from_notification_router(sources["notification_router"], OPTIONAL_JSON_ARTIFACTS["notification_router"])
    decisions += _from_alfred(sources["alfred_operational_briefing"], OPTIONAL_JSON_ARTIFACTS["alfred_operational_briefing"])
    decisions += _from_morning(sources["morning_briefing"], OPTIONAL_JSON_ARTIFACTS["morning_briefing"])
    decisions += _from_work_packages(root)
    decisions += _from_messages(root)

    queue = {
        "version": 1,
        "generated_at": _now(),
        "non_authoritative": True,
        "local_only": True,
        "notifies_steward": False,
        "summary": {"decision_count": len(decisions), "empty": len(decisions) == 0, "warning_count": len(warnings)},
        "decisions": decisions,
        "empty_state": "No pending Steward decisions were found in available local artifacts." if not decisions else None,
        "source_warnings": warnings,
        "constraints": {"does_not_approve_decisions": True, "does_not_notify_steward": True, "generated_output_authoritative": False},
    }
    if write:
        (root / JSON_OUTPUT).parent.mkdir(parents=True, exist_ok=True)
        (root / JSON_OUTPUT).write_text(json.dumps(queue, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        (root / MARKDOWN_OUTPUT).parent.mkdir(parents=True, exist_ok=True)
        (root / MARKDOWN_OUTPUT).write_text(format_decision_queue_markdown(queue) + "\n", encoding="utf-8")
    return queue


def format_decision_queue_markdown(queue: dict[str, Any]) -> str:
    lines = ["# Steward Decision Queue", "", f"Generated: {queue.get('generated_at')}", "", "Local-only, non-authoritative panel. It does not approve decisions or notify the Steward.", ""]
    decisions = queue.get("decisions") or []
    if not decisions:
        lines += ["## Pending Decisions", f"- {queue.get('empty_state') or 'No decisions pending.'}", ""]
    else:
        lines += ["## Pending Decisions"]
        for d in decisions:
            lines.append(f"- **{d.get('title')}** ({d.get('urgency')}, {d.get('status')}) — {d.get('reason')} Requested by: {d.get('requested_by')}. Action: {d.get('recommended_action')}. Source: `{d.get('source_artifact')}`")
        lines.append("")
    if queue.get("source_warnings"):
        lines += ["## Source Warnings"] + [f"- {w.get('type')}: {w.get('path')}" for w in queue.get("source_warnings", [])]
    return "\n".join(lines)
