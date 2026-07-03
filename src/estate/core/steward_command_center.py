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

ARTIFACTS = {
    "morning_briefing": ["runtime/operations/morning_briefing.json", "operations/briefings/morning_briefing.md"],
    "mailbox_summary": ["runtime/collaboration/mailbox_index.json", "collaboration/mailboxes/index.json"],
    "work_package_pipeline": ["runtime/work_packages/assignment_queue.json", "operations/work_packages/assignment_queue.md"],
    "validation_status": ["runtime/validation/local_operational_validation_run.json", "operations/validation/local_operational_validation_run.md", "runtime/audit/latest.json"],
    "capability_lifecycle": ["runtime/capabilities/capability_lifecycle_report.json", "operations/capabilities/capability_lifecycle_report.md"],
    "dependency_graph": ["runtime/dependencies/dependency_graph.json", "operations/dependencies/dependency_graph.md"],
    "mailbox_sync": ["runtime/mailboxes/synchronization_duty_latest.json", "operations/mailboxes/synchronization_duty.md", "collaboration/status/worker_inbox_summary.json"],
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

def generate_command_center(root=None, write=True):
    root = _root(root)
    resident_cards = build_resident_cards(root)
    resident_panels = {f"{str(card.get('name', '')).lower()}_resident_card": card for card in resident_cards["cards"]}
    panels = {
        **resident_panels,
        "morning_briefing": _read_artifact(root, ARTIFACTS["morning_briefing"]),
        "steward_decision_queue": _decision_queue_artifact(root),
        "mailbox_summary": _read_artifact(root, ARTIFACTS["mailbox_summary"]),
        "work_package_pipeline": _work_package_pipeline_artifact(root),
        "validation_status": _read_artifact(root, ARTIFACTS["validation_status"]),
    }
    panels["validation_health_dashboard"] = _build_validation_health_dashboard(root)
    generated_at = _now()
    payload = {"version": 1, "generated_at": generated_at, "local_only": True, "panels": panels}
    payload["status_bar"] = _build_status_bar(root, panels, generated_at)
    payload["activity_console"] = _build_activity_console(root, panels, generated_at)
    if write:
        out = root / "runtime" / "steward" / "command_center.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(render_command_center_html(payload), encoding="utf-8")
    return payload


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

def render_command_center_html(payload):
    p = payload.get("panels", {})
    panels = [
        _panel("Alfred Resident Card", _resident_html(p.get("alfred_resident_card", {})), "ready" if p.get("alfred_resident_card", {}).get("available") else "placeholder"),
        _panel("Helen Resident Card", _resident_html(p.get("helen_resident_card", {})), "ready" if p.get("helen_resident_card", {}).get("available") else "placeholder"),
        _panel("Morning Briefing", _artifact_html(p.get("morning_briefing", {})), "ready" if p.get("morning_briefing", {}).get("available") else "placeholder"),
        _panel("Steward Decision Queue", _decision_queue_html(p.get("steward_decision_queue", {})), "ready" if p.get("steward_decision_queue", {}).get("available") else "placeholder"),
        _panel("Mailbox Summary", _artifact_html(p.get("mailbox_summary", {})), "ready" if p.get("mailbox_summary", {}).get("available") else "placeholder"),
        _panel("Work Package Pipeline", _work_package_pipeline_html(p.get("work_package_pipeline", {})), "ready" if p.get("work_package_pipeline", {}).get("available") else "placeholder"),
        _panel("Validation and Estate Health", _validation_health_html(p.get("validation_health_dashboard", {})), "ready"),
        _panel("Validation Status", _artifact_html(p.get("validation_status", {})), "ready" if p.get("validation_status", {}).get("available") else "placeholder"),
    ]
    status_bar = _status_bar_html(payload.get("status_bar", {}))
    activity_console = _activity_console_html(payload.get("activity_console", {}))
    generated = html.escape(str(payload.get("generated_at")))
    return (
        '<!doctype html>\n<html lang="en"><head><meta charset="utf-8"><title>Office of the Steward</title>\n'
        '<style>body{font-family:system-ui,sans-serif;margin:2rem 2rem 9rem;background:#f6f3ed;color:#241f1a}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:1rem}.panel{background:#fff;border:1px solid #d6cbbb;border-radius:12px;padding:1rem;box-shadow:0 1px 4px #0001}.placeholder{color:#6b4e16}.source{font-size:.85rem;color:#61584d}pre{white-space:pre-wrap;max-height:18rem;overflow:auto;background:#f8f8f8;padding:.75rem;border-radius:8px}dt{font-weight:700}dd{margin:0 0 .5rem}.status-bar{position:fixed;left:0;right:0;bottom:0;z-index:10;display:flex;gap:.75rem;flex-wrap:wrap;align-items:center;padding:.6rem .9rem;background:#241f1a;color:#fff;border-top:3px solid #b9904a;box-shadow:0 -2px 8px #0002}.status-item{font-size:.85rem;white-space:nowrap}.status-item strong{color:#f2d28b}.activity-console{position:fixed;left:1rem;right:1rem;bottom:3.3rem;z-index:9;background:#fff;border:1px solid #bcae9b;border-radius:12px;box-shadow:0 2px 12px #0002}.activity-console details{padding:.75rem}.activity-console summary{cursor:pointer;font-weight:700}.activity-console table{width:100%;border-collapse:collapse;margin-top:.5rem;max-height:16rem;display:block;overflow:auto}.activity-console th,.activity-console td,.pipeline-view th,.pipeline-view td,.health-table th,.health-table td{border-bottom:1px solid #eee;padding:.35rem;text-align:left;vertical-align:top}.pipeline-view table,.health-table{width:100%;border-collapse:collapse;margin:.5rem 0 1rem}.pipeline-view textarea{width:100%;font-family:ui-monospace,monospace;font-size:.8rem;background:#f8f8f8;border:1px solid #d6cbbb;border-radius:6px}.severity,.health-badge{border-radius:999px;padding:.1rem .4rem;background:#e9ecef}.severity.warning,.severity.missing,.health-badge.warning,.health-badge.missing{background:#fff3cd;color:#6b4e16}.health-badge.fail{background:#f8d7da;color:#842029}.health-badge.pass{background:#d1e7dd;color:#0f5132}</style></head>\n'
        f'<body><header><h1>Office of the Steward — Local Command Center</h1><p>Local-only skeleton. Generated: {generated}. This dashboard summarizes existing Estate artifacts and shows placeholders for missing capabilities.</p></header><main class="grid">{"".join(panels)}</main>{activity_console}{status_bar}{_refresh_script()}</body></html>\n'
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
