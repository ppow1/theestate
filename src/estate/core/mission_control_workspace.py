"""Local Mission Control workspace assembler.

Mission Control is an overview surface only: it reads existing Estate artifacts,
shows gaps explicitly, and never becomes the authority for records.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

from estate.core.paths import ESTATE_ROOT

MISSION_SOURCES = {
    "command_center": "runtime/steward/command_center.html",
    "work_packages": "runtime/work_packages/assignment_queue.json",
    "worker_runtime": "runtime/workers/worker_runtime_monitor.json",
    "worker_heartbeat": "runtime/workers/worker_runtime_heartbeat.json",
    "validation": "runtime/validation/local_operational_validation_run.json",
    "mailboxes": "runtime/mailboxes/synchronization_duty.json",
    "decisions": "operations/steward/decision_queue.md",
    "recalls": "runtime/audit/recall_audit_log.json",
    "notifications": "runtime/notifications/notification_center_workspace.json",
    "roadmap": "operations/boards/roadmap.md",
}


def _root(root=None):
    return Path(root) if root is not None else ESTATE_ROOT


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _source(root, name, rel):
    path = root / rel
    if not path.exists():
        return {"name": name, "path": rel, "available": False, "state": "missing", "summary": "Supporting artifact is not available yet."}
    try:
        if path.suffix == ".json":
            data = _read_json(path)
            summary = data.get("summary") if isinstance(data, dict) else None
            keys = sorted(data.keys()) if isinstance(data, dict) else []
            return {"name": name, "path": rel, "available": True, "state": "ready", "summary": summary or {"keys": keys[:8]}}
        text = path.read_text(encoding="utf-8")
        first_heading = next((line.lstrip("# ").strip() for line in text.splitlines() if line.startswith("#")), path.name)
        return {"name": name, "path": rel, "available": True, "state": "ready", "summary": {"title": first_heading}}
    except Exception as exc:
        return {"name": name, "path": rel, "available": False, "state": "warning", "summary": f"Artifact exists but could not be read: {exc}"}


def build_mission_control_workspace(root=None, write=True):
    """Build the Mission Control payload from local operational artifacts."""
    root = _root(root)
    generated_at = _now()
    sources = [_source(root, name, rel) for name, rel in MISSION_SOURCES.items()]
    missing = [source for source in sources if not source["available"]]
    ready = [source for source in sources if source["available"]]
    payload = {
        "available": True,
        "path": "runtime/steward/mission_control_workspace.json",
        "kind": "mission_control_workspace",
        "data": {
            "version": 1,
            "workspace_id": "mission_control_workspace",
            "generated_at": generated_at,
            "local_only": True,
            "authority_boundary": "read_only_overview",
            "source_of_truth_boundary": "Mission Control summarizes existing Estate artifacts and does not replace their source files.",
            "degrades_gracefully": True,
            "summary": {
                "source_count": len(sources),
                "ready_source_count": len(ready),
                "missing_source_count": len(missing),
                "state": "ready" if not missing else "partial",
                "recommended_next_action": "Open source artifacts for decisions; regenerate missing runtime reports when needed.",
            },
            "lanes": [
                {"lane_id": "operations", "title": "Operations", "sources": ["command_center", "validation", "roadmap"]},
                {"lane_id": "work", "title": "Work Execution", "sources": ["work_packages", "worker_runtime", "worker_heartbeat"]},
                {"lane_id": "communications", "title": "Communications", "sources": ["mailboxes", "notifications", "decisions", "recalls"]},
            ],
            "sources": sources,
            "warnings": [{"source": source["name"], "message": source["summary"], "path": source["path"]} for source in missing],
        },
    }
    if write:
        out = root / "runtime" / "steward" / "mission_control_workspace.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload
