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


def generate_command_center(root=None, write=True):
    root = _root(root)
    resident_cards = build_resident_cards(root)
    resident_panels = {f"{str(card.get('name', '')).lower()}_resident_card": card for card in resident_cards["cards"]}
    panels = {
        **resident_panels,
        "morning_briefing": _read_artifact(root, ARTIFACTS["morning_briefing"]),
        "steward_decision_queue": {"available": False, "path": None, "placeholder": "Steward Decision Queue panel is reserved for the decision queue implementation."},
        "mailbox_summary": _read_artifact(root, ARTIFACTS["mailbox_summary"]),
        "work_package_pipeline": _read_artifact(root, ARTIFACTS["work_package_pipeline"]),
        "validation_status": _read_artifact(root, ARTIFACTS["validation_status"]),
    }
    payload = {"version": 1, "generated_at": _now(), "local_only": True, "panels": panels}
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


def _artifact_html(artifact):
    if not artifact.get("available"):
        path = artifact.get("path") or "not yet produced"
        return f'<p class="placeholder">{html.escape(artifact.get("placeholder", "Unavailable"))}</p><p class="source">Source: {html.escape(str(path))}</p>'
    if artifact.get("kind") == "json":
        content = _summarize_json(artifact.get("data"))
    else:
        content = (artifact.get("text") or "").strip()[:1000] or "Text artifact is present but empty."
    return f'<pre>{html.escape(content)}</pre><p class="source">Source: {html.escape(artifact.get("path", ""))}</p>'


def render_command_center_html(payload):
    p = payload.get("panels", {})
    panels = [
        _panel("Alfred Resident Card", _resident_html(p.get("alfred_resident_card", {})), "ready" if p.get("alfred_resident_card", {}).get("available") else "placeholder"),
        _panel("Helen Resident Card", _resident_html(p.get("helen_resident_card", {})), "ready" if p.get("helen_resident_card", {}).get("available") else "placeholder"),
        _panel("Morning Briefing", _artifact_html(p.get("morning_briefing", {})), "ready" if p.get("morning_briefing", {}).get("available") else "placeholder"),
        _panel("Steward Decision Queue", _artifact_html(p.get("steward_decision_queue", {})), "placeholder"),
        _panel("Mailbox Summary", _artifact_html(p.get("mailbox_summary", {})), "ready" if p.get("mailbox_summary", {}).get("available") else "placeholder"),
        _panel("Work Package Pipeline", _artifact_html(p.get("work_package_pipeline", {})), "ready" if p.get("work_package_pipeline", {}).get("available") else "placeholder"),
        _panel("Validation Status", _artifact_html(p.get("validation_status", {})), "ready" if p.get("validation_status", {}).get("available") else "placeholder"),
    ]
    return """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Office of the Steward</title>
<style>body{font-family:system-ui,sans-serif;margin:2rem;background:#f6f3ed;color:#241f1a}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:1rem}.panel{background:#fff;border:1px solid #d6cbbb;border-radius:12px;padding:1rem;box-shadow:0 1px 4px #0001}.placeholder{color:#6b4e16}.source{font-size:.85rem;color:#61584d}pre{white-space:pre-wrap;max-height:18rem;overflow:auto;background:#f8f8f8;padding:.75rem;border-radius:8px}dt{font-weight:700}dd{margin:0 0 .5rem}</style></head>
<body><header><h1>Office of the Steward — Local Command Center</h1><p>Local-only skeleton. Generated: %s. This dashboard summarizes existing Estate artifacts and shows placeholders for missing capabilities.</p></header><main class="grid">%s</main></body></html>
""" % (html.escape(str(payload.get("generated_at"))), "".join(panels))


def serve_command_center(host="127.0.0.1", port=8765, root=None):
    root = _root(root)
    payload = generate_command_center(root=root, write=True)
    html_doc = render_command_center_html(payload).encode("utf-8")

    class Handler(SimpleHTTPRequestHandler):
        def do_GET(self):
            if self.path in ("/", "/index.html", "/command-center"):
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(html_doc)))
                self.end_headers()
                self.wfile.write(html_doc)
                return
            self.send_error(404, "Command center only serves the local dashboard.")

    return ThreadingHTTPServer((host, port), Handler)
