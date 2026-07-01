"""Operational coordination helpers for the Estate Collaboration Layer.

These helpers implement repository-local routing and inbox observation without
changing the Collaboration Layer architecture. Alfred remains the operational
coordinator; this module only automates durable file inspection and routing
recommendations.
"""

import json
from datetime import datetime
from pathlib import Path

from estate.core.paths import ESTATE_ROOT
from estate.core.collaboration_events import append_event

DEFAULT_WORKER_RULES = [
    {
        "worker": "worker.documentation",
        "keywords": ["documentation", "docs", "manual", "readme", "handbook"],
        "message_types": ["documentation", "work_package"],
    },
    {
        "worker": "worker.audit",
        "keywords": ["audit", "validate", "validation", "check"],
        "message_types": ["audit", "validation"],
    },
    {
        "worker": "worker.implementation",
        "keywords": ["implement", "code", "test", "fix", "build"],
        "message_types": ["implementation", "work_package"],
    },
]

DEFAULT_QUEUE = "alfred.review"
OPEN_MESSAGE_STATUSES = {"open", "new", "queued", "ready"}


def _now():
    return datetime.now().isoformat(timespec="seconds")


def _read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def collaboration_paths(root=None):
    if root:
        base = Path(root)
    else:
        base = ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd()
    return {
        "root": base,
        "messages": base / "collaboration" / "messages",
        "status": base / "collaboration" / "status",
        "runtime": base / "runtime" / "collaboration",
        "routing": base / "runtime" / "collaboration" / "routing",
        "inboxes": base / "runtime" / "collaboration" / "worker_inboxes",
    }


def load_routing_config(root=None):
    paths = collaboration_paths(root)
    config_path = paths["root"] / "collaboration" / "routing_rules.json"
    if not config_path.exists():
        return {
            "version": 1,
            "default_queue": DEFAULT_QUEUE,
            "worker_rules": DEFAULT_WORKER_RULES,
        }
    return _read_json(config_path)


def _message_text(message):
    payload = message.get("payload", {}) if isinstance(message.get("payload", {}), dict) else {}
    parts = [
        message.get("id", ""),
        message.get("message_type", ""),
        message.get("destination", ""),
        payload.get("title", ""),
        payload.get("summary", ""),
        payload.get("instructions", ""),
    ]
    return " ".join(str(part).lower() for part in parts if part is not None)


def validate_message_envelope(message):
    required = ["id", "version", "created_at", "created_by", "source", "destination", "classification", "message_type", "priority", "status", "payload"]
    missing = [field for field in required if field not in message]
    if not isinstance(message.get("payload", {}), dict):
        missing.append("payload.object")
    return missing


def route_message(message, config=None):
    config = config or load_routing_config()
    text = _message_text(message)
    message_type = str(message.get("message_type", "")).lower()
    destination = str(message.get("destination", "")).strip()

    if destination and destination not in {"queue", "inbox", "alfred", "alfred.review"}:
        return {
            "worker": destination,
            "reason": "explicit_destination",
            "score": 100,
        }

    best = {"worker": config.get("default_queue", DEFAULT_QUEUE), "reason": "default_queue", "score": 0}
    for rule in config.get("worker_rules", []):
        score = 0
        if message_type in [item.lower() for item in rule.get("message_types", [])]:
            score += 5
        score += sum(1 for keyword in rule.get("keywords", []) if keyword.lower() in text)
        if score > best["score"]:
            best = {
                "worker": rule.get("worker", config.get("default_queue", DEFAULT_QUEUE)),
                "reason": "routing_rule",
                "score": score,
            }
    return best


def load_open_messages(root=None):
    paths = collaboration_paths(root)
    paths["messages"].mkdir(parents=True, exist_ok=True)
    messages = []
    errors = []
    for path in sorted(paths["messages"].glob("*.json")):
        try:
            message = _read_json(path)
        except Exception as exc:
            errors.append({"path": str(path), "error": str(exc)})
            continue
        if str(message.get("status", "")).lower() in OPEN_MESSAGE_STATUSES:
            messages.append({"path": str(path.relative_to(paths["root"])), "message": message})
    return messages, errors


