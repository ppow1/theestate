"""Transport-independent notification routing for recall-worthy Estate events.

The router classifies structured Estate events into a small v1 notification
surface. It intentionally does not know about any delivery transport; adapters
may consume recall-eligible records later, after Alfred has made the recall
assessment required by policy.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

from estate.core.paths import ESTATE_ROOT

POLICY_PATH = "data/policy/steward_recall_reasons.json"
REPORT_PATH = "runtime/notifications/notification_router_report.json"
ROUTINE_SUCCESS_TYPES = {
    "successful_codex_run",
    "codex_run_success",
    "completed_work",
    "normal_mailbox_update",
    "mailbox_update",
    "routine_mail",
    "normal_board_update",
    "normal_validation",
    "informational_status_change",
}
TRANSPORT_FIELD_DENYLIST = {
    "gotify",
    "gotify_url",
    "gotify_token",
    "gotify_priority",
    "gotify_message",
    "gotify_title",
    "transport_adapter",
    "notification_attempt_id",
}


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def estate_root(root=None):
    if root is not None:
        return Path(root)
    if ESTATE_ROOT.exists():
        return ESTATE_ROOT
    return Path.cwd()


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _read_policy(root, warnings):
    path = root / POLICY_PATH
    if not path.exists():
        warnings.append({"type": "missing_optional_input", "path": POLICY_PATH, "message": "Recall policy artifact is unavailable; built-in v1 reason ids are used."})
        return {
            "version": "1.0",
            "approved_recall_reasons": [{"id": reason} for reason in ("constitutional", "architectural", "operational", "security", "hr")],
            "non_recall_events": sorted(ROUTINE_SUCCESS_TYPES),
        }
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        warnings.append({"type": "malformed_optional_input", "path": POLICY_PATH, "message": str(exc)})
        return {"version": "1.0", "approved_recall_reasons": [], "non_recall_events": sorted(ROUTINE_SUCCESS_TYPES)}


def _approved_reason_ids(policy):
    return {str(item.get("id")) for item in policy.get("approved_recall_reasons", []) if isinstance(item, dict) and item.get("id")}


def _clean_transport_details(value):
    if isinstance(value, dict):
        return {k: _clean_transport_details(v) for k, v in value.items() if str(k).lower() not in TRANSPORT_FIELD_DENYLIST}
    if isinstance(value, list):
        return [_clean_transport_details(v) for v in value]
    return value


def _event_id(event, index=0):
    return event.get("id") or event.get("event_id") or f"event-{index + 1:04d}"


def _priority_for(event, notification_class):
    if event.get("priority"):
        return event["priority"]
    if notification_class == "recall":
        return "urgent"
    return "normal"


def _missing_evidence(event):
    missing = []
    evidence = event.get("evidence") or {}
    for field in (
        "triggering_artifact",
        "blocked_decision",
        "steward_only_rationale",
        "options_or_recommended_next_action",
        "consequence_of_waiting",
        "continuity_assessment",
        "supporting_references",
    ):
        if event.get(field) in (None, "", []) and evidence.get(field) in (None, "", []):
            missing.append(field)
    return missing


def route_notification_event(event, policy=None, index=0):
    """Classify one structured Estate event as recall or informational.

    The caller is expected to pass Alfred-assessed recall candidates. Worker
    requests alone are treated as candidates and become recall only when the
    event says Alfred validated the policy match.
    """
    policy = policy or {"version": "1.0", "approved_recall_reasons": []}
    event = dict(event or {})
    warnings = []
    event_type = str(event.get("event_type") or event.get("type") or "unknown")
    reason = event.get("recall_reason") or event.get("primary_recall_reason")
    approved_reasons = _approved_reason_ids(policy)
    alfred_validated = bool(event.get("alfred_validated") or event.get("requested_by") == "alfred" or event.get("source") == "alfred")
    routine = event_type in ROUTINE_SUCCESS_TYPES or event.get("status") in {"success", "completed", "ok"}

    missing = _missing_evidence(event)
    for field in missing:
        warnings.append({"type": "missing_optional_input", "field": field, "message": "Optional routing evidence was not supplied; event is still recorded."})

    is_recall = bool(reason in approved_reasons and alfred_validated and not routine)
    notification_class = "recall" if is_recall else "informational"
    evidence = _clean_transport_details(event.get("evidence") or {})

    audit = {
        "router_version": 1,
        "policy_version": policy.get("version"),
        "source_event_id": _event_id(event, index),
        "source": event.get("source") or "unknown",
        "event_type": event_type,
        "alfred_validated": alfred_validated,
        "primary_recall_reason": reason,
        "non_recall_events_checked": sorted(ROUTINE_SUCCESS_TYPES),
        "missing_optional_fields": missing,
        "supporting_references": event.get("supporting_references") or evidence.get("supporting_references") or [],
    }

    return {
        "id": f"notification-{_event_id(event, index)}",
        "class": notification_class,
        "eligible_for_immediate_delivery": notification_class == "recall",
        "reason": reason or event.get("reason") or f"{event_type} routed as {notification_class}",
        "requested_by": event.get("requested_by") or "alfred" if alfred_validated else event.get("requested_by") or "unknown",
        "priority": _priority_for(event, notification_class),
        "action": event.get("action") or ("prepare_recall_delivery" if notification_class == "recall" else "defer_to_briefing"),
        "summary": event.get("summary") or event.get("title") or event_type,
        "audit": audit,
        "warnings": warnings,
    }


def route_notification_events(events=None, root=None, write=False):
    root = estate_root(root)
    warnings = []
    policy = _read_policy(root, warnings)
    events = list(events or [])
    notifications = [route_notification_event(event, policy=policy, index=i) for i, event in enumerate(events)]
    for item in notifications:
        warnings.extend(item.get("warnings", []))
    report = {
        "version": 1,
        "generated_at": _now(),
        "summary": {
            "event_count": len(events),
            "recall_count": sum(1 for item in notifications if item["class"] == "recall"),
            "informational_count": sum(1 for item in notifications if item["class"] == "informational"),
            "immediate_delivery_eligible_count": sum(1 for item in notifications if item["eligible_for_immediate_delivery"]),
        },
        "notifications": notifications,
        "warnings": warnings,
        "constraints": {
            "transport_independent": True,
            "adapter_implemented": False,
            "workers_may_notify_steward_directly": False,
            "alfred_required_for_recall": True,
        },
    }
    if write:
        _write_json(root / REPORT_PATH, report)
    return report


def generate_notification_router_report(root=None, write=True):
    """Generate a baseline report without fabricating recall events."""
    return route_notification_events([], root=root, write=write)


def format_notification_router_report(report):
    summary = report.get("summary", {})
    return "\n".join([
        "Notification Router v1",
        f"Events: {summary.get('event_count', 0)}",
        f"Recall: {summary.get('recall_count', 0)}",
        f"Informational: {summary.get('informational_count', 0)}",
        f"Immediate delivery eligible: {summary.get('immediate_delivery_eligible_count', 0)}",
    ])
