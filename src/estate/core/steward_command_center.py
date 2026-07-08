"""Local Office of the Steward command center web surface.

This module builds a lightweight, local-first HTML dashboard from existing
Estate artifacts. It intentionally avoids authentication, cloud services, and
new business logic; missing support artifacts become visible placeholders.
"""

import html
import json
import re
from datetime import datetime, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from estate.core.paths import ESTATE_ROOT
from estate.core.resident_cards import build_resident_cards
from estate.core.resident_conversations import build_resident_conversations_workspace
from estate.core.decision_queue import generate_decision_queue
from estate.core.assignment_queue import generate_assignment_queue
from estate.core.mailbox_index import generate_mailbox_index
from estate.core.global_search_command_palette import build_global_palette
from estate.core.mission_control_workspace import build_mission_control_workspace
from estate.core.steward_presence import generate_steward_presence_state
from estate.core.capability_dependency_visualization import generate_capability_dependency_visualization
from estate.core.operator_activity_stream import generate_operator_activity_stream
from estate.core.operations_notification_center import generate_operations_notification_center
from estate.core.office_operational_activity import load_office_operational_activity
from estate.core.orchestrator_intake_decisions import load_office_intake_decision_surface
from estate.core.estate_service_catalog import COMMAND_SURFACES, generate_estate_service_catalog
from estate.core.operations_center_workspace_profiles import resolve_workspace_profile, PROFILES_OUTPUT as WORKSPACE_PROFILES_OUTPUT
from estate.core.operations_center_settings import load_operations_center_settings, SETTINGS_OUTPUT
from estate.core.resident_interaction import resident_surface, process_chat, load_history, forget_conversation, alfred_llm_diagnostic
from estate.ai_services.steward_model_selector import build_steward_ai_services_panel
from estate.core.office_command_surface import controls_for_tab, execute_office_action
from urllib.parse import urlparse


OFFICE_NAVIGATION = [
    {"id": "home", "label": "Home", "panel": "home", "tab": "home"},
    {"id": "mission-control", "label": "Mission Control", "panel": "mission_control_workspace", "tab": "mission-control"},
    {"id": "alfred", "label": "Alfred", "panel": "alfred_resident_card", "tab": "alfred"},
    {"id": "helen", "label": "Helen", "panel": "helen_resident_card", "tab": "helen"},
    {"id": "resident-conversations", "label": "Resident Conversations", "panel": "resident_conversations_workspace", "tab": "resident-conversations"},
    {"id": "ai-services-models", "label": "AI Services / Models", "panel": "ai_services_models", "tab": "ai-services-models"},
    {"id": "daily-board", "label": "Daily Board", "panel": "morning_briefing", "tab": "daily-board"},
    {"id": "operational-activity", "label": "Operational Activity", "panel": "operational_activity", "tab": "operational-activity"},
    {"id": "active-projects", "label": "Active Projects", "panel": "work_package_pipeline", "tab": "projects"},
    {"id": "expansion-roadmap", "label": "Expansion Roadmap", "panel": "expansion_roadmap", "tab": "roadmap"},
    {"id": "parking-lot", "label": "Parking Lot", "panel": "parking_lot", "tab": "parking"},
    {"id": "work-packages", "label": "Work Packages", "panel": "work_package_pipeline", "tab": "work-packages"},
    {"id": "mailboxes", "label": "Mailboxes", "panel": "mailbox_operations_center", "tab": "mailboxes"},
    {"id": "recalls", "label": "Recalls", "panel": "steward_recall_operations", "tab": "recalls"},
    {"id": "notifications", "label": "Notifications", "panel": "operations_notification_center", "tab": "notifications"},
    {"id": "validation", "label": "Validation", "panel": "validation_health_dashboard", "tab": "validation"},
    {"id": "search", "label": "Search", "panel": "search", "tab": "search"},
    {"id": "settings", "label": "Settings", "panel": "settings", "tab": "settings"},
    {"id": "help", "label": "Help", "panel": "help", "tab": "help"},
    {"id": "about", "label": "About", "panel": "about", "tab": "about"},
]

OFFICE_TABS = [
    {"id": "home", "label": "Home"},
    {"id": "mission-control", "label": "Mission Control"},
    {"id": "alfred", "label": "Alfred"},
    {"id": "helen", "label": "Helen"},
    {"id": "resident-conversations", "label": "Resident Conversations"},
    {"id": "ai-services-models", "label": "AI Services / Models"},
    {"id": "daily-board", "label": "Daily Board"},
    {"id": "operational-activity", "label": "Operational Activity"},
    {"id": "projects", "label": "Projects"},
    {"id": "roadmap", "label": "Roadmap"},
    {"id": "parking", "label": "Parking Lot"},
    {"id": "work-packages", "label": "Work Packages"},
    {"id": "mailboxes", "label": "Mailboxes"},
    {"id": "recalls", "label": "Recalls"},
    {"id": "notifications", "label": "Notifications"},
    {"id": "validation", "label": "Validation"},
    {"id": "search", "label": "Search"},
    {"id": "settings", "label": "Settings"},
    {"id": "help", "label": "Help"},
    {"id": "about", "label": "About"},
]

ARTIFACTS = {
    "morning_briefing": ["runtime/operations/morning_briefing.json", "operations/briefings/morning_briefing.md"],
    "mailbox_summary": ["runtime/collaboration/mailbox_index.json", "collaboration/mailboxes/index.json"],
    "work_package_pipeline": ["runtime/work_packages/assignment_queue.json", "operations/work_packages/assignment_queue.md"],
    "validation_status": ["runtime/validation/local_operational_validation_run.json", "operations/validation/local_operational_validation_run.md", "runtime/audit/latest.json"],
    "capability_lifecycle": ["runtime/capabilities/capability_lifecycle_report.json", "operations/capabilities/capability_lifecycle_report.md"],
    "capability_dependency_visualization": ["runtime/capabilities/capability_dependency_visualization.json", "operations/capabilities/capability_dependency_visualization.md"],
    "dependency_graph": ["runtime/dependencies/dependency_graph.json", "operations/dependencies/dependency_graph.md"],
    "mailbox_sync": ["runtime/mailboxes/synchronization_duty_latest.json", "operations/mailboxes/synchronization_duty.md", "collaboration/status/worker_inbox_summary.json"],
    "check_updates": ["runtime/updates/check_updates_latest.json", "operations/updates/check_updates_latest.md"],
    "worker_inbox_summary": ["collaboration/status/worker_inbox_summary.json"],
    "recall_audit": ["runtime/audit/recall_audit_log.json", "operations/audit/recall_audit_log_summary.md"],
    "notification_router": ["runtime/notifications/notification_router_report.json"],
    "gotify_delivery": ["runtime/notifications/gotify_delivery_report.json"],
    "notification_center": ["runtime/notifications/notification_center_workspace.json", "operations/notifications/notification_center_workspace.md"],
    "recall_decision_model": ["docs/operations/Steward_Recall_Decision_Model_v1.md", "data/policy/steward_recall_reasons.json"],
    "worker_heartbeat": ["runtime/workers/worker_runtime_heartbeat.json", "runtime/workers/heartbeat.json", "operations/workers/runtime_heartbeat.md"],
    "worker_runtime_monitor": ["runtime/workers/worker_runtime_monitor.json", "operations/workers/worker_runtime_monitor.md"],
    "steward_presence": ["runtime/steward/steward_presence_state.json", "operations/steward/steward_presence_state.md"],
    "execution_activity": ["runtime/execution_activity/current.json", "runtime/execution_activity/report.md"],
}


def _root(root=None):
    if root is not None:
        return Path(root)
    if ESTATE_ROOT.exists():
        return ESTATE_ROOT
    return Path.cwd()


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _rel(path, root):
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def _read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _read_artifact(root, candidates):
    for rel in candidates:
        path = root / rel
        if not path.exists():
            continue
        try:
            if path.suffix == ".json":
                return {"available": True, "path": rel, "kind": "json", "data": _read_json(path)}
            return {"available": True, "path": rel, "kind": "text", "text": path.read_text(encoding="utf-8")}
        except Exception as exc:
            return {"available": False, "path": rel, "placeholder": f"Artifact exists but could not be read: {exc}"}
    return {"available": False, "path": None, "placeholder": "Supporting artifact is not available yet."}


def _summarize_json(data):
    if not isinstance(data, dict):
        return str(data)[:500]
    for key in ("summary", "status", "report", "metadata"):
        if key in data:
            return json.dumps(data[key], indent=2, sort_keys=True)[:1000]
    keys = ", ".join(sorted(str(k) for k in data.keys())[:12])
    return f"Available JSON artifact with keys: {keys}"



def _count_mailboxes(root):
    artifact = _read_artifact(root, ARTIFACTS["mailbox_summary"])
    if not artifact.get("available"):
        return None
    data = artifact.get("data") or {}
    summary = data.get("summary") if isinstance(data, dict) else None
    if isinstance(summary, dict):
        for key in ("mailbox_count", "mailboxes", "message_count", "total_messages"):
            value = summary.get(key)
            if isinstance(value, int):
                return value
    if isinstance(data, dict) and isinstance(data.get("mailboxes"), list):
        return len(data["mailboxes"])
    return None


def _mailbox_label_maps(root):
    personnel = _read_artifact(root, ["data/registry/personnel.json"])
    mailboxes = _read_artifact(root, ["data/registry/mailboxes.json"])
    labels = {}
    kinds = {}
    if personnel.get("available") and isinstance(personnel.get("data"), list):
        for person in personnel["data"]:
            mailbox_id = person.get("mailbox_id")
            if mailbox_id is not None:
                labels[int(mailbox_id)] = person.get("display_name") or person.get("current_title") or f"mailbox.{mailbox_id}"
                kinds[int(mailbox_id)] = "resident/worker"
    if mailboxes.get("available") and isinstance(mailboxes.get("data"), list):
        for box in mailboxes["data"]:
            mailbox_id = box.get("mailbox_id")
            if mailbox_id is not None:
                labels.setdefault(int(mailbox_id), box.get("display_name") or f"mailbox.{mailbox_id}")
                kinds[int(mailbox_id)] = box.get("mailbox_type") or "office"
    return labels, kinds


def _is_open_message(message):
    status = str(message.get("status") or "open").lower()
    ack = str(message.get("ack_status") or "").lower()
    return status not in {"closed", "done", "archived"} and ack not in {"acknowledged", "resolved"}


def _message_summary(message):
    return {
        "message_id": message.get("message_id") or message.get("id") or "unknown",
        "title": message.get("title") or ((message.get("payload") or {}).get("title") if isinstance(message.get("payload"), dict) else None) or "Untitled message",
        "path": message.get("path") or message.get("source_path"),
        "created_at": message.get("created_at"),
        "status": message.get("status") or "open",
        "requires_ack": bool(message.get("requires_ack")),
        "ack_status": message.get("ack_status"),
        "priority": message.get("priority") or "normal",
        "source": message.get("source") or message.get("created_by"),
        "destination": message.get("destination") or (f"mailbox.{message.get('destination_mailbox_id')}" if message.get("destination_mailbox_id") is not None else "unresolved"),
        "warning": message.get("warning"),
    }


def _mailbox_operations_center_artifact(root):
    index_artifact = _read_artifact(root, ARTIFACTS["mailbox_summary"])
    sync_artifact = _read_artifact(root, ARTIFACTS["mailbox_sync"])
    updates_artifact = _read_artifact(root, ARTIFACTS["check_updates"])
    worker_artifact = _read_artifact(root, ARTIFACTS["worker_inbox_summary"])
    labels, kinds = _mailbox_label_maps(root)
    messages = []
    warnings = []
    communication_bus_used = False
    if index_artifact.get("available") and isinstance(index_artifact.get("data"), dict):
        messages = index_artifact["data"].get("messages") or []
    elif (root / "collaboration" / "messages").exists():
        try:
            generated_index = generate_mailbox_index(root=root, write=False)
            messages = generated_index.get("messages") or []
            communication_bus_used = True
        except Exception as exc:
            for path in sorted((root / "collaboration" / "messages").glob("*.json")):
                try:
                    item = _read_json(path)
                    if isinstance(item, dict):
                        item = dict(item)
                        item.setdefault("path", _rel(path, root))
                        messages.append(item)
                except Exception as message_exc:
                    messages.append({"title": path.stem, "path": _rel(path, root), "warning": f"malformed message: {message_exc}"})
            communication_bus_used = bool(messages)
            warnings.append({"title": "Communication Bus resolver warning", "warning": f"Mailbox resolver unavailable; showing raw Communication Bus summaries: {exc}", "path": "collaboration/messages/*.json"})
    by_mailbox = {}
    open_messages = []
    ack_required = []
    steward_waiting = []
    for message in messages:
        if not isinstance(message, dict):
            continue
        mailbox_id = message.get("destination_mailbox_id")
        if mailbox_id is None:
            key = "unresolved"
            label = "Unresolved destination"
            kind = "warning"
        else:
            key = str(mailbox_id)
            label = labels.get(int(mailbox_id), f"mailbox.{mailbox_id}")
            kind = kinds.get(int(mailbox_id), "mailbox")
        bucket = by_mailbox.setdefault(key, {"mailbox_id": mailbox_id, "label": label, "kind": kind, "message_count": 0, "open_count": 0, "ack_required_count": 0, "waiting_on_steward_count": 0, "messages": []})
        summary = _message_summary(message)
        bucket["message_count"] += 1
        bucket["messages"].append(summary)
        if _is_open_message(message):
            bucket["open_count"] += 1
            open_messages.append(summary)
        if message.get("requires_ack") and str(message.get("ack_status") or "pending").lower() not in {"acknowledged", "resolved"}:
            bucket["ack_required_count"] += 1
            ack_required.append(summary)
        destination_text = str(message.get("destination") or "").lower()
        if mailbox_id == 1 or "steward" in destination_text or "founder" in destination_text:
            bucket["waiting_on_steward_count"] += 1
            steward_waiting.append(summary)
        if message.get("warning") or mailbox_id is None:
            warnings.append(summary)
    sync_data = sync_artifact.get("data") if isinstance(sync_artifact.get("data"), dict) else {}
    sync_summary = sync_data.get("summary") if isinstance(sync_data.get("summary"), dict) else {}
    last_sync = sync_data.get("generated_at") or sync_summary.get("last_sync_time") or sync_summary.get("last_mailbox_synchronization_time") or (_artifact_mtime(root, sync_artifact.get("path")).isoformat(timespec="seconds") if _artifact_mtime(root, sync_artifact.get("path")) else None)
    data = {
        "summary": {
            "message_count": len(messages),
            "open_message_count": len(open_messages),
            "ack_required_count": len(ack_required),
            "waiting_on_steward_count": len(steward_waiting),
            "warning_count": len(warnings),
            "mailbox_count": len(by_mailbox),
            "last_mailbox_synchronization_time": last_sync,
        },
        "by_mailbox": sorted(by_mailbox.values(), key=lambda item: (str(item.get("kind")), str(item.get("label")))),
        "open_messages": open_messages,
        "ack_required_messages": ack_required,
        "steward_waiting_messages": steward_waiting,
        "destination_warnings": warnings,
        "sources": {
            "mailbox_index": index_artifact.get("path"),
            "mailbox_synchronization": sync_artifact.get("path"),
            "check_updates": updates_artifact.get("path"),
            "communication_bus": "collaboration/messages/*.json" if communication_bus_used else "collaboration/messages/*.json",
            "worker_inbox_summary": worker_artifact.get("path"),
            "personnel_registry": "data/registry/personnel.json",
            "mailbox_registry": "data/registry/mailboxes.json",
        },
        "missing_sources": [name for name, artifact in {"mailbox_index": index_artifact, "mailbox_synchronization": sync_artifact, "check_updates": updates_artifact, "worker_inbox_summary": worker_artifact}.items() if not artifact.get("available")],
    }
    available = bool(index_artifact.get("available") or communication_bus_used)
    return {"available": available, "path": index_artifact.get("path") or ("collaboration/messages/*.json" if communication_bus_used else "collaboration/mailboxes/index.json"), "kind": "mailbox_operations_center", "data": data, "placeholder": index_artifact.get("placeholder")}


def _pending_decision_count(decision_artifact):
    if not decision_artifact.get("available"):
        return None
    decisions = (decision_artifact.get("data") or {}).get("decisions") or []
    return len(decisions)


def _validation_label(validation_artifact):
    if not validation_artifact.get("available"):
        return "Validation unavailable"
    data = validation_artifact.get("data") or {}
    if isinstance(data, dict):
        summary = data.get("summary") if isinstance(data.get("summary"), dict) else {}
        failed = summary.get("failed")
        if failed == 0:
            return "Validation passing"
        if isinstance(failed, int):
            return f"Validation has {failed} failure(s)"
        for key in ("status", "result", "state"):
            if data.get(key):
                return str(data[key])
    return "Validation artifact present"


def _artifact_link(rel):
    if not rel:
        return "not yet produced"
    return f'<a href="{html.escape(str(rel))}">{html.escape(str(rel))}</a>'


def _artifact_mtime(root, rel):
    if not rel:
        return None
    path = root / rel
    if not path.exists():
        return None
    return datetime.fromtimestamp(path.stat().st_mtime, timezone.utc)


def _warning_text(item):
    if isinstance(item, dict):
        return item.get("message") or item.get("type") or json.dumps(item, sort_keys=True)
    return str(item)


def _artifact_health(root, key, label, *, stale_after_hours=48):
    artifact = _read_artifact(root, ARTIFACTS[key])
    state = "pass"
    warnings = []
    failures = []
    blocked = []
    if not artifact.get("available"):
        state = "missing"
        warnings.append(artifact.get("placeholder") or "Artifact is not available yet.")
    data = artifact.get("data") if isinstance(artifact.get("data"), dict) else {}
    if data:
        summary = data.get("summary") if isinstance(data.get("summary"), dict) else {}
        raw_warnings = data.get("warnings") or []
        warnings.extend(_warning_text(w) for w in raw_warnings[:6])
        failed = summary.get("failed_steps", summary.get("failed", 0))
        if failed:
            state = "fail"
            failures.append(f"{failed} failure(s) reported.")
        if summary.get("ok") is False:
            state = "fail"
            failures.append("Summary reports ok=false.")
        stale_workers = summary.get("stale_worker_count", 0)
        if stale_workers:
            state = "warning" if state != "fail" else state
            warnings.append(f"{stale_workers} stale worker heartbeat record(s).")
        status_counts = summary.get("status_counts") if isinstance(summary.get("status_counts"), dict) else {}
        if status_counts.get("blocked"):
            state = "warning" if state != "fail" else state
            blocked.append(f"{status_counts.get('blocked')} worker(s) blocked.")
        if summary.get("warning_count") and state == "pass":
            state = "warning"
    mtime = _artifact_mtime(root, artifact.get("path"))
    if mtime and (datetime.now(timezone.utc) - mtime).total_seconds() > stale_after_hours * 3600:
        if state == "pass":
            state = "warning"
        warnings.append(f"Artifact may be stale; last modified {mtime.isoformat(timespec='seconds')}.")
    return {
        "label": label,
        "state": state,
        "path": artifact.get("path"),
        "last_modified": mtime.isoformat(timespec="seconds") if mtime else None,
        "warnings": warnings,
        "failures": failures,
        "blocked": blocked,
    }


def _build_validation_health_dashboard(root):
    checks = [
        _artifact_health(root, "validation_status", "Local operational validation"),
        _artifact_health(root, "capability_lifecycle", "Capability lifecycle report"),
        _artifact_health(root, "dependency_graph", "Dependency graph report"),
        _artifact_health(root, "mailbox_sync", "Mailbox synchronization report"),
        _artifact_health(root, "recall_audit", "Recall audit report"),
        _artifact_health(root, "worker_heartbeat", "Worker heartbeat report", stale_after_hours=2),
        _artifact_health(root, "worker_runtime_monitor", "Worker runtime monitor", stale_after_hours=2),
    ]
    completions = _completion_records(root)
    reviews = _review_records(root)
    if not completions:
        checks.append({"label": "Work package completion records", "state": "missing", "path": "collaboration/work_packages/completions", "last_modified": None, "warnings": ["No completion records found."], "failures": [], "blocked": []})
    else:
        unreviewed = [wp for wp, record in completions.items() if record.get("ready_for_ca_review") and not reviews.get(wp)]
        checks.append({"label": "Work package completion/review records", "state": "warning" if unreviewed else "pass", "path": "collaboration/work_packages/completions", "last_modified": None, "warnings": [f"{len(unreviewed)} completion(s) ready for CA review without review record."] if unreviewed else [], "failures": [], "blocked": []})
    states = [c["state"] for c in checks]
    overall = "fail" if "fail" in states else ("warning" if any(s in states for s in ("warning", "missing")) else "pass")
    last_success = None
    for check in checks:
        if check["label"] == "Local operational validation" and check["state"] == "pass":
            last_success = check.get("last_modified")
    if overall == "pass":
        action = "Continue normal operations; no validation action is currently required."
    elif "fail" in states:
        action = "Review failing validation source reports before proceeding with dependent work."
    else:
        action = "Refresh stale or missing local artifacts, then rerun local operational validation."
    return {
        "available": True,
        "path": "runtime/steward/command_center.html",
        "kind": "validation_health",
        "data": {
            "overall_health": overall,
            "last_successful_validation_time": last_success,
            "recommended_next_action": action,
            "checks": checks,
            "current_warnings": [w for c in checks for w in c.get("warnings", [])],
            "blocked_subsystems": [b for c in checks for b in c.get("blocked", [])],
        },
    }