def run_routing_engine(root=None):
    paths = collaboration_paths(root)
    config = load_routing_config(root)
    messages, errors = load_open_messages(root)
    decisions = []
    for item in messages:
        message = item["message"]
        missing = validate_message_envelope(message)
        decision = {
            "message_id": message.get("id"),
            "source_path": item["path"],
            "created_at": _now(),
            "valid": not missing,
            "missing_fields": missing,
            "route": route_message(message, config) if not missing else {"worker": "alfred.review", "reason": "invalid_envelope", "score": 0},
        }
        decisions.append(decision)

    report = {
        "version": 1,
        "generated_at": _now(),
        "open_messages": len(messages),
        "decisions": decisions,
        "errors": errors,
    }
    _write_json(paths["routing"] / "latest.json", report)
    for decision in decisions:
        try:
            append_event(
                "message.routed",
                "collaboration.routing_engine",
                {
                    "source_path": decision.get("source_path"),
                    "valid": decision.get("valid"),
                    "missing_fields": decision.get("missing_fields", []),
                    "route": decision.get("route", {}),
                },
                subject_id=decision.get("message_id"),
                root=paths["root"],
            )
        except Exception as exc:
            errors.append({"path": "runtime/collaboration/events/events.jsonl", "error": str(exc)})
    return report


def watch_worker_inboxes(root=None):
    paths = collaboration_paths(root)
    routing = run_routing_engine(root)
    inboxes = {}
    for decision in routing.get("decisions", []):
        worker = decision.get("route", {}).get("worker", DEFAULT_QUEUE)
        inboxes.setdefault(worker, []).append(decision)

    summary = {
        "version": 1,
        "generated_at": _now(),
        "worker_count": len(inboxes),
        "message_count": sum(len(items) for items in inboxes.values()),
        "workers": [
            {"worker": worker, "message_count": len(items), "messages": items}
            for worker, items in sorted(inboxes.items())
        ],
        "errors": routing.get("errors", []),
    }
    _write_json(paths["status"] / "worker_inbox_summary.json", summary)
    for worker, items in inboxes.items():
        safe_name = worker.replace("/", "_").replace("\\", "_").replace(":", "_")
        _write_json(paths["inboxes"] / f"{safe_name}.json", {"version": 1, "worker": worker, "messages": items})
    try:
        append_event(
            "inbox.updated",
            "collaboration.inbox_watcher",
            {"worker_count": summary["worker_count"], "message_count": summary["message_count"], "workers": [item["worker"] for item in summary["workers"]]},
            root=paths["root"],
        )
    except Exception as exc:
        summary.setdefault("errors", []).append({"path": "runtime/collaboration/events/events.jsonl", "error": str(exc)})
    return summary


def format_routing_report(report):
    lines = ["Estate Collaboration Routing", f"Open messages: {report.get('open_messages', 0)}"]
    for decision in report.get("decisions", []):
        route = decision.get("route", {})
        lines.append(f"- {decision.get('message_id')} -> {route.get('worker')} ({route.get('reason')}, score={route.get('score')})")
    if report.get("errors"):
        lines.append("Errors:")
        for error in report["errors"]:
            lines.append(f"- {error.get('path')}: {error.get('error')}")
    return "\n".join(lines)


def format_inbox_summary(summary):
    lines = ["Estate Worker Inbox Watcher", f"Workers: {summary.get('worker_count', 0)}", f"Messages: {summary.get('message_count', 0)}"]
    for worker in summary.get("workers", []):
        lines.append(f"- {worker.get('worker')}: {worker.get('message_count')} message(s)")
    return "\n".join(lines)
