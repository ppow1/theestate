"""Durable audit logging for approved Steward Recall notifications.

The recall audit log records Notification Router-approved recall events after a
transport adapter has produced a delivery result. It does not classify recall
candidates itself and therefore must be fed router output rather than raw worker
requests.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

from estate.core.paths import ESTATE_ROOT

AUDIT_LOG_PATH = "runtime/audit/recall_audit_log.json"
SUMMARY_PATH = "operations/audit/recall_audit_log_summary.md"


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def estate_root(root=None):
    if root is not None:
        return Path(root)
    if ESTATE_ROOT.exists():
        return ESTATE_ROOT
    return Path.cwd()


def _read_json(path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def empty_recall_audit_log():
    return {
        "version": 1,
        "generated_at": _now(),
        "summary": {
            "record_count": 0,
            "acknowledged_count": 0,
            "pending_acknowledgement_count": 0,
        },
        "records": [],
        "constraints": {
            "append_only": True,
            "notification_router_required": True,
            "acknowledgement_ux_implemented": False,
        },
    }


def load_recall_audit_log(root=None):
    path = estate_root(root) / AUDIT_LOG_PATH
    log = _read_json(path, empty_recall_audit_log())
    log.setdefault("version", 1)
    log.setdefault("records", [])
    log.setdefault("constraints", {})
    return log


def _record_id(notification, delivery_result):
    delivery_id = delivery_result.get("delivery_id") or delivery_result.get("attempt_id") or delivery_result.get("id") or "delivery-unknown"
    return f"recall-audit-{notification.get('id', 'notification-unknown')}-{delivery_id}"


def _delivery_status(delivery_result):
    if "status" in delivery_result:
        return delivery_result["status"]
    if delivery_result.get("ok") is True:
        return "delivered" if not delivery_result.get("dry_run") else "dry_run_validated"
    return "failed"


def build_recall_audit_record(notification, delivery_result=None, *, acknowledged=False, acknowledged_at=None, timestamp=None):
    """Build a durable audit record from router output and adapter result."""
    notification = dict(notification or {})
    delivery_result = dict(delivery_result or {})
    audit = notification.get("audit") or {}
    if notification.get("class") != "recall" or not notification.get("eligible_for_immediate_delivery"):
        raise ValueError("Recall audit records require Notification Router recall output eligible for immediate delivery.")

    return {
        "record_id": _record_id(notification, delivery_result),
        "timestamp": timestamp or delivery_result.get("completed_at") or delivery_result.get("sent_at") or _now(),
        "originating_worker": audit.get("source") or notification.get("source") or "unknown",
        "requested_by": notification.get("requested_by") or "unknown",
        "recall_reason": audit.get("primary_recall_reason") or notification.get("reason"),
        "priority": notification.get("priority") or delivery_result.get("priority") or "urgent",
        "transport": delivery_result.get("transport") or delivery_result.get("adapter") or "unknown",
        "delivery_result": {
            "status": _delivery_status(delivery_result),
            "ok": bool(delivery_result.get("ok", False)),
            "dry_run": bool(delivery_result.get("dry_run", False)),
            "delivery_id": delivery_result.get("delivery_id") or delivery_result.get("attempt_id") or delivery_result.get("id"),
            "message": delivery_result.get("message"),
        },
        "acknowledgement_state": "acknowledged" if acknowledged else "pending",
        "acknowledgement_timestamp": acknowledged_at if acknowledged else None,
        "notification_id": notification.get("id"),
        "source_event_id": audit.get("source_event_id"),
        "supporting_references": audit.get("supporting_references") or [],
    }


def _summarize(records):
    acknowledged = sum(1 for record in records if record.get("acknowledgement_state") == "acknowledged")
    return {
        "record_count": len(records),
        "acknowledged_count": acknowledged,
        "pending_acknowledgement_count": len(records) - acknowledged,
    }


def append_recall_audit_record(notification, delivery_result=None, *, root=None, dry_run=False, acknowledged=False, acknowledged_at=None):
    """Append a new recall audit record without modifying historical records.

    Duplicate record ids are treated as already-present so repeated adapter
    processing is safe. In dry-run mode the would-be record is returned but no
    filesystem writes occur.
    """
    root = estate_root(root)
    log = load_recall_audit_log(root)
    record = build_recall_audit_record(notification, delivery_result, acknowledged=acknowledged, acknowledged_at=acknowledged_at)
    existing_ids = {item.get("record_id") for item in log.get("records", [])}
    appended = record["record_id"] not in existing_ids
    if appended:
        log["records"] = [*log.get("records", []), record]
    log["generated_at"] = _now()
    log["summary"] = _summarize(log.get("records", []))

    result = {"ok": True, "dry_run": dry_run, "appended": appended, "record": record, "log": log, "path": AUDIT_LOG_PATH}
    if not dry_run:
        _write_json(root / AUDIT_LOG_PATH, log)
    return result


def generate_recall_audit_summary(root=None):
    log = load_recall_audit_log(root)
    lines = [
        "# Recall Audit Log Summary",
        "",
        f"Generated at: {log.get('generated_at')}",
        f"Records: {log.get('summary', {}).get('record_count', 0)}",
        f"Pending acknowledgement: {log.get('summary', {}).get('pending_acknowledgement_count', 0)}",
        "",
    ]
    for record in log.get("records", []):
        lines.append(f"- {record.get('record_id')} | {record.get('timestamp')} | {record.get('recall_reason')} | {record.get('transport')} | {record.get('delivery_result', {}).get('status')} | ack: {record.get('acknowledgement_state')}")
    text = "\n".join(lines) + "\n"
    path = estate_root(root) / SUMMARY_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return {"ok": True, "path": SUMMARY_PATH, "summary": log.get("summary", {})}