def _active_worker_count(root):
    artifact = _read_artifact(root, ["runtime/workers/worker_runtime_monitor.json", "runtime/workers/worker_runtime_heartbeat.json", "runtime/workers/heartbeat.json", "operations/workers/runtime_heartbeat.md"])
    if artifact.get("kind") == "json":
        data = artifact.get("data") or {}
        summary = data.get("summary") if isinstance(data, dict) else None
        if isinstance(summary, dict) and isinstance(summary.get("active_worker_count"), int):
            return summary.get("active_worker_count")
        workers = data.get("workers") if isinstance(data, dict) else None
        if isinstance(workers, list):
            return sum(1 for worker in workers if str(worker.get("status", "")).lower() == "active")
    if artifact.get("available") and artifact.get("kind") == "text":
        text = artifact.get("text") or ""
        return text.lower().count(": active")
    return None


def _build_status_bar(root, panels, generated_at):
    validation = panels.get("validation_status", {})
    pending = _pending_decision_count(panels.get("steward_decision_queue", {}))
    mailbox_count = _count_mailboxes(root)
    mailbox_ops_summary = (((panels.get("mailbox_operations_center") or {}).get("data") or {}).get("summary") or {})
    recall_ops_summary = (((panels.get("steward_recall_operations") or {}).get("data") or {}).get("summary") or {})
    notification_summary = (((panels.get("operations_notification_center") or {}).get("data") or {}).get("summary") or {})
    execution_summary = (((panels.get("execution_activity") or {}).get("data") or {}).get("summary") or {})
    active_workers = _active_worker_count(root)
    steward_presence = (((panels.get("steward_presence") or {}).get("data") or {}).get("summary") or {})
    missing = sum(1 for value in panels.values() if isinstance(value, dict) and not value.get("available"))
    health = ((panels.get("validation_health_dashboard") or {}).get("data") or {})
    health_state = health.get("overall_health")
    estate_status = "Needs data" if missing else ({"pass": "Nominal", "warning": "Warnings", "fail": "Failing", "missing": "Needs data"}.get(health_state) or "Nominal")
    return {
        "estate_status": estate_status,
        "last_refresh_time": generated_at,
        "validation_state": _validation_label(validation),
        "pending_decisions": pending,
        "mailbox_count": mailbox_count,
        "mailbox_open_count": mailbox_ops_summary.get("open_message_count"),
        "mailbox_ack_required_count": mailbox_ops_summary.get("ack_required_count"),
        "mailbox_warning_count": mailbox_ops_summary.get("warning_count"),
        "active_recall_count": recall_ops_summary.get("active_recall_count"),
        "notification_count": notification_summary.get("filtered_notification_count"),
        "notification_unavailable_source_count": notification_summary.get("unavailable_source_count"),
        "execution_active_count": execution_summary.get("active_count"),
        "execution_blocked_count": execution_summary.get("blocked_count"),
        "execution_attention_required_count": execution_summary.get("attention_required_count"),
        "execution_failed_count": execution_summary.get("failed_count"),
        "active_workers": active_workers,
        "steward_presence_state": steward_presence.get("state"),
        "version": "Operations Center v1 / Status Console v1",
        "verbosity": "normal",
        "missing_sources": missing,
        "health_state": health_state,
        "recommended_next_action": health.get("recommended_next_action"),
    }


def _event(ts, source, topic, severity, message):
    return {"timestamp": ts or "unknown", "source": source, "topic": topic, "severity": severity, "message": message}


def _build_activity_console(root, panels, generated_at):
    stream = generate_operator_activity_stream(root=root, write=False, verbosity="normal", limit=25)
    events = [_event(generated_at, "steward.command_center", "refresh", "info", "Operations Center data refreshed quietly from local artifacts.")]
    events.extend({"timestamp": e.get("timestamp"), "source": e.get("source"), "topic": e.get("topic"), "severity": e.get("severity"), "message": e.get("message"), "link": e.get("link")} for e in stream.get("events", []))
    execution_summary = (((panels.get("execution_activity") or {}).get("data") or {}).get("summary") or {})
    if execution_summary:
        severity = "warning" if execution_summary.get("attention_required_count") or execution_summary.get("blocked_count") or execution_summary.get("failed_count") else "info"
        events.append(_event(
            generated_at,
            "execution_activity",
            "current",
            severity,
            f"Execution activity: active={execution_summary.get('active_count', 0)}, blocked={execution_summary.get('blocked_count', 0)}, attention={execution_summary.get('attention_required_count', 0)}, failed={execution_summary.get('failed_count', 0)}.",
        ))
    if len(events) == 1:
        events.append(_event(generated_at, "local artifacts", "empty", "info", stream.get("empty_state") or "No recent operational activity records were found."))
    return {"collapsed_by_default": True, "verbosity_options": stream.get("verbosity_levels", ["quiet", "normal", "detailed", "diagnostic"]), "selected_verbosity": stream.get("selected_verbosity", "normal"), "filters": stream.get("filters", {}), "available_sources": stream.get("available_sources", []), "events": events[:25]}


def _completion_records(root):
    records = {}
    completion_dir = root / "collaboration" / "work_packages" / "completions"
    if not completion_dir.exists():
        return records
    for path in sorted(completion_dir.glob("*.json")):
        try:
            data = _read_json(path)
        except Exception:
            continue
        wp_id = data.get("work_package_id")
        if wp_id:
            data = dict(data)
            data["path"] = _rel(path, root)
            records[wp_id] = data
    return records


def _review_records(root):
    records = {}
    for path in sorted((root / "collaboration" / "messages").glob("*review*.json")):
        try:
            data = _read_json(path)
        except Exception:
            continue
        text = json.dumps(data)
        for wp_id in set(re.findall(r"WP-\d{4}|WP-[A-Z]+-\d{3}", text)):
            records.setdefault(wp_id, []).append({"path": _rel(path, root), "title": (data.get("payload") or {}).get("title") or data.get("id")})
    return records


def _codex_command_for_package(root, rel_path):
    path = root / rel_path
    if not path.exists() or path.suffix != ".md":
        return None
    return f"Read:\n\n{rel_path}\n\nand do exactly what it says."


def _pipeline_state(entry, completion, reviews):
    if completion and completion.get("ready_for_ca_review") and not reviews:
        return "review-ready"
    state = str(entry.get("state") or "missing-data").lower()
    if state in {"claimed", "open", "active"}:
        return "active"
    if state == "blocked" or entry.get("blockers"):
        return "blocked"
    if state == "completed":
        return "completed"
    if state == "pending":
        return "pending"
    return "missing-data"


def _work_package_pipeline_artifact(root):
    try:
        queue = generate_assignment_queue(root=root, write=True)
        completions = _completion_records(root)
        reviews = _review_records(root)
        sections = {name: [] for name in ["pending", "active", "blocked", "review-ready", "completed", "missing-data"]}
        for entry in queue.get("work_packages", []):
            wp_id = entry.get("work_package_id")
            completion = completions.get(wp_id, {})
            review = reviews.get(wp_id, [])
            state = _pipeline_state(entry, completion, review)
            command = _codex_command_for_package(root, entry.get("path", "")) if state == "pending" else None
            item = {
                "work_package_id": wp_id or "unknown",
                "title": wp_id or "Unknown work package",
                "path": entry.get("path"),
                "state": state,
                "source_state": entry.get("state"),
                "mode": str(entry.get("mode") or "missing").lower(),
                "dependency_notes": "; ".join(entry.get("dependencies") or entry.get("blockers") or []) or "None recorded",
                "owner": entry.get("owner") or "unassigned",
                "next_action": entry.get("next_action") or "Review missing work package metadata.",
                "completion_status": "ready_for_ca_review" if completion.get("ready_for_ca_review") else (completion.get("codex_status") or "not completed"),
                "review_status": "review recorded" if review else "review not recorded",
                "codex_command": command,
            }
            item["title"] = _pipeline_title(root, item["path"], item["work_package_id"])
            sections[state].append(item)
        return {"available": True, "path": "runtime/work_packages/assignment_queue.json", "kind": "work_package_pipeline", "data": {"summary": queue.get("summary", {}), "sections": sections, "source": "assignment queue, completion records, review messages, launch queue documents, local validation artifacts"}}
    except Exception as exc:
        return {"available": False, "path": "runtime/work_packages/assignment_queue.json", "placeholder": f"Work package pipeline could not be generated: {exc}"}


def _pipeline_title(root, rel_path, fallback):
    try:
        for line in (root / rel_path).read_text(encoding="utf-8").splitlines():
            if line.startswith("# "):
                return line[2:].strip()
    except Exception:
        pass
    return fallback or "Unknown work package"



def _markdown_table(text, heading):
    lines = text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if line.strip().lower() == f"## {heading}".lower():
            start = i + 1
            break
    if start is None:
        return []
    table = []
    for line in lines[start:]:
        if line.startswith("## "):
            break
        if line.strip().startswith("|"):
            table.append(line.strip())
    if len(table) < 2:
        return []
    headers = [h.strip() for h in table[0].strip("|").split("|")]
    rows = []
    for raw in table[2:]:
        values = [v.strip() for v in raw.strip("|").split("|")]
        if not values or all(v in {"", "-"} for v in values):
            continue
        rows.append({headers[i]: values[i] if i < len(values) else "" for i in range(len(headers))})
    return rows


def _markdown_bullets(text, heading):
    lines = text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if line.strip().lower() == f"## {heading}".lower():
            start = i + 1
            break
    if start is None:
        return []
    items = []
    for line in lines[start:]:
        if line.startswith("## "):
            break
        if line.strip().startswith("- "):
            items.append(line.strip()[2:])
    return items


def _source_status(artifact):
    return {"available": bool(artifact.get("available")), "path": artifact.get("path"), "placeholder": artifact.get("placeholder")}


def _daily_board_workspace_artifact(root):
    daily = _read_artifact(root, ["operations/boards/daily_board.md", "operations/board/latest.md"])
    active = _read_artifact(root, ["operations/boards/active_work.md"])
    integration = _read_artifact(root, ["runtime/operations/daily_board_integration.json", "operations/boards/daily_board_integration.md"])
    parking = _read_artifact(root, ["operations/boards/parking_lot.md"])
    alfred = _read_artifact(root, ["runtime/alfred/operational_briefing.json", "operations/alfred/operational_briefing.md"])
    pipeline = _work_package_pipeline_artifact(root)

    daily_text = daily.get("text") or ""
    parking_text = parking.get("text") or ""
    integration_text = integration.get("text") or ""
    alfred_text = alfred.get("text") or ""
    priorities = _markdown_table(daily_text, "Today")
    waiting = _markdown_table(daily_text, "Waiting")
    blocked = _markdown_table(daily_text, "Blocked")
    review = _markdown_table(daily_text, "Review Required")
    parking_items = _markdown_table(parking_text, "Parking Lot Items")
    promotion_conditions = _markdown_bullets(integration_text, "Parking Lot Promotion Conditions")
    recommended = _markdown_bullets(integration_text, "Recommended Next Actions") + _markdown_bullets(alfred_text, "Recommended Next Actions")
    pipeline_sections = (((pipeline.get("data") or {}).get("sections") or {}) if pipeline.get("available") else {})
    active_items = _markdown_table(active.get("text") or "", "Active Work") or (pipeline_sections.get("active") or [])[:8]
    pipeline_blocked = pipeline_sections.get("blocked") or []
    available = any(a.get("available") for a in [daily, active, integration, parking, alfred])
    return {
        "available": available,
        "path": "operations/boards/daily_board.md; operations/boards/parking_lot.md",
        "kind": "daily_board_workspace",
        "placeholder": None if available else "Daily Board and Parking Lot source artifacts are not available yet.",
        "data": {
            "daily_priorities": priorities,
            "waiting_items": waiting,
            "blocked_items": blocked + pipeline_blocked,
            "review_required": review,
            "active_board_items": active_items,
            "parking_lot_items": parking_items,
            "promotion_conditions": promotion_conditions,
            "items_recommended_for_review": _markdown_bullets(integration_text, "Parking Lot Items Ready for Review"),
            "recommended_next_actions": recommended,
            "sources": {"daily_board": _source_status(daily), "active_work": _source_status(active), "daily_board_integration": _source_status(integration), "parking_lot": _source_status(parking), "work_package_pipeline": _source_status(pipeline), "alfred_operational_briefing": _source_status(alfred)},
        },
    }


def _first_markdown_heading(text, fallback):
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return fallback


def _status_bucket(value):
    state = str(value or "proposed").strip().lower()
    if state in {"active", "in progress", "open", "claimed"}:
        return "active"
    if state in {"planned", "pending", "ready", "queued"}:
        return "planned"
    if state in {"completed", "complete", "done", "closed"}:
        return "completed"
    return "proposed"


def _roadmap_row_item(row, source_path):
    title = row.get("Capability") or row.get("Initiative") or row.get("Epic") or row.get("Mission") or "Roadmap item"
    status = _status_bucket(row.get("Status"))
    return {
        "title": title,
        "status": status,
        "horizon": row.get("Current Milestone") or row.get("Target Milestone") or row.get("Horizon") or "Not specified",
        "dependency_notes": row.get("Key Dependency") or row.get("Dependency") or row.get("Dependencies") or "None recorded",
        "next_step": row.get("Future Initiative") or row.get("Next Action") or "Review source artifact.",
        "source": source_path,
    }


def _expansion_roadmap_artifact(root):
    roadmap = _read_artifact(root, ["operations/boards/roadmap.md"])
    missions = _read_artifact(root, ["data/registry/missions.json"])
    parking = _read_artifact(root, ["operations/boards/parking_lot.md"])
    capabilities = _read_artifact(root, ARTIFACTS["capability_lifecycle"])
    charter = _read_artifact(root, ["docs/operations/Autonomous_Estate_Operations_Charter_v1.md", "collaboration/work_packages/pending/WP-0033_SERIES_autonomous_operations_charter.md"])
    sources = {"roadmap": _source_status(roadmap), "mission_registry": _source_status(missions), "parking_lot": _source_status(parking), "capability_lifecycle": _source_status(capabilities), "autonomous_operations_charter": _source_status(charter)}
    items = []
    if roadmap.get("available"):
        for row in _markdown_table(roadmap.get("text") or "", "Roadmap"):
            items.append(_roadmap_row_item(row, roadmap.get("path")))
    if missions.get("available") and isinstance(missions.get("data"), dict):
        for mission in (missions["data"].get("missions") or []):
            items.append({"title": mission.get("mission_title") or mission.get("mission_id") or "Mission", "status": _status_bucket(mission.get("status")), "horizon": mission.get("mission_type") or "mission registry", "dependency_notes": ", ".join(mission.get("related_work_packages") or []) or "None recorded", "next_step": mission.get("notes") or "Review mission registry entry.", "source": missions.get("path")})
    parking_items = []
    if parking.get("available"):
        for row in _markdown_table(parking.get("text") or "", "Parking Lot Items"):
            item = {"title": row.get("Idea") or row.get("Item") or "Parking Lot item", "status": "proposed", "horizon": row.get("Target Milestone") or "future review", "dependency_notes": row.get("Promotion Condition") or "Human review required before work package creation.", "next_step": "Eligible for future work package review only; not promoted automatically.", "source": parking.get("path")}
            parking_items.append(item); items.append(item)
    pending_architecture = []
    for path in sorted((root / "Architecture" / "ADR").glob("*.md")):
        text = path.read_text(encoding="utf-8")
        rel = _rel(path, root)
        title = _first_markdown_heading(text, path.stem)
        status_match = re.search(r"(?im)^status:\s*(.+)$", text)
        status = _status_bucket(status_match.group(1) if status_match else ("proposed" if "Proposal" in title else "planned"))
        pending_architecture.append({"title": title, "status": status, "source": rel})
    current_horizon = "Not available yet."
    if roadmap.get("available"):
        current_horizon = "Strategic roadmap active; daily commitments remain on the Daily Board."
    available = any(src.get("available") for src in sources.values()) or bool(pending_architecture)
    return {"available": available, "path": "operations/boards/roadmap.md; data/registry/missions.json; Architecture/ADR", "kind": "expansion_roadmap_workspace", "placeholder": None if available else "Expansion roadmap source artifacts are not available yet.", "data": {"current_horizon": current_horizon, "items": items, "upcoming_epics": [i for i in items if i["status"] in {"planned", "proposed"}][:12], "pending_architecture_decisions": pending_architecture, "planned_not_active": [i for i in items if i["status"] in {"planned", "proposed"}], "future_work_package_candidates": parking_items, "sources": sources}}


def _recall_identity(*parts):
    for part in parts:
        if part not in (None, ""):
            return str(part)
    return "recall"


def _recall_ack_state(value):
    if value in (None, ""):
        return "unknown"
    return str(value).lower()


def _recall_stage(ack_state, delivery_result, decision_state):
    ack = str(ack_state or "unknown").lower()
    delivery = str(delivery_result or "unknown").lower()
    decision = str(decision_state or "pending").lower()
    if ack in {"acknowledged", "complete", "completed", "resolved", "not_required"}:
        return "acknowledged"
    if delivery in {"failed", "error", "transport_failure"}:
        return "delivery_failed"
    if delivery in {"sent", "delivered", "dry_run", "warning"}:
        return "delivered_pending_ack"
    if decision in {"approved", "eligible", "prepare_recall_delivery", "pending", "queued"}:
        return "active_request"
    return "unknown"


def _recall_active(stage, ack_state):
    return stage in {"active_request", "delivered_pending_ack", "delivery_failed", "unknown"} and str(ack_state or "unknown").lower() not in {"acknowledged", "complete", "completed", "resolved", "not_required"}


def _merge_recall(items, key, update):
    item = items.setdefault(key, {
        "recall_id": key,
        "reason": "unknown",
        "requested_by": "unknown",
        "originating_worker": "unknown",
        "alfred_decision_state": "pending/unknown",
        "transport_used": "unknown",
        "delivery_result": "unknown",
        "acknowledgement_state": "unknown",
        "timestamp": "unknown",
        "source_artifacts": [],
    })
    for field, value in update.items():
        if field == "source_artifacts":
            for source in value or []:
                if source and source not in item["source_artifacts"]:
                    item["source_artifacts"].append(source)
        elif value not in (None, "", "unknown") or item.get(field) in (None, "", "unknown", "pending/unknown"):
            item[field] = value
    item["acknowledgement_state"] = _recall_ack_state(item.get("acknowledgement_state"))
    item["lifecycle_stage"] = _recall_stage(item.get("acknowledgement_state"), item.get("delivery_result"), item.get("alfred_decision_state"))
    item["active"] = _recall_active(item["lifecycle_stage"], item.get("acknowledgement_state"))


