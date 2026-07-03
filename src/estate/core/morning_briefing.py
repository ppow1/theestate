"""Morning Briefing v1 generator.

Builds a concise, non-authoritative Steward briefing from existing Estate
operational artifacts. Missing optional inputs are warnings, not failures.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from estate.core.paths import ESTATE_ROOT

JSON_OUTPUT = "runtime/briefings/morning_briefing.json"
MARKDOWN_OUTPUT = "operations/briefings/morning_briefing.md"

OPTIONAL_ARTIFACTS = {
    "alfred_operational_briefing": "operations/alfred/operational_briefing.md",
    "mailbox_sync_duty": "runtime/mailboxes/synchronization_duty_latest.json",
    "mailbox_sync_duty_doc": "operations/mailboxes/synchronization_duty.md",
    "check_updates": "runtime/updates/check_updates_latest.json",
    "check_updates_doc": "operations/updates/check_updates_latest.md",
    "local_operational_validation": "runtime/validation/local_operational_validation_latest.json",
    "local_operational_validation_doc": "operations/validation/local_operational_validation_run.md",
    "daily_board": "operations/boards/daily_board.md",
    "daily_board_integration": "operations/boards/daily_board_integration.md",
    "parking_lot": "operations/boards/parking_lot.md",
    "recall_audit_log": "runtime/audit/recall_audit_log.json",
    "notification_router": "runtime/notifications/notification_router_report.json",
    "worker_runtime_monitor": "runtime/workers/worker_runtime_monitor.json",
    "worker_runtime_heartbeat": "runtime/workers/worker_runtime_heartbeat.json",
    "mission_registry": "data/registry/missions.json",
    "assignment_queue": "runtime/work_packages/assignment_queue.json",
    "autonomous_work_queue_scheduler": "operations/work_packages/autonomous_work_queue_scheduler.md",
    "mission_control_workspace": "runtime/steward/mission_control_workspace.json",
}

WORK_PACKAGE_DIRS = {
    "pending": "collaboration/work_packages/pending",
    "completed": "collaboration/work_packages/completed",
    "completions": "collaboration/work_packages/completions",
    "open": "collaboration/work_packages/open",
}


def estate_root(root: str | Path | None = None) -> Path:
    if root is not None:
        return Path(root)
    return ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _read_json(path: Path, warnings: list[dict[str, Any]]) -> Any | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        warnings.append({"type": "malformed_optional_input", "path": str(path), "message": str(exc)})
        return None


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _first_lines(text: str, limit: int = 5) -> list[str]:
    lines = [line.strip() for line in text.splitlines() if line.strip() and not line.strip().startswith("#")]
    return lines[:limit]


def _artifact(root: Path, key: str, warnings: list[dict[str, Any]]) -> dict[str, Any]:
    rel = OPTIONAL_ARTIFACTS[key]
    path = root / rel
    if not path.exists():
        warnings.append({"type": "missing_optional_artifact", "artifact": key, "path": rel})
        return {"present": False, "path": rel}
    data: Any = None
    if path.suffix == ".json":
        data = _read_json(path, warnings)
    else:
        data = _read_text(path)
    return {"present": True, "path": rel, "data": data}


def _list_files(root: Path, rel: str) -> list[Path]:
    path = root / rel
    if not path.exists():
        return []
    return sorted([item for item in path.iterdir() if item.is_file() and item.name != ".gitkeep"])


def _rel(root: Path, path: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def _completion_summary(path: Path, root: Path | None = None) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        data = {}
    return {
        "id": data.get("work_package_id") or path.stem.replace("_codex_done", ""),
        "status": data.get("codex_status") or data.get("status") or "completed",
        "summary": data.get("summary") or path.stem,
        "path": _rel(root, path) if root is not None else str(path),
    }


def _mission_status(mission_data: Any) -> dict[str, Any]:
    missions = mission_data.get("missions", []) if isinstance(mission_data, dict) else []
    counts: dict[str, int] = {}
    highlighted = []
    for mission in missions:
        if not isinstance(mission, dict):
            continue
        status = str(mission.get("status") or "unknown")
        counts[status] = counts.get(status, 0) + 1
        if status in {"active", "planned", "blocked", "at_risk", "warning"}:
            highlighted.append({
                "mission_id": mission.get("mission_id"),
                "title": mission.get("mission_title") or mission.get("title"),
                "status": status,
                "related_work_packages": mission.get("related_work_packages") or [],
                "notes": mission.get("notes"),
                "path": OPTIONAL_ARTIFACTS["mission_registry"],
            })
    return {"counts": counts, "highlighted": highlighted[:5]}


def _worker_runtime_summary(monitor: Any, heartbeat: Any) -> dict[str, Any]:
    source = monitor if isinstance(monitor, dict) else heartbeat if isinstance(heartbeat, dict) else {}
    summary = source.get("summary", {}) if isinstance(source, dict) else {}
    warnings = source.get("warnings", []) if isinstance(source, dict) else []
    workers = source.get("workers", []) if isinstance(source, dict) else []
    return {"summary": summary, "warnings": warnings[:5], "workers": workers[:5]}


def _work_packages(root: Path) -> dict[str, Any]:
    pending = _list_files(root, WORK_PACKAGE_DIRS["pending"])
    open_items = _list_files(root, WORK_PACKAGE_DIRS["open"])
    completions = _list_files(root, WORK_PACKAGE_DIRS["completions"])
    recent_completions = sorted(completions, key=lambda p: p.stat().st_mtime, reverse=True)[:5]
    return {
        "completed_work": [_completion_summary(path, root) for path in recent_completions],
        "pending_approvals": [{"id": p.stem.split("_")[0], "title": p.stem, "path": str(p.relative_to(root))} for p in pending[:10]],
        "failed_or_blocked_work": [{"id": p.stem.split("_")[0], "title": p.stem, "path": str(p.relative_to(root))} for p in open_items[:10]],
        "counts": {"pending": len(pending), "open": len(open_items), "completions": len(completions)},
    }


def _summary_counts(data: Any) -> dict[str, Any]:
    return data.get("summary", {}) if isinstance(data, dict) else {}


def generate_morning_briefing(root: str | Path | None = None, write: bool = True) -> dict[str, Any]:
    root = estate_root(root)
    warnings: list[dict[str, Any]] = []
    artifacts = {key: _artifact(root, key, warnings) for key in OPTIONAL_ARTIFACTS}
    work = _work_packages(root)

    mailbox_counts = _summary_counts(artifacts["mailbox_sync_duty"].get("data"))
    recall_counts = _summary_counts(artifacts["recall_audit_log"].get("data"))
    router_counts = _summary_counts(artifacts["notification_router"].get("data"))
    validation_counts = _summary_counts(artifacts["local_operational_validation"].get("data"))
    worker_runtime = _worker_runtime_summary(artifacts["worker_runtime_monitor"].get("data"), artifacts["worker_runtime_heartbeat"].get("data"))
    mission_status = _mission_status(artifacts["mission_registry"].get("data"))

    outstanding_recalls = []
    recall_data = artifacts["recall_audit_log"].get("data")
    if isinstance(recall_data, dict):
        outstanding_recalls = [r for r in recall_data.get("records", []) if r.get("acknowledgement_state") != "acknowledged"][:5]

    recommended = []
    if work["pending_approvals"]:
        recommended.append("Review pending work package approvals.")
    if outstanding_recalls:
        recommended.append("Review outstanding recall acknowledgements.")
    if validation_counts.get("failure_count") or validation_counts.get("error_count"):
        recommended.append("Review local operational validation failures before merging or launching additional work.")
    if worker_runtime.get("summary", {}).get("stale_worker_count") or worker_runtime.get("summary", {}).get("blocked_worker_count"):
        recommended.append("Review worker runtime warnings and blocked or stale workers.")
    if mission_status.get("highlighted"):
        recommended.append("Review highlighted mission status items against the mission registry.")
    if warnings:
        recommended.append("Regenerate or inspect missing optional operational artifacts.")
    if not recommended:
        recommended.append("Proceed with normal Estate operations.")

    briefing = {
        "version": 1,
        "generated_at": _now(),
        "non_authoritative": True,
        "sections": {
            "summary": {
                "completed_work_count": len(work["completed_work"]),
                "failed_or_blocked_work_count": len(work["failed_or_blocked_work"]),
                "pending_decision_count": len(work["pending_approvals"]),
                "outstanding_recall_count": len(outstanding_recalls),
                "warning_count": len(warnings),
                "source_artifact_count": len(artifacts),
            },
            "accomplishments": work["completed_work"],
            "completed_work": work["completed_work"],
            "failures": work["failed_or_blocked_work"],
            "failed_or_blocked_work": work["failed_or_blocked_work"],
            "pending_decisions": work["pending_approvals"],
            "pending_approvals": work["pending_approvals"],
            "outstanding_recalls": outstanding_recalls,
            "mailbox_summary": mailbox_counts,
            "board_changes": {
                "daily_board_present": artifacts["daily_board"].get("present"),
                "daily_board_integration_present": artifacts["daily_board_integration"].get("present"),
                "parking_lot_highlights": _first_lines(artifacts["parking_lot"].get("data") or "", 3),
            },
            "worker_runtime": worker_runtime,
            "mission_status": mission_status,
            "validation_warnings": {
                "local_validation_summary": validation_counts,
                "notification_router_summary": router_counts,
                "artifact_warnings": warnings[:10],
            },
            "recommended_next_actions": recommended[:5],
            "estimated_review_time": f"{max(3, min(15, 3 + len(work['pending_approvals']) + len(outstanding_recalls) + len(warnings) // 2))} minutes",
        },
        "source_artifacts": {key: {"present": value["present"], "path": value["path"]} for key, value in artifacts.items()},
        "warnings": warnings,
        "constraints": {"notifies_steward": False, "executes_work": False, "authoritative_record": False},
    }
    if write:
        _write_outputs(root, briefing)
    return briefing


def _write_outputs(root: Path, briefing: dict[str, Any]) -> None:
    json_path = root / JSON_OUTPUT
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(briefing, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path = root / MARKDOWN_OUTPUT
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(format_morning_briefing(briefing), encoding="utf-8")


def format_morning_briefing(briefing: dict[str, Any]) -> str:
    s = briefing.get("sections", {})
    lines = ["# Morning Briefing", "", f"Generated at: {briefing.get('generated_at')}", "", "Non-authoritative operational summary.", ""]
    lines += ["## Summary", f"- {s.get('summary') or {}}", ""]
    labels = [
        ("Accomplishments", "accomplishments"), ("Failures", "failures"),
        ("Pending decisions", "pending_decisions"), ("Outstanding recalls", "outstanding_recalls"),
    ]
    for title, key in labels:
        lines += [f"## {title}"]
        items = s.get(key) or []
        lines += [f"- {item.get('id') or item.get('record_id')}: {item.get('summary') or item.get('title') or item.get('recall_reason') or item.get('path')}" for item in items[:5]] or ["- None identified."]
        lines.append("")
    lines += ["## Mailbox summary", f"- {s.get('mailbox_summary') or 'No mailbox summary available.'}", ""]
    lines += ["## Board changes"] + [f"- {x}" for x in (s.get("board_changes", {}).get("parking_lot_highlights") or ["No board highlights available."])] + [""]
    lines += ["## Worker runtime", f"- {s.get('worker_runtime', {}).get('summary') or 'No worker runtime summary available.'}", ""]
    lines += ["## Mission status", f"- {s.get('mission_status', {}).get('counts') or 'No mission status available.'}", ""]
    lines += ["## Warnings"] + ([f"- {w.get('type')}: {w.get('path') or w.get('artifact')}" for w in s.get("validation_warnings", {}).get("artifact_warnings", [])] or ["- None identified."]) + [""]
    lines += ["## Recommended next actions"] + [f"- {x}" for x in s.get("recommended_next_actions", [])] + ["", f"Estimated review time: {s.get('estimated_review_time')}", ""]
    return "\n".join(lines)
