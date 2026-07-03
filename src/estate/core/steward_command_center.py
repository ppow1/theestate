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
from estate.core.decision_queue import generate_decision_queue
from estate.core.assignment_queue import generate_assignment_queue
from estate.core.mailbox_index import generate_mailbox_index


OFFICE_NAVIGATION = [
    {"id": "home", "label": "Home", "panel": "home", "tab": "home"},
    {"id": "alfred", "label": "Alfred", "panel": "alfred_resident_card", "tab": "alfred"},
    {"id": "helen", "label": "Helen", "panel": "helen_resident_card", "tab": "helen"},
    {"id": "daily-board", "label": "Daily Board", "panel": "morning_briefing", "tab": "daily-board"},
    {"id": "active-projects", "label": "Active Projects", "panel": "work_package_pipeline", "tab": "projects"},
    {"id": "expansion-roadmap", "label": "Expansion Roadmap", "panel": "expansion_roadmap", "tab": "roadmap"},
    {"id": "parking-lot", "label": "Parking Lot", "panel": "parking_lot", "tab": "parking"},
    {"id": "work-packages", "label": "Work Packages", "panel": "work_package_pipeline", "tab": "work-packages"},
    {"id": "mailboxes", "label": "Mailboxes", "panel": "mailbox_operations_center", "tab": "mailboxes"},
    {"id": "validation", "label": "Validation", "panel": "validation_health_dashboard", "tab": "validation"},
    {"id": "search", "label": "Search", "panel": "search", "tab": "search"},
    {"id": "settings", "label": "Settings", "panel": "settings", "tab": "settings"},
    {"id": "about", "label": "About", "panel": "about", "tab": "about"},
]

OFFICE_TABS = [
    {"id": "home", "label": "Home"},
    {"id": "alfred", "label": "Alfred"},
    {"id": "helen", "label": "Helen"},
    {"id": "daily-board", "label": "Daily Board"},
    {"id": "projects", "label": "Projects"},
    {"id": "roadmap", "label": "Roadmap"},
    {"id": "parking", "label": "Parking Lot"},
    {"id": "work-packages", "label": "Work Packages"},
    {"id": "mailboxes", "label": "Mailboxes"},
    {"id": "validation", "label": "Validation"},
    {"id": "search", "label": "Search"},
    {"id": "settings", "label": "Settings"},
    {"id": "about", "label": "About"},
]

ARTIFACTS = {
    "morning_briefing": ["runtime/operations/morning_briefing.json", "operations/briefings/morning_briefing.md"],
    "mailbox_summary": ["runtime/collaboration/mailbox_index.json", "collaboration/mailboxes/index.json"],
    "work_package_pipeline": ["runtime/work_packages/assignment_queue.json", "operations/work_packages/assignment_queue.md"],
    "validation_status": ["runtime/validation/local_operational_validation_run.json", "operations/validation/local_operational_validation_run.md", "runtime/audit/latest.json"],
    "capability_lifecycle": ["runtime/capabilities/capability_lifecycle_report.json", "operations/capabilities/capability_lifecycle_report.md"],
    "dependency_graph": ["runtime/dependencies/dependency_graph.json", "operations/dependencies/dependency_graph.md"],
    "mailbox_sync": ["runtime/mailboxes/synchronization_duty_latest.json", "operations/mailboxes/synchronization_duty.md", "collaboration/status/worker_inbox_summary.json"],
    "check_updates": ["runtime/updates/check_updates_latest.json", "operations/updates/check_updates_latest.md"],
    "worker_inbox_summary": ["collaboration/status/worker_inbox_summary.json"],
    "recall_audit": ["runtime/audit/recall_audit_log.json", "operations/audit/recall_audit_log_summary.md"],
    "worker_heartbeat": ["runtime/workers/worker_runtime_heartbeat.json", "runtime/workers/heartbeat.json", "operations/workers/runtime_heartbeat.md"],
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
    artifact = _read_artifact(root, ["runtime/workers/worker_runtime_heartbeat.json", "runtime/workers/heartbeat.json", "operations/workers/runtime_heartbeat.md"])
    if artifact.get("kind") == "json":
        data = artifact.get("data") or {}
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
    active_workers = _active_worker_count(root)
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
        "active_workers": active_workers,
        "version": "Operations Center v1 / Status Console v1",
        "verbosity": "normal",
        "missing_sources": missing,
        "health_state": health_state,
        "recommended_next_action": health.get("recommended_next_action"),
    }


def _event(ts, source, topic, severity, message):
    return {"timestamp": ts or "unknown", "source": source, "topic": topic, "severity": severity, "message": message}


def _build_activity_console(root, panels, generated_at):
    events = [_event(generated_at, "steward.command_center", "refresh", "info", "Operations Center data refreshed quietly from local artifacts.")]
    for name, artifact in panels.items():
        source = artifact.get("path") or name if isinstance(artifact, dict) else name
        if isinstance(artifact, dict) and not artifact.get("available"):
            events.append(_event(generated_at, source, name, "missing", artifact.get("placeholder") or "Data source is not available yet."))
    completions_dir = root / "collaboration" / "work_packages" / "completions"
    if completions_dir.exists():
        for path in sorted(completions_dir.glob("*_codex_done.json"), key=lambda p: p.stat().st_mtime, reverse=True)[:5]:
            try:
                data = _read_json(path)
                events.append(_event(data.get("completed_at") or generated_at, _rel(path, root), data.get("work_package_id") or "work_package", "info", data.get("summary") or "Work package completion recorded."))
            except Exception as exc:
                events.append(_event(generated_at, _rel(path, root), "completion", "warning", f"Completion record could not be read: {exc}"))
    if len(events) == 1:
        events.append(_event(generated_at, "local artifacts", "empty", "info", "No recent operational activity records were found."))
    return {"collapsed_by_default": True, "verbosity_options": ["quiet", "normal", "detailed", "diagnostic"], "selected_verbosity": "normal", "events": events[:25]}


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

def generate_command_center(root=None, write=True):
    root = _root(root)
    resident_cards = build_resident_cards(root)
    resident_panels = {f"{str(card.get('name', '')).lower()}_resident_card": card for card in resident_cards["cards"]}
    panels = {
        **resident_panels,
        "morning_briefing": _read_artifact(root, ARTIFACTS["morning_briefing"]),
        "steward_decision_queue": _decision_queue_artifact(root),
        "mailbox_summary": _read_artifact(root, ARTIFACTS["mailbox_summary"]),
        "mailbox_operations_center": _mailbox_operations_center_artifact(root),
        "work_package_pipeline": _work_package_pipeline_artifact(root),
        "validation_status": _read_artifact(root, ARTIFACTS["validation_status"]),
        "expansion_roadmap": _read_artifact(root, ["operations/boards/roadmap.md"]),
        "parking_lot": _read_artifact(root, ["operations/boards/parking_lot.md"]),
        "daily_board_workspace": _daily_board_workspace_artifact(root),
        "search": _placeholder_panel("search", "Search", "Institutional search workspace is reserved for a future interactive panel; use the local estate-search CLI until then."),
        "settings": _placeholder_panel("settings", "Settings", "Settings are reserved for local theme, refresh, filter, layout, notification, and verbosity controls."),
        "about": {"available": True, "path": "src/estate/core/steward_command_center.py", "kind": "about", "data": {"component": "Office of the Steward command center", "version": "Operations Center v1 / Office Shell v1", "local_only": True}},
    }
    panels["validation_health_dashboard"] = _build_validation_health_dashboard(root)
    generated_at = _now()
    payload = {"version": 1, "generated_at": generated_at, "local_only": True, "panels": panels, "navigation": _office_navigation(panels), "tabs": _office_tabs(panels)}
    payload["status_bar"] = _build_status_bar(root, panels, generated_at)
    payload["activity_console"] = _build_activity_console(root, panels, generated_at)
    if write:
        out = root / "runtime" / "steward" / "command_center.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(render_command_center_html(payload), encoding="utf-8")
    return payload



def _placeholder_panel(panel_id, title, description, source="future Office package"):
    return {"available": False, "path": source, "kind": "placeholder", "panel_id": panel_id, "title": title, "placeholder": description}


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