def _build_steward_recall_operations(root):
    audit = _read_artifact(root, ARTIFACTS["recall_audit"])
    router = _read_artifact(root, ARTIFACTS["notification_router"])
    gotify = _read_artifact(root, ARTIFACTS["gotify_delivery"])
    center = _read_artifact(root, ARTIFACTS["notification_center"])
    morning = _read_artifact(root, ARTIFACTS["morning_briefing"])
    decision_model = _read_artifact(root, ARTIFACTS["recall_decision_model"])
    sources = {"recall_audit": audit, "notification_router": router, "gotify_delivery": gotify, "notification_center": center, "morning_briefing": morning, "recall_decision_model": decision_model}
    recalls = {}

    if isinstance(audit.get("data"), dict):
        for record in audit["data"].get("records", []) or []:
            if not isinstance(record, dict):
                continue
            key = _recall_identity(record.get("record_id"), record.get("notification_id"), record.get("id"))
            _merge_recall(recalls, key, {
                "reason": record.get("recall_reason") or record.get("reason"),
                "requested_by": record.get("requested_by") or record.get("source") or record.get("originating_worker"),
                "originating_worker": record.get("originating_worker") or record.get("source") or record.get("requested_by"),
                "alfred_decision_state": record.get("alfred_decision_state") or record.get("decision_state") or "approved/recorded",
                "transport_used": record.get("transport") or record.get("transport_used"),
                "delivery_result": record.get("delivery_result") or record.get("delivery_status"),
                "acknowledgement_state": record.get("acknowledgement_state"),
                "timestamp": record.get("timestamp") or record.get("created_at") or record.get("recorded_at"),
                "source_artifacts": [audit.get("path")],
            })

    if isinstance(router.get("data"), dict):
        for note in router["data"].get("notifications", []) or []:
            if not isinstance(note, dict) or note.get("class") != "recall":
                continue
            key = _recall_identity(note.get("id"), note.get("notification_id"), note.get("summary"))
            _merge_recall(recalls, key, {
                "reason": note.get("reason") or (note.get("audit") or {}).get("primary_recall_reason"),
                "requested_by": note.get("requested_by"),
                "originating_worker": note.get("originating_worker") or note.get("requested_by"),
                "alfred_decision_state": note.get("action") or ("eligible" if note.get("eligible_for_immediate_delivery") else "queued"),
                "timestamp": note.get("timestamp") or note.get("created_at"),
                "source_artifacts": [router.get("path")],
            })

    if isinstance(gotify.get("data"), dict):
        data = gotify["data"]
        payload = data.get("payload") if isinstance(data.get("payload"), dict) else {}
        key = _recall_identity(data.get("notification_id"), data.get("recall_id"), payload.get("message"), "gotify_delivery")
        _merge_recall(recalls, key, {
            "reason": data.get("reason") or payload.get("message"),
            "transport_used": "gotify",
            "delivery_result": data.get("status") or ("delivered" if data.get("ok") else "failed"),
            "timestamp": data.get("generated_at"),
            "source_artifacts": [gotify.get("path")],
        })

    if isinstance(morning.get("data"), dict):
        sections = morning["data"].get("sections") if isinstance(morning["data"].get("sections"), dict) else {}
        for recall in sections.get("outstanding_recalls", []) or []:
            if not isinstance(recall, dict):
                continue
            key = _recall_identity(recall.get("record_id"), recall.get("id"), recall.get("recall_reason"))
            _merge_recall(recalls, key, {
                "reason": recall.get("recall_reason") or recall.get("reason"),
                "acknowledgement_state": recall.get("acknowledgement_state"),
                "source_artifacts": [morning.get("path")],
            })

    data = center.get("data") if isinstance(center.get("data"), dict) else {}
    for recall in (data.get("recalls") or data.get("recall_requests") or []):
        if isinstance(recall, dict):
            key = _recall_identity(recall.get("record_id"), recall.get("id"), recall.get("notification_id"))
            _merge_recall(recalls, key, {**recall, "reason": recall.get("reason") or recall.get("recall_reason"), "source_artifacts": [center.get("path")]})

    recall_list = sorted(recalls.values(), key=lambda item: str(item.get("timestamp") or ""), reverse=True)
    active_count = sum(1 for item in recall_list if item.get("active"))
    missing_sources = [name for name, artifact in sources.items() if not artifact.get("available")]
    available = True
    return {"available": available, "path": "runtime/audit/recall_audit_log.json; runtime/notifications/notification_router_report.json", "kind": "steward_recall_operations", "placeholder": None, "data": {"summary": {"recall_count": len(recall_list), "active_recall_count": active_count, "missing_source_count": len(missing_sources)}, "recalls": recall_list, "missing_sources": missing_sources, "sources": {name: _source_status(artifact) for name, artifact in sources.items()}, "constraints": {"does_not_send_recalls": True, "does_not_approve_recalls": True, "does_not_bypass_alfred": True}}}

def generate_command_center(root=None, write=True):
    root = _root(root)
    resident_cards = build_resident_cards(root)
    resident_panels = {f"{str(card.get('name', '')).lower()}_resident_card": card for card in resident_cards["cards"]}
    panels = {
        **resident_panels,
        "capability_dependency_visualization": {"available": True, "path": "runtime/capabilities/capability_dependency_visualization.json", "kind": "capability_dependency_visualization", "data": generate_capability_dependency_visualization(root, write=write)},
        "mission_control_workspace": build_mission_control_workspace(root),
        "morning_briefing": _read_artifact(root, ARTIFACTS["morning_briefing"]),
        "operational_activity": load_office_operational_activity(root),
        "orchestrator_intake_decisions": load_office_intake_decision_surface(root),
        "steward_decision_queue": _decision_queue_artifact(root),
        "mailbox_summary": _read_artifact(root, ARTIFACTS["mailbox_summary"]),
        "mailbox_operations_center": _mailbox_operations_center_artifact(root),
        "resident_conversations_workspace": build_resident_conversations_workspace(root),
        "ai_services_models": build_steward_ai_services_panel(root),
        "steward_recall_operations": _build_steward_recall_operations(root),
        "operations_notification_center": {"available": True, "path": "runtime/notifications/operations_notification_center.json", "kind": "json", "data": generate_operations_notification_center(root=root, write=write)},
        "work_package_pipeline": _work_package_pipeline_artifact(root),
        "execution_activity": _read_artifact(root, ARTIFACTS["execution_activity"]),
        "validation_status": _read_artifact(root, ARTIFACTS["validation_status"]),
        "expansion_roadmap": _expansion_roadmap_artifact(root),
        "parking_lot": _read_artifact(root, ["operations/boards/parking_lot.md"]),
        "daily_board_workspace": _daily_board_workspace_artifact(root),
        "search": _global_search_panel(root),
        "steward_presence": {"available": True, "path": "runtime/steward/steward_presence_state.json", "kind": "json", "data": generate_steward_presence_state(root=root, write=False)},
        "settings": _settings_panel(root),
        "help": _help_panel(root),
        "about": _about_panel(root),
        "alfred_chat": _alfred_chat_panel(root),
    }
    if isinstance(panels.get("mission_control_workspace"), dict) and isinstance(panels["mission_control_workspace"].get("data"), dict):
        panels["mission_control_workspace"]["data"]["capability_dependency_visualization"] = panels.get("capability_dependency_visualization")
    panels["validation_health_dashboard"] = _build_validation_health_dashboard(root)
    generated_at = _now()
    panels["operations_center_layout"] = _operations_center_layout_framework(panels, generated_at)
    settings_manager = load_operations_center_settings(root)
    default_profile = settings_manager["settings"].get("workspace", {}).get("default_profile", "mission-control")
    workspace_profile = resolve_workspace_profile(root, profile_name=default_profile, available_panels={tab["id"] for tab in OFFICE_TABS})
    payload = {"version": 1, "generated_at": generated_at, "local_only": True, "panels": panels, "navigation": _office_navigation(panels), "tabs": _office_tabs(panels), "layout_framework": panels["operations_center_layout"], "workspace_profile": workspace_profile, "settings_manager": settings_manager, "office_actions": {tab["id"]: controls_for_tab(tab["id"]) for tab in OFFICE_TABS}}
    payload["status_bar"] = _build_status_bar(root, panels, generated_at)
    payload["activity_console"] = _build_activity_console(root, panels, generated_at)
    if write:
        out = root / "runtime" / "steward" / "command_center.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(render_command_center_html(payload), encoding="utf-8")
    return payload




def _operations_center_layout_framework(panels, generated_at):
    regions = [
        {"id": "top_navigation_tabs", "label": "Top navigation tabs", "role": "workspace_switcher", "selector": "#workspace-tabs", "dynamic_update": "tab activation updates visibility without page refresh"},
        {"id": "left_navigation_panel", "label": "Collapsible left navigation", "role": "panel_index", "selector": "#office-navigation", "dynamic_update": "collapsed-by-default drawer opens temporarily without reserving workspace width"},
        {"id": "main_workspace", "label": "Main workspace", "role": "active_tab_content", "selector": "main.workspace", "dynamic_update": "workspace views are hidden/shown in place"},
        {"id": "bottom_activity_stream", "label": "Dockable bottom activity stream", "role": "activity_console", "selector": "#activity-console", "dynamic_update": "quiet refresh replaces activity console from local JSON"},
        {"id": "status_bar", "label": "Status bar", "role": "operational_status", "selector": "#status-bar", "dynamic_update": "quiet refresh replaces status bar from local JSON"},
        {"id": "command_console", "label": "Command console", "role": "global_search_command_palette", "selector": "#global-search-input", "dynamic_update": "command results filter locally without refresh"},
    ]
    workspace_templates = [
        {"id": tab["id"], "label": tab["label"], "panel_available": True, "version": "layout-framework-v1"}
        for tab in OFFICE_TABS
    ]
    return {
        "available": True,
        "path": "runtime/steward/command_center.html; browser localStorage key estate.operations_center.layout.v1",
        "kind": "operations_center_layout_framework",
        "data": {
            "version": "layout-framework-v1",
            "generated_at": generated_at,
            "local_only": True,
            "layout_preference_key": "estate.operations_center.layout.v1",
            "quiet_refresh_regions": ["status_bar", "bottom_activity_stream"],
            "regions": regions,
            "workspace_templates": workspace_templates,
            "default_preferences": {
                "active_tab": "home",
                "navigation_collapsed": True,
                "left_navigation": "collapsed",
                "activity_console_dock": "bottom",
                "activity_console_visible": True,
                "visible_panels": {item["id"]: True for item in OFFICE_NAVIGATION},
                "tab_order": [tab["id"] for tab in OFFICE_TABS],
            },
            "future_integration_points": ["Alfred", "TTS/STT", "Mission Control"],
            "workspace_profiles": {"enabled": True, "profiles_output": WORKSPACE_PROFILES_OUTPUT, "default_profile": "mission-control", "rapid_switching": "profile selector applies active tab, tab order, panel visibility, and activity console settings without page refresh"},
            "state_authority": "browser-local layout preferences and local workspace profile artifacts only; expanded legacy left navigation states are interpreted as collapsed; operational records remain in existing local artifacts",
        },
    }

def _placeholder_panel(panel_id, title, description, source="future Office package"):
    return {"available": False, "path": source, "kind": "placeholder", "panel_id": panel_id, "title": title, "placeholder": description}


def _global_search_panel(root):
    try:
        palette = build_global_palette(root, write=True)
        return {"available": True, "path": palette.get("index_path"), "kind": "global_search_command_palette", "data": palette}
    except Exception as exc:
        return {"available": False, "path": "runtime/search/global_command_palette.json", "kind": "global_search_command_palette", "placeholder": f"Global search palette is unavailable: {exc}"}


def _office_navigation(panels):
    items = []
    for item in OFFICE_NAVIGATION:
        panel = panels.get(item["panel"], {})
        items.append({**item, "available": bool(panel.get("available")) if isinstance(panel, dict) else False})
    return {"collapsed_by_default": False, "items": items}


def _office_tabs(panels):
    return [{**tab, "available": True} for tab in OFFICE_TABS]


def _office_placeholder_html(title, description, source="future Office package"):
    return f'<p class="placeholder">{html.escape(description)}</p><p class="source">Integration point: {html.escape(source)}</p>'


def _unknown(value="unknown/unavailable"):
    return value


def _safe_version(data):
    if not isinstance(data, dict):
        return _unknown()
    for key in ("version", "schema_version", "index_version", "router_version", "policy_version"):
        value = data.get(key)
        if value not in (None, ""):
            return value
    return _unknown()


def _runtime_path(root, rel):
    return {"label": rel, "path": str((root / rel).resolve()), "available": (root / rel).exists()}


def _settings_panel(root):
    managed = load_operations_center_settings(root)
    settings = managed["settings"]
    workspace = settings.get("workspace", {})
    operator = settings.get("operator_visibility", {})
    refresh = settings.get("refresh", {})
    return {
        "available": True,
        "path": SETTINGS_OUTPUT,
        "kind": "settings",
        "data": {
            "settings_schema_version": settings.get("settings_schema_version"),
            "ui_version": managed.get("ui_version"),
            "theme": {"value": (settings.get("appearance") or {}).get("theme"), "options": ["light", "dark", "system"]},
            "accent": (settings.get("appearance") or {}).get("accent"),
            "default_workspace_profile": workspace.get("default_profile"),
            "refresh_behavior": {"quiet_refresh_seconds": refresh.get("quiet_refresh_seconds"), "mode": refresh.get("mode")},
            "visible_panels": workspace.get("visible_panels") or {},
            "tab_order": [tab["id"] for tab in OFFICE_TABS],
            "pinned_views": [workspace.get("default_active_tab") or "mission-control", "validation", "mailboxes"],
            "global_verbosity": {"value": operator.get("global_verbosity"), "options": ["quiet", "normal", "detailed", "diagnostic"]},
            "default_verbosity_profile": operator.get("default_verbosity_profile"),
            "per_topic_verbosity": {"operations": operator.get("global_verbosity"), "validation": "detailed", "mailboxes": operator.get("global_verbosity")},
            "per_resident_verbosity": {"Alfred": operator.get("global_verbosity"), "Helen": operator.get("global_verbosity")},
            "activity_console_visible": workspace.get("bottom_activity_stream_visible"),
            "status_bar_visible": workspace.get("status_bar_visible"),
            "command_console": settings.get("command_console"),
            "warnings": managed.get("warnings", []),
            "persistence": "local-first Settings Manager; no secrets, cloud settings, or account policy",
        },
    }



def _doc_link(root, rel, label=None, summary=None):
    path = root / rel
    return {"label": label or rel, "path": rel, "available": path.exists(), "summary": summary or "Authoritative local document/artifact."}


def _help_panel(root):
    """Build an informational Operations Center help surface from existing registries."""
    catalog = generate_estate_service_catalog(root=root, write=False)
    profile = resolve_workspace_profile(root, available_panels={tab["id"] for tab in OFFICE_TABS})
    command_records = []
    for service in catalog.get("services", []):
        for command in service.get("command_aliases") or []:
            command_records.append({
                "command": command,
                "service": service.get("name"),
                "status": "available" if service.get("operational_status") in {"implemented", "active", "operational"} else "unknown/unavailable",
                "source_artifacts": service.get("source_artifact_links") or [],
            })
    if not command_records:
        for surface in COMMAND_SURFACES:
            for command in surface.get("commands") or []:
                command_records.append({
                    "command": command,
                    "service": surface.get("service_name"),
                    "status": "available" if (root / "src/estate/cli/main.py").exists() else "unknown/unavailable",
                    "source_artifacts": surface.get("implementation_references") or [],
                })
    command_records = sorted(command_records, key=lambda item: (item.get("command") or "", item.get("service") or ""))
    docs = [
        _doc_link(root, "docs/operations/Mission_Control_Workspace_v1.md", "Mission Control Workspace", "Mission Control authoritative operations document."),
        _doc_link(root, "docs/operations/Operations_Board_Runtime_Integration.md", "Operations Board Runtime Integration", "Operations board integration notes."),
        _doc_link(root, "operations/services/estate_service_catalog.md", "Estate Service Catalog", "Service catalog generated report; source of links, not new authority."),
        _doc_link(root, "operations/validation/reports/WP-0092_validation.md", "WP-0092 validation report", "Reusable validation output when generated."),
        _doc_link(root, "runtime/validation/work_packages/WP-0092_validation.json", "WP-0092 validation JSON", "Machine-readable validation output when generated."),
        _doc_link(root, "collaboration/work_packages/pending/WP-0092_SERIES_operations_center_help_and_about.md", "WP-0092 work package", "Implementation scope and requirements."),
    ]
    panels = [{"id": item["id"], "label": item["label"], "available": True, "source_panel": item.get("panel")} for item in OFFICE_NAVIGATION]
    workspaces = [{"id": item["id"], "label": item["label"], "available": True} for item in OFFICE_TABS]
    unavailable = []
    unavailable.extend({"feature": doc["label"], "reason": f"Missing optional local artifact: {doc['path']}"} for doc in docs if not doc["available"])
    if not command_records:
        unavailable.append({"feature": "Command console help", "reason": "No service catalog command aliases were available."})
    return {"available": True, "path": "local help aggregation from service catalog, layout framework, workspace profiles, and documentation registry", "kind": "operations_center_help", "data": {
        "ui_version": "Operations Center v1 / Help and About surfaces v1",
        "active_workspace_profile": profile.get("selected_profile"),
        "workspace_profile": profile.get("profile"),
        "panels": panels,
        "workspaces": workspaces,
        "command_console_help": {"summary": "Use Search as the command console. It filters registered local command aliases and reports unavailable commands without executing them.", "commands": command_records[:40], "command_count": len(command_records), "source": "Estate Service Catalog command aliases"},
        "service_catalog_links": ["runtime/services/estate_service_catalog.json", "operations/services/estate_service_catalog.md"],
        "validation_status_links": ["runtime/validation/work_packages/WP-0092_validation.json", "operations/validation/reports/WP-0092_validation.md", "runtime/validation/production_readiness.json"],
        "documentation_links": docs,
        "authority_notes": ["Informational surface only; existing local artifacts remain authoritative.", "Local-first operation; no network calls or governance changes.", "Missing optional artifacts are shown as unknown/unavailable instead of failing the UI."],
        "known_unavailable_features": unavailable,
    }}

def _about_panel(root):
    package = _read_artifact(root, ["pyproject.toml", "package.json"])
    alfred = _read_artifact(root, ["docs/alfred_v1_status.md", "residents/alfred.md"])
    helen = _read_artifact(root, ["residents/helen.md", "docs/operations/helen/operating_brief.md"])
    document_registry = _read_artifact(root, ["data/registry/documents.json"])
    mailbox_registry = _read_artifact(root, ["data/registry/mailboxes.json"])
    routing = _read_artifact(root, ["collaboration/routing_rules.json"])
    work_package_schema = _read_artifact(root, ["collaboration/templates/work_package_v1.md"])
    envelope_schema = _read_artifact(root, ["docs/collaboration/schemas/Canonical_Message_Envelope_v1.md", "collaboration/templates/message_envelope_v1.json"])
    settings_manager = load_operations_center_settings(root)
    inventory = [
        {"component": "Estate", "version": _safe_version(package.get("data")), "status": "local repository available"},
        {"component": "Operations Center UI", "version": "Operations Center v1 / Settings & About inventory v1", "status": "available"},
        {"component": "Operations Center Settings Manager", "version": settings_manager.get("ui_version", _unknown()), "status": "available", "path": settings_manager.get("path")},
        {"component": "Alfred", "version": "v1" if alfred.get("available") else _unknown(), "status": "available" if alfred.get("available") else _unknown()},
        {"component": "Helen", "version": "unknown/unavailable", "status": "available" if helen.get("available") else _unknown()},
        {"component": "Document registry/schema", "version": _safe_version(document_registry.get("data")), "status": "available" if document_registry.get("available") else _unknown()},
        {"component": "Mailbox registry/schema", "version": _safe_version(mailbox_registry.get("data")), "status": "available" if mailbox_registry.get("available") else _unknown()},
        {"component": "Communication Bus", "version": _safe_version(routing.get("data")), "status": "available" if routing.get("available") or envelope_schema.get("available") else _unknown()},
        {"component": "Work Package schema", "version": "v1" if work_package_schema.get("available") else _unknown(), "status": "available" if work_package_schema.get("available") else _unknown()},
    ]
    return {"available": True, "path": "local component inventory", "kind": "about", "data": {"inventory": inventory, "runtime_paths": [_runtime_path(root, rel) for rel in ["runtime/steward/command_center.html", "runtime", "data/registry", "collaboration", "operations"]], "local_only": True}}


def _script_json(data):
    """Return JSON safe for embedding in a non-executable script element."""
    return json.dumps(data, sort_keys=True).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")


def _js_json_literal(data):
    """Return a JSON literal safe inside an executable script block."""
    return _script_json(data).replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")


def _global_search_html(artifact):
    if not artifact.get("available"):
        return _office_placeholder_html("Search", artifact.get("placeholder", "Search is unavailable."), artifact.get("path", "runtime/search/global_command_palette.json"))
    data = artifact.get("data") or {}
    records = (data.get("commands") or []) + (data.get("artifacts") or [])
    safe_records = _script_json(records)
    domains = ", ".join(data.get("domains") or [])
    return f"""<section class="global-search-palette" aria-label="Global Search and Command Palette">
<p>Search updates incrementally across Work Packages, Missions, Mailboxes, Residents, Daily Board, Parking Lot, Validation artifacts, Documentation, and registered commands. Press <kbd>/</kbd> to focus search.</p>
<label for="global-search-input">Global search / command</label>
<input id="global-search-input" type="search" autocomplete="off" placeholder="Search artifacts or commands" aria-describedby="global-search-help" />
<p id="global-search-help" class="source">Local-only. Commands are explicit registrations; unavailable commands report why they cannot run. Domains: {html.escape(domains)}</p>
<div id="global-search-results" role="list" aria-live="polite"></div>
<script id="global-palette-data" type="application/json">{safe_records}</script>
<p class="source">Source: {html.escape(str(artifact.get("path") or "runtime/search/global_command_palette.json"))}</p>
</section>"""



