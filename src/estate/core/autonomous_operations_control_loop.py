"""Autonomous Operations Control Loop.

Evidence-only control loop that recommends whether Estate autonomous operations
may continue. It never launches work, sends notifications, or overrides Alfred,
recall authority, or Steward approvals.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from estate.core.paths import ESTATE_ROOT

CONTROL_JSON = "runtime/autonomy/autonomous_operations_state.json"
CONTROL_MARKDOWN = "operations/autonomy/autonomous_operations_control_loop.md"
MISSION_CONTROL_JSON = "runtime/mission_control/autonomous_operations_control_loop.json"

SOURCE_PATHS = {
    "scheduler": "runtime/work_packages/autonomous_work_queue_scheduler.json",
    "worker_monitor": "runtime/workers/worker_runtime_monitor.json",
    "steward_presence": "runtime/steward/steward_presence_state.json",
    "morning_briefing": "runtime/operations/morning_briefing.json",
    "local_validation": "runtime/validation/local_operational_validation_run.json",
    "operational_validation": "runtime/validation/operational_validation_report.json",
    "notification_router": "runtime/notifications/notification_router_report.json",
    "recall_audit": "runtime/audit/recall_audit_log.json",
    "operations_board": "runtime/operations/daily_board_integration.json",
}


def _root(root: str | Path | None = None) -> Path:
    return Path(root) if root is not None else (ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd())


def _now(now: datetime | None = None) -> str:
    return (now or datetime.now(timezone.utc)).astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _read_json(root: Path, rel: str) -> tuple[Any | None, dict[str, Any]]:
    path = root / rel
    if not path.exists():
        return None, {"type": "missing_evidence", "path": rel, "message": f"Required control-loop evidence is unavailable: {rel}"}
    try:
        return json.loads(path.read_text(encoding="utf-8")), {}
    except Exception as exc:
        return None, {"type": "unreadable_evidence", "path": rel, "message": str(exc)}


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _validation_failed(payload: Any) -> bool:
    if not isinstance(payload, dict):
        return True
    statuses = [str(step.get("status", "")).lower() for step in payload.get("steps", []) if isinstance(step, dict)]
    explicit = str(payload.get("status") or payload.get("overall_status") or "").lower()
    return explicit in {"failed", "fail", "error"} or any(status in {"failed", "fail", "error"} for status in statuses)


def _conflicting_sources(sources: dict[str, Any]) -> list[dict[str, Any]]:
    conflicts: list[dict[str, Any]] = []
    presence_state = ((sources.get("steward_presence") or {}).get("current_state") if isinstance(sources.get("steward_presence"), dict) else None)
    scheduler_ready = (((sources.get("scheduler") or {}).get("summary") or {}).get("ready_count") if isinstance(sources.get("scheduler"), dict) else None)
    if presence_state in {"recall_requested", "recall_sent"} and scheduler_ready and int(scheduler_ready) > 0:
        conflicts.append({"type": "recall_vs_ready_work", "message": "Recall lifecycle evidence conflicts with ready autonomous work evidence.", "paths": [SOURCE_PATHS["steward_presence"], SOURCE_PATHS["scheduler"]]})
    return conflicts


def generate_autonomous_operations_control_loop(*, root: str | Path | None = None, write: bool = True, now: datetime | None = None) -> dict[str, Any]:
    root_path = _root(root)
    generated_at = _now(now)
    evidence: dict[str, dict[str, Any]] = {}
    warnings: list[dict[str, Any]] = []
    sources: dict[str, Any] = {}
    for name, rel in SOURCE_PATHS.items():
        payload, warning = _read_json(root_path, rel)
        sources[name] = payload
        evidence[name] = {"path": rel, "available": payload is not None}
        if warning:
            warnings.append(warning)

    blocked: list[dict[str, Any]] = []
    if warnings:
        blocked.append({"type": "missing_or_unreadable_evidence", "message": "One or more evidence artifacts are missing or unreadable.", "items": warnings})

    presence = sources.get("steward_presence") if isinstance(sources.get("steward_presence"), dict) else {}
    presence_state = presence.get("current_state")
    recalls = presence_state in {"recall_requested", "recall_sent"}
    if recalls:
        blocked.append({"type": "active_recall_lifecycle", "message": f"Steward recall state is {presence_state}; autonomous continuation requires recall authority resolution.", "path": SOURCE_PATHS["steward_presence"]})

    scheduler = sources.get("scheduler") if isinstance(sources.get("scheduler"), dict) else {}
    ready_count = int((scheduler.get("summary") or {}).get("ready_count") or 0)
    if ready_count == 0:
        blocked.append({"type": "no_ready_work", "message": "Scheduler reports no ready autonomous work.", "path": SOURCE_PATHS["scheduler"]})

    worker = sources.get("worker_monitor") if isinstance(sources.get("worker_monitor"), dict) else {}
    worker_summary = worker.get("summary") or {}
    if int(worker_summary.get("blocked_worker_count") or 0) > 0 or int(worker_summary.get("active_worker_count") or 0) > 0:
        blocked.append({"type": "worker_not_clear", "message": "Worker monitor reports active or blocked workers; do not start additional autonomous continuation.", "path": SOURCE_PATHS["worker_monitor"]})

    for key in ("local_validation", "operational_validation"):
        if sources.get(key) is not None and _validation_failed(sources[key]):
            blocked.append({"type": "failed_validation", "message": f"Validation artifact reports failure: {key}.", "path": SOURCE_PATHS[key]})

    conflicts = _conflicting_sources(sources)
    if conflicts:
        blocked.extend(conflicts)

    if recalls:
        decision = "recall-recommended"
        status = "recall_pending"
        reason = "Recall lifecycle evidence takes precedence over autonomous continuation."
        next_action = "Alfred should keep operations paused and route through approved recall authority; do not notify directly from this control loop."
    elif blocked:
        decision = "pause"
        status = "paused_or_unknown"
        reason = "Control-loop evidence is missing, conflicting, failed, or has no ready work."
        next_action = "Refresh evidence artifacts and ask Alfred/Steward authority to review blocked conditions before continuing."
    else:
        decision = "continue"
        status = "continuation_allowed_advisory"
        reason = "All required local evidence is available, validation did not fail, workers are clear, and ready work exists."
        next_action = f"Alfred may recommend the scheduler's next package ({(scheduler.get('summary') or {}).get('recommended_next_work_package')}) for authorized continuation without executing it automatically."

    payload = {
        "version": 1,
        "generated_at": generated_at,
        "local_first": True,
        "authority_boundary": "advisory_only_does_not_execute_work_notify_steward_or_bypass_alfred_recall_or_steward_approval",
        "status": status,
        "decision": decision,
        "reason": reason,
        "recommended_next_action": next_action,
        "evidence_paths_used": evidence,
        "blocked_conditions": blocked,
        "warnings": warnings,
    }
    if write:
        _write_json(root_path / CONTROL_JSON, payload)
        md_path = root_path / CONTROL_MARKDOWN
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text(format_autonomous_operations_control_loop(payload), encoding="utf-8")
        _write_json(root_path / MISSION_CONTROL_JSON, {"source": "autonomous_operations_control_loop", "generated_at": generated_at, "status": status, "decision": decision, "blocked_condition_count": len(blocked), "report": CONTROL_MARKDOWN})
    return payload


def format_autonomous_operations_control_loop(payload: dict[str, Any]) -> str:
    lines = [
        "# Autonomous Operations Control Loop",
        "",
        f"Generated: {payload.get('generated_at')}",
        f"Status: {payload.get('status')}",
        f"Decision: {payload.get('decision')}",
        f"Reason: {payload.get('reason')}",
        f"Recommended next action: {payload.get('recommended_next_action')}",
        "",
        "This control loop is advisory and local-first. It does not execute work, notify the Steward, or bypass Alfred, recall authority, or Steward approvals.",
        "",
        "## Evidence Paths Used",
    ]
    for name, info in payload.get("evidence_paths_used", {}).items():
        lines.append(f"- {name}: {info.get('path')} (available: {info.get('available')})")
    lines += ["", "## Blocked Conditions"]
    if not payload.get("blocked_conditions"):
        lines.append("- None")
    for item in payload.get("blocked_conditions", []):
        lines.append(f"- {item.get('type')}: {item.get('message')}")
    return "\n".join(lines) + "\n"
