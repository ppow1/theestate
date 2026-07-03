"""Autonomous local work queue scheduler for Estate work packages.

The scheduler is deliberately local-first and advisory. It reads existing Estate
artifacts, classifies work packages into operational queues, and recommends a
next eligible package without launching workers or bypassing Steward approvals.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from estate.core.assignment_queue import generate_assignment_queue
from estate.core.paths import ESTATE_ROOT

SCHEDULER_JSON = "runtime/work_packages/autonomous_work_queue_scheduler.json"
SCHEDULER_MARKDOWN = "operations/work_packages/autonomous_work_queue_scheduler.md"
ACTIVITY_CONSOLE_JSON = "runtime/activity_console/work_queue_scheduler.json"


def estate_root(root: str | Path | None = None) -> Path:
    return Path(root) if root is not None else (ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd())


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _read_json(path: Path) -> tuple[Any | None, str | None]:
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except Exception as exc:
        return None, str(exc)


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _completed_ids(root: Path) -> set[str]:
    ids: set[str] = set()
    for path in (root / "collaboration" / "work_packages" / "completions").glob("*.json"):
        payload, _ = _read_json(path)
        if isinstance(payload, dict) and payload.get("codex_status", "done") == "done" and payload.get("work_package_id"):
            ids.add(str(payload["work_package_id"]))
    return ids


def _load_dependency_graph(root: Path, warnings: list[dict[str, Any]]) -> dict[str, list[str]]:
    path = root / "runtime" / "dependencies" / "dependency_graph.json"
    if not path.exists():
        warnings.append({"type": "missing_optional_artifact", "path": str(path.relative_to(root)), "message": "Dependency graph not available; scheduler will use dependencies parsed from work packages."})
        return {}
    payload, error = _read_json(path)
    if error or not isinstance(payload, dict):
        warnings.append({"type": "unreadable_optional_artifact", "path": str(path.relative_to(root)), "message": error or "Dependency graph is not an object."})
        return {}
    deps: dict[str, list[str]] = {}
    for edge in payload.get("edges", []):
        if isinstance(edge, dict) and edge.get("source") and edge.get("target"):
            deps.setdefault(str(edge["source"]), []).append(str(edge["target"]))
    return deps


def _load_workers(root: Path, warnings: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
    path = root / "runtime" / "workers" / "worker_runtime_heartbeat.json"
    if not path.exists():
        warnings.append({"type": "missing_optional_artifact", "path": str(path.relative_to(root)), "message": "Worker runtime summary not available; scheduler will not assume worker availability."})
        return [], 0
    payload, error = _read_json(path)
    if error or not isinstance(payload, dict):
        warnings.append({"type": "unreadable_optional_artifact", "path": str(path.relative_to(root)), "message": error or "Worker runtime summary is not an object."})
        return [], 0
    workers = [w for w in payload.get("workers", []) if isinstance(w, dict)]
    available = [w for w in workers if w.get("status") == "idle" and not w.get("stale")]
    if not available:
        warnings.append({"type": "no_available_workers", "path": str(path.relative_to(root)), "message": "No fresh idle worker heartbeat found; recommendation remains advisory only."})
    return workers, len(available)


def _with_dependency_state(item: dict[str, Any], deps: list[str], completed: set[str]) -> dict[str, Any]:
    missing = [dep for dep in deps if dep.startswith("WP-") and dep not in completed]
    enriched = dict(item)
    enriched["dependencies"] = deps
    enriched["unmet_dependencies"] = missing
    return enriched


def generate_autonomous_work_queue_scheduler(root: str | Path | None = None, write: bool = True) -> dict[str, Any]:
    """Classify local work packages and recommend the next eligible package."""
    root_path = estate_root(root)
    generated_at = _now()
    warnings: list[dict[str, Any]] = []
    assignment = generate_assignment_queue(root_path, write=False)
    completed = _completed_ids(root_path)
    graph_deps = _load_dependency_graph(root_path, warnings)
    workers, available_worker_count = _load_workers(root_path, warnings)

    queues = {"ready": [], "waiting": [], "blocked": [], "running": [], "review": []}
    for item in assignment.get("work_packages", []):
        wp_id = item.get("work_package_id")
        deps = list(dict.fromkeys([*item.get("dependencies", []), *graph_deps.get(str(wp_id), [])]))
        enriched = _with_dependency_state(item, deps, completed)
        state = str(item.get("state", "")).lower()
        if state in {"claimed", "running", "in_progress", "in progress"}:
            queues["running"].append(enriched)
        elif state in {"completed", "done"} or wp_id in completed:
            queues["review"].append(enriched)
        elif item.get("blockers") or state == "blocked":
            queues["blocked"].append(enriched)
        elif enriched["unmet_dependencies"]:
            queues["waiting"].append(enriched)
        else:
            queues["ready"].append(enriched)

    recommended = queues["ready"][0] if queues["ready"] else None
    all_warnings = warnings + assignment.get("warnings", [])
    payload = {
        "version": 1,
        "generated_at": generated_at,
        "local_first": True,
        "authority_boundary": "advisory_only_never_launches_codex_or_bypasses_steward_approvals",
        "worker_availability": {"worker_count": len(workers), "available_worker_count": available_worker_count},
        "summary": {key + "_count": len(value) for key, value in queues.items()} | {"warning_count": len(all_warnings), "recommended_next_work_package": recommended.get("work_package_id") if recommended else None},
        "recommended_next_work_package": recommended,
        "queues": queues,
        "warnings": all_warnings,
    }
    if write:
        _write_json(root_path / SCHEDULER_JSON, payload)
        md_path = root_path / SCHEDULER_MARKDOWN
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text(format_autonomous_work_queue_scheduler(payload), encoding="utf-8")
        _write_json(root_path / ACTIVITY_CONSOLE_JSON, {"kind": "activity_console_event", "source": "autonomous_work_queue_scheduler", "generated_at": generated_at, "summary": payload["summary"], "recommended_next_work_package": payload["summary"]["recommended_next_work_package"]})
    return payload


def format_autonomous_work_queue_scheduler(payload: dict[str, Any]) -> str:
    lines = [
        "# Autonomous Work Queue Scheduler",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        "This scheduler is advisory, local-first, and never launches Codex or bypasses Steward approvals.",
        "",
        "## Summary",
    ]
    for key in ["ready_count", "waiting_count", "blocked_count", "running_count", "review_count", "warning_count"]:
        lines.append(f"- {key.replace('_', ' ').title()}: {payload['summary'].get(key, 0)}")
    lines.append(f"- Recommended next work package: {payload['summary'].get('recommended_next_work_package') or 'None'}")
    for queue_name, items in payload.get("queues", {}).items():
        lines += ["", f"## {queue_name.title()} Queue"]
        if not items:
            lines.append("- None")
        for item in items:
            unmet = f"; unmet dependencies: {', '.join(item.get('unmet_dependencies', []))}" if item.get("unmet_dependencies") else ""
            lines.append(f"- {item.get('work_package_id')} — {item.get('path')} (state: {item.get('state')}{unmet})")
    if payload.get("warnings"):
        lines += ["", "## Warnings"]
        for warning in payload["warnings"]:
            lines.append(f"- {warning.get('type')}: {warning.get('message')} ({warning.get('path', 'n/a')})")
    return "\n".join(lines) + "\n"