def _alfred_chat_panel(root):
    surface = resident_surface("alfred", root=root)
    history = load_history("alfred", root=root)
    diagnostic = alfred_llm_diagnostic(root, write=True)
    return {
        "available": True,
        "kind": "alfred_operations_center_chat",
        "path": "runtime/resident_interactions/sessions",
        "surface": surface,
        "history": history,
        "llm_diagnostic": diagnostic,
        "endpoints": {
            "history": "/api/residents/alfred/chat",
            "send": "/api/residents/alfred/chat",
            "surface": "/api/residents/alfred/surface",
        },
        "authority_message": "Alfred may summarize, recommend, and propose next actions from local Estate artifacts; Alfred will not execute privileged actions or claim Steward authorization from chat.",
        "memory_message": "Conversation turns are persisted locally through the WP-0126 resident interaction framework and can be reloaded from runtime/resident_interactions/sessions. Steward-directed forget/redaction remains available through the resident API.",
        "local_first_message": "Local-first operation: local LLM is used when available through the WP-0126 adapter path; deterministic fallback is used when no local model is available.",
        "diagnostics_message": "Adapter diagnostics are shown per response: provider/model, fallback state, safe adapter error, request/response timestamps, and transport/timeout status. Secrets are redacted.",
    }


def _attachment_html(attachments):
    if not attachments:
        return ""
    items = []
    for a in attachments:
        label = f"{a.get('kind','attachment')} {a.get('attachment_id','')} ({a.get('mime_type','unknown')}, {a.get('size_bytes',0)} bytes, vision={a.get('vision_status','unknown')})"
        thumb = ""
        if a.get("kind") == "image" and str(a.get("storage_path") or "").startswith("runtime/resident_interactions/attachments/"):
            thumb = f"<br><img class='alfred-attachment-thumb' src='/{html.escape(str(a.get('storage_path')))}' alt='Local pasted image thumbnail' loading='lazy'>"
        summary = f"<br><span>{html.escape(str(a.get('summary') or 'No local visual summary stored.'))}</span>" if a.get("summary") else ""
        items.append(f"<li><code>{html.escape(label)}</code>{thumb}{summary}</li>")
    return "<ul class='alfred-attachments'>" + "".join(items) + "</ul>"

def _alfred_chat_html(panel):
    surface = panel.get("surface") or {}
    history = panel.get("history") or {}
    sessions = history.get("sessions") or []
    turn_items = []
    for session in sessions[-5:]:
        for turn in (session.get("turns") or [])[-3:]:
            turn_items.append(
                "<article class='alfred-chat-turn'>"
                f"<p><strong>Steward:</strong> {html.escape(str(turn.get('user_message') or ''))}</p>"
                f"<p><strong>Alfred:</strong> {html.escape(str(turn.get('resident_response') or ''))}</p>"
                f"{_attachment_html(turn.get('attachments') or [])}"
                f"<p class='source'>Mode: {html.escape(str((turn.get('llm') or {}).get('mode') or 'unknown'))} / provider: {html.escape(str((turn.get('llm') or {}).get('provider') or 'unknown'))} / model: {html.escape(str((turn.get('llm') or {}).get('model') or 'unknown'))} · Session {html.escape(str(session.get('session_id') or 'unknown'))} · {html.escape(str(turn.get('created_at') or 'unknown'))}</p>"
                "</article>"
            )
    history_html = "".join(turn_items) or "<p class='placeholder'>No prior Alfred chat turns are recorded yet. Send a message to create persisted Estate memory.</p>"
    return f"""
<section class="alfred-chat" aria-label="Alfred Operations Center chat">
  <h3>Chat with Alfred</h3>
  <p>{html.escape(str(panel.get('authority_message') or ''))}</p>
  <p class="source">{html.escape(str(panel.get('memory_message') or ''))}</p>
  <p class="source">{html.escape(str(panel.get('local_first_message') or ''))}</p>
  <p class="source">{html.escape(str(panel.get('diagnostics_message') or ''))}</p>
  <dl>
    <dt>Resident API standard</dt><dd>{html.escape(str(surface.get('resident_api_standard_version') or 'unknown'))}</dd>
    <dt>Alfred implementation</dt><dd>{html.escape(str(surface.get('resident_implementation_version') or 'unknown'))}</dd>
    <dt>Expected LLM provider</dt><dd>{html.escape(str((panel.get('llm_diagnostic') or {}).get('expected_provider') or 'none'))}</dd>
    <dt>Provider reachable</dt><dd>{html.escape(str((panel.get('llm_diagnostic') or {}).get('provider_reachable') or 'unknown'))}</dd>
    <dt>Generation result</dt><dd>{html.escape(str((panel.get('llm_diagnostic') or {}).get('generation_result') or 'not_attempted'))}</dd>
    <dt>Timeout seconds</dt><dd>{html.escape(str((panel.get('llm_diagnostic') or {}).get('timeout_seconds') or 'unknown'))}</dd>
    <dt>Prompt size summary</dt><dd>{html.escape(str((panel.get('llm_diagnostic') or {}).get('prompt_size_summary') or 'recorded per response'))}</dd>
    <dt>LLM failure reason</dt><dd>{html.escape(str((panel.get('llm_diagnostic') or {}).get('failure_reason') or 'none'))}</dd>
    <dt>Recovery hint</dt><dd>{html.escape(str((panel.get('llm_diagnostic') or {}).get('recovery_hint') or 'No recovery hint available.'))}</dd>
    <dt>Diagnostic artifact</dt><dd><code>{html.escape(str((panel.get('llm_diagnostic') or {}).get('diagnostic_path') or 'runtime/residents/alfred/llm_diagnostics.json'))}</code></dd>
    <dt>Surface endpoint</dt><dd><code>/api/residents/alfred/surface</code></dd>
  </dl>
  <form id="alfred-chat-form" data-resident-chat="alfred">
    <label for="alfred-chat-input">Message Alfred</label>
    <textarea id="alfred-chat-input" name="message" rows="3" placeholder="Alfred, what do you notice in this screenshot?"></textarea>
    <div id="alfred-paste-help" class="source">Paste screenshots/images or text snippets here. Attachments stay local under runtime/resident_interactions/attachments.</div>
    <div id="alfred-pending-attachments" class="alfred-attachments" aria-live="polite"></div>
    <button id="alfred-chat-send" type="submit">Send to Alfred</button>
  </form>
  <div id="alfred-chat-response" data-state="idle" role="status" aria-live="polite"></div>
  <h4>Recent Alfred conversation history</h4>
  <div id="alfred-chat-history">{history_html}</div>
</section>"""

def _home_workspace_html(payload):
    status = payload.get("status_bar", {})
    return "".join([
        "<p>The Office shell is active. Use the left navigation or workspace tabs to switch between operational areas without crowding every panel onto one screen.</p>",
        _panel("Alfred Front Door", _alfred_chat_html(payload.get("panels", {}).get("alfred_chat", {})), "ready"),
        _panel("Steward Decision Queue", _decision_queue_html(payload.get("panels", {}).get("steward_decision_queue", {})), "ready"),
        "<ul>",
        f"<li>Estate status: {html.escape(str(status.get('estate_status') or 'unknown'))}</li>",
        f"<li>Validation: {html.escape(str(status.get('validation_state') or 'unknown'))}</li>",
        f"<li>Recommended next action: {html.escape(str(status.get('recommended_next_action') or 'Review local artifacts.'))}</li>",
        "</ul>",
    ])

def _panel(title, body, status="placeholder"):
    return f'<section class="panel {html.escape(status)}"><h2>{html.escape(title)}</h2>{body}</section>'


def _resident_html(card):
    if not card.get("available"):
        return f'<p class="placeholder">Resident record is not available yet.</p><p class="source">Details: {html.escape(str(card.get("details_link", "Not available yet")))}</p>'
    fields = ["name", "role", "operational_status", "presence_state", "current_duty"]
    rows = [f"<dt>{html.escape(field.replace('_', ' ').title())}</dt><dd>{html.escape(str(card.get(field) or 'Not available yet'))}</dd>" for field in fields]
    rows.append(f"<dt>Runtime Boundary</dt><dd>{html.escape('Visible presence only; autonomous execution is not active' if card.get('visible_presence_only') else 'Not available yet')}</dd>")
    mailbox = card.get("mailbox") or {}
    mailbox_label = mailbox.get("display_name") or "Not available yet"
    if mailbox.get("mailbox_id") is not None:
        mailbox_label = f"{mailbox_label} ({mailbox.get('mailbox_id')})"
    rows.append(f"<dt>Mailbox</dt><dd>{html.escape(str(mailbox_label))}</dd>")
    activity = card.get("last_activity") or {}
    rows.append(f"<dt>Last Activity</dt><dd>{html.escape(str(activity.get('summary') or 'Not available yet'))}</dd>")
    rows.append(f"<dt>Needs Steward</dt><dd>{html.escape(str(card.get('needs_steward') or 'No'))}</dd>")
    rows.append(f"<dt>Resident Details</dt><dd>{html.escape(str(card.get('details_link') or 'Not available yet'))}</dd>")
    return f"<dl>{''.join(rows)}</dl>"


def _resident_conversations_html(artifact):
    if not artifact.get("available"):
        return _artifact_html(artifact)
    data = artifact.get("data") or {}
    conversations = data.get("conversations") or []
    selector = "".join(
        f"<option>{html.escape(str(item))}</option>"
        for item in data.get("resident_selection", [])
    )
    cards = []
    for item in conversations:
        mailbox = item.get("mailbox") or {}
        mailbox_label = mailbox.get("display_name") or "Not available yet"
        if mailbox.get("mailbox_id") is not None:
            mailbox_label = f"{mailbox_label} ({mailbox.get('mailbox_id')})"
        messages = item.get("recent_messages") or []
        if messages:
            message_rows = "".join(
                "<tr>"
                f"<td>{html.escape(str(message.get('title') or 'Untitled message'))}</td>"
                f"<td>{html.escape(str(message.get('source') or 'Not available yet'))}</td>"
                f"<td>{html.escape(str(message.get('destination') or 'Not available yet'))}</td>"
                f"<td>{html.escape(str(message.get('status') or 'open'))}</td>"
                f"<td>{html.escape(str(message.get('path') or 'Not available yet'))}</td>"
                "</tr>"
                for message in messages
            )
            message_html = f"<table><thead><tr><th>Message</th><th>Source</th><th>Destination</th><th>Status</th><th>Source artifact</th></tr></thead><tbody>{message_rows}</tbody></table>"
        else:
            message_html = "<p class='placeholder'>No conversation-related institutional messages are available for this resident yet.</p>"
        sessions = item.get("recent_sessions") or []
        if sessions:
            session_rows = "".join(
                "<tr>"
                f"<td>{html.escape(str(session.get('session_id') or 'unknown'))}</td>"
                f"<td>{html.escape(str(session.get('status') or 'unknown'))}</td>"
                f"<td>{html.escape(str(session.get('outcome_label') or 'informational'))}</td>"
                f"<td>{html.escape(str(session.get('authority_label') or 'non-authoritative conversation session'))}</td>"
                f"<td>{html.escape(str(session.get('path') or 'Not available yet'))}</td>"
                "</tr>"
                for session in sessions
            )
            session_html = f"<table><thead><tr><th>Session</th><th>Status</th><th>Outcome</th><th>Authority</th><th>Audit artifact</th></tr></thead><tbody>{session_rows}</tbody></table>"
        else:
            session_html = "<p class='placeholder'>No local resident conversation sessions are recorded yet.</p>"
        source_rows = "".join(f"<li>{html.escape(str(source))}</li>" for source in item.get("source_artifacts") or [])
        source_html = f"<ul>{source_rows}</ul>" if source_rows else "<p class='placeholder'>No linked source artifacts are available yet.</p>"
        cards.append(
            "<article class='resident-conversation-card'>"
            f"<h3>{html.escape(str(item.get('resident_name') or 'Unknown resident'))}</h3>"
            f"<p><strong>Role:</strong> {html.escape(str(item.get('role') or 'Not available yet'))}</p>"
            f"<p><strong>Status:</strong> {html.escape(str(item.get('status') or 'Not available yet'))}</p>"
            f"<p><strong>Mailbox summary:</strong> {html.escape(str(mailbox_label))}</p>"
            f"<p class='placeholder'><strong>Conversation panel:</strong> {html.escape(str(item.get('conversation_placeholder') or 'Not available yet'))}</p>"
            f"<p class='placeholder'><strong>Transcript / audit:</strong> {html.escape(str(item.get('transcript_audit_placeholder') or 'Not available yet'))}</p>"
            "<h4>Local conversation sessions</h4>"
            f"{session_html}"
            "<h4>Recent institutional messages</h4>"
            f"{message_html}"
            "<h4>Linked source artifacts</h4>"
            f"{source_html}"
            "</article>"
        )
    warnings = "".join(f"<li>{html.escape(str(warning))}</li>" for warning in artifact.get("warnings") or [])
    warning_html = f"<details><summary>Workspace warnings</summary><ul>{warnings}</ul></details>" if warnings else ""
    return (
        "<section class='resident-conversations'>"
        f"<p class='source'>{html.escape(str(data.get('record_policy') or 'Conversation is an interface surface only.'))}</p>"
        f"<label>Resident selection <select>{selector}</select></label>"
        f"{''.join(cards)}"
        f"{warning_html}"
        f"<p class='source'>Sources: {html.escape(str(artifact.get('path') or 'local resident conversation workspace'))}</p>"
        "</section>"
    )



def _decision_queue_artifact(root):
    try:
        queue = generate_decision_queue(root=root, write=True)
        return {"available": True, "path": "runtime/steward/decision_queue.json", "kind": "decision_queue", "data": queue}
    except Exception as exc:
        return {"available": False, "path": "runtime/steward/decision_queue.json", "placeholder": f"Decision queue could not be generated: {exc}"}


def _decision_queue_html(artifact):
    if not artifact.get("available"):
        return _artifact_html(artifact)
    data = artifact.get("data") or {}
    decisions = data.get("decisions") or []
    if not decisions:
        return f'<p class="placeholder">{html.escape(data.get("empty_state") or "No pending Steward decisions were found.")}</p><p class="source">Source: {html.escape(artifact.get("path", ""))}</p>'
    rows = []
    for decision in decisions[:10]:
        title = html.escape(str(decision.get("title") or "Untitled decision item"))
        meta = html.escape(f"{decision.get('urgency') or 'normal'} · {decision.get('status') or 'pending'} · requested by {decision.get('requested_by') or 'unknown'}")
        reason = html.escape(str(decision.get("reason") or ""))
        action = html.escape(str(decision.get("recommended_action") or ""))
        source = html.escape(str(decision.get("source_artifact") or artifact.get("path") or ""))
        rows.append(f"<li><strong>{title}</strong><br><span class='source'>{meta}</span><br>{reason}<br><em>{action}</em><br><span class='source'>Source: {source}</span></li>")
    return f"<ul>{''.join(rows)}</ul><p class='source'>Source: {html.escape(artifact.get('path', ''))}</p>"


def _work_package_pipeline_html(artifact):
    if not artifact.get("available"):
        return _artifact_html(artifact)
    data = artifact.get("data") or {}
    sections = data.get("sections") or {}
    order = [("pending", "Pending"), ("active", "Active"), ("blocked", "Blocked"), ("review-ready", "Review-ready"), ("completed", "Completed"), ("missing-data", "Missing-data")]
    out = ["<div class='pipeline-view'>"]
    for key, label in order:
        items = sections.get(key) or []
        out.append(f"<section class='pipeline-section {html.escape(key)}'><h3>{html.escape(label)} ({len(items)})</h3>")
        if not items:
            out.append("<p class='placeholder'>No work packages in this state.</p></section>")
            continue
        out.append("<table><thead><tr><th>ID</th><th>Title</th><th>Mode</th><th>Owner</th><th>Dependencies</th><th>Next action</th><th>Completion / Review</th></tr></thead><tbody>")
        for item in items[:12]:
            command = item.get("codex_command")
            action = html.escape(str(item.get("next_action") or ""))
            if command:
                action += f"<br><textarea readonly rows='4' aria-label='Codex command for {html.escape(str(item.get('work_package_id')))}'>{html.escape(command)}</textarea>"
            out.append("<tr>"
                f"<td>{html.escape(str(item.get('work_package_id')))}</td>"
                f"<td>{html.escape(str(item.get('title')))}<br><span class='source'>{html.escape(str(item.get('path') or 'missing path'))}</span></td>"
                f"<td>{html.escape(str(item.get('mode')))}</td>"
                f"<td>{html.escape(str(item.get('owner')))}</td>"
                f"<td>{html.escape(str(item.get('dependency_notes')))}</td>"
                f"<td>{action}</td>"
                f"<td>{html.escape(str(item.get('completion_status')))} / {html.escape(str(item.get('review_status')))}</td>"
                "</tr>")
        out.append("</tbody></table></section>")
    out.append(f"<p class='source'>Source: {html.escape(artifact.get('path', ''))}; {html.escape(str(data.get('source') or 'local artifacts'))}</p></div>")
    return "".join(out)


def _validation_health_html(artifact):
    data = artifact.get("data") or {}
    checks = data.get("checks") or []
    badge = html.escape(str(data.get("overall_health") or "missing"))
    out = [f"<div class='health-summary'><p><strong>Overall Estate health:</strong> <span class='health-badge {badge}'>{badge}</span></p>"]
    out.append(f"<p><strong>Last successful validation:</strong> {html.escape(str(data.get('last_successful_validation_time') or 'Not available yet'))}</p>")
    out.append(f"<p><strong>Recommended next action:</strong> {html.escape(str(data.get('recommended_next_action') or 'Review source reports.'))}</p></div>")
    out.append("<table class='health-table'><thead><tr><th>Subsystem</th><th>State</th><th>Warnings</th><th>Failures / blocked</th><th>Source</th></tr></thead><tbody>")
    for check in checks:
        state = html.escape(str(check.get("state") or "missing"))
        warnings = "<br>".join(html.escape(str(w)) for w in (check.get("warnings") or [])) or "None"
        problems = "<br>".join(html.escape(str(v)) for v in ((check.get("failures") or []) + (check.get("blocked") or []))) or "None"
        source = _artifact_link(check.get("path"))
        out.append("<tr>"
                   f"<td>{html.escape(str(check.get('label')))}</td>"
                   f"<td><span class='health-badge {state}'>{state}</span></td>"
                   f"<td>{warnings}</td>"
                   f"<td>{problems}</td>"
                   f"<td>{source}</td>"
                   "</tr>")
    out.append("</tbody></table><p class='source'>Generated dashboard is advisory and links to source reports; it does not replace validation logic.</p>")
    return "".join(out)


def _mailbox_message_list(messages, empty_text):
    if not messages:
        return f"<p class='placeholder'>{html.escape(empty_text)}</p>"
    rows = []
    for message in messages[:12]:
        title = html.escape(str(message.get("title") or "Untitled message"))
        meta = html.escape(" · ".join(str(v) for v in [message.get("priority"), message.get("status"), message.get("created_at")] if v))
        path = html.escape(str(message.get("path") or "missing source path"))
        ack = "ack required" if message.get("requires_ack") else "no ack"
        warning = f"<br><span class='mailbox-warning'>{html.escape(str(message.get('warning')))}</span>" if message.get("warning") else ""
        rows.append(f"<li><strong>{title}</strong><br><span class='source'>{meta} · {html.escape(ack)}</span>{warning}<br><span class='source'>Source: {path}</span></li>")
    return f"<ul>{''.join(rows)}</ul>"


def _mailbox_operations_center_html(artifact):
    if not artifact.get("available"):
        return _artifact_html(artifact)
    data = artifact.get("data") or {}
    summary = data.get("summary") or {}
    cards = [
        ("Messages", summary.get("message_count")),
        ("Open", summary.get("open_message_count")),
        ("Ack required", summary.get("ack_required_count")),
        ("Waiting on Steward", summary.get("waiting_on_steward_count")),
        ("Warnings", summary.get("warning_count")),
        ("Last sync", summary.get("last_mailbox_synchronization_time") or "not available"),
    ]
    out = ["<div class='mailbox-operations-center'><h3>Mailbox Operations Center</h3>", "<div class='mailbox-kpis'>"]
    for label, value in cards:
        out.append(f"<span class='mailbox-kpi'><strong>{html.escape(label)}</strong><span>{html.escape(str(value if value is not None else 'missing'))}</span></span>")
    out.append("</div><h3>Mailbox summary by resident / office / worker</h3>")
    mailboxes = data.get("by_mailbox") or []
    if not mailboxes:
        out.append("<p class='placeholder'>No mailbox messages were found in the current artifacts.</p>")
    else:
        out.append("<table><thead><tr><th>Mailbox</th><th>Type</th><th>Messages</th><th>Open</th><th>Ack required</th><th>Waiting on Steward</th><th>Details</th></tr></thead><tbody>")
        for box in mailboxes:
            details = _mailbox_message_list(box.get("messages") or [], "No messages in this mailbox.")
            out.append("<tr>"
                       f"<td>{html.escape(str(box.get('label') or 'Unknown mailbox'))}</td>"
                       f"<td>{html.escape(str(box.get('kind') or 'mailbox'))}</td>"
                       f"<td>{html.escape(str(box.get('message_count') or 0))}</td>"
                       f"<td>{html.escape(str(box.get('open_count') or 0))}</td>"
                       f"<td>{html.escape(str(box.get('ack_required_count') or 0))}</td>"
                       f"<td>{html.escape(str(box.get('waiting_on_steward_count') or 0))}</td>"
                       f"<td><details><summary>Show summarized messages</summary>{details}</details></td>"
                       "</tr>")
        out.append("</tbody></table>")
    out.append("<h3>Unread / open messages</h3>" + _mailbox_message_list(data.get("open_messages") or [], "No open messages were found."))
    out.append("<h3>Acknowledgement-required messages</h3>" + _mailbox_message_list(data.get("ack_required_messages") or [], "No acknowledgement-required messages were found."))
    out.append("<h3>Messages waiting on the Steward</h3>" + _mailbox_message_list(data.get("steward_waiting_messages") or [], "No messages are currently addressed to or waiting on the Steward."))
    out.append("<h3>Unresolved or ambiguous destination warnings</h3>" + _mailbox_message_list(data.get("destination_warnings") or [], "No unresolved destination warnings were found."))
    if data.get("missing_sources"):
        out.append(f"<p class='placeholder'>Missing supporting mailbox artifact(s): {html.escape(', '.join(data.get('missing_sources')))}</p>")
    sources = data.get("sources") or {}
    out.append("<p class='source'>Sources: " + "; ".join(f"{html.escape(str(k))}: {html.escape(str(v or 'not available'))}" for k, v in sources.items()) + ". This panel summarizes only; it does not mark mail read or acknowledged.</p></div>")
    return "".join(out)



