"""Local Office of the Steward command center web surface.

This module builds a lightweight, local-first HTML dashboard from existing
Estate artifacts. It intentionally avoids authentication, cloud services, and
new business logic; missing support artifacts become visible placeholders.
"""

import html
import json
from datetime import datetime, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from estate.core.paths import ESTATE_ROOT
from estate.core.resident_cards import build_resident_cards
from estate.core.decision_queue import generate_decision_queue

ARTIFACTS = {
    "morning_briefing": ["runtime/operations/morning_briefing.json", "operations/briefings/morning_briefing.md"],
    "mailbox_summary": ["runtime/collaboration/mailbox_index.json", "collaboration/mailboxes/index.json"],
    "work_package_pipeline": ["runtime/work_packages/assignment_queue.json", "operations/work_packages/assignment_queue.md"],
    "validation_status": ["runtime/validation/local_operational_validation_run.json", "operations/validation/local_operational_validation_run.md", "runtime/audit/latest.json"],
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


def _active_worker_count(root):
    artifact = _read_artifact(root, ["runtime/workers/heartbeat.json", "operations/workers/runtime_heartbeat.md"])
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
    estate_status = "Needs data" if missing else "Nominal"
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

def generate_command_center(root=None, write=True):
    root = _root(root)
    resident_cards = build_resident_cards(root)
    resident_panels = {f"{str(card.get('name', '')).lower()}_resident_card": card for card in resident_cards["cards"]}
    panels = {
        **resident_panels,
        "morning_briefing": _read_artifact(root, ARTIFACTS["morning_briefing"]),
        "steward_decision_queue": _decision_queue_artifact(root),
        "mailbox_summary": _read_artifact(root, ARTIFACTS["mailbox_summary"]),
        "work_package_pipeline": _read_artifact(root, ARTIFACTS["work_package_pipeline"]),
        "validation_status": _read_artifact(root, ARTIFACTS["validation_status"]),
    }
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
        _panel("Work Package Pipeline", _artifact_html(p.get("work_package_pipeline", {})), "ready" if p.get("work_package_pipeline", {}).get("available") else "placeholder"),
        _panel("Validation Status", _artifact_html(p.get("validation_status", {})), "ready" if p.get("validation_status", {}).get("available") else "placeholder"),
    ]
    status_bar = _status_bar_html(payload.get("status_bar", {}))
    activity_console = _activity_console_html(payload.get("activity_console", {}))
    generated = html.escape(str(payload.get("generated_at")))
    return (
        '<!doctype html>\n<html lang="en"><head><meta charset="utf-8"><title>Office of the Steward</title>\n'
        '<style>body{font-family:system-ui,sans-serif;margin:2rem 2rem 9rem;background:#f6f3ed;color:#241f1a}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:1rem}.panel{background:#fff;border:1px solid #d6cbbb;border-radius:12px;padding:1rem;box-shadow:0 1px 4px #0001}.placeholder{color:#6b4e16}.source{font-size:.85rem;color:#61584d}pre{white-space:pre-wrap;max-height:18rem;overflow:auto;background:#f8f8f8;padding:.75rem;border-radius:8px}dt{font-weight:700}dd{margin:0 0 .5rem}.status-bar{position:fixed;left:0;right:0;bottom:0;z-index:10;display:flex;gap:.75rem;flex-wrap:wrap;align-items:center;padding:.6rem .9rem;background:#241f1a;color:#fff;border-top:3px solid #b9904a;box-shadow:0 -2px 8px #0002}.status-item{font-size:.85rem;white-space:nowrap}.status-item strong{color:#f2d28b}.activity-console{position:fixed;left:1rem;right:1rem;bottom:3.3rem;z-index:9;background:#fff;border:1px solid #bcae9b;border-radius:12px;box-shadow:0 2px 12px #0002}.activity-console details{padding:.75rem}.activity-console summary{cursor:pointer;font-weight:700}.activity-console table{width:100%;border-collapse:collapse;margin-top:.5rem;max-height:16rem;display:block;overflow:auto}.activity-console th,.activity-console td{border-bottom:1px solid #eee;padding:.35rem;text-align:left;vertical-align:top}.severity{border-radius:999px;padding:.1rem .4rem;background:#e9ecef}.severity.warning,.severity.missing{background:#fff3cd;color:#6b4e16}</style></head>\n'
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
