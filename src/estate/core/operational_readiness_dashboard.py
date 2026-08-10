"""Operational Readiness Dashboard.

Read-only aggregation of existing Estate operational signals. The dashboard is a
status surface only: authoritative state remains in the source artifacts linked
from each subsystem.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from estate.core.paths import ESTATE_ROOT

READINESS_JSON = "runtime/operations/operational_readiness_dashboard.json"
READINESS_MARKDOWN = "operations/readiness/operational_readiness_dashboard.md"

SOURCE_PATHS = {
    "mission_control": "runtime/steward/mission_control_workspace.json",
    "validation_metrics": "runtime/validation/validation_metrics_dashboard.json",
    "worker_runtime_monitor": "runtime/workers/worker_runtime_monitor.json",
    "autonomous_operations_control_loop": "runtime/autonomy/autonomous_operations_state.json",
    "notification_center": "runtime/notifications/operations_notification_center.json",
    "steward_presence_state": "runtime/steward/steward_presence_state.json",
    "operations_board": "runtime/operations/operations_board.json",
}


def _root(root: str | Path | None = None) -> Path:
    return Path(root) if root is not None else (ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd())


def _now(now: datetime | None = None) -> str:
    return (now or datetime.now(timezone.utc)).astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _read_json(root: Path, rel: str) -> tuple[Any | None, dict[str, Any] | None]:
    path = root / rel
    if not path.exists():
        return None, {"type": "unavailable_artifact", "path": rel, "message": f"Artifact is unavailable: {rel}"}
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except Exception as exc:
        return None, {"type": "unreadable_artifact", "path": rel, "message": str(exc)}


def _count(payload: dict[str, Any], path: list[str], default: int = 0) -> int:
    value: Any = payload
    for key in path:
        if not isinstance(value, dict):
            return default
        value = value.get(key)
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def _list(payload: dict[str, Any], key: str) -> list[Any]:
    value = payload.get(key)
    return value if isinstance(value, list) else []


def _source_status(name: str, rel: str, payload: Any, warning: dict[str, Any] | None) -> dict[str, Any]:
    if warning:
        return {"name": name, "path": rel, "available": False, "status": "unavailable", "drill_down": rel, "summary": warning["message"]}
    if not isinstance(payload, dict):
        return {"name": name, "path": rel, "available": False, "status": "unavailable", "drill_down": rel, "summary": "Artifact is not a JSON object."}
    status = payload.get("status") or payload.get("decision") or (payload.get("summary") or {}).get("state") or (payload.get("data") or {}).get("summary", {}).get("state") or "available"
    return {"name": name, "path": rel, "available": True, "status": str(status), "drill_down": rel, "summary": payload.get("summary") or (payload.get("data") or {}).get("summary") or {}}


def generate_operational_readiness_dashboard(*, root: str | Path | None = None, write: bool = True, now: datetime | None = None) -> dict[str, Any]:
    root_path = _root(root)
    warnings: list[dict[str, Any]] = []
    payloads: dict[str, Any] = {}
    sources: list[dict[str, Any]] = []
    for name, rel in SOURCE_PATHS.items():
        payload, warning = _read_json(root_path, rel)
        payloads[name] = payload
        if warning:
            warnings.append(warning)
        sources.append(_source_status(name, rel, payload, warning))

    blocking: list[dict[str, Any]] = []
    degraded: list[dict[str, Any]] = []

    unavailable = [s for s in sources if not s["available"]]
    if unavailable:
        degraded.append({"type": "unavailable_subsystems", "message": "One or more source artifacts are unavailable.", "sources": [s["name"] for s in unavailable]})

    validation = payloads.get("validation_metrics") if isinstance(payloads.get("validation_metrics"), dict) else {}
    validation_summary = validation.get("summary") or {}
    if _count(validation, ["summary", "fail_count"]) > 0 or _count(validation, ["summary", "confirmed_defect_count"]) > 0:
        blocking.append({"type": "validation_failure_or_defect", "message": "Validation metrics report failures or confirmed defects.", "path": SOURCE_PATHS["validation_metrics"]})
    elif _count(validation, ["summary", "conditional_pass_count"]) > 0 or _count(validation, ["summary", "open_observation_count"]) > 0:
        degraded.append({"type": "validation_observations", "message": "Validation metrics contain conditional passes or open observations.", "path": SOURCE_PATHS["validation_metrics"]})

    workers = payloads.get("worker_runtime_monitor") if isinstance(payloads.get("worker_runtime_monitor"), dict) else {}
    worker_summary = workers.get("summary") or {}
    if _count(workers, ["summary", "blocked_worker_count"]) > 0:
        blocking.append({"type": "blocked_workers", "message": "Worker Runtime Monitor reports blocked workers.", "path": SOURCE_PATHS["worker_runtime_monitor"]})
    if _count(workers, ["summary", "stale_worker_count"]) > 0 or _count(workers, ["summary", "offline_worker_count"]) > 0 or _count(workers, ["summary", "unknown_worker_count"]) > 0:
        degraded.append({"type": "worker_availability_degraded", "message": "Worker Runtime Monitor reports stale, offline, or unknown workers.", "path": SOURCE_PATHS["worker_runtime_monitor"]})

    autonomy = payloads.get("autonomous_operations_control_loop") if isinstance(payloads.get("autonomous_operations_control_loop"), dict) else {}
    if autonomy.get("decision") in {"pause", "recall-recommended"}:
        blocking.append({"type": "autonomous_operations_not_clear", "message": f"Autonomous control loop decision is {autonomy.get('decision')}.", "path": SOURCE_PATHS["autonomous_operations_control_loop"]})

    presence = payloads.get("steward_presence_state") if isinstance(payloads.get("steward_presence_state"), dict) else {}
    presence_state = presence.get("current_state")
    active_recall_states = {"recall_requested", "recall_sent"}
    active_recalls = []
    if presence_state in active_recall_states:
        active_recalls.append({"source": "steward_presence_state", "state": presence_state, "path": SOURCE_PATHS["steward_presence_state"]})
        blocking.append({"type": "active_recall", "message": f"Steward presence state is {presence_state}.", "path": SOURCE_PATHS["steward_presence_state"]})

    notifications = payloads.get("notification_center") if isinstance(payloads.get("notification_center"), dict) else {}
    for item in _list(notifications, "recalls") + _list(notifications, "active_recalls") + _list(notifications, "notifications"):
        if isinstance(item, dict) and str(item.get("status") or item.get("state") or "").lower() in {"open", "pending", "active", "requested", "sent"}:
            active_recalls.append({"source": "notification_center", "id": item.get("id") or item.get("notification_id"), "status": item.get("status") or item.get("state"), "path": SOURCE_PATHS["notification_center"]})

    board = payloads.get("operations_board") if isinstance(payloads.get("operations_board"), dict) else {}
    for item in _list(board, "blocked_work") + _list((board.get("summary") or {}) if isinstance(board, dict) else {}, "blocked_work"):
        if isinstance(item, dict):
            blocking.append({"type": "operations_board_blocker", "message": item.get("title") or item.get("message") or "Operations Board reports blocked work.", "path": SOURCE_PATHS["operations_board"]})

    mission = payloads.get("mission_control") if isinstance(payloads.get("mission_control"), dict) else {}
    mission_summary = (mission.get("data") or {}).get("summary") if isinstance(mission.get("data"), dict) else mission.get("summary") or {}
    if str((mission_summary or {}).get("state") or "").lower() in {"partial", "degraded", "warning"}:
        degraded.append({"type": "mission_control_partial", "message": "Mission Control reports a partial or degraded source set.", "path": SOURCE_PATHS["mission_control"]})

    if unavailable and len(unavailable) == len(sources):
        readiness = "startup"
        next_action = "Generate baseline operational artifacts before relying on readiness status."
    elif blocking:
        readiness = "blocked"
        next_action = "Resolve blocking issues in the linked source artifacts before autonomous or steward-assisted operation."
    elif degraded:
        readiness = "degraded"
        next_action = "Refresh or review degraded source artifacts, then reassess readiness."
    else:
        readiness = "healthy"
        next_action = "Continue normal operation; use drill-down links for routine review."

    result = {
        "version": 1,
        "generated_at": _now(now),
        "authority_boundary": "read_only_aggregation_not_source_of_truth_no_execution_no_governance_change",
        "refresh_behavior": "quiet_refresh_safe",
        "overall_readiness_status": readiness,
        "blocking_issues": blocking,
        "degraded_subsystems": degraded,
        "active_recalls": active_recalls,
        "worker_availability": worker_summary or {"available": False},
        "validation_health_summary": validation_summary or {"available": False},
        "recommended_next_operational_action": next_action,
        "sources": sources,
        "warnings": warnings,
    }
    if write:
        (root_path / READINESS_JSON).parent.mkdir(parents=True, exist_ok=True)
        (root_path / READINESS_MARKDOWN).parent.mkdir(parents=True, exist_ok=True)
        (root_path / READINESS_JSON).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        (root_path / READINESS_MARKDOWN).write_text(format_operational_readiness_dashboard(result), encoding="utf-8")
    return result


def format_operational_readiness_dashboard(payload: dict[str, Any]) -> str:
    lines = [
        "# Operational Readiness Dashboard",
        "",
        f"Generated: {payload.get('generated_at')}",
        f"Overall readiness status: {payload.get('overall_readiness_status')}",
        f"Recommended next operational action: {payload.get('recommended_next_operational_action')}",
        "",
        "Read-only aggregation. Authoritative state remains in the linked source artifacts; this dashboard does not execute work or change governance.",
        "",
        "## Blocking Issues",
    ]
    lines += [f"- {i.get('type')}: {i.get('message')} (`{i.get('path')}`)" for i in payload.get("blocking_issues") or []] or ["- None"]
    lines += ["", "## Degraded Subsystems"]
    lines += [f"- {i.get('type')}: {i.get('message')} (`{i.get('path', 'multiple')}`)" for i in payload.get("degraded_subsystems") or []] or ["- None"]
    lines += ["", "## Active Recalls"]
    lines += [f"- {i.get('source')}: {i.get('state') or i.get('status') or i.get('id')} (`{i.get('path')}`)" for i in payload.get("active_recalls") or []] or ["- None"]
    lines += ["", "## Worker Availability"]
    for key, value in (payload.get("worker_availability") or {}).items():
        lines.append(f"- {key}: {value}")
    lines += ["", "## Validation Health Summary"]
    for key, value in (payload.get("validation_health_summary") or {}).items():
        lines.append(f"- {key}: {value}")
    lines += ["", "## Drill-Down Links"]
    for source in payload.get("sources") or []:
        state = "available" if source.get("available") else "unavailable"
        lines.append(f"- {source.get('name')}: `{source.get('drill_down')}` ({state}; status: {source.get('status')})")
    if payload.get("warnings"):
        lines += ["", "## Unavailable Artifacts"] + [f"- {w.get('type')}: {w.get('message')} (`{w.get('path')}`)" for w in payload["warnings"]]
    return "\n".join(lines) + "\n"


def format_operational_readiness_summary(payload: dict[str, Any]) -> str:
    return (
        "Operational Readiness Dashboard\n"
        f"Status: {payload.get('overall_readiness_status')}\n"
        f"Blocking issues: {len(payload.get('blocking_issues') or [])}\n"
        f"Degraded subsystems: {len(payload.get('degraded_subsystems') or [])}\n"
        f"Active recalls: {len(payload.get('active_recalls') or [])}\n"
        f"Next action: {payload.get('recommended_next_operational_action')}\n"
        f"JSON: {READINESS_JSON}\nMarkdown: {READINESS_MARKDOWN}"
    )