def _board_rows(items, columns, empty_text):
    if not items:
        return f"<p class='placeholder'>{html.escape(empty_text)}</p>"
    out = ["<table><thead><tr>" + "".join(f"<th>{html.escape(c)}</th>" for c in columns) + "</tr></thead><tbody>"]
    for item in items[:20]:
        out.append("<tr>" + "".join(f"<td>{html.escape(str(item.get(c) or item.get(c.lower()) or ''))}</td>" for c in columns) + "</tr>")
    out.append("</tbody></table>")
    return "".join(out)


def _daily_board_workspace_html(artifact, parking_only=False):
    if not artifact.get("available"):
        return _artifact_html(artifact)
    data = artifact.get("data") or {}
    out = ["<div class='daily-board-workspace'>"]
    if not parking_only:
        out.append("<p>This workspace keeps today’s Daily Board separate from deferred Parking Lot ideas. Parking Lot items are shown for review only and are not automatically promoted.</p>")
        out.append("<h3>Current daily priorities</h3>" + _board_rows(data.get("daily_priorities") or [], ["ID", "Task", "Owner", "Status", "Blocker", "Review Required", "Next Action"], "No current daily priorities were found in the Daily Board."))
        out.append("<h3>Active board items</h3>" + _board_rows(data.get("active_board_items") or [], ["ID", "Item", "Owner", "Status", "Next Action"], "No active board items were found in available artifacts."))
        out.append("<h3>Blocked items</h3>" + _board_rows(data.get("blocked_items") or [], ["ID", "Item", "Blocker", "Owner", "Escalation Needed"], "No blocked items were found in available board or pipeline artifacts."))
        out.append("<h3>Review required</h3>" + _board_rows(data.get("review_required") or [], ["ID", "Item", "Reviewer", "Reason", "Ready Since"], "No Daily Board review-required items were found."))
    out.append("<h3>Parking Lot items</h3>" + _board_rows(data.get("parking_lot_items") or [], ["ID", "Idea", "Category", "Priority", "Originator", "Status", "Promotion Condition"], "No Parking Lot items were found."))
    out.append("<h3>Promotion conditions (informational only)</h3>")
    conditions = data.get("promotion_conditions") or []
    out.append("<ul>" + "".join(f"<li>{html.escape(str(item))}</li>" for item in conditions[:20]) + "</ul>" if conditions else "<p class='placeholder'>No documented promotion conditions were found.</p>")
    out.append("<h3>Items recommended for review</h3>")
    review = data.get("items_recommended_for_review") or []
    out.append("<ul>" + "".join(f"<li>{html.escape(str(item))}</li>" for item in review[:12]) + "</ul>" if review else "<p class='placeholder'>No review recommendations were found.</p>")
    if not parking_only:
        actions = data.get("recommended_next_actions") or []
        out.append("<h3>Recommended next actions</h3>" + ("<ul>" + "".join(f"<li>{html.escape(str(item))}</li>" for item in actions[:12]) + "</ul>" if actions else "<p class='placeholder'>No recommended next actions were found.</p>"))
    sources = data.get("sources") or {}
    out.append("<p class='source'>Sources: " + "; ".join(f"{html.escape(name)}: {html.escape(str((src or {}).get('path') or (src or {}).get('placeholder') or 'not available'))}" for name, src in sources.items()) + ".</p></div>")
    return "".join(out)


def _expansion_roadmap_html(artifact):
    if not artifact.get("available"):
        return _artifact_html(artifact)
    data = artifact.get("data") or {}
    out = ["<div class='expansion-roadmap-workspace'>"]
    out.append("<p>This workspace keeps expansion planning separate from Active Projects and the Daily Board. It is advisory and does not approve, commit, or promote future work.</p>")
    out.append(f"<p><strong>Current roadmap horizon:</strong> {html.escape(str(data.get('current_horizon') or 'Not available yet.'))}</p>")
    def roadmap_table(title, rows, empty):
        buf = [f"<h3>{html.escape(title)}</h3>"]
        if not rows:
            buf.append(f"<p class='placeholder'>{html.escape(empty)}</p>")
            return "".join(buf)
        buf.append("<table><thead><tr><th>Item</th><th>Status</th><th>Horizon</th><th>Dependency notes</th><th>Next step</th><th>Source</th></tr></thead><tbody>")
        for item in rows[:20]:
            buf.append("<tr>" + f"<td>{html.escape(str(item.get('title') or 'Untitled'))}</td><td>{html.escape(str(item.get('status') or 'proposed'))}</td><td>{html.escape(str(item.get('horizon') or 'Not specified'))}</td><td>{html.escape(str(item.get('dependency_notes') or 'None recorded'))}</td><td>{html.escape(str(item.get('next_step') or 'Review source artifact.'))}</td><td>{_artifact_link(item.get('source'))}</td>" + "</tr>")
        buf.append("</tbody></table>")
        return "".join(buf)
    out.append(roadmap_table("Roadmap items by evidence-backed state", data.get("items") or [], "No roadmap items were found in available artifacts."))
    out.append(roadmap_table("Upcoming epics", data.get("upcoming_epics") or [], "No upcoming epics were found."))
    out.append(roadmap_table("Planned but not active initiatives", data.get("planned_not_active") or [], "No planned but inactive initiatives were found."))
    out.append(roadmap_table("Items eligible for future work packages", data.get("future_work_package_candidates") or [], "No future work package candidates were found."))
    arch = data.get("pending_architecture_decisions") or []
    out.append("<h3>Pending architecture decisions</h3>")
    if arch:
        out.append("<ul>" + "".join(f"<li>{html.escape(str(a.get('title')))} — {html.escape(str(a.get('status')))}<br><span class='source'>Source: {_artifact_link(a.get('source'))}</span></li>" for a in arch[:12]) + "</ul>")
    else:
        out.append("<p class='placeholder'>No pending architecture decision documents were found.</p>")
    sources = data.get("sources") or {}
    out.append("<p class='source'>Sources: " + "; ".join(f"{html.escape(name)}: {html.escape(str((src or {}).get('path') or (src or {}).get('placeholder') or 'not available'))}" for name, src in sources.items()) + ".</p></div>")
    return "".join(out)

def _steward_recall_operations_html(artifact):
    if not artifact.get("available"):
        return _artifact_html(artifact)
    data = artifact.get("data") or {}
    summary = data.get("summary") or {}
    recalls = data.get("recalls") or []
    out = ["<div class='steward-recall-operations'>"]
    out.append("<p>This view is reserved for Steward Recall operations and is separate from ordinary notifications. It summarizes existing artifacts only; it does not send, approve, escalate, or acknowledge recalls.</p>")
    cards = [("Total recalls", summary.get("recall_count")), ("Active recalls", summary.get("active_recall_count")), ("Missing sources", summary.get("missing_source_count"))]
    out.append("<div class='mailbox-kpis'>" + "".join(f"<span class='mailbox-kpi'><strong>{html.escape(label)}</strong><span>{html.escape(str(value if value is not None else 'missing'))}</span></span>" for label, value in cards) + "</div>")
    if not recalls:
        out.append("<p class='placeholder'>No recall requests were found in available local artifacts.</p>")
    else:
        out.append("<table><thead><tr><th>Recall</th><th>Reason</th><th>Requested by / origin</th><th>Alfred state</th><th>Transport</th><th>Delivery</th><th>Acknowledgement</th><th>Lifecycle</th><th>Timestamp</th><th>Sources</th></tr></thead><tbody>")
        for recall in recalls[:25]:
            sources = "<br>".join(_artifact_link(src) for src in recall.get("source_artifacts") or []) or "not available"
            lifecycle = html.escape(str(recall.get("lifecycle_stage") or "unknown"))
            out.append("<tr>"
                       f"<td>{html.escape(str(recall.get('recall_id') or 'recall'))}</td>"
                       f"<td>{html.escape(str(recall.get('reason') or 'unknown'))}</td>"
                       f"<td>{html.escape(str(recall.get('requested_by') or 'unknown'))}<br><span class='source'>{html.escape(str(recall.get('originating_worker') or 'unknown'))}</span></td>"
                       f"<td>{html.escape(str(recall.get('alfred_decision_state') or 'pending/unknown'))}</td>"
                       f"<td>{html.escape(str(recall.get('transport_used') or 'unknown'))}</td>"
                       f"<td>{html.escape(str(recall.get('delivery_result') or 'unknown'))}</td>"
                       f"<td>{html.escape(str(recall.get('acknowledgement_state') or 'unknown'))}</td>"
                       f"<td><span class='health-badge {lifecycle}'>{lifecycle}</span></td>"
                       f"<td>{html.escape(str(recall.get('timestamp') or 'unknown'))}</td>"
                       f"<td>{sources}</td>"
                       "</tr>")
        out.append("</tbody></table>")
    if data.get("missing_sources"):
        out.append(f"<p class='placeholder'>Missing recall artifact(s): {html.escape(', '.join(data.get('missing_sources')))}</p>")
    sources = data.get("sources") or {}
    out.append("<p class='source'>Sources: " + "; ".join(f"{html.escape(name)}: {html.escape(str((src or {}).get('path') or (src or {}).get('placeholder') or 'not available'))}" for name, src in sources.items()) + ". Alfred remains the recall authority path; this panel is read-only.</p></div>")
    return "".join(out)


def _capability_dependency_visualization_html(artifact):
    if not artifact.get("available"):
        return _artifact_html(artifact)
    data = artifact.get("data") or {}
    summary = data.get("summary") or {}
    out = ["<div class='capability-dependency-visualization'>"]
    out.append("<p>Read-only capability dependency view. It shows only explicit registry/dependency metadata and links nodes back to authoritative artifacts.</p>")
    out.append("<div class='mailbox-kpis'>" + "".join(f"<span class='mailbox-kpi'><strong>{html.escape(label)}</strong><span>{html.escape(str(value))}</span></span>" for label, value in [("Nodes", summary.get("node_count", 0)), ("Edges", summary.get("edge_count", 0)), ("Warnings", summary.get("warning_count", 0))]) + "</div>")
    nodes = data.get("nodes") or []
    if nodes:
        out.append("<table><thead><tr><th>Capability</th><th>Readiness</th><th>Implementation</th><th>Validation</th><th>Upstream</th><th>Downstream</th><th>Authoritative links</th></tr></thead><tbody>")
        for node in nodes[:50]:
            links = "<br>".join(_artifact_link(src) for src in node.get("source_artifact_links") or [node.get("authoritative_artifact")])
            out.append("<tr>"
                       f"<td>{html.escape(str(node.get('label') or node.get('id')))}<br><span class='source'>{html.escape(str(node.get('id')))}</span></td>"
                       f"<td><span class='health-badge {html.escape(str(node.get('readiness') or 'unknown'))}'>{html.escape(str(node.get('readiness') or 'unknown'))}</span></td>"
                       f"<td>{html.escape(str(node.get('implementation_status') or 'unknown'))}</td>"
                       f"<td>{html.escape(str(node.get('validation_status') or 'unknown'))}</td>"
                       f"<td>{html.escape(', '.join(node.get('upstream_dependencies') or []) or 'None explicitly recorded')}</td>"
                       f"<td>{html.escape(', '.join(node.get('downstream_dependents') or []) or 'None explicitly recorded')}</td>"
                       f"<td>{links or 'unresolved external reference'}</td>"
                       "</tr>")
        out.append("</tbody></table>")
    else:
        out.append("<p class='placeholder'>No capability nodes are available.</p>")
    edges = data.get("edges") or []
    out.append("<h3>Explicit relationships</h3>")
    if edges:
        out.append("<ul>" + "".join(f"<li><code>{html.escape(str(e.get('source')))}</code> → <code>{html.escape(str(e.get('target')))}</code> ({html.escape(str(e.get('dependency_type')))}), source {_artifact_link(e.get('source_artifact'))}</li>" for e in edges[:50]) + "</ul>")
    else:
        out.append("<p class='placeholder'>No explicit dependency relationships were found.</p>")
    out.append("<p class='source'>Sources: " + html.escape(str(data.get("inputs", {}))) + ". This panel is read-only and does not modify governance or lifecycle state.</p></div>")
    return "".join(out)


def _operational_activity_html(artifact):
    data = artifact or {}
    expected = data.get("expected_status_artifact_paths") or []
    errors = data.get("errors") or []
    summary = data.get("summary") or {}
    out = ["<div class='operational-activity-panel'>"]
    out.append("<p>Read-only operational activity surface. Every item below comes from runtime operational status artifacts; this panel does not write events, dispatch workers, or invent activity.</p>")
    out.append("<div class='mailbox-kpis'>" + "".join(f"<span class='mailbox-kpi'><strong>{html.escape(label)}</strong><span>{html.escape(str(value))}</span></span>" for label, value in [("Activities", summary.get("activity_count", 0)), ("Status artifacts found", summary.get("status_artifact_found", False)), ("Malformed/error artifacts", summary.get("error_count", 0)), ("Runtime dir accessible", data.get("runtime_directory_accessible"))]) + "</div>")
    if not data.get("available"):
        out.append(f"<p class='placeholder'>{html.escape(data.get('empty_state') or 'No active operational status found.')}</p>")
        out.append("<p class='source'>Expected status artifact paths: " + html.escape(', '.join(expected)) + ". No fake green status is shown.</p>")
    if errors:
        out.append("<h3>Status artifact errors</h3><ul>" + "".join(f"<li><strong>{html.escape(str(e.get('path')))}</strong>: {html.escape(str(e.get('message')))}</li>" for e in errors) + "</ul>")
    latest = data.get("latest_status") or {}
    if latest:
        fresh = latest.get("freshness") or {}
        out.append("<h3>Latest status</h3><p><strong>" + html.escape(str(latest.get("activity_id") or "unknown")) + "</strong> — " + html.escape(str(latest.get("current_state") or "unknown")) + " · <span class='health-badge " + html.escape(str(fresh.get("state") or "uncertain")) + "'>" + html.escape(str(fresh.get("state") or "uncertain")) + "</span><br>" + html.escape(str(latest.get("display_message") or "")) + "</p>")
    intake_surface = data.get("orchestrator_intake_decisions") or {}
    intake_items = intake_surface.get("items") or []
    out.append(f"<section class='pipeline-section orchestrator-intake'><h3>Orchestrator Intake Decisions ({len(intake_items)})</h3>")
    if not intake_items:
        out.append("<p class='placeholder'>No pending or blocked Orchestrator intake items are awaiting decisions.</p></section>")
    else:
        out.append("<table><thead><tr><th>Intake</th><th>Work package</th><th>Source / mission</th><th>Summary</th><th>Class / priority</th><th>Requirements</th><th>Latest decision</th><th>Available decisions</th></tr></thead><tbody>")
        for item in intake_items[:25]:
            decisions = item.get('available_decisions') or []
            controls = []
            for decision_name in decisions:
                controls.append("<button class='office-action' data-office-action='orchestrator_intake.record_decision' data-intake-id='" + html.escape(str(item.get('intake_id') or '')) + "' data-decision='" + html.escape(str(decision_name)) + "' data-decided-by='Steward'>" + html.escape(str(decision_name)) + "</button>")
            latest_decision = item.get('latest_decision') or {}
            requirements = f"boundary={item.get('boundary_review_required')}<br>approval={item.get('approval_required')}<br>validation={item.get('validation_required')}"
            if item.get('summary_redacted'):
                summary_text = str(item.get('safe_summary') or '') + ' (redacted by classification rule)'
            else:
                summary_text = str(item.get('safe_summary') or '')
            out.append("<tr>"
                       f"<td>{html.escape(str(item.get('intake_id') or 'unknown'))}<br><span class='source'>{html.escape(str(item.get('state') or 'unknown'))}</span></td>"
                       f"<td>{html.escape(str(item.get('work_package_id') or item.get('work_package_path') or 'none'))}</td>"
                       f"<td>{html.escape(str(item.get('source') or 'unknown'))}<br>{html.escape(str(item.get('mission') or ''))}</td>"
                       f"<td>{html.escape(summary_text)}</td>"
                       f"<td>{html.escape(str(item.get('classification') or 'Estate Internal'))}<br><span class='source'>{html.escape(str(item.get('priority') or 'normal'))}</span></td>"
                       f"<td>{requirements}</td>"
                       f"<td>{html.escape(str(latest_decision.get('decision') or 'none'))}</td>"
                       f"<td>{''.join(controls)}</td>"
                       "</tr>")
        out.append("</tbody></table></section>")
    groups = data.get("groups") or {}
    for key, label in data.get("group_order") or []:
        items = groups.get(key) or []
        out.append(f"<section class='pipeline-section {html.escape(str(key))}'><h3>{html.escape(str(label))} ({len(items)})</h3>")
        if not items:
            out.append("<p class='placeholder'>No operational status items in this group.</p></section>")
            continue
        out.append("<table><thead><tr><th>Worker / provider</th><th>Assignment</th><th>State</th><th>Elapsed</th><th>Budget / class</th><th>Validation / attention</th><th>Message</th><th>Artifacts</th><th>Freshness</th></tr></thead><tbody>")
        for item in items[:25]:
            fresh = item.get("freshness") or {}
            artifacts = item.get("artifact_paths") or []
            artifact_text = "<br>".join(html.escape(str(a)) for a in artifacts[:6]) or "None recorded"
            worker_provider = f"{html.escape(str(item.get('worker_id') or item.get('worker_role') or 'unknown'))}<br><span class='source'>{html.escape(str(item.get('provider_id') or item.get('provider_type') or 'provider unknown'))}</span>"
            assignment = item.get('assignment_id') or item.get('work_package_id') or item.get('request_id') or item.get('activity_id') or 'unknown'
            msg = item.get('display_message') or ''
            if item.get('message_redacted'):
                msg += ' (redacted by classification rule)'
            out.append("<tr>"
                       f"<td>{worker_provider}</td>"
                       f"<td>{html.escape(str(assignment))}</td>"
                       f"<td>{html.escape(str(item.get('current_state') or 'unknown'))}</td>"
                       f"<td>{html.escape(str(item.get('elapsed_seconds') if item.get('elapsed_seconds') is not None else 'unknown'))}s</td>"
                       f"<td>{html.escape(str(item.get('budget_source') or 'unknown'))}<br><span class='source'>{html.escape(str(item.get('classification') or 'Estate Internal'))}</span></td>"
                       f"<td>{html.escape(str(item.get('validation_status') or 'not_validated'))}<br>attention={html.escape(str(item.get('requires_attention')))}</td>"
                       f"<td>{html.escape(str(msg))}</td>"
                       f"<td>{artifact_text}</td>"
                       f"<td><span class='health-badge {html.escape(str(fresh.get('state') or 'uncertain'))}'>{html.escape(str(fresh.get('state') or 'uncertain'))}</span><br><span class='source'>{html.escape(str(fresh.get('message') or ''))}</span></td>"
                       "</tr>")
        out.append("</tbody></table></section>")
    out.append("<p class='source'>Sources: " + html.escape(str(data.get("path") or "; ".join(expected))) + ". Classification behavior: " + html.escape(str(data.get("classification_behavior") or "safe display")) + "</p></div>")
    return "".join(out)

def _artifact_html(artifact):
    if not artifact.get("available"):
        path = artifact.get("path") or "not yet produced"
        return f'<p class="placeholder">{html.escape(artifact.get("placeholder", "Unavailable"))}</p><p class="source">Source: {html.escape(str(path))}</p>'
    if artifact.get("kind") == "json":
        content = _summarize_json(artifact.get("data"))
    else:
        content = (artifact.get("text") or "").strip()[:1000] or "Text artifact is present but empty."
    return f'<pre>{html.escape(content)}</pre><p class="source">Source: {html.escape(artifact.get("path", ""))}</p>'



