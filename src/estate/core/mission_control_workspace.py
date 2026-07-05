"""Local Mission Control workspace assembler.

Mission Control is an overview surface only: it reads existing Estate artifacts,
shows gaps explicitly, and never becomes the authority for records.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

from estate.core.paths import ESTATE_ROOT
from estate.core.capability_dependency_visualization import generate_capability_dependency_visualization
from estate.core.capability_gap_report import generate_capability_gap_report
from estate.core.validation_metrics_dashboard import generate_validation_metrics_dashboard

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
    "capability_dependencies": "runtime/capabilities/capability_dependency_visualization.json",
    "capability_gap_report": "runtime/capabilities/capability_gap_report.json",
}


def _root(root=None):
    return Path(root) if root is not None else ESTATE_ROOT


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _source(root, name, rel):
    path = root / rel
    if not path.exists() and name == "capability_gap_report":
        try:
            data = generate_capability_gap_report(root, write=False)
            return {"name": name, "path": rel, "available": True, "state": "ready", "summary": data.get("summary", {})}
        except Exception as exc:
            return {"name": name, "path": rel, "available": False, "state": "warning", "summary": f"Capability gap report could not be generated: {exc}"}
    if not path.exists() and name == "capability_dependencies":
        try:
            data = generate_capability_dependency_visualization(root, write=False)
            return {"name": name, "path": rel, "available": True, "state": "ready", "summary": data.get("summary", {})}
        except Exception as exc:
            return {"name": name, "path": rel, "available": False, "state": "warning", "summary": f"Capability dependency visualization could not be generated: {exc}"}
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



def _validation_integration(root):
    warnings = []
    metrics_path = root / "runtime" / "validation" / "validation_metrics_dashboard.json"
    latest_path = root / "runtime" / "validation" / "work_packages" / "latest.json"
    try:
        metrics = _read_json(metrics_path) if metrics_path.exists() else generate_validation_metrics_dashboard(root, write=True)
    except Exception as exc:
        metrics = {}
        warnings.append({"type": "validation_metrics_unavailable", "message": str(exc), "path": "runtime/validation/validation_metrics_dashboard.json"})
    try:
        latest = _read_json(latest_path) if latest_path.exists() else {}
    except Exception as exc:
        latest = {}
        warnings.append({"type": "latest_validation_unavailable", "message": str(exc), "path": "runtime/validation/work_packages/latest.json"})
    summary = metrics.get("summary") if isinstance(metrics.get("summary"), dict) else {}
    sources = metrics.get("sources") if isinstance(metrics.get("sources"), list) else []
    recent_activity = {
        "work_package_id": latest.get("work_package_id"),
        "validation_status": latest.get("validation_status"),
        "markdown_report": latest.get("markdown_report") or latest.get("latest_validation_report_path"),
        "json_report": latest.get("json_report"),
        "generated_at": latest.get("generated_at") or latest.get("validation_id"),
    } if latest else {"available": False}
    status = "unavailable" if not summary else ("blocked" if summary.get("fail_count") or summary.get("confirmed_defect_count") else ("watch" if summary.get("conditional_pass_count") or summary.get("open_observation_count") else "passing"))
    return {
        "status": status,
        "overall_validation_status": status,
        "open_observations_count": int(summary.get("open_observation_count") or 0),
        "confirmed_defects_count": int(summary.get("confirmed_defect_count") or 0),
        "conditional_pass_count": int(summary.get("conditional_pass_count") or 0),
        "fail_count": int(summary.get("fail_count") or 0),
        "most_recent_validation_activity": recent_activity,
        "artifact_links": [
            {"label": "Validation metrics dashboard", "path": "runtime/validation/validation_metrics_dashboard.json", "available": metrics_path.exists()},
            {"label": "Validation metrics dashboard markdown", "path": "operations/validation/validation_metrics_dashboard.md", "available": (root / "operations" / "validation" / "validation_metrics_dashboard.md").exists()},
            {"label": "Latest work-package validation pointer", "path": "runtime/validation/work_packages/latest.json", "available": latest_path.exists()},
        ] + [{"label": source.get("name"), "path": source.get("path"), "available": source.get("available")} for source in sources],
        "recommended_next_validation_action": "Review validation failures or confirmed defects before dependent work." if status == "blocked" else ("Review open observations and conditional passes." if status == "watch" else ("Generate validation metrics dashboard." if status == "unavailable" else "Continue normal validation cadence.")),
        "source_of_truth_boundary": "Mission Control displays validation health from existing source validation artifacts; validation artifacts remain authoritative.",
        "warnings": warnings + (metrics.get("warnings") if isinstance(metrics.get("warnings"), list) else []),
    }

def build_mission_control_workspace(root=None, write=True):
    """Build the Mission Control payload from local operational artifacts."""
    root = _root(root)
    generated_at = _now()
    sources = [_source(root, name, rel) for name, rel in MISSION_SOURCES.items()]
    validation_integration = _validation_integration(root)
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
                "validation_status": validation_integration.get("overall_validation_status"),
                "ready_source_count": len(ready),
                "missing_source_count": len(missing),
                "state": "ready" if not missing else "partial",
                "recommended_next_action": "Open source artifacts for decisions; regenerate missing runtime reports when needed.",
            },
            "lanes": [
                {"lane_id": "operations", "title": "Operations", "sources": ["command_center", "validation", "roadmap", "capability_dependencies", "capability_gap_report"]},
                {"lane_id": "work", "title": "Work Execution", "sources": ["work_packages", "worker_runtime", "worker_heartbeat"]},
                {"lane_id": "communications", "title": "Communications", "sources": ["mailboxes", "notifications", "decisions", "recalls"]},
            ],
            "validation_health": validation_integration,
            "sources": sources,
            "warnings": [{"source": source["name"], "message": source["summary"], "path": source["path"]} for source in missing],
        },
    }
    if write:
        out = root / "runtime" / "steward" / "mission_control_workspace.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload
