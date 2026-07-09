"""Operator Activity Stream for the Operations Center.

Read-only aggregation of existing operational artifacts into a filterable event
feed. This module does not emit operational events or replace source logs.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

from estate.core.paths import ESTATE_ROOT

JSON_OUTPUT = "runtime/steward/operator_activity_stream.json"
MARKDOWN_OUTPUT = "operations/steward/operator_activity_stream.md"
PROFILES_OUTPUT = "runtime/steward/operator_activity_profiles.json"
DEFAULT_PROFILE_NAME = "default"
VERBOSITY_LEVELS = ["quiet", "normal", "detailed", "diagnostic"]
SEVERITY_ORDER = {"error": 0, "warning": 1, "missing": 1, "info": 2, "debug": 3}
SOURCE_ARTIFACTS = {
    "mission_control": ["runtime/steward/mission_control_workspace.json"],
    "workers": ["runtime/workers/worker_runtime_monitor.json", "runtime/workers/worker_runtime_heartbeat.json"],
    "validation": ["runtime/validation/local_operational_validation_run.json", "runtime/audit/latest.json"],
    "notifications": ["runtime/notifications/notification_router_report.json", "runtime/notifications/notification_center_workspace.json"],
    "mailboxes": ["runtime/collaboration/mailbox_index.json", "collaboration/mailboxes/index.json", "runtime/mailboxes/synchronization_duty_latest.json"],
    "service_health": ["runtime/services/service_status_board.json", "runtime/services/service_health_registry.json"],
    "work_packages": ["runtime/work_packages/assignment_queue.json"],
    "execution_activity": ["runtime/execution_activity/current.json"],
    "execution_dispatch": ["runtime/execution_dispatch/current.json"],
    "completions": ["collaboration/work_packages/completions"],
}


def _root(root=None):
    return Path(root) if root is not None else (ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd())


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _rel(path, root):
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def _mtime(path):
    return datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(timespec="seconds")


def _event(root, timestamp, source, topic, severity, message, artifact, *, verbosity="normal", link_path=None, metadata=None):
    rel = link_path or artifact
    return {
        "timestamp": timestamp or "unknown",
        "source": source,
        "topic": topic,
        "severity": severity,
        "message": str(message or "No message provided."),
        "verbosity": verbosity,
        "artifact": artifact,
        "link": {"path": rel, "available": bool(rel and (root / rel).exists())},
        "metadata": metadata or {},
    }


def _summary_event(root, source, artifact, data):
    summary = data.get("summary") if isinstance(data, dict) else {}
    if not isinstance(summary, dict):
        summary = {}
    warning_count = summary.get("warning_count") or len(data.get("warnings") or []) if isinstance(data, dict) else 0
    failed = summary.get("failed_steps", summary.get("failed", 0))
    severity = "error" if failed else ("warning" if warning_count else "info")
    title = source.replace("_", " ").title()
    return _event(root, data.get("generated_at") or _mtime(root / artifact), source, "summary", severity, f"{title} artifact available; warnings={warning_count}, failures={failed or 0}.", artifact, metadata={"summary": summary})


def _collect_events(root):
    events = []
    inputs = []
    for source, rels in SOURCE_ARTIFACTS.items():
        for rel in rels:
            path = root / rel
            if path.is_dir():
                inputs.append({"source": source, "path": rel, "available": True})
                for child in sorted(path.glob("*_codex_done.json"), key=lambda p: p.stat().st_mtime, reverse=True)[:12]:
                    try:
                        data = _read_json(child)
                        artifact = _rel(child, root)
                        events.append(_event(root, data.get("completed_at") or _mtime(child), source, data.get("work_package_id") or "completion", "info", data.get("summary") or "Work package completion recorded.", artifact, verbosity="quiet"))
                    except Exception as exc:
                        artifact = _rel(child, root)
                        events.append(_event(root, _now(), source, "completion", "warning", f"Completion record could not be read: {exc}", artifact))
                continue
            inputs.append({"source": source, "path": rel, "available": path.exists()})
            if not path.exists():
                events.append(_event(root, _now(), source, "missing_source", "missing", "Supporting artifact is not available yet.", rel, verbosity="normal"))
                continue
            if path.suffix == ".json":
                try:
                    data = _read_json(path)
                    events.append(_summary_event(root, source, rel, data))
                    for warning in (data.get("warnings") or [])[:8] if isinstance(data, dict) else []:
                        events.append(_event(root, data.get("generated_at") or _mtime(path), source, "warning", "warning", warning.get("message") if isinstance(warning, dict) else warning, rel, verbosity="detailed"))
                except Exception as exc:
                    events.append(_event(root, _mtime(path), source, "read_error", "error", f"Artifact could not be parsed: {exc}", rel))
            else:
                events.append(_event(root, _mtime(path), source, "artifact", "info", "Source artifact is present.", rel, verbosity="detailed"))
    return events, inputs


def _valid_verbosity(value):
    return value if value in VERBOSITY_LEVELS else "normal"


def _default_profiles():
    return {
        DEFAULT_PROFILE_NAME: {
            "name": DEFAULT_PROFILE_NAME,
            "description": "Concise operational summaries for routine Mission Control use.",
            "verbosity": "normal",
            "source_verbosity": {},
            "sources": [],
            "severities": [],
            "ui": {"theme": "system"},
        }
    }


def load_operator_activity_profiles(root=None):
    root = _root(root)
    path = root / PROFILES_OUTPUT
    profiles = _default_profiles()
    if path.exists():
        try:
            data = _read_json(path)
            stored = data.get("profiles", data) if isinstance(data, dict) else {}
            if isinstance(stored, dict):
                profiles.update({name: profile for name, profile in stored.items() if isinstance(profile, dict)})
        except Exception:
            pass
    return profiles


def save_operator_activity_profile(root=None, *, name=DEFAULT_PROFILE_NAME, sources=None, severities=None, verbosity="normal", source_verbosity=None, ui_theme="system", description=None):
    root = _root(root)
    profiles = load_operator_activity_profiles(root)
    profile = {
        "name": name,
        "description": description or f"Saved Operator Activity Stream profile: {name}.",
        "verbosity": _valid_verbosity(verbosity),
        "source_verbosity": {k: _valid_verbosity(v) for k, v in (source_verbosity or {}).items()},
        "sources": list(sources or []),
        "severities": list(severities or []),
        "ui": {"theme": ui_theme if ui_theme in {"system", "light", "dark"} else "system"},
        "updated_at": _now(),
    }
    profiles[name] = profile
    (root / "runtime/steward").mkdir(parents=True, exist_ok=True)
    (root / PROFILES_OUTPUT).write_text(json.dumps({"version": 1, "profiles": profiles}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return profile


def _resolve_profile(root, profile_name, sources, severities, verbosity, source_verbosity, ui_theme):
    profiles = load_operator_activity_profiles(root)
    selected = profiles.get(profile_name or DEFAULT_PROFILE_NAME, profiles[DEFAULT_PROFILE_NAME])
    return {
        "name": selected.get("name", profile_name or DEFAULT_PROFILE_NAME),
        "verbosity": _valid_verbosity(verbosity or selected.get("verbosity", "normal")),
        "source_verbosity": {**(selected.get("source_verbosity") or {}), **(source_verbosity or {})},
        "sources": list(sources if sources is not None else selected.get("sources", [])),
        "severities": list(severities if severities is not None else selected.get("severities", [])),
        "ui": {"theme": ui_theme or (selected.get("ui") or {}).get("theme", "system")},
        "available_profiles": sorted(profiles),
    }


def _filter_events(events, sources=None, severities=None, verbosity="normal", source_verbosity=None):
    src = set(sources or [])
    sev = set(severities or [])
    source_verbosity = source_verbosity or {}
    filtered = []
    for event in events:
        if src and event["source"] not in src:
            continue
        if sev and event["severity"] not in sev:
            continue
        event_verbosity = event.get("verbosity", "normal")
        effective = _valid_verbosity(source_verbosity.get(event["source"], verbosity))
        allowed = set(VERBOSITY_LEVELS[: VERBOSITY_LEVELS.index(effective) + 1])
        if event_verbosity in allowed:
            filtered.append(event)
    return sorted(filtered, key=lambda e: str(e.get("timestamp") or ""), reverse=True)


def generate_operator_activity_stream(root=None, write=True, sources=None, severities=None, verbosity=None, limit=50, profile=DEFAULT_PROFILE_NAME, save_profile=None, source_verbosity=None, ui_theme=None):
    root = _root(root)
    resolved = _resolve_profile(root, profile, sources, severities, verbosity, source_verbosity, ui_theme)
    if save_profile:
        save_operator_activity_profile(root, name=save_profile, sources=resolved["sources"], severities=resolved["severities"], verbosity=resolved["verbosity"], source_verbosity=resolved["source_verbosity"], ui_theme=resolved["ui"]["theme"])
        resolved = _resolve_profile(root, save_profile, None, None, None, None, None)
    events, inputs = _collect_events(root)
    filtered = _filter_events(events, sources=resolved["sources"], severities=resolved["severities"], verbosity=resolved["verbosity"], source_verbosity=resolved["source_verbosity"])[:limit]
    summary = {"total_event_count": len(events), "filtered_event_count": len(filtered), "source_count": len(SOURCE_ARTIFACTS), "warning_count": sum(1 for e in filtered if e["severity"] in {"warning", "missing"}), "error_count": sum(1 for e in filtered if e["severity"] == "error")}
    payload = {"version": 2, "generated_at": _now(), "authority": "read_only_operator_activity_stream_not_source_of_truth", "refresh_behavior": "quiet_live_updates_from_local_artifact_refresh", "verbosity_levels": VERBOSITY_LEVELS, "selected_profile": resolved["name"], "selected_verbosity": resolved["verbosity"], "source_verbosity": resolved["source_verbosity"], "filters": {"sources": resolved["sources"], "severities": resolved["severities"]}, "available_sources": sorted(SOURCE_ARTIFACTS), "available_profiles": resolved["available_profiles"], "ui_preferences": resolved["ui"], "empty_state": "No activity matches the selected filters." if not filtered else None, "inputs": inputs, "summary": summary, "events": filtered, "operations_center_integration": {"dockable_bottom_status_panel_ready": True, "read_only": True, "json_output": JSON_OUTPUT, "markdown_output": MARKDOWN_OUTPUT, "profiles_output": PROFILES_OUTPUT, "future_light_dark_ui_settings_ready": True}}
    if write:
        (root / "runtime/steward").mkdir(parents=True, exist_ok=True)
        (root / JSON_OUTPUT).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        (root / "operations/steward").mkdir(parents=True, exist_ok=True)
        (root / MARKDOWN_OUTPUT).write_text(format_operator_activity_stream(payload) + "\n", encoding="utf-8")
    return payload


def format_operator_activity_stream(payload):
    lines = ["# Operator Activity Stream", "", "Read-only Operations Center event feed aggregated from existing artifacts; it does not become an event source.", "", f"Generated: {payload.get('generated_at')}", f"Refresh behavior: {payload.get('refresh_behavior')}", f"Verbosity: {payload.get('selected_verbosity')}", "", "## Summary"]
    for key, value in (payload.get("summary") or {}).items():
        lines.append(f"- {key}: {value}")
    lines += ["", "## Events"]
    if not payload.get("events"):
        lines.append(f"- {payload.get('empty_state') or 'No events available.'}")
    for event in payload.get("events", []):
        lines.append(f"- [{event.get('severity')}] {event.get('timestamp')} — {event.get('source')} / {event.get('topic')}: {event.get('message')} (source: `{event.get('artifact')}`)")
    return "\n".join(lines)


def format_operator_activity_stream_summary(payload):
    summary = payload.get("summary") or {}
    return "\n".join(["Operator Activity Stream", f"Generated: {payload.get('generated_at')}", f"Events: {summary.get('filtered_event_count', 0)} / {summary.get('total_event_count', 0)}", f"Warnings: {summary.get('warning_count', 0)}", f"Errors: {summary.get('error_count', 0)}"])