def _fmt_indicator(label, value):
    display = "missing" if value is None else str(value)
    return f'<span class="status-item"><strong>{html.escape(label)}</strong> <span>{html.escape(display)}</span></span>'


def _status_bar_html(status):
    items = [
        ("Estate", status.get("estate_status")),
        ("Refresh", status.get("last_refresh_time")),
        ("Validation", status.get("validation_state")),
        ("Health", status.get("health_state")),
        ("Decisions", status.get("pending_decisions")),
        ("Mailbox", status.get("mailbox_count")),
        ("Mail open", status.get("mailbox_open_count")),
        ("Mail ack", status.get("mailbox_ack_required_count")),
        ("Mail warn", status.get("mailbox_warning_count")),
        ("Active recalls", status.get("active_recall_count")),
        ("Notifications", status.get("notification_count")),
        ("Exec active", status.get("execution_active_count")),
        ("Exec blocked", status.get("execution_blocked_count")),
        ("Exec attention", status.get("execution_attention_required_count")),
        ("Exec failed", status.get("execution_failed_count")),
        ("Workers", status.get("active_workers")),
        ("Steward", status.get("steward_presence_state")),
        ("Verbosity", status.get("verbosity")),
        ("Version", status.get("version")),
    ]
    return f'<footer id="status-bar" class="status-bar" aria-live="polite">{"".join(_fmt_indicator(label, value) for label, value in items)}</footer>'


def _activity_console_html(console):
    options = "".join(
        f'<option value="{html.escape(option)}" {"selected" if option == console.get("selected_verbosity") else ""}>{html.escape(option.title())}</option>'
        for option in console.get("verbosity_options", ["quiet", "normal", "detailed", "diagnostic"])
    )
    events = console.get("events") or []
    if not events:
        rows = '<tr><td colspan="5" class="placeholder">No activity data is available yet.</td></tr>'
    else:
        rows = "".join(
            "<tr>"
            f"<td>{html.escape(str(event.get('timestamp') or 'unknown'))}</td>"
            f"<td>{html.escape(str(event.get('source') or 'unknown'))}</td>"
            f"<td>{html.escape(str(event.get('topic') or 'general'))}</td>"
            f"<td><span class='severity {html.escape(str(event.get('severity') or 'info'))}'>{html.escape(str(event.get('severity') or 'info'))}</span></td>"
            f"<td>{html.escape(str(event.get('message') or 'No message provided.'))}</td>"
            "</tr>"
            for event in events
        )
    open_attr = "" if console.get("collapsed_by_default", True) else " open"
    return f"""<aside id="activity-console" class="activity-console">
<details{open_attr}><summary>Activity Console</summary>
<label for="verbosity-selector">Verbosity</label> <select id="verbosity-selector">{options}</select>
<table id="activity-events"><thead><tr><th>Timestamp</th><th>Source</th><th>Topic</th><th>Severity</th><th>Message</th></tr></thead><tbody>{rows}</tbody></table>
<p class="source">Quiet refresh updates only status and console regions from local JSON.</p>
</details></aside>"""



def _snapshot_source_artifacts(payload):
    artifacts = []
    for panel_id, panel in (payload.get("panels") or {}).items():
        if not isinstance(panel, dict):
            continue
        paths = panel.get("path")
        if not paths:
            continue
        for path in str(paths).split(";"):
            path = path.strip()
            if path:
                artifacts.append({"panel_id": panel_id, "path": path, "available": bool(panel.get("available")), "kind": panel.get("kind") or "unknown"})
    return artifacts


def build_office_snapshot_manifest(payload):
    """Build the schema metadata mirrored by the browser-side Office Snapshot export."""
    active_tab = ((payload.get("workspace_profile") or {}).get("profile") or {}).get("active_tab") or "home"
    return {
        "schema_version": "office-snapshot-v1",
        "local_only": True,
        "created_at": _now(),
        "active_tab": active_tab,
        "active_navigation_item": active_tab,
        "package_contents": ["snapshot_manifest.json", "page.html", "dom_state.json", "ui_metadata.json", "styles.css", "scripts.js", "source_artifacts.json", "README.md"],
        "known_limitations": ["Screenshot capture is not included in WP-0117 first pass; use a separate local screenshot if needed.", "Browser security may prevent fetching some external stylesheet/script bodies; references and failures are recorded instead."],
        "source_artifact_count": len(_snapshot_source_artifacts(payload)),
    }

def _refresh_script():
    return """<script>
async function refreshOperationsChrome(){
  if(location.protocol === 'file:'){ updateUiRuntimeDiagnostic('ready', 'UI runtime: scripts loaded / navigation bound / active tab: ' + getActiveOfficeTab()); return; }
  try{
    const response = await fetch('/status.json', {cache: 'no-store'});
    if(!response.ok) return;
    const payload = await response.json();
    const parser = new DOMParser();
    const doc = parser.parseFromString(payload.status_bar_html + payload.activity_console_html, 'text/html');
    const nextStatus = doc.querySelector('#status-bar');
    const nextConsole = doc.querySelector('#activity-console');
    const currentStatus = document.querySelector('#status-bar');
    const currentConsole = document.querySelector('#activity-console');
    if(nextStatus && currentStatus) currentStatus.replaceWith(nextStatus);
    if(nextConsole && currentConsole) currentConsole.replaceWith(nextConsole);
  }catch(error){ console.debug('Quiet refresh skipped', error); }
}
window.addEventListener('load', () => { refreshOperationsChrome(); if(location.protocol !== 'file:') window.setInterval(refreshOperationsChrome, 30000); });
</script>"""

def _layout_framework_html(artifact):
    data = artifact.get("data") or {}
    region_rows = "".join(f"<tr><td>{html.escape(str(r.get('label')))}</td><td>{html.escape(str(r.get('role')))}</td><td>{html.escape(str(r.get('selector')))}</td><td>{html.escape(str(r.get('dynamic_update')))}</td></tr>" for r in data.get("regions") or [])
    default_preferences = html.escape(json.dumps(data.get("default_preferences") or {}, indent=2, sort_keys=True))
    futures = ", ".join(str(item) for item in data.get("future_integration_points") or [])
    return (
        "<section class='layout-framework' aria-label='Operations Center Layout Framework'>"
        f"<p><strong>Version:</strong> {html.escape(str(data.get('version', 'unknown/unavailable')))} · <strong>Preference key:</strong> <code>{html.escape(str(data.get('layout_preference_key')))}</code></p>"
        "<p>This framework defines modular regions for the Operations Center shell while preserving existing UI state ownership.</p>"
        f"<table><thead><tr><th>Region</th><th>Role</th><th>Selector</th><th>Dynamic update behavior</th></tr></thead><tbody>{region_rows}</tbody></table>"
        f"<h3>Default workspace preferences</h3><pre>{default_preferences}</pre>"
        f"<p class='source'>State authority: {html.escape(str(data.get('state_authority')))}. Future integration points: {html.escape(futures)}.</p>"
        "</section>"
    )


def _settings_html(artifact):
    data = artifact.get("data") or {}
    theme = data.get("theme") or {}
    verbosity = data.get("global_verbosity") or {}
    visible = data.get("visible_panels") or {}
    topic = data.get("per_topic_verbosity") or {}
    resident = data.get("per_resident_verbosity") or {}
    theme_options = "".join(f"<option {'selected' if option == theme.get('value') else ''}>{html.escape(str(option))}</option>" for option in theme.get("options", []))
    verbosity_options = "".join(f"<option {'selected' if option == verbosity.get('value') else ''}>{html.escape(str(option))}</option>" for option in verbosity.get("options", []))
    panel_rows = "".join(f"<label><input type='checkbox' checked disabled> {html.escape(str(label))}</label>" for label in visible)
    topic_rows = "".join(f"<dt>{html.escape(str(k).title())}</dt><dd>{html.escape(str(v))}</dd>" for k, v in topic.items())
    resident_rows = "".join(f"<dt>{html.escape(str(k))}</dt><dd>{html.escape(str(v))}</dd>" for k, v in resident.items())
    tab_order = ", ".join(str(tab) for tab in data.get("tab_order") or [])
    pinned = ", ".join(str(tab) for tab in data.get("pinned_views") or [])
    refresh = data.get("refresh_behavior") or {}
    warnings = data.get("warnings") or []
    warning_rows = "".join(f"<li>{html.escape(str(w.get('setting') or w.get('type')))} — {html.escape(str(w.get('message')))}</li>" for w in warnings)
    return (
        "<div class='settings-surface'>"
        "<p class='source'>Local-first UI preferences. Controls are initial placeholders unless marked by the browser shell; no secrets or cloud settings are stored.</p>"
        f"<p><strong>Settings version:</strong> {html.escape(str(data.get('settings_schema_version', 'unknown/unavailable')))} · <strong>UI config:</strong> {html.escape(str(data.get('ui_version', 'unknown/unavailable')))}</p>"
        f"<label>Theme <select disabled>{theme_options}</select></label>"
        f"<p><strong>Accent:</strong> {html.escape(str(data.get('accent', 'unknown/unavailable')))} · <strong>Default workspace:</strong> {html.escape(str(data.get('default_workspace_profile', 'unknown/unavailable')))} · <strong>Default verbosity profile:</strong> {html.escape(str(data.get('default_verbosity_profile', 'unknown/unavailable')))}</p>"
        f"<label>Global verbosity <select disabled>{verbosity_options}</select></label>"
        f"<p><strong>Refresh behavior:</strong> quiet local refresh every {html.escape(str(refresh.get('quiet_refresh_seconds', 'unknown/unavailable')))} seconds.</p>"
        f"<p><strong>Activity console visible:</strong> {html.escape(str(data.get('activity_console_visible', 'unknown/unavailable')))} · <strong>Status bar visible:</strong> {html.escape(str(data.get('status_bar_visible', 'unknown/unavailable')))}</p>"
        f"<p><strong>Tab order:</strong> {html.escape(tab_order)}</p>"
        f"<p><strong>Pinned views:</strong> {html.escape(pinned)}</p>"
        f"<h3>Visible panels</h3><div class='settings-grid'>{panel_rows}</div>"
        f"<h3>Per-topic verbosity placeholders</h3><dl>{topic_rows}</dl>"
        f"<h3>Per-resident verbosity placeholders</h3><dl>{resident_rows}</dl>"
        f"<h3>Safe-default warnings</h3><ul>{warning_rows or '<li>None</li>'}</ul>"
        f"<p class='source'>{html.escape(str(data.get('persistence')))}</p>"
        "</div>"
    )



def _help_html(artifact):
    data = artifact.get("data") or {}
    profile = data.get("workspace_profile") or {}
    panels = data.get("panels") or []
    workspaces = data.get("workspaces") or []
    command_help = data.get("command_console_help") or {}
    commands = command_help.get("commands") or []
    docs = data.get("documentation_links") or []
    unavailable = data.get("known_unavailable_features") or []
    notes = data.get("authority_notes") or []
    panel_rows = "".join(f"<tr><td>{html.escape(str(item.get('label')))}</td><td>{html.escape(str(item.get('id')))}</td><td>{html.escape('available' if item.get('available') else 'unknown/unavailable')}</td></tr>" for item in panels)
    workspace_rows = "".join(f"<tr><td>{html.escape(str(item.get('label')))}</td><td>{html.escape(str(item.get('id')))}</td><td>{html.escape('available' if item.get('available') else 'unknown/unavailable')}</td></tr>" for item in workspaces)
    command_rows = "".join(f"<tr><td><code>{html.escape(str(item.get('command')))}</code></td><td>{html.escape(str(item.get('service')))}</td><td>{html.escape(str(item.get('status')))}</td></tr>" for item in commands) or "<tr><td colspan='3'>unknown/unavailable</td></tr>"
    doc_rows = "".join(f"<tr><td>{html.escape(str(item.get('label')))}</td><td>{html.escape(str(item.get('path')))}</td><td>{html.escape('available' if item.get('available') else 'unknown/unavailable')}</td><td>{html.escape(str(item.get('summary')))}</td></tr>" for item in docs)
    unavailable_rows = "".join(f"<li><strong>{html.escape(str(item.get('feature')))}</strong>: {html.escape(str(item.get('reason')))}</li>" for item in unavailable) or "<li>No known unavailable help features from local artifacts.</li>"
    note_rows = "".join(f"<li>{html.escape(str(note))}</li>" for note in notes)
    service_links = ", ".join(data.get("service_catalog_links") or [])
    validation_links = ", ".join(data.get("validation_status_links") or [])
    return (
        "<section class='operations-help' aria-label='Operations Center Help'>"
        f"<p><strong>UI version:</strong> {html.escape(str(data.get('ui_version', 'unknown/unavailable')))}</p>"
        f"<p><strong>Active workspace profile:</strong> {html.escape(str(data.get('active_workspace_profile') or 'unknown/unavailable'))}; active tab: {html.escape(str(profile.get('active_tab') or 'unknown/unavailable'))}</p>"
        "<h3>Available panels</h3>"
        f"<table><thead><tr><th>Panel</th><th>ID</th><th>Status</th></tr></thead><tbody>{panel_rows}</tbody></table>"
        "<h3>Available workspaces</h3>"
        f"<table><thead><tr><th>Workspace</th><th>ID</th><th>Status</th></tr></thead><tbody>{workspace_rows}</tbody></table>"
        "<h3>Command Console Help</h3>"
        f"<p>{html.escape(str(command_help.get('summary') or 'unknown/unavailable'))} Command aliases listed: {html.escape(str(command_help.get('command_count', 0)))}.</p>"
        f"<table><thead><tr><th>Command</th><th>Service</th><th>Status</th></tr></thead><tbody>{command_rows}</tbody></table>"
        "<h3>Service Catalog and Validation Links</h3>"
        f"<p><strong>Service catalog:</strong> {html.escape(service_links)}</p><p><strong>Validation status:</strong> {html.escape(validation_links)}</p>"
        "<h3>Documentation Links</h3>"
        f"<table><thead><tr><th>Document</th><th>Path</th><th>Status</th><th>Summary</th></tr></thead><tbody>{doc_rows}</tbody></table>"
        "<h3>Local-first / Authority Boundary Notes</h3>"
        f"<ul>{note_rows}</ul>"
        "<h3>Known Unavailable Features</h3>"
        f"<ul>{unavailable_rows}</ul>"
        f"<p class='source'>Source: {html.escape(str(artifact.get('path') or 'local help aggregation'))}</p>"
        "</section>"
    )

def _about_html(artifact):
    data = artifact.get("data") or {}
    inventory = data.get("inventory") or []
    runtime_paths = data.get("runtime_paths") or []
    rows = "".join(f"<tr><td>{html.escape(str(item.get('component')))}</td><td>{html.escape(str(item.get('version') or 'unknown/unavailable'))}</td><td>{html.escape(str(item.get('status') or 'unknown/unavailable'))}</td></tr>" for item in inventory)
    path_rows = "".join(f"<tr><td>{html.escape(str(item.get('label')))}</td><td>{html.escape(str(item.get('path')))}</td><td>{html.escape('available' if item.get('available') else 'unknown/unavailable')}</td></tr>" for item in runtime_paths)
    return (
        "<h3>Component / Version Inventory</h3>"
        f"<table><thead><tr><th>Component</th><th>Version</th><th>Status</th></tr></thead><tbody>{rows}</tbody></table>"
        "<h3>Local Runtime Paths Used by the UI</h3>"
        f"<table><thead><tr><th>Artifact</th><th>Path</th><th>Status</th></tr></thead><tbody>{path_rows}</tbody></table>"
        f"<p class='source'>Source: {html.escape(str(artifact.get('path') or 'local component inventory'))}; local-only: {html.escape(str(data.get('local_only', True)))}</p>"
    )


def _nav_html(navigation, active_tab="home"):
    items = navigation.get("items") or []
    buttons = []
    for item in items:
        status = "ready" if item.get("available") else "placeholder"
        tab = str(item.get('tab') or '')
        active = " active" if tab == active_tab else ""
        current = " aria-current='page'" if tab == active_tab else ""
        safe_tab = html.escape(tab, quote=True)
        buttons.append(f"<button type='button' class='nav-item {status}{active}' data-tab='{safe_tab}' aria-controls='workspace-{safe_tab}'{current}>{html.escape(str(item.get('label')))}</button>")
    return f"<aside id='office-navigation' class='office-navigation' aria-label='Collapsed Office navigation drawer'><details><summary>Office Navigation</summary><div class='nav-items'>{''.join(buttons)}</div></details></aside>"


def _tab_bar_html(tabs, active_tab="home"):
    buttons = []
    for index, tab in enumerate(tabs or []):
        tab_id = str(tab.get('id') or '')
        is_active = tab_id == active_tab or (index == 0 and not active_tab)
        selected = "true" if is_active else "false"
        active = " active" if is_active else ""
        safe_tab = html.escape(tab_id, quote=True)
        buttons.append(f"<button type='button' id='tab-{safe_tab}' class='workspace-tab{active}' role='tab' aria-selected='{selected}' aria-controls='workspace-{safe_tab}' data-tab='{safe_tab}'>{html.escape(str(tab.get('label')))}</button>")
    return f"<div id='workspace-tabs' class='workspace-tabs' role='tablist'>{''.join(buttons)}</div>"


def _workspace_section(tab_id, label, body, active=False):
    active_class = " active" if active else ""
    hidden = "" if active else " hidden"
    safe_tab_id = html.escape(str(tab_id), quote=True)
    return f"<section id='workspace-{safe_tab_id}' class='workspace-view{active_class}' role='tabpanel'{hidden}><h2>{html.escape(label)}</h2>{body}</section>"



def _mission_control_html(panel):
    data = panel.get("data") if isinstance(panel.get("data"), dict) else panel
    summary = data.get("summary", {}) if isinstance(data, dict) else {}
    sources = data.get("sources", []) if isinstance(data, dict) else []
    lanes = data.get("lanes", []) if isinstance(data, dict) else []
    source_map = {source.get("name"): source for source in sources if isinstance(source, dict)}
    lane_cards = []
    for lane in lanes:
        cards = []
        for source_id in lane.get("sources", []):
            source = source_map.get(source_id, {"name": source_id, "available": False, "state": "missing", "path": "", "summary": "Not registered."})
            state = "ready" if source.get("available") else "placeholder"
            cards.append(f"<li class='{state}'><strong>{html.escape(str(source.get('name')))}</strong><br><span class='source'>{html.escape(str(source.get('path') or ''))}</span><br>{html.escape(str(source.get('state')))}</li>")
        lane_cards.append(f"<section class='panel'><h3>{html.escape(str(lane.get('title')))}</h3><ul>{''.join(cards)}</ul></section>")
    warnings = ''.join(f"<li>{html.escape(str(w.get('source')))}: {html.escape(str(w.get('message')))}</li>" for w in data.get("warnings", [])) if isinstance(data, dict) else ""
    return _panel("Mission Control", f"<p>State: <strong>{html.escape(str(summary.get('state', 'unknown')))}</strong> · Ready sources: {html.escape(str(summary.get('ready_source_count', 0)))} / {html.escape(str(summary.get('source_count', 0)))}</p><p>{html.escape(str(summary.get('recommended_next_action', '')))}</p>{''.join(lane_cards)}<h3>Capability Dependencies</h3>{_capability_dependency_visualization_html(data.get('capability_dependency_visualization', {})) if isinstance(data, dict) and data.get('capability_dependency_visualization') else ''}<h3>Warnings</h3><ul>{warnings or '<li>No Mission Control source warnings.</li>'}</ul>", "ready" if panel.get("available") else "placeholder")


def _operations_notification_center_html(panel):
    if not panel.get("available"):
        return _artifact_html(panel)
    data = panel.get("data") or {}
    summary = data.get("summary") or {}
    rows = []
    for note in data.get("notifications") or []:
        link = (note.get("source_link") or {}).get("path")
        rows.append("<tr>"
                    f"<td><span class='severity {html.escape(str(note.get('severity')))}'>{html.escape(str(note.get('severity')))}</span></td>"
                    f"<td>{html.escape(str(note.get('source')))}</td>"
                    f"<td>{html.escape(str(note.get('title')))}<br><span class='source'>{html.escape(str(note.get('message')))}</span></td>"
                    f"<td>{html.escape(str(note.get('state')))} / local ack={html.escape(str(note.get('locally_acknowledged')))}</td>"
                    f"<td>{_artifact_link(link)}</td>"
                    "</tr>")
    if not rows:
        rows.append('<tr><td colspan="5" class="placeholder">No notifications match the selected filters.</td></tr>')
    body = "<p>Aggregator only; acknowledgements are local Notification Center state and do not mutate authoritative source events.</p>"
    body += "<div class='mailbox-kpis'>" + "".join(f"<span class='mailbox-kpi'><strong>{html.escape(label)}</strong><span>{html.escape(str(value))}</span></span>" for label, value in [("Filtered", summary.get("filtered_notification_count", 0)), ("Total", summary.get("total_notification_count", 0)), ("Unavailable sources", summary.get("unavailable_source_count", 0)), ("Local acknowledgements", summary.get("locally_acknowledged_count", 0))]) + "</div>"
    body += "<table><thead><tr><th>Severity</th><th>Source</th><th>Notification</th><th>State</th><th>Source artifact</th></tr></thead><tbody>" + "".join(rows) + "</tbody></table>"
    body += f"<p class='source'>Quiet refresh: {html.escape(str(data.get('refresh_behavior')))}. Source: {html.escape(str(panel.get('path')))}</p>"
    return _panel("Operations Center Notification Center", body, "ready")

