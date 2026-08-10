"""Operations Center Notification Center aggregation.

Read-only Steward-facing aggregation of existing notification-like artifacts. This
module is not a notification transport and does not mutate authoritative sources.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

from estate.core.paths import ESTATE_ROOT
from estate.core.operator_activity_stream import generate_operator_activity_stream

JSON_OUTPUT = "runtime/notifications/operations_notification_center.json"
MARKDOWN_OUTPUT = "operations/notifications/operations_notification_center.md"
ACK_OUTPUT = "runtime/notifications/operations_notification_center_acknowledgements.json"
SEVERITY_ORDER = {"critical": 0, "error": 1, "warning": 2, "missing": 2, "info": 3, "debug": 4}
SOURCES = {
    "service_health": ["runtime/services/service_status_board.json", "runtime/services/service_health_registry.json"],
    "validation": ["runtime/validation/local_operational_validation_run.json", "runtime/validation/validation_metrics_dashboard.json", "validation/observations/validation_observations.jsonl"],
    "workers": ["runtime/workers/worker_runtime_monitor.json", "runtime/workers/worker_runtime_heartbeat.json"],
    "mission_control": ["runtime/steward/mission_control_workspace.json"],
    "mailboxes": ["runtime/collaboration/mailbox_index.json", "collaboration/mailboxes/index.json"],
    "hr": ["runtime/hr/onboarding_latest.json", "operations/hr/onboarding_latest.md"],
    "recalls": ["runtime/audit/recall_audit_log.json", "runtime/notifications/notification_router_report.json"],
    "readiness": ["runtime/operations/operational_readiness_dashboard.json", "runtime/validation/production_readiness.json"],
    "completions": ["collaboration/work_packages/completions"],
}


def _root(root=None):
    return Path(root) if root is not None else (ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd())


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _rel(path, root):
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def _read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _mtime(path):
    return datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(timespec="seconds")


def load_notification_acknowledgements(root=None):
    path = _root(root) / ACK_OUTPUT
    if not path.exists():
        return {}
    try:
        data = _read_json(path)
        return data.get("acknowledgements", {}) if isinstance(data, dict) else {}
    except Exception:
        return {}


def _notification(root, source, severity, title, message, artifact, *, identifier=None, timestamp=None, authoritative_state=None, metadata=None):
    nid = identifier or f"{source}:{artifact}:{title}"
    link_available = bool(artifact and (root / artifact).exists())
    return {
        "id": nid,
        "timestamp": timestamp or _now(),
        "source": source,
        "severity": severity if severity in SEVERITY_ORDER else "info",
        "title": str(title or "Operational notification"),
        "message": str(message or title or "No detail provided."),
        "state": authoritative_state or "unacknowledged",
        "acknowledgement_scope": "local_notification_center_only",
        "source_link": {"path": artifact, "available": link_available},
        "metadata": metadata or {},
    }


def _warning_notifications(root, source, rel, data):
    notes = []
    warnings = data.get("warnings") if isinstance(data, dict) else None
    for idx, warning in enumerate(warnings or []):
        msg = warning.get("message") if isinstance(warning, dict) else str(warning)
        notes.append(_notification(root, source, "warning", "Warning", msg, rel, identifier=f"{source}:{rel}:warning:{idx}", timestamp=data.get("generated_at") or _mtime(root / rel)))
    return notes


def _collect_from_json(root, source, rel, data):
    notes = []
    notes.extend(_warning_notifications(root, source, rel, data))
    if source == "validation":
        summary = data.get("summary", {}) if isinstance(data, dict) else {}
        failed = summary.get("failed_steps") or summary.get("failed") or 0
        if failed:
            notes.append(_notification(root, source, "error", "Validation failures", f"Validation reports {failed} failed step(s).", rel, timestamp=data.get("generated_at") or _mtime(root / rel), metadata={"summary": summary}))
    if source in {"service_health", "readiness", "workers"}:
        summary = data.get("summary", {}) if isinstance(data, dict) else {}
        wc = summary.get("warning_count") or len(data.get("warnings") or []) if isinstance(data, dict) else 0
        ec = summary.get("error_count") or summary.get("failed") or summary.get("failed_steps") or 0
        if wc or ec:
            severity = "error" if ec else "warning"
            notes.append(_notification(root, source, severity, f"{source.replace('_', ' ').title()} attention", f"warnings={wc}; errors/failures={ec}", rel, timestamp=data.get("generated_at") or _mtime(root / rel), metadata={"summary": summary}))
    if source == "mission_control" and isinstance(data, dict):
        for idx, rec in enumerate(data.get("recommendations") or data.get("warnings") or []):
            msg = rec.get("message") or rec.get("recommendation") if isinstance(rec, dict) else str(rec)
            notes.append(_notification(root, source, "info", "Mission Control recommendation", msg, rel, identifier=f"{source}:{rel}:recommendation:{idx}", timestamp=data.get("generated_at") or _mtime(root / rel)))
    if source == "mailboxes" and isinstance(data, dict):
        for idx, message in enumerate(data.get("messages") or []):
            if not isinstance(message, dict):
                continue
            if message.get("requires_ack") or str(message.get("priority", "")).lower() in {"high", "urgent"}:
                notes.append(_notification(root, source, "warning" if message.get("requires_ack") else "info", message.get("title") or "Mailbox notice", message.get("summary") or message.get("body") or message.get("title"), message.get("path") or rel, identifier=f"mailbox:{message.get('message_id') or idx}", timestamp=message.get("created_at") or data.get("generated_at") or _mtime(root / rel), authoritative_state=message.get("ack_status") or "unacknowledged"))
    if source == "recalls" and isinstance(data, dict):
        records = data.get("records") or data.get("notifications") or []
        for idx, record in enumerate(records):
            if not isinstance(record, dict):
                continue
            is_recall = record.get("class") == "recall" or "recall" in str(record.get("reason") or record.get("recall_reason") or "").lower()
            if is_recall:
                notes.append(_notification(root, source, "warning", "Steward recall state", record.get("reason") or record.get("recall_reason") or record.get("summary"), rel, identifier=f"recall:{record.get('id') or record.get('record_id') or idx}", timestamp=record.get("timestamp") or record.get("created_at") or data.get("generated_at") or _mtime(root / rel), authoritative_state=record.get("acknowledgement_state") or "unacknowledged"))
    return notes


def _collect_notifications(root):
    notifications = []
    inputs = []
    for source, rels in SOURCES.items():
        for rel in rels:
            path = root / rel
            inputs.append({"source": source, "path": rel, "available": path.exists()})
            if path.is_dir():
                for child in sorted(path.glob("*_codex_done.json"), key=lambda p: p.stat().st_mtime, reverse=True)[:10]:
                    try:
                        data = _read_json(child)
                        notifications.append(_notification(root, "completions", "info", "Completion/review-ready signal", data.get("work_package_id") or child.stem, _rel(child, root), identifier=f"completion:{child.stem}", timestamp=data.get("completed_at") or _mtime(child), authoritative_state="review_ready" if data.get("ready_for_ca_review") else "completed"))
                    except Exception as exc:
                        notifications.append(_notification(root, "completions", "warning", "Unreadable completion receipt", str(exc), _rel(child, root), timestamp=_mtime(child)))
                continue
            if not path.exists():
                continue
            if path.suffix == ".jsonl":
                for idx, line in enumerate(path.read_text(encoding="utf-8").splitlines()[:50]):
                    try:
                        item = json.loads(line)
                    except Exception:
                        continue
                    if item.get("status") != "closed":
                        notifications.append(_notification(root, source, item.get("severity") if item.get("severity") in SEVERITY_ORDER else "warning", item.get("observation_id") or "Validation observation", item.get("observed_behavior"), rel, identifier=f"validation-observation:{item.get('observation_id') or idx}", timestamp=item.get("timestamp") or _mtime(path), authoritative_state=item.get("status") or "open"))
                continue
            if path.suffix == ".json":
                try:
                    notifications.extend(_collect_from_json(root, source, rel, _read_json(path)))
                except Exception as exc:
                    notifications.append(_notification(root, source, "error", "Source read error", str(exc), rel, timestamp=_mtime(path)))
            else:
                notifications.append(_notification(root, source, "info", "Source artifact available", "Text source is available for review.", rel, timestamp=_mtime(path)))
    return notifications, inputs


def generate_operations_notification_center(root=None, write=True, sources=None, severities=None, acknowledged=None, limit=100):
    root = _root(root)
    acknowledgements = load_notification_acknowledgements(root)
    notifications, inputs = _collect_notifications(root)
    for note in notifications:
        ack = acknowledgements.get(note["id"])
        note["locally_acknowledged"] = bool(ack)
        if ack:
            note["local_acknowledgement"] = ack
    source_filter = set(sources or [])
    severity_filter = set(severities or [])
    filtered = []
    for note in notifications:
        if source_filter and note["source"] not in source_filter:
            continue
        if severity_filter and note["severity"] not in severity_filter:
            continue
        if acknowledged is not None and note.get("locally_acknowledged") is not acknowledged:
            continue
        filtered.append(note)
    filtered = sorted(filtered, key=lambda n: (SEVERITY_ORDER.get(n["severity"], 9), str(n.get("timestamp") or "")))[:limit]
    activity = generate_operator_activity_stream(root=root, write=False, sources=["notifications"], limit=10)
    counts = {sev: sum(1 for n in filtered if n["severity"] == sev) for sev in SEVERITY_ORDER}
    total_count = len(notifications)
    locally_acknowledged_count = sum(1 for n in notifications if n.get("locally_acknowledged"))
    locally_unacknowledged_count = total_count - locally_acknowledged_count
    payload = {"version": 1, "generated_at": _now(), "authority": "aggregator_only_not_source_of_truth", "local_only": True, "refresh_behavior": "quiet_refresh_from_local_artifacts", "filters": {"sources": list(sources or []), "severities": list(severities or []), "acknowledged": acknowledged}, "available_sources": sorted(SOURCES), "inputs": inputs, "summary": {"total_notification_count": total_count, "filtered_notification_count": len(filtered), "unavailable_source_count": sum(1 for i in inputs if not i["available"]), "locally_acknowledged_count": locally_acknowledged_count, "locally_unacknowledged_count": locally_unacknowledged_count, "severity_counts": counts}, "notifications": filtered, "operations_center_integration": {"status_bar_notification_count": total_count, "status_bar_unacknowledged_count": locally_unacknowledged_count, "filtered_display_limit": limit, "activity_stream_event_count": len(activity.get("events") or []), "read_only": True, "acknowledgement_mutates_authoritative_sources": False, "json_output": JSON_OUTPUT, "markdown_output": MARKDOWN_OUTPUT}}
    if write:
        (root / "runtime/notifications").mkdir(parents=True, exist_ok=True)
        (root / JSON_OUTPUT).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        (root / "operations/notifications").mkdir(parents=True, exist_ok=True)
        (root / MARKDOWN_OUTPUT).write_text(format_operations_notification_center(payload) + "\n", encoding="utf-8")
    return payload


def acknowledge_operations_notification(notification_id, root=None, actor="local-steward"):
    root = _root(root)
    data = {"version": 1, "acknowledgements": load_notification_acknowledgements(root)}
    data["acknowledgements"][notification_id] = {"acknowledged_at": _now(), "actor": actor, "scope": "local_notification_center_only"}
    path = root / ACK_OUTPUT
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return data["acknowledgements"][notification_id]


def format_operations_notification_center(payload):
    lines = ["# Operations Center Notification Center", "", "Read-only aggregation from existing Estate artifacts; not a notification transport or source of truth.", "", f"Generated: {payload.get('generated_at')}", f"Refresh behavior: {payload.get('refresh_behavior')}", "", "## Summary"]
    for key, value in (payload.get("summary") or {}).items():
        lines.append(f"- {key}: {value}")
    lines += ["", "## Notifications"]
    for note in payload.get("notifications") or []:
        link = (note.get("source_link") or {}).get("path")
        ack = "acknowledged locally" if note.get("locally_acknowledged") else note.get("state")
        lines.append(f"- [{note.get('severity')}] {note.get('source')} — {note.get('title')}: {note.get('message')} ({ack}; source: `{link}`)")
    if not payload.get("notifications"):
        lines.append("- No notifications match the selected filters.")
    return "\n".join(lines)


def format_operations_notification_center_summary(payload):
    summary = payload.get("summary") or {}
    return "\n".join(["Operations Center Notification Center", f"Generated: {payload.get('generated_at')}", f"Notifications: {summary.get('total_notification_count', 0)}", f"Locally unacknowledged: {summary.get('locally_unacknowledged_count', 0)}", f"Filtered display: {summary.get('filtered_notification_count', 0)}", f"Unavailable sources: {summary.get('unavailable_source_count', 0)}"])
