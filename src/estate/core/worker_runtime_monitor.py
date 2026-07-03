"""Worker Runtime Monitor.

Builds an advisory, evidence-only view of worker availability from local Estate
runtime artifacts. It does not schedule work, launch workers, or infer state
without a source artifact.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from estate.core.paths import ESTATE_ROOT
from estate.core.worker_runtime_heartbeat import DEFAULT_STALE_AFTER_MINUTES, generate_worker_runtime_summary

MONITOR_JSON = "runtime/workers/worker_runtime_monitor.json"
MONITOR_MARKDOWN = "operations/workers/worker_runtime_monitor.md"
OPTIONAL_SOURCES = {
    "heartbeat_summary": "runtime/workers/worker_runtime_heartbeat.json",
    "assignment_queue": "runtime/work_packages/assignment_queue.json",
    "mailbox_summary": "collaboration/status/worker_inbox_summary.json",
    "mailbox_sync": "runtime/mailboxes/synchronization_duty_latest.json",
    "validation": "runtime/validation/local_operational_validation_run.json",
}


def _root(root: str | Path | None = None) -> Path:
    return Path(root) if root is not None else (ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd())


def _iso(dt: datetime | None = None) -> str:
    return (dt or datetime.now(timezone.utc)).astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except ValueError:
        return None


def _read_json(root: Path, rel: str, warnings: list[dict[str, Any]], *, optional: bool = True) -> dict[str, Any] | None:
    path = root / rel
    if not path.exists():
        if optional:
            warnings.append({"type": "missing_optional_artifact", "path": rel, "message": f"Optional artifact is not available: {rel}"})
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {"value": data}
    except Exception as exc:  # local artifact may be malformed; warn, do not fail
        warnings.append({"type": "unreadable_artifact", "path": rel, "message": str(exc)})
        return None


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _worker_id_from_item(item: dict[str, Any]) -> str | None:
    return item.get("worker_id") or item.get("worker") or item.get("owner") or item.get("id")


def _assignment_map(queue: dict[str, Any] | None) -> dict[str, list[dict[str, Any]]]:
    assignments: dict[str, list[dict[str, Any]]] = {}
    if not isinstance(queue, dict):
        return assignments
    for wp in queue.get("work_packages") or []:
        if not isinstance(wp, dict):
            continue
        owner = wp.get("owner")
        if not owner or owner == "unassigned":
            continue
        entry = {
            "work_package_id": wp.get("work_package_id"),
            "state": wp.get("state"),
            "path": wp.get("path"),
            "next_action": wp.get("next_action"),
            "blockers": wp.get("blockers") or [],
            "evidence": "assignment_queue_owner",
        }
        assignments.setdefault(str(owner), []).append(entry)
    return assignments


def _mailbox_map(mailbox: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    if not isinstance(mailbox, dict):
        return result
    for worker in mailbox.get("workers") or []:
        if not isinstance(worker, dict):
            continue
        worker_id = _worker_id_from_item(worker)
        if worker_id:
            result[str(worker_id)] = {"message_count": worker.get("message_count", 0), "evidence": "worker_inbox_summary"}
    return result


def generate_worker_runtime_monitor(
    *,
    root: str | Path | None = None,
    stale_after_minutes: int = DEFAULT_STALE_AFTER_MINUTES,
    write: bool = True,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Generate an evidence-only worker runtime monitor report."""
    root_path = _root(root)
    current_time = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    warnings: list[dict[str, Any]] = []

    heartbeat = _read_json(root_path, OPTIONAL_SOURCES["heartbeat_summary"], warnings)
    if heartbeat is None and (root_path / "runtime/workers/heartbeats").exists():
        heartbeat = generate_worker_runtime_summary(root=root_path, stale_after_minutes=stale_after_minutes, write=False, now=current_time)
        warnings.append({"type": "derived_from_heartbeat_files", "path": "runtime/workers/heartbeats", "message": "Heartbeat summary was absent; monitor read local heartbeat files directly."})

    assignment_queue = _read_json(root_path, OPTIONAL_SOURCES["assignment_queue"], warnings)
    mailbox_summary = _read_json(root_path, OPTIONAL_SOURCES["mailbox_summary"], warnings)
    _read_json(root_path, OPTIONAL_SOURCES["mailbox_sync"], warnings)
    _read_json(root_path, OPTIONAL_SOURCES["validation"], warnings)

    assignments = _assignment_map(assignment_queue)
    mailboxes = _mailbox_map(mailbox_summary)
    workers: dict[str, dict[str, Any]] = {}

    for item in (heartbeat or {}).get("workers") or []:
        if not isinstance(item, dict):
            continue
        worker_id = _worker_id_from_item(item)
        if not worker_id:
            warnings.append({"type": "heartbeat_without_worker_id", "path": item.get("source_path"), "message": "Heartbeat worker entry lacks worker_id."})
            continue
        last_activity = item.get("last_heartbeat") or item.get("last_activity")
        parsed = _parse_time(last_activity)
        stale = bool(item.get("stale")) or parsed is None or parsed < current_time - timedelta(minutes=stale_after_minutes)
        status = item.get("status")
        current_assignments = assignments.get(str(worker_id), [])
        recommended = None
        if status == "blocked":
            recommended = item.get("blocking_reason") or "Review blocker evidence for this worker."
        elif stale:
            recommended = "Refresh worker heartbeat before acting on this status."
        elif status == "idle" and current_assignments:
            recommended = "Confirm whether assigned work is still current."
        elif status == "idle":
            recommended = "Worker appears available based on reported heartbeat."
        elif status == "active":
            recommended = "Allow current assignment to continue unless blocked evidence appears."
        elif status == "offline":
            recommended = "Do not assign work until a fresh heartbeat reports availability."
        workers[str(worker_id)] = {
            "worker_id": str(worker_id),
            "status": status,
            "health": "stale" if stale else status,
            "stale": stale,
            "last_activity": last_activity,
            "current_activity": item.get("current_activity"),
            "current_assignment": current_assignments[0] if current_assignments else None,
            "assignments": current_assignments,
            "blocking_reason": item.get("blocking_reason"),
            "last_completed_work_package": item.get("last_completed_work_package"),
            "mailbox": mailboxes.get(str(worker_id)),
            "recommended_next_action": recommended,
            "evidence": [e for e in [item.get("source_path") or "runtime/workers/worker_runtime_heartbeat.json", "runtime/work_packages/assignment_queue.json" if current_assignments else None, "collaboration/status/worker_inbox_summary.json" if str(worker_id) in mailboxes else None] if e],
            "state_basis": "reported heartbeat status; stale derives from heartbeat age; assignment/mailbox fields only appear when source artifacts name this worker",
        }

    for worker_id, assigned in assignments.items():
        workers.setdefault(worker_id, {
            "worker_id": worker_id,
            "status": "unknown",
            "health": "unknown",
            "stale": None,
            "last_activity": None,
            "current_activity": None,
            "current_assignment": assigned[0] if assigned else None,
            "assignments": assigned,
            "blocking_reason": None,
            "last_completed_work_package": None,
            "mailbox": mailboxes.get(worker_id),
            "recommended_next_action": "Request a worker heartbeat before relying on availability.",
            "evidence": ["runtime/work_packages/assignment_queue.json"],
            "state_basis": "assignment evidence only; runtime status is unknown because no heartbeat evidence exists",
        })

    worker_list = sorted(workers.values(), key=lambda w: w["worker_id"])
    active = [w for w in worker_list if w.get("status") == "active" and not w.get("stale")]
    blocked = [w for w in worker_list if w.get("status") == "blocked" or (w.get("current_assignment") or {}).get("blockers")]
    stale = [w for w in worker_list if w.get("stale") is True]
    offline = [w for w in worker_list if w.get("status") == "offline"]
    idle = [w for w in worker_list if w.get("status") == "idle" and not w.get("stale")]
    status_counts: dict[str, int] = {}
    for worker in worker_list:
        status_counts[str(worker.get("status") or "unknown")] = status_counts.get(str(worker.get("status") or "unknown"), 0) + 1

    payload = {
        "version": 1,
        "generated_at": _iso(current_time),
        "stale_after_minutes": stale_after_minutes,
        "constraints": {"scheduler": False, "automatic_launch": False, "remote_monitoring": False, "state_inference_without_evidence": False},
        "summary": {
            "worker_count": len(worker_list),
            "active_worker_count": len(active),
            "idle_worker_count": len(idle),
            "blocked_worker_count": len(blocked),
            "stale_worker_count": len(stale),
            "offline_worker_count": len(offline),
            "unknown_worker_count": status_counts.get("unknown", 0),
            "warning_count": len(warnings),
            "status_counts": status_counts,
            "recommended_next_action": "Refresh missing/stale worker evidence before assignment decisions." if warnings or stale else "Use reported worker status as advisory evidence only.",
        },
        "workers": worker_list,
        "active_workers": active,
        "idle_workers": idle,
        "blocked_workers": blocked,
        "stale_workers": stale,
        "offline_workers": offline,
        "warnings": warnings,
    }
    if write:
        _write_json(root_path / MONITOR_JSON, payload)
        md_path = root_path / MONITOR_MARKDOWN
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text(format_worker_runtime_monitor(payload), encoding="utf-8")
    return payload


def format_worker_runtime_monitor(payload: dict[str, Any]) -> str:
    summary = payload.get("summary", {})
    lines = [
        "# Worker Runtime Monitor",
        "",
        f"Generated: {payload.get('generated_at')}",
        "",
        "This monitor is advisory and evidence-only. It does not schedule work, launch workers, perform remote monitoring, or infer worker availability without source artifacts.",
        "",
        "## Summary",
        f"- Workers observed: {summary.get('worker_count', 0)}",
        f"- Active: {summary.get('active_worker_count', 0)}",
        f"- Idle: {summary.get('idle_worker_count', 0)}",
        f"- Blocked: {summary.get('blocked_worker_count', 0)}",
        f"- Stale: {summary.get('stale_worker_count', 0)}",
        f"- Offline: {summary.get('offline_worker_count', 0)}",
        f"- Unknown: {summary.get('unknown_worker_count', 0)}",
        f"- Warnings: {summary.get('warning_count', 0)}",
        f"- Stale threshold: {payload.get('stale_after_minutes')} minutes",
        f"- Recommended next action: {summary.get('recommended_next_action')}",
        "",
        "## Workers",
    ]
    if not payload.get("workers"):
        lines.append("- No worker evidence found in available artifacts.")
    for worker in payload.get("workers") or []:
        assignment = worker.get("current_assignment") or {}
        assignment_text = assignment.get("work_package_id") or "none"
        blocked = f"; blocker: {worker.get('blocking_reason')}" if worker.get("blocking_reason") else ""
        lines.append(f"- {worker.get('worker_id')}: {worker.get('status')} / {worker.get('health')}; last activity: {worker.get('last_activity') or 'unknown'}; assignment: {assignment_text}; next: {worker.get('recommended_next_action')}{blocked}")
    if payload.get("warnings"):
        lines += ["", "## Warnings"]
        for warning in payload.get("warnings") or []:
            lines.append(f"- {warning.get('type')}: {warning.get('message')} ({warning.get('path')})")
    return "\n".join(lines) + "\n"