def _ai_services_models_html(panel):
    data = panel.get("data") or {}
    services = data.get("services") or []
    models = data.get("models") or []
    dashboard = data.get("dashboard") or {}
    prefs = ((data.get("model_preferences") or {}).get("preferences") or {})
    assigns = ((data.get("model_assignments") or {}).get("assignments") or {})
    approvals = (data.get("approvals") or {}).get("requests") or []
    actions = data.get("actions") or {}
    rows = ["<div class='ai-services-models'><p>Steward-governed local AI services and model selector. Actions are backed by ai-services CLI/API hooks and do not bypass policy gates.</p>"]
    rows.append("<h3>Dashboard</h3><div class='mailbox-kpis'>" + "".join(f"<span class='mailbox-kpi'><strong>{html.escape(str(k).replace('_',' ').title())}</strong><span>{html.escape(str(v))}</span></span>" for k, v in dashboard.items()) + "</div>")
    rows.append("<h3>Operational Controls</h3><table><thead><tr><th>Action</th><th>Local command hook</th></tr></thead><tbody>" + "".join(f"<tr><td>{html.escape(str(k).replace('_',' ').title())}</td><td><code>{html.escape(str(v))}</code></td></tr>" for k, v in actions.items()) + "</tbody></table>")
    rows.append("<h3>Services</h3><table><thead><tr><th>Service</th><th>Type</th><th>Endpoint / Ports</th><th>State / Health</th><th>Operations</th><th>Approval</th><th>Paths / Logs</th></tr></thead><tbody>")
    for svc in services:
        details = {"manifest": svc.get("manifest_path"), "models": svc.get("model_locations"), "host_policy": svc.get("host_policy"), "pid": svc.get("pid"), "last_health_result": svc.get("last_health_result"), "last_startup_time": svc.get("last_startup_time"), "startup_failures": svc.get("startup_failures"), "process_exit_code": svc.get("process_exit_code"), "working_directory": svc.get("working_directory"), "launcher": svc.get("launcher"), "local_only": svc.get("local_only")}
        rows.append("<tr>" + f"<td>{html.escape(str(svc.get('service_id')))}<br><span class='source'>{html.escape(str(svc.get('display_name')))}</span></td>" + f"<td>{html.escape(str(svc.get('service_type')))}</td>" + f"<td>{html.escape(str(svc.get('endpoint')))}<br>{html.escape(str(svc.get('ports')))}</td>" + f"<td>{html.escape(str(svc.get('current_state')))} / {html.escape(str(svc.get('health_status')))}<br><span class='source'>last: {html.escape(str(svc.get('last_operation')))}</span></td>" + f"<td>{html.escape(', '.join(svc.get('available_operations') or []))}<details><summary>Manifest operations</summary><pre>{html.escape(json.dumps(svc.get('operations') or {}, indent=2, sort_keys=True))}</pre></details></td>" + f"<td><pre>{html.escape(json.dumps(svc.get('approval_requirements') or {}, sort_keys=True))}</pre></td>" + f"<td><pre>{html.escape(json.dumps(details, indent=2, sort_keys=True))}</pre><span class='source'>log: {html.escape(str(svc.get('log_reference') or 'none'))}</span></td>" + "</tr>")
    rows.append("</tbody></table><h3>Model Inventory</h3><table><thead><tr><th>Model</th><th>Service</th><th>Source</th><th>Inventory State</th><th>Roles</th></tr></thead><tbody>")
    for m in models:
        roles = [name for name in ["installed", "currently_loaded", "preferred", "assigned", "default", "unavailable", "unresolved"] if m.get(name)]
        rows.append(f"<tr><td>{html.escape(str(m.get('model_id')))}<br><span class='source'>{html.escape(str(m.get('name')))}</span></td><td>{html.escape(str(m.get('backing_service')))}</td><td>{html.escape(str(m.get('source')))}<br><span class='source'>{html.escape(str(m.get('source_path') or m.get('model_location') or ''))}</span></td><td>{html.escape(str(m.get('source_status')))} / {html.escape(str(m.get('classification_status')))}</td><td>{html.escape(', '.join(roles) or 'known')}</td></tr>")
    rows.append("</tbody></table><h3>Estate Model Preferences</h3><pre>" + html.escape(json.dumps(prefs, indent=2, sort_keys=True)) + "</pre>")
    rows.append("<h3>Worker / Resident Assignments and Permissions</h3><pre>" + html.escape(json.dumps(assigns, indent=2, sort_keys=True)) + "</pre>")
    rows.append("<h3>Authority / Approvals</h3><pre>" + html.escape(json.dumps({"pending":[a for a in approvals if a.get('state') == 'requires_approval'], "approved":[a for a in approvals if a.get('state') == 'approved'], "denied":[a for a in approvals if a.get('state') == 'denied']}, indent=2, sort_keys=True)) + "</pre>")
    rows.append("<h3>Rediscovery / Audit</h3><pre>" + html.escape(json.dumps(data.get('audit_tail') or [], indent=2, sort_keys=True)) + "</pre>")
    rows.append(f"<p class='source'>Sources: {html.escape(str(panel.get('path')))}. Static HTML renders copyable local commands rather than executing host commands.</p></div>")
    return _panel("AI Services / Models", ''.join(rows), "ready")


def _office_action_controls_html(payload, tab_id):
    controls = (payload.get("office_actions") or {}).get(tab_id) or []
    if not controls:
        return ""
    rows = []
    for c in controls:
        aid = html.escape(str(c.get("action_id")), quote=True)
        label = html.escape(str(c.get("label") or c.get("action_id")))
        availability = c.get("availability") or "gated"
        note = html.escape(str(c.get("disabled_reason") or c.get("note") or ""))
        req = c.get("requires_input")
        input_html = ""
        if req:
            input_html = f"<input type='text' data-action-input='{html.escape(str(req), quote=True)}' placeholder='{html.escape(str(req))}'>"
        disabled = " disabled" if availability != "available" else ""
        button = f"<button type='button' data-office-action='{aid}'{disabled}>{label}</button>"
        rows.append(f"<tr><td>{button}<br>{input_html}</td><td>{html.escape(str(availability))}</td><td>{note}</td><td><code>{html.escape(str(c.get('handler') or 'gated'))}</code></td></tr>")
    return "<section class='panel office-actions'><h3>Operational Controls</h3><p class='source'>Every available control dispatches to a local handler. Gated controls are unavailable with a concrete reason.</p><table><thead><tr><th>Control</th><th>Availability</th><th>Outcome note / gating reason</th><th>Handler</th></tr></thead><tbody>" + "".join(rows) + "</tbody></table><pre id='office-action-result-" + html.escape(tab_id, quote=True) + "' class='office-action-result'>No action run yet.</pre></section>"