def _home_workspace_html(payload):
    status = payload.get("status_bar", {})
    return "".join([
        "<p>The Office shell is active. Use the left navigation or workspace tabs to switch between operational areas without crowding every panel onto one screen.</p>",
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
    fields = ["name", "role", "operational_status", "current_duty"]
    rows = [f"<dt>{html.escape(field.replace('_', ' ').title())}</dt><dd>{html.escape(str(card.get(field) or ''))}</dd>" for field in fields]
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
        ("Workers", status.get("active_workers")),
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


def _refresh_script():
    return """<script>
async function refreshOperationsChrome(){
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
window.addEventListener('load', () => window.setInterval(refreshOperationsChrome, 30000));
</script>"""

def _about_html(artifact):
    data = artifact.get("data") or {}
    rows = "".join(f"<dt>{html.escape(str(k).replace('_', ' ').title())}</dt><dd>{html.escape(str(v))}</dd>" for k, v in data.items())
    return f"<dl>{rows}</dl><p class='source'>Source: {html.escape(str(artifact.get('path') or 'local component inventory'))}</p>"


def _nav_html(navigation):
    items = navigation.get("items") or []
    buttons = []
    for item in items:
        status = "ready" if item.get("available") else "placeholder"
        buttons.append(f"<button class='nav-item {status}' data-tab='{html.escape(str(item.get('tab')))}'>{html.escape(str(item.get('label')))}</button>")
    return f"<aside id='office-navigation' class='office-navigation'><details open><summary>Office Navigation</summary>{''.join(buttons)}</details></aside>"


def _tab_bar_html(tabs):
    buttons = []
    for index, tab in enumerate(tabs or []):
        selected = "true" if index == 0 else "false"
        active = " active" if index == 0 else ""
        buttons.append(f"<button id='tab-{html.escape(str(tab.get('id')))}' class='workspace-tab{active}' role='tab' aria-selected='{selected}' data-tab='{html.escape(str(tab.get('id')))}'>{html.escape(str(tab.get('label')))}</button>")
    return f"<div id='workspace-tabs' class='workspace-tabs' role='tablist'>{''.join(buttons)}</div>"


def _workspace_section(tab_id, label, body, active=False):
    active_class = " active" if active else ""
    hidden = "" if active else " hidden"
    return f"<section id='workspace-{html.escape(tab_id)}' class='workspace-view{active_class}' role='tabpanel'{hidden}><h2>{html.escape(label)}</h2>{body}</section>"


def render_command_center_html(payload):
    p = payload.get("panels", {})
    tab_bodies = [
        ("home", "Home", _home_workspace_html(payload)),
        ("alfred", "Alfred Resident Card", _resident_html(p.get("alfred_resident_card", {}))),
        ("helen", "Helen Resident Card", _resident_html(p.get("helen_resident_card", {}))),
        ("daily-board", "Daily Board / Parking Lot Workspace", _panel("Morning Briefing", _artifact_html(p.get("morning_briefing", {})), "ready" if p.get("morning_briefing", {}).get("available") else "placeholder") + _daily_board_workspace_html(p.get("daily_board_workspace", {}))),
        ("projects", "Work Package Pipeline", _work_package_pipeline_html(p.get("work_package_pipeline", {}))),
        ("roadmap", "Expansion Roadmap", _artifact_html(p.get("expansion_roadmap", {}))),
        ("parking", "Parking Lot", _daily_board_workspace_html(p.get("daily_board_workspace", {}), parking_only=True)),
        ("work-packages", "Work Packages", _work_package_pipeline_html(p.get("work_package_pipeline", {}))),
        ("mailboxes", "Mailbox Summary / Operations Center", _mailbox_operations_center_html(p.get("mailbox_operations_center", {}))),
        ("validation", "Validation and Estate Health", _validation_health_html(p.get("validation_health_dashboard", {})) + _panel("Validation Status", _artifact_html(p.get("validation_status", {})), "ready" if p.get("validation_status", {}).get("available") else "placeholder")),
        ("search", "Search", _office_placeholder_html("Search", p.get("search", {}).get("placeholder", "Search workspace is not implemented yet."))),
        ("settings", "Settings", _office_placeholder_html("Settings", p.get("settings", {}).get("placeholder", "Settings workspace is not implemented yet."))),
        ("about", "About", _about_html(p.get("about", {}))),
    ]
    workspace = "".join(_workspace_section(tab_id, label, body, active=(i == 0)) for i, (tab_id, label, body) in enumerate(tab_bodies))
    status_bar = _status_bar_html(payload.get("status_bar", {}))
    activity_console = _activity_console_html(payload.get("activity_console", {}))
    generated = html.escape(str(payload.get("generated_at")))
    css = """body{font-family:system-ui,sans-serif;margin:0 0 9rem;background:#f6f3ed;color:#241f1a}.office-shell{display:grid;grid-template-columns:minmax(13rem,17rem) 1fr;min-height:calc(100vh - 7rem)}header{padding:1.25rem 1.5rem;background:#fff;border-bottom:1px solid #d6cbbb}.office-navigation{background:#2f2921;color:#fff;padding:1rem}.office-navigation summary{cursor:pointer;font-weight:700;margin-bottom:.75rem}.nav-item{display:block;width:100%;margin:.25rem 0;padding:.55rem .65rem;text-align:left;border:1px solid #5b5045;border-radius:8px;background:#40382f;color:#fff;cursor:pointer}.nav-item.placeholder{opacity:.78}.workspace{padding:1rem 1.25rem}.workspace-tabs{display:flex;gap:.35rem;overflow:auto;border-bottom:1px solid #d6cbbb;margin-bottom:1rem}.workspace-tab{padding:.55rem .75rem;border:1px solid #d6cbbb;border-bottom:0;border-radius:8px 8px 0 0;background:#eee3d3;cursor:pointer;white-space:nowrap}.workspace-tab.active{background:#fff;font-weight:700}.workspace-view{background:#fff;border:1px solid #d6cbbb;border-radius:0 12px 12px 12px;padding:1rem;box-shadow:0 1px 4px #0001}.workspace-view[hidden]{display:none}.panel{background:#fff;border:1px solid #d6cbbb;border-radius:12px;padding:1rem;margin:1rem 0}.placeholder{color:#6b4e16}.source{font-size:.85rem;color:#61584d}pre{white-space:pre-wrap;max-height:18rem;overflow:auto;background:#f8f8f8;padding:.75rem;border-radius:8px}dt{font-weight:700}dd{margin:0 0 .5rem}.status-bar{position:fixed;left:0;right:0;bottom:0;z-index:10;display:flex;gap:.75rem;flex-wrap:wrap;align-items:center;padding:.6rem .9rem;background:#241f1a;color:#fff;border-top:3px solid #b9904a;box-shadow:0 -2px 8px #0002}.status-item{font-size:.85rem;white-space:nowrap}.status-item strong{color:#f2d28b}.activity-console{position:fixed;left:1rem;right:1rem;bottom:3.3rem;z-index:9;background:#fff;border:1px solid #bcae9b;border-radius:12px;box-shadow:0 2px 12px #0002}.activity-console details{padding:.75rem}.activity-console summary{cursor:pointer;font-weight:700}.activity-console table{width:100%;border-collapse:collapse;margin-top:.5rem;max-height:16rem;display:block;overflow:auto}.activity-console th,.activity-console td,.pipeline-view th,.pipeline-view td,.health-table th,.health-table td,.mailbox-operations-center th,.mailbox-operations-center td{border-bottom:1px solid #eee;padding:.35rem;text-align:left;vertical-align:top}.pipeline-view table,.health-table,.mailbox-operations-center table{width:100%;border-collapse:collapse;margin:.5rem 0 1rem}.pipeline-view textarea{width:100%;font-family:ui-monospace,monospace;font-size:.8rem;background:#f8f8f8;border:1px solid #d6cbbb;border-radius:6px}.severity,.health-badge{border-radius:999px;padding:.1rem .4rem;background:#e9ecef}.mailbox-kpis{display:flex;gap:.5rem;flex-wrap:wrap}.mailbox-kpi{display:flex;flex-direction:column;min-width:8rem;background:#f8f3e8;border:1px solid #d6cbbb;border-radius:10px;padding:.55rem}.mailbox-warning{color:#842029}.severity.warning,.severity.missing,.health-badge.warning,.health-badge.missing{background:#fff3cd;color:#6b4e16}.health-badge.fail{background:#f8d7da;color:#842029}.health-badge.pass{background:#d1e7dd;color:#0f5132}@media(max-width:800px){.office-shell{grid-template-columns:1fr}.office-navigation{position:static}}"""
    script = """<script>
function activateOfficeTab(id){
  document.querySelectorAll('.workspace-view').forEach(view => { const active = view.id === 'workspace-' + id; view.hidden = !active; view.classList.toggle('active', active); });
  document.querySelectorAll('[data-tab]').forEach(button => { const active = button.dataset.tab === id; if(button.classList.contains('workspace-tab')) button.setAttribute('aria-selected', active ? 'true' : 'false'); button.classList.toggle('active', active); });
}
document.addEventListener('click', event => { const button = event.target.closest('[data-tab]'); if(button) activateOfficeTab(button.dataset.tab); });
</script>"""
    return (
        '<!doctype html>\n<html lang="en"><head><meta charset="utf-8"><title>Office of the Steward</title>\n'
        f'<style>{css}</style></head>\n'
        f'<body><header><h1>Office of the Steward — Local Command Center</h1><p>Local-only Office shell. Generated: {generated}. Navigation, tabs, status, activity, and placeholders are backed by local artifacts only.</p></header><div class="office-shell">{_nav_html(payload.get("navigation", {}))}<main class="workspace">{_tab_bar_html(payload.get("tabs", []))}{workspace}</main></div>{activity_console}{status_bar}{script}{_refresh_script()}</body></html>\n'
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
            self.send_error(404, "Command center only serves the local dashboard.")

    return ThreadingHTTPServer((host, port), Handler)
