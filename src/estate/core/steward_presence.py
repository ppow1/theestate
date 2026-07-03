"""Steward Presence and Recall State Machine.

Builds a bounded, evidence-only state report from Estate-approved local recall
and operations artifacts. It does not observe the Steward, send notifications,
or change recall authority.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from estate.core.paths import ESTATE_ROOT

PRESENCE_JSON = "runtime/steward/steward_presence_state.json"
PRESENCE_MARKDOWN = "operations/steward/steward_presence_state.md"
VALID_STATES = {
    "present",
    "away",
    "autonomous_operation",
    "recall_requested",
    "recall_sent",
    "recall_acknowledged",
    "resumed",
    "unknown",
}
ALLOWED_TRANSITIONS = {
    "unknown": VALID_STATES - {"unknown"},
    "present": {"away", "autonomous_operation", "recall_requested", "unknown"},
    "away": {"present", "autonomous_operation", "recall_requested", "unknown"},
    "autonomous_operation": {"present", "away", "recall_requested", "unknown"},
    "recall_requested": {"recall_sent", "recall_acknowledged", "unknown"},
    "recall_sent": {"recall_acknowledged", "recall_requested", "unknown"},
    "recall_acknowledged": {"resumed", "present", "unknown"},
    "resumed": {"present", "autonomous_operation", "away", "unknown"},
}
SOURCE_PATHS = {
    "recall_audit_log": "runtime/audit/recall_audit_log.json",
    "notification_router": "runtime/notifications/notification_router_report.json",
    "gotify_delivery": "runtime/notifications/gotify_delivery_report.json",
    "notification_center": "runtime/notifications/notification_center_workspace.json",
    "morning_briefing": "runtime/operations/morning_briefing.json",
}


def _root(root: str | Path | None = None) -> Path:
    return Path(root) if root is not None else (ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd())


def _iso(dt: datetime | None = None) -> str:
    return (dt or datetime.now(timezone.utc)).astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _read_json(root: Path, rel: str, warnings: list[dict[str, Any]]) -> dict[str, Any] | None:
    path = root / rel
    if not path.exists():
        warnings.append({"type": "missing_evidence", "path": rel, "message": f"Evidence artifact is not available: {rel}"})
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        warnings.append({"type": "unreadable_evidence", "path": rel, "message": str(exc)})
        return None
    return data if isinstance(data, dict) else {"value": data}


def validate_transition(from_state: str, to_state: str) -> dict[str, Any]:
    if from_state not in VALID_STATES or to_state not in VALID_STATES:
        return {"ok": False, "from_state": from_state, "to_state": to_state, "reason": "unknown_state"}
    if from_state == to_state:
        return {"ok": True, "from_state": from_state, "to_state": to_state, "reason": "no_op"}
    ok = to_state in ALLOWED_TRANSITIONS[from_state]
    return {"ok": ok, "from_state": from_state, "to_state": to_state, "reason": "allowed" if ok else "invalid_transition"}


def apply_transition(state: dict[str, Any], to_state: str, *, evidence: str, reason: str, timestamp: str | None = None) -> dict[str, Any]:
    current = state.get("current_state", "unknown")
    result = validate_transition(current, to_state)
    event = {"timestamp": timestamp or _iso(), "from_state": current, "to_state": to_state, "ok": result["ok"], "reason": reason, "evidence": evidence}
    history = [*state.get("transition_history", []), event]
    updated = dict(state)
    updated["transition_history"] = history
    if not result["ok"]:
        updated.setdefault("warnings", []).append({"type": "invalid_transition", "message": f"Invalid transition {current} -> {to_state}", "evidence": evidence})
        return updated
    updated["current_state"] = to_state
    updated["last_transition_at"] = event["timestamp"]
    return updated


def _new_state(now: datetime | None = None) -> dict[str, Any]:
    return {
        "version": 1,
        "generated_at": _iso(now),
        "current_state": "unknown",
        "last_transition_at": None,
        "transition_history": [],
        "warnings": [],
        "constraints": {
            "evidence_only": True,
            "biometric_or_passive_surveillance": False,
            "sends_notifications": False,
            "bypasses_alfred_or_recall_authority": False,
            "mobile_app_behavior": False,
        },
    }


def _latest_recall_record(records: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not records:
        return None
    return sorted(records, key=lambda r: r.get("timestamp") or "")[-1]


def generate_steward_presence_state(*, root: str | Path | None = None, write: bool = True, now: datetime | None = None) -> dict[str, Any]:
    root_path = _root(root)
    state = _new_state(now)
    sources = {name: _read_json(root_path, rel, state["warnings"]) for name, rel in SOURCE_PATHS.items()}
    state["sources"] = {name: {"path": SOURCE_PATHS[name], "available": data is not None} for name, data in sources.items()}

    audit = sources.get("recall_audit_log") or {}
    records = audit.get("records") if isinstance(audit.get("records"), list) else []
    latest = _latest_recall_record([r for r in records if isinstance(r, dict)])
    router = sources.get("notification_router") or {}
    router_recalls = [n for n in router.get("notifications", []) if isinstance(n, dict) and n.get("class") == "recall"] if isinstance(router.get("notifications"), list) else []

    if latest:
        state = apply_transition(state, "recall_requested", evidence=SOURCE_PATHS["recall_audit_log"], reason="recall audit record exists", timestamp=latest.get("timestamp"))
        delivery_result = latest.get("delivery_result")
        status = ((delivery_result or {}).get("status") if isinstance(delivery_result, dict) else delivery_result or "").lower()
        if status in {"delivered", "dry_run_validated", "sent", "accepted"}:
            state = apply_transition(state, "recall_sent", evidence=SOURCE_PATHS["recall_audit_log"], reason=f"delivery status: {status}", timestamp=latest.get("timestamp"))
        if latest.get("acknowledgement_state") == "acknowledged":
            state = apply_transition(state, "recall_acknowledged", evidence=SOURCE_PATHS["recall_audit_log"], reason="recall acknowledgement recorded", timestamp=latest.get("acknowledgement_timestamp") or latest.get("timestamp"))
    elif router_recalls:
        event = sorted(router_recalls, key=lambda n: n.get("created_at") or n.get("id") or "")[-1]
        state = apply_transition(state, "recall_requested", evidence=SOURCE_PATHS["notification_router"], reason="router recall output exists", timestamp=event.get("created_at"))
    else:
        state["warnings"].append({"type": "unknown_state", "message": "No approved local evidence establishes Steward presence or recall lifecycle state.", "path": None})

    state["summary"] = {
        "state": state["current_state"],
        "warning_count": len(state["warnings"]),
        "transition_count": len(state["transition_history"]),
        "alfred_guidance": "request_or_continue_recall_path" if state["current_state"] in {"recall_requested", "recall_sent"} else ("resume_or_confirm_operations" if state["current_state"] in {"recall_acknowledged", "resumed", "present"} else "treat_as_unknown_until_evidence_refresh"),
    }
    if write:
        json_path = root_path / PRESENCE_JSON
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        md_path = root_path / PRESENCE_MARKDOWN
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text(format_steward_presence_state(state), encoding="utf-8")
    return state


def format_steward_presence_state(payload: dict[str, Any]) -> str:
    lines = [
        "# Steward Presence and Recall State",
        "",
        f"Generated: {payload.get('generated_at')}",
        f"Current state: {payload.get('current_state')}",
        f"Alfred guidance: {(payload.get('summary') or {}).get('alfred_guidance')}",
        "",
        "This report is evidence-only. It does not track the Steward outside Estate-approved local artifacts and does not send notifications.",
        "",
        "## Transition History",
    ]
    if not payload.get("transition_history"):
        lines.append("- No explicit transition evidence found; state remains unknown.")
    for event in payload.get("transition_history") or []:
        lines.append(f"- {event.get('timestamp')}: {event.get('from_state')} -> {event.get('to_state')} ({event.get('reason')}; evidence: {event.get('evidence')})")
    if payload.get("warnings"):
        lines += ["", "## Warnings"]
        for warning in payload.get("warnings") or []:
            lines.append(f"- {warning.get('type')}: {warning.get('message')} ({warning.get('path') or 'no path'})")
    return "\n".join(lines) + "\n"