def render_command_center_html(payload):
    p = payload.get("panels", {})
    tab_bodies = [
        ("home", "Home", _home_workspace_html(payload)),
        ("mission-control", "Mission Control Workspace", _office_action_controls_html(payload, "mission-control") + _mission_control_html(p.get("mission_control_workspace", {}))),
        ("alfred", "Alfred Resident Card", _office_action_controls_html(payload, "alfred") + _resident_html(p.get("alfred_resident_card", {})) + _alfred_chat_html(p.get("alfred_chat", {}))),
        ("helen", "Helen Resident Card", _resident_html(p.get("helen_resident_card", {}))),
        ("resident-conversations", "Resident Conversations Workspace", _resident_conversations_html(p.get("resident_conversations_workspace", {}))),
        ("ai-services-models", "AI Services / Models", _office_action_controls_html(payload, "ai-services-models") + _ai_services_models_html(p.get("ai_services_models", {}))),
        ("daily-board", "Daily Board / Parking Lot Workspace", _office_action_controls_html(payload, "daily-board") + _panel("Morning Briefing", _artifact_html(p.get("morning_briefing", {})), "ready" if p.get("morning_briefing", {}).get("available") else "placeholder") + _daily_board_workspace_html(p.get("daily_board_workspace", {}))),
        ("operational-activity", "Operational Activity", _operational_activity_html(p.get("operational_activity", {}))),
        ("projects", "Work Package Pipeline", _work_package_pipeline_html(p.get("work_package_pipeline", {}))),
        ("roadmap", "Expansion Roadmap", _expansion_roadmap_html(p.get("expansion_roadmap", {}))),
        ("parking", "Parking Lot", _daily_board_workspace_html(p.get("daily_board_workspace", {}), parking_only=True)),
        ("work-packages", "Work Packages", _office_action_controls_html(payload, "work-packages") + _work_package_pipeline_html(p.get("work_package_pipeline", {}))),
        ("mailboxes", "Mailbox Summary / Operations Center", _mailbox_operations_center_html(p.get("mailbox_operations_center", {}))),
        ("recalls", "Steward Recall Operations", _steward_recall_operations_html(p.get("steward_recall_operations", {}))),
        ("notifications", "Operations Center Notification Center", _office_action_controls_html(payload, "notifications") + _operations_notification_center_html(p.get("operations_notification_center", {}))),
        ("validation", "Validation and Estate Health", _office_action_controls_html(payload, "validation") + _validation_health_html(p.get("validation_health_dashboard", {})) + _panel("Validation Status", _artifact_html(p.get("validation_status", {})), "ready" if p.get("validation_status", {}).get("available") else "placeholder")),
        ("search", "Global Search and Command Palette", _global_search_html(p.get("search", {}))),
        ("settings", "Settings", _settings_html(p.get("settings", {})) + _layout_framework_html(p.get("operations_center_layout", {}))),
        ("help", "Help", _help_html(p.get("help", {}))),
        ("about", "About", _about_html(p.get("about", {}))),
    ]
    selected_profile = (payload.get('workspace_profile') or {}).get('profile') or {}
    active_tab = selected_profile.get('active_tab') or 'home'
    workspace = "".join(_workspace_section(tab_id, label, body, active=(tab_id == active_tab)) for i, (tab_id, label, body) in enumerate(tab_bodies))
    status_bar = _status_bar_html(payload.get("status_bar", {}))
    activity_console = _activity_console_html(payload.get("activity_console", {}))
    generated = html.escape(str(payload.get("generated_at")))
    source_artifacts_json = _script_json(_snapshot_source_artifacts(payload))
    snapshot_manifest_json = _script_json(build_office_snapshot_manifest(payload))
    css = """body{font-family:system-ui,sans-serif;margin:0 0 9rem;background:#f6f3ed;color:#241f1a}.office-shell{display:grid;grid-template-columns:1fr;min-height:calc(100vh - 7rem)}header{padding:1.25rem 1.5rem;background:#fff;border-bottom:1px solid #d6cbbb}.office-navigation{position:fixed;top:1rem;left:1rem;z-index:20;max-width:min(20rem,calc(100vw - 2rem));color:#fff}.office-navigation details{background:#2f2921;border:1px solid #5b5045;border-radius:12px;box-shadow:0 6px 20px #0003;overflow:hidden}.office-navigation summary{cursor:pointer;font-weight:700;padding:.65rem .85rem;list-style:none}.office-navigation summary::-webkit-details-marker{display:none}.office-navigation summary::before{content:'☰';margin-right:.45rem}.office-navigation details[open] summary{border-bottom:1px solid #5b5045}.office-navigation .nav-items{padding:.45rem .75rem .75rem;max-height:70vh;overflow:auto}.nav-item{display:block;width:100%;margin:.25rem 0;padding:.55rem .65rem;text-align:left;border:1px solid #5b5045;border-radius:8px;background:#40382f;color:#fff;cursor:pointer}.nav-item.placeholder{opacity:.78}.workspace{padding:1rem 1.25rem;min-width:0}.workspace-tabs{display:flex;gap:.35rem;overflow:auto;border-bottom:1px solid #d6cbbb;margin-bottom:1rem}.workspace-tab{padding:.55rem .75rem;border:1px solid #d6cbbb;border-bottom:0;border-radius:8px 8px 0 0;background:#eee3d3;cursor:pointer;white-space:nowrap}.workspace-tab.active{background:#fff;font-weight:700}.workspace-view{background:#fff;border:1px solid #d6cbbb;border-radius:0 12px 12px 12px;padding:1rem;box-shadow:0 1px 4px #0001}.workspace-view[hidden]{display:none}.panel{background:#fff;border:1px solid #d6cbbb;border-radius:12px;padding:1rem;margin:1rem 0}.placeholder{color:#6b4e16}.source{font-size:.85rem;color:#61584d}pre{white-space:pre-wrap;max-height:18rem;overflow:auto;background:#f8f8f8;padding:.75rem;border-radius:8px}dt{font-weight:700}dd{margin:0 0 .5rem}.status-bar{position:fixed;left:0;right:0;bottom:0;z-index:10;display:flex;gap:.75rem;flex-wrap:wrap;align-items:center;padding:.6rem .9rem;background:#241f1a;color:#fff;border-top:3px solid #b9904a;box-shadow:0 -2px 8px #0002}.status-item{font-size:.85rem;white-space:nowrap}.status-item strong{color:#f2d28b}.activity-console{position:fixed;left:1rem;right:1rem;bottom:3.3rem;z-index:9;background:#fff;border:1px solid #bcae9b;border-radius:12px;box-shadow:0 2px 12px #0002}.activity-console details{padding:.75rem}.activity-console summary{cursor:pointer;font-weight:700}.activity-console table{width:100%;border-collapse:collapse;margin-top:.5rem;max-height:16rem;display:block;overflow:auto}.activity-console th,.activity-console td,.pipeline-view th,.pipeline-view td,.health-table th,.health-table td,.mailbox-operations-center th,.mailbox-operations-center td,.steward-recall-operations th,.steward-recall-operations td,.resident-conversations th,.resident-conversations td{border-bottom:1px solid #eee;padding:.35rem;text-align:left;vertical-align:top}.pipeline-view table,.health-table,.mailbox-operations-center table,.steward-recall-operations table,.resident-conversations table{width:100%;border-collapse:collapse;margin:.5rem 0 1rem}.pipeline-view textarea{width:100%;font-family:ui-monospace,monospace;font-size:.8rem;background:#f8f8f8;border:1px solid #d6cbbb;border-radius:6px}.severity,.health-badge{border-radius:999px;padding:.1rem .4rem;background:#e9ecef}.mailbox-kpis{display:flex;gap:.5rem;flex-wrap:wrap}.mailbox-kpi{display:flex;flex-direction:column;min-width:8rem;background:#f8f3e8;border:1px solid #d6cbbb;border-radius:10px;padding:.55rem}.mailbox-warning{color:#842029}.severity.warning,.severity.missing,.health-badge.warning,.health-badge.missing{background:#fff3cd;color:#6b4e16}.health-badge.fail{background:#f8d7da;color:#842029}.health-badge.pass{background:#d1e7dd;color:#0f5132}.alfred-chat textarea{width:100%;font:inherit;margin:.35rem 0}.alfred-chat button{padding:.45rem .75rem}.alfred-chat-turn{border-left:3px solid #b9904a;padding-left:.75rem;margin:.75rem 0}.alfred-attachments{margin:.4rem 0;padding:.4rem;background:#fbf7ef;border:1px solid #eadcc8;border-radius:8px}.alfred-attachment-thumb{max-width:180px;max-height:120px;border:1px solid #d6cbbb;border-radius:6px;margin-top:.25rem}.global-search-palette input{width:100%;font-size:1rem;padding:.65rem;border:1px solid #bcae9b;border-radius:8px}.settings-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(12rem,1fr));gap:.35rem}.settings-surface label{display:block;margin:.45rem 0}.settings-surface select{margin-left:.4rem}.palette-result{border-bottom:1px solid #eee;padding:.55rem 0}.palette-result button{margin-top:.25rem}.palette-result.unavailable{opacity:.8}.result-meta{font-size:.85rem;color:#61584d}.snapshot-toolbar{display:flex;gap:.75rem;align-items:center;flex-wrap:wrap;margin-top:.75rem}.snapshot-toolbar button{padding:.5rem .8rem;border:1px solid #8b6f3d;border-radius:8px;background:#3f6b50;color:#fff;font-weight:700;cursor:pointer}.snapshot-toolbar .snapshot-status{font-size:.9rem;color:#61584d}.ui-runtime-diagnostic{margin-top:.75rem;padding:.55rem .75rem;border:1px solid #b9904a;border-radius:8px;background:#fff8e8;color:#4b3515;font-size:.92rem}.ui-runtime-diagnostic[data-state='ready']{background:#eaf7ef;border-color:#3f6b50;color:#163d25}.ui-runtime-diagnostic[data-state='error']{background:#f8d7da;border-color:#842029;color:#842029}@media(max-width:800px){.office-navigation{top:.5rem;left:.5rem}.workspace{padding:.75rem}}"""
    script = """<script>
const LAYOUT_PREF_KEY = 'estate.operations_center.layout.v1';
const WORKSPACE_PROFILE = __PROFILE_JSON__;
function readLayoutPreferences(){ try{return JSON.parse(localStorage.getItem(LAYOUT_PREF_KEY) || '{}');}catch(error){return {};} }
function writeLayoutPreferences(update){ try{ const next = {...readLayoutPreferences(), ...update}; localStorage.setItem(LAYOUT_PREF_KEY, JSON.stringify(next)); return next; }catch(error){ updateUiRuntimeDiagnostic('ready', 'UI runtime: scripts loaded / navigation bound / local preferences unavailable / active tab: ' + getActiveOfficeTab()); return readLayoutPreferences(); } }
function getActiveOfficeTab(){ const active = document.querySelector('.workspace-tab.active') || document.querySelector('.nav-item.active'); return active && active.dataset ? active.dataset.tab : 'unknown'; }
function getCommandCenterMode(){ return location.protocol === 'file:' ? 'file safe static' : 'served'; }
function updateUiRuntimeDiagnostic(state, message){ const el = document.querySelector('#ui-runtime-diagnostic'); if(!el) return; el.dataset.state = state; el.textContent = message + ' / mode: ' + getCommandCenterMode(); }
function activateOfficeTab(id, persist=true){
  const target = document.getElementById('workspace-' + id);
  if(!target){ updateUiRuntimeDiagnostic('error', 'UI runtime: navigation bound / missing workspace for tab: ' + id); return false; }
  document.querySelectorAll('.workspace-view').forEach(view => { const active = view.id === 'workspace-' + id; view.hidden = !active; view.classList.toggle('active', active); });
  document.querySelectorAll('[data-tab]').forEach(button => { const active = button.dataset.tab === id; if(button.classList.contains('workspace-tab')) button.setAttribute('aria-selected', active ? 'true' : 'false'); if(button.classList.contains('nav-item')){ if(active) button.setAttribute('aria-current', 'page'); else button.removeAttribute('aria-current'); } button.classList.toggle('active', active); });
  updateUiRuntimeDiagnostic('ready', 'UI runtime: scripts loaded / navigation bound / active tab: ' + id);
  if(persist) writeLayoutPreferences({active_tab: id});
  return true;
}
function applyWorkspaceProfile(profile){ if(!profile) return; if(profile.panel_arrangements && profile.panel_arrangements.activity_console_visible === false){ const consoleEl = document.querySelector('#activity-console'); if(consoleEl) consoleEl.setAttribute('hidden',''); } if(profile.active_tab) activateOfficeTab(profile.active_tab, false); }
function normalizeNavigationState(value){ return value === 'expanded' ? 'collapsed' : (value || 'collapsed'); }
function restoreLayoutPreferences(){ const prefs = readLayoutPreferences(); prefs.left_navigation = normalizeNavigationState(prefs.left_navigation || prefs.navigation_state); applyWorkspaceProfile(WORKSPACE_PROFILE.profile); if(prefs.active_tab) activateOfficeTab(prefs.active_tab, false); }
function bindOfficeNavigation(){ document.addEventListener('click', event => { const button = event.target.closest && event.target.closest('[data-tab]'); if(button){ event.preventDefault(); activateOfficeTab(button.dataset.tab); const drawer = button.closest('#office-navigation details'); if(drawer) drawer.open = false; } }); updateUiRuntimeDiagnostic('ready', 'UI runtime: scripts loaded / navigation bound / active tab: ' + getActiveOfficeTab()); }
function initOfficeRuntime(){ bindOfficeNavigation(); restoreLayoutPreferences(); renderGlobalPaletteResults(); bindOfficeActions(); if(getCommandCenterMode() === 'served') loadAlfredHistory(); renderPendingAttachments(); }

async function runOfficeAction(button){
  const actionId = button.dataset.officeAction;
  const panel = button.closest('.office-actions');
  const resultEl = panel ? panel.querySelector('.office-action-result') : null;
  const body = {action_id: actionId};
  Object.entries(button.dataset).forEach(([key, value]) => { if(key !== 'officeAction') body[key.replace(/[A-Z]/g, m => '_' + m.toLowerCase())] = value; });
  if(panel){ panel.querySelectorAll('[data-action-input]').forEach(input => { body[input.dataset.actionInput] = input.value; }); }
  if(resultEl) resultEl.textContent = 'Running ' + actionId + ' locally...';
  try{
    if(getCommandCenterMode() !== 'served') throw new Error('Office action execution requires served local mode; static file mode cannot POST to local handlers.');
    const response = await fetch('/api/office/actions/execute', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(body)});
    const payload = await response.json();
    if(resultEl) resultEl.textContent = JSON.stringify(payload, null, 2);
  }catch(error){ if(resultEl) resultEl.textContent = JSON.stringify({outcome:'blocked', steward_message:String(error), authority_gating_status:'served_mode_required'}, null, 2); }
}
function bindOfficeActions(){ document.addEventListener('click', event => { const button = event.target.closest && event.target.closest('[data-office-action]'); if(button){ event.preventDefault(); runOfficeAction(button); } }); }

function whenDomReady(callback){ if(document.readyState === 'loading') document.addEventListener('DOMContentLoaded', callback, {once:true}); else callback(); }
whenDomReady(initOfficeRuntime);
function renderGlobalPaletteResults(){
  const input = document.querySelector('#global-search-input');
  const output = document.querySelector('#global-search-results');
  const dataEl = document.querySelector('#global-palette-data');
  if(!input || !output || !dataEl) return;
  const records = JSON.parse(dataEl.textContent || '[]');
  const terms = input.value.trim().toLowerCase().split(/\\s+/).filter(Boolean);
  const matches = records.filter(item => !terms.length || terms.every(term => [item.id,item.title,item.domain,item.path,item.excerpt,item.category,item.cli].join(' ').toLowerCase().includes(term))).slice(0, 25);
  output.innerHTML = matches.length ? matches.map(item => {
    const available = item.available !== false;
    const title = item.title || item.id || item.path || 'Untitled';
    const meta = [item.kind, item.domain, item.path || item.cli || item.operation].filter(Boolean).join(' · ');
    const reason = available ? '' : `<p class="placeholder">Unavailable: ${item.unavailable_reason || 'Command unavailable.'}</p>`;
    const action = available && item.operation === 'activate_tab' ? `<button type="button" onclick="activateOfficeTab('${item.target}')">Open</button>` : '';
    return `<article class="palette-result ${available ? '' : 'unavailable'}" role="listitem"><strong>${title}</strong><div class="result-meta">${meta}</div>${reason}${action}</article>`;
  }).join('') : '<p class="placeholder">No matching local artifacts or registered commands.</p>';
}
document.addEventListener('input', event => { if(event.target && event.target.id === 'global-search-input') renderGlobalPaletteResults(); });
document.addEventListener('keydown', event => { if(event.key === '/' && !event.target.matches('input, textarea')){ event.preventDefault(); activateOfficeTab('search'); setTimeout(() => document.querySelector('#global-search-input')?.focus(), 0); } });

async function loadAlfredHistory(){
  const history = document.querySelectorAll('#alfred-chat-history');
  if(!history.length) return;
  try{
    const response = await fetch('/api/residents/alfred/chat');
    const data = await response.json();
    const turns = (data.sessions || []).flatMap(session => (session.turns || []).map(turn => ({...turn, session_id: session.session_id}))).slice(-8).reverse();
    const html = turns.length ? turns.map(turn => `<article class="alfred-chat-turn"><p><strong>Steward:</strong> ${escapeHtml(turn.user_message || '')}</p><p><strong>Alfred:</strong> ${escapeHtml(turn.resident_response || '')}</p>${attachmentHtml(turn.attachments || [])}<p class="source">${llmSourceLine(turn)} · Session ${escapeHtml(turn.session_id || '')} · ${escapeHtml(turn.created_at || '')}</p></article>`).join('') : '<p class="placeholder">No prior Alfred chat turns are recorded yet.</p>';
    history.forEach(el => el.innerHTML = html);
  }catch(error){ history.forEach(el => el.innerHTML = '<p class="placeholder">Unable to reload Alfred history from the local endpoint.</p>'); }
}

let pendingAlfredAttachments = [];
function attachmentHtml(list){ if(!list.length) return ''; return `<ul class="alfred-attachments">${list.map(a => { const safePath = String(a.storage_path || ''); const img = a.kind === 'image' && safePath.startsWith('runtime/resident_interactions/attachments/') ? `<br><img class="alfred-attachment-thumb" src="/${escapeHtml(safePath)}" alt="Local pasted image thumbnail" loading="lazy">` : ''; return `<li><code>${escapeHtml(a.kind || 'attachment')} ${escapeHtml(a.attachment_id || '')} (${escapeHtml(a.mime_type || 'unknown')}, ${escapeHtml(a.size_bytes || 0)} bytes, vision=${escapeHtml(a.vision_status || 'unknown')})</code>${img}</li>`; }).join('')}</ul>`; }
function renderPendingAttachments(){ const el = document.querySelector('#alfred-pending-attachments'); if(!el) return; el.innerHTML = pendingAlfredAttachments.length ? '<strong>Pending local attachments</strong>' + pendingAlfredAttachments.map((a,i) => `<div><code>${escapeHtml(a.kind)} ${escapeHtml(a.original_filename || 'clipboard')}</code> <button type="button" data-remove-attachment="${i}">Remove</button></div>`).join('') : '<span class="source">No pending attachments.</span>'; }
function blobToBase64(blob){ return new Promise((resolve,reject) => { const reader = new FileReader(); reader.onload = () => resolve(String(reader.result).split(',')[1] || ''); reader.onerror = reject; reader.readAsDataURL(blob); }); }
document.addEventListener('paste', async event => { const input = event.target && event.target.closest && event.target.closest('#alfred-chat-input'); if(!input) return; const items = Array.from((event.clipboardData && event.clipboardData.items) || []); for(const item of items){ if(item.type && item.type.startsWith('image/')){ event.preventDefault(); const file = item.getAsFile(); if(file){ pendingAlfredAttachments.push({kind:'image', source:'clipboard_paste', original_filename:file.name || 'clipboard-image.png', mime_type:file.type || 'image/png', data_base64: await blobToBase64(file)}); } } } const text = event.clipboardData && event.clipboardData.getData('text/plain'); if(text && text.length > 500){ pendingAlfredAttachments.push({kind:'text_snippet', source:'clipboard_paste', original_filename:'clipboard-text.txt', mime_type:'text/plain', text}); } renderPendingAttachments(); });
document.addEventListener('click', event => { const btn = event.target.closest('[data-remove-attachment]'); if(btn){ pendingAlfredAttachments.splice(Number(btn.dataset.removeAttachment), 1); renderPendingAttachments(); } });

function llmSourceLine(turn){ const llm = turn.llm || {}; const diag = turn.diagnostics || {}; const contract = turn.response_contract || {}; const degraded = (contract.failed || contract.timed_out || llm.fallback_used) ? 'DEGRADED ' : ''; const fallback = (diag.fallback_reason || llm.fallback_reason) ? ` / fallback: ${escapeHtml(diag.fallback_reason || llm.fallback_reason)}` : ''; const err = (diag.sanitized_error || diag.last_adapter_error) ? ` / adapter error: ${escapeHtml(diag.sanitized_error || diag.last_adapter_error)}` : ''; return `${degraded}Mode: ${escapeHtml(llm.mode || 'unknown')} / Type: ${escapeHtml(contract.response_type || 'unknown')} / Status: ${escapeHtml(contract.status || 'unknown')} / Adapter: ${escapeHtml(diag.local_llm_adapter_available === false ? 'unavailable' : 'available')} / provider: ${escapeHtml(diag.selected_provider || llm.provider || 'unknown')} / model: ${escapeHtml(diag.selected_model || llm.model || 'unknown')} / generation attempted: ${escapeHtml(String(diag.generation_attempted ?? llm.generation_attempted ?? false))} / generation result: ${escapeHtml(diag.generation_result_state || llm.generation_result_state || 'unknown')} / timeout seconds: ${escapeHtml(String(diag.timeout_seconds ?? llm.timeout_seconds ?? 'unknown'))} / prompt size: ${escapeHtml(JSON.stringify(diag.prompt_size || llm.prompt_size || {}))} / recovery hint: ${escapeHtml(diag.recovery_hint || llm.recovery_hint || 'none')} / generation endpoint: ${escapeHtml(diag.generation_endpoint || llm.generation_endpoint || 'none')} / discovered models: ${escapeHtml(String(diag.discovered_models_count ?? llm.discovered_models_count ?? 'unknown'))} / request: ${escapeHtml(diag.last_request_timestamp || 'unknown')} / response: ${escapeHtml(diag.last_response_timestamp || 'unknown')}${fallback}${err}`; }
function escapeHtml(value){ return String(value).replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char])); }
document.addEventListener('submit', async event => {
  const form = event.target.closest('#alfred-chat-form');
  if(!form) return;
  event.preventDefault();
  const input = form.querySelector('#alfred-chat-input');
  const output = document.querySelectorAll('#alfred-chat-response');
  output.forEach(el => { el.dataset.state = 'processing'; el.textContent = 'Alfred is reviewing local Estate context...'; });
  const timeout = new Promise((_, reject) => setTimeout(() => reject(new Error('resident_chat_timeout_after_30s')), 30000));
  try{
    const response = await Promise.race([fetch('/api/residents/alfred/chat', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({message: input.value, action:'conversation', attachments: pendingAlfredAttachments})}), timeout]);
    const data = await response.json();
    output.forEach(el => { el.dataset.state = data.turn ? 'completed' : 'failed'; el.textContent = data.turn ? `${data.turn.resident_response}\n${llmSourceLine(data.turn)}` : `Alfred request failed safely: ${data.error || response.statusText || 'no response body'}`; });
    input.value = '';
    pendingAlfredAttachments = []; renderPendingAttachments();
    await loadAlfredHistory();
  }catch(error){
    output.forEach(el => { el.dataset.state = 'failed'; el.textContent = `Alfred request failed safely: ${error.message || error}. Retry when the local resident API is reachable. Endpoint: /api/residents/alfred/chat`; });
  }
});

function utf8Bytes(text){ return new TextEncoder().encode(String(text)); }
function crc32(bytes){ let c = ~0; for(const b of bytes){ c ^= b; for(let k=0;k<8;k++) c = (c >>> 1) ^ (0xEDB88320 & -(c & 1)); } return ~c >>> 0; }
function dosDateTime(date){ const y=Math.max(1980,date.getFullYear()); return {time:(date.getHours()<<11)|(date.getMinutes()<<5)|(date.getSeconds()>>1), date:((y-1980)<<9)|((date.getMonth()+1)<<5)|date.getDate()}; }
function u16(n){ return [n & 255, (n>>>8)&255]; }
function u32(n){ return [n & 255, (n>>>8)&255, (n>>>16)&255, (n>>>24)&255]; }
function makeZip(files){
  const chunks=[]; const central=[]; let offset=0; const stamp=dosDateTime(new Date());
  for(const file of files){
    const name=utf8Bytes(file.name); const data=file.bytes instanceof Uint8Array ? file.bytes : utf8Bytes(file.text || ''); const crc=crc32(data);
    const local=new Uint8Array([...u32(0x04034b50),...u16(20),...u16(0),...u16(0),...u16(stamp.time),...u16(stamp.date),...u32(crc),...u32(data.length),...u32(data.length),...u16(name.length),...u16(0),...name]);
    chunks.push(local,data);
    central.push(new Uint8Array([...u32(0x02014b50),...u16(20),...u16(20),...u16(0),...u16(0),...u16(stamp.time),...u16(stamp.date),...u32(crc),...u32(data.length),...u32(data.length),...u16(name.length),...u16(0),...u16(0),...u16(0),...u16(0),...u32(0),...u32(offset),...name]));
    offset += local.length + data.length;
  }
  const centralSize=central.reduce((n,c)=>n+c.length,0); const end=new Uint8Array([...u32(0x06054b50),...u16(0),...u16(0),...u16(files.length),...u16(files.length),...u32(centralSize),...u32(offset),...u16(0)]);
  return new Blob([...chunks,...central,end], {type:'application/zip'});
}
function currentUiMetadata(){
  const activeTab = document.querySelector('.workspace-tab.active')?.dataset.tab || 'unknown';
  return {schema_version:'office-snapshot-v1', captured_at:new Date().toISOString(), url:location.href, path:location.pathname, viewport:{width:innerWidth,height:innerHeight}, user_agent:navigator.userAgent, active_tab:activeTab, active_navigation_item:document.querySelector('.nav-item.active')?.textContent || activeTab, local_only:true};
}
function collectDomState(){
  return {active_tab:document.querySelector('.workspace-tab.active')?.dataset.tab || null, visible_panels:[...document.querySelectorAll('.workspace-view:not([hidden])')].map(e=>e.id), details:[...document.querySelectorAll('details')].map((e,i)=>({index:i, summary:e.querySelector('summary')?.textContent || '', open:e.open})), collapsed_sections:[...document.querySelectorAll('details:not([open])')].map(e=>e.querySelector('summary')?.textContent || '')};
}
async function exportOfficeSnapshot(){
  const status=document.querySelector('#office-snapshot-status'); if(status) status.textContent='Building local snapshot ZIP\\u2026';
  try{
    const styles=[...document.querySelectorAll('style')].map((e,i)=>`/* inline style ${i+1} */\\n${e.textContent}`).join('\\n\\n');
    const scripts=[...document.querySelectorAll('script')].map((e,i)=> e.src ? `/* script reference ${i+1}: ${e.src} */` : `/* inline script ${i+1} */\\n${e.textContent}`).join('\\n\\n');
    const metadata=currentUiMetadata();
    const manifest={...JSON.parse(document.querySelector('#office-snapshot-manifest')?.textContent || '{}'), ...metadata, package_contents:['snapshot_manifest.json','page.html','dom_state.json','ui_metadata.json','styles.css','scripts.js','source_artifacts.json','README.md'], privacy_notice:'Local-only browser-created download. No external upload is performed by this feature.'};
    const files=[
      {name:'snapshot_manifest.json', text:JSON.stringify(manifest,null,2)},
      {name:'page.html', text:'<!doctype html>\\n'+document.documentElement.outerHTML},
      {name:'dom_state.json', text:JSON.stringify(collectDomState(),null,2)},
      {name:'ui_metadata.json', text:JSON.stringify(metadata,null,2)},
      {name:'styles.css', text:styles || '/* no inline styles captured */'},
      {name:'scripts.js', text:scripts || '/* no inline scripts or references captured */'},
      {name:'source_artifacts.json', text:document.querySelector('#office-snapshot-source-artifacts')?.textContent || '[]'},
      {name:'README.md', text:'# Office Snapshot\\n\\nThis ZIP was assembled locally in the browser from the rendered Office of the Steward page. It may contain internal Estate information visible in the UI. Screenshot capture is a known future enhancement for WP-0117.\\n'}
    ];
    const url=URL.createObjectURL(makeZip(files)); const a=document.createElement('a'); a.href=url; a.download=`office-snapshot-${new Date().toISOString().replace(/[:.]/g,'-')}.zip`; document.body.appendChild(a); a.click(); a.remove(); setTimeout(()=>URL.revokeObjectURL(url),1000);
    if(status) status.textContent='Snapshot ZIP downloaded locally.';
  }catch(error){ if(status) status.textContent=`Snapshot export failed after DOM capture attempt: ${error.message}`; console.error('Office Snapshot export failed', error); }
}
document.addEventListener('click', event => { if(event.target.closest('#office-snapshot-button')) exportOfficeSnapshot(); });

window.addEventListener('load', () => { updateUiRuntimeDiagnostic('ready', 'UI runtime: scripts loaded / navigation bound / active tab: ' + getActiveOfficeTab()); });
</script>"""
    script = script.replace("__PROFILE_JSON__", _js_json_literal(payload.get("workspace_profile", {})))
    return (
        '<!doctype html>\n<html lang="en"><head><meta charset="utf-8"><title>Office of the Steward</title>\n'
        f'<style>{css}</style></head>\n'
        f'<body><script id="office-snapshot-source-artifacts" type="application/json">{source_artifacts_json}</script><script id="office-snapshot-manifest" type="application/json">{snapshot_manifest_json}</script><header><h1>Office of the Steward — Local Command Center</h1><p>Local-only Office shell. Generated: {generated}. Navigation, tabs, status, activity, and placeholders are backed by local artifacts only.</p><div class="snapshot-toolbar" aria-label="Office Snapshot export"><button id="office-snapshot-button" type="button">Office Snapshot</button><span id="office-snapshot-status" class="snapshot-status">Downloads a local ZIP; may contain internal Estate UI state. No upload is performed.</span></div><div id="ui-runtime-diagnostic" class="ui-runtime-diagnostic" data-state="not-initialized" role="status">UI runtime: script not initialized; navigation may not work</div><noscript><div class="ui-runtime-diagnostic" data-state="error">UI runtime: JavaScript is disabled; workspace tabs require JavaScript.</div></noscript></header><div class="office-shell">{_nav_html(payload.get("navigation", {}), active_tab)}<main class="workspace">{_tab_bar_html(payload.get("tabs", []), active_tab)}{workspace}</main></div>{activity_console}{status_bar}{script}{_refresh_script()}</body></html>\n'
    )

def serve_command_center(host="127.0.0.1", port=8765, root=None):
    root = _root(root)
    generate_command_center(root=root, write=True)

    class Handler(SimpleHTTPRequestHandler):
        def do_GET(self):
            if self.path in ("/", "/index.html", "/command-center"):
                html_doc = render_command_center_html(generate_command_center(root=root, write=True)).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(html_doc)))
                self.end_headers()
                self.wfile.write(html_doc)
                return
            if self.path == "/status.json":
                payload = generate_command_center(root=root, write=False)
                body = json.dumps({
                    "generated_at": payload.get("generated_at"),
                    "status_bar": payload.get("status_bar"),
                    "activity_console": payload.get("activity_console"),
                    "status_bar_html": _status_bar_html(payload.get("status_bar", {})),
                    "activity_console_html": _activity_console_html(payload.get("activity_console", {})),
                }).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            parsed = urlparse(self.path)
            parts = [p for p in parsed.path.split("/") if p]
            if len(parts) == 4 and parts[:2] == ["api", "residents"] and parts[3] == "surface":
                body = json.dumps(resident_surface(parts[2], root=root), indent=2, sort_keys=True).encode("utf-8")
                self.send_response(200); self.send_header("Content-Type", "application/json; charset=utf-8"); self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body); return
            if len(parts) == 4 and parts[:2] == ["api", "residents"] and parts[3] == "chat":
                body = json.dumps(load_history(parts[2], root=root), indent=2, sort_keys=True).encode("utf-8")
                self.send_response(200); self.send_header("Content-Type", "application/json; charset=utf-8"); self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body); return
            if parsed.path.startswith("/runtime/resident_interactions/attachments/"):
                rel = parsed.path.lstrip("/")
                path = (root / rel).resolve()
                base = (root / "runtime/resident_interactions/attachments").resolve()
                if str(path).startswith(str(base)) and path.is_file():
                    data = path.read_bytes(); ctype = "image/png" if path.suffix.lower()==".png" else "image/jpeg" if path.suffix.lower() in {".jpg",".jpeg"} else "application/octet-stream"
                    self.send_response(200); self.send_header("Content-Type", ctype); self.send_header("Content-Length", str(len(data))); self.end_headers(); self.wfile.write(data); return
            self.send_error(404, "Command center only serves the local dashboard and local resident APIs.")

        def do_POST(self):
            parsed = urlparse(self.path); parts = [p for p in parsed.path.split("/") if p]
            length = int(self.headers.get("Content-Length", "0") or "0")
            try:
                data = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
            except Exception:
                data = {}
            if parts == ["api", "office", "actions", "execute"]:
                action_id = data.pop("action_id", "")
                payload = execute_office_action(action_id, root=root, **data)
            elif len(parts) == 4 and parts[:2] == ["api", "residents"] and parts[3] == "chat":
                payload = process_chat(parts[2], data.get("message") or data.get("user_message") or "", session_id=data.get("session_id"), action=data.get("action") or "summarize", root=root, attachments=data.get("attachments") or [])
            elif len(parts) == 4 and parts[:2] == ["api", "residents"] and parts[3] == "forget":
                payload = forget_conversation(data.get("session_id") or "", turn_id=data.get("turn_id"), memory_status=data.get("memory_status") or "forgotten", reason=data.get("reason") or "Steward-directed redaction", root=root)
            else:
                self.send_error(404, "Unknown local Office API endpoint."); return
            body = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")
            self.send_response(200 if payload.get("outcome") != "failed" and payload.get("ok", True) else 400); self.send_header("Content-Type", "application/json; charset=utf-8"); self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body); return

    return ThreadingHTTPServer((host, port), Handler)
