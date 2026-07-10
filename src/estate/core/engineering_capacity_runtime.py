"""Engineering Capacity Runtime.

Combines provider capacity/health evidence with local worker runtime evidence into
an Office-readable dashboard artifact. The runtime is advisory only: it never
launches workers, consumes cloud seats, or schedules work.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from estate.core.paths import ESTATE_ROOT
from estate.core.provider_health import generate_provider_health_summary, utc_now_iso, _write_json
from estate.core.worker_runtime_monitor import generate_worker_runtime_monitor

RUNTIME_JSON = Path("runtime/engineering_capacity/dashboard.json")
RUNTIME_MD = Path("runtime/engineering_capacity/dashboard.md")
OFFICE_HANDOFF_MD = Path("operations/engineering_capacity/runtime_dashboard.md")

CLOUD_CODEX_HINTS = ("codex", "openai", "chatgpt")
LOCAL_WORKER_HINTS = ("local", "cli", "worker", "ollama")
FUEL_STATES = {"idle": 100, "available": 85, "busy": 55, "saturated": 20, "quota_limited": 0, "unknown": None}


def _root(root: str | Path | None = None) -> Path:
    return Path(root) if root is not None else (ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd())


def _provider_kind(provider: dict[str, Any]) -> str:
    text = " ".join(str(provider.get(k) or "").lower() for k in ["provider_id", "display_name", "provider_type"])
    if any(hint in text for hint in CLOUD_CODEX_HINTS):
        return "cloud_codex_seat"
    if any(hint in text for hint in LOCAL_WORKER_HINTS):
        return "local_worker_capacity"
    return "other_provider"


def _fuel_gauge(provider: dict[str, Any]) -> dict[str, Any]:
    capacity_state = provider.get("capacity_state") or "unknown"
    quota = provider.get("quota_remaining")
    percent = FUEL_STATES.get(capacity_state)
    if isinstance(quota, (int, float)) and provider.get("max_jobs"):
        try:
            percent = max(0, min(100, int((float(quota) / float(provider["max_jobs"])) * 100)))
        except (TypeError, ValueError, ZeroDivisionError):
            pass
    health = provider.get("health_status") or "unknown"
    blocked = health in {"blocked", "offline", "out_of_quota"} or capacity_state == "quota_limited"
    return {"percent": percent, "state": "empty" if blocked else capacity_state, "basis": "latest provider health/capacity artifacts"}


def generate_engineering_capacity_dashboard(*, root: str | Path | None = None, stale_after_minutes: int = 30, write: bool = True) -> dict[str, Any]:
    root_path = _root(root)
    provider_summary = generate_provider_health_summary(root=root_path, write=True)
    worker_monitor = generate_worker_runtime_monitor(root=root_path, stale_after_minutes=stale_after_minutes, write=True)

    providers = []
    cloud_seats = []
    local_providers = []
    for provider in provider_summary.get("providers") or []:
        item = dict(provider)
        item["capacity_kind"] = _provider_kind(item)
        item["fuel_gauge"] = _fuel_gauge(item)
        providers.append(item)
        if item["capacity_kind"] == "cloud_codex_seat":
            cloud_seats.append(item)
        elif item["capacity_kind"] == "local_worker_capacity":
            local_providers.append(item)

    workers = worker_monitor.get("workers") or []
    idle_workers = [w for w in workers if w.get("status") == "idle" and not w.get("stale")]
    blocked_workers = worker_monitor.get("blocked_workers") or []
    warning_count = len(worker_monitor.get("warnings") or [])
    constrained_cloud = [p for p in cloud_seats if p.get("health_status") in {"blocked", "offline", "out_of_quota"} or p.get("capacity_state") in {"saturated", "quota_limited"}]

    recommended = "Capacity evidence is green; Steward may assign work using normal governance."
    if constrained_cloud or blocked_workers or warning_count:
        recommended = "Review constrained cloud seats, blocked workers, and missing/stale evidence before assigning additional engineering work."
    elif not idle_workers:
        recommended = "No idle local worker evidence is available; refresh worker heartbeats before expanding local execution."

    payload = {
        "version": 1,
        "generated_at": utc_now_iso(),
        "constraints": {"advisory_only": True, "does_not_launch_workers": True, "does_not_consume_cloud_seats": True, "does_not_schedule_work": True},
        "summary": {
            "provider_count": len(providers),
            "cloud_codex_seat_count": len(cloud_seats),
            "constrained_cloud_codex_seat_count": len(constrained_cloud),
            "local_worker_provider_count": len(local_providers),
            "worker_count": len(workers),
            "idle_worker_count": len(idle_workers),
            "blocked_worker_count": len(blocked_workers),
            "worker_warning_count": warning_count,
            "recommended_next_action": recommended,
        },
        "cloud_codex_seats": cloud_seats,
        "local_worker_providers": local_providers,
        "providers": providers,
        "workers": workers,
        "source_artifacts": ["runtime/providers/health/status/summary.json", "runtime/workers/worker_runtime_monitor.json"],
        "office_install_handoff": {"dashboard_json": str(RUNTIME_JSON), "dashboard_markdown": str(RUNTIME_MD), "operator_handoff": str(OFFICE_HANDOFF_MD)},
    }
    if write:
        _write_json(root_path / RUNTIME_JSON, payload)
        text = format_engineering_capacity_dashboard(payload)
        for rel in (RUNTIME_MD, OFFICE_HANDOFF_MD):
            path = root_path / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
    return payload


def format_engineering_capacity_dashboard(payload: dict[str, Any]) -> str:
    s = payload.get("summary", {})
    lines = ["# Engineering Capacity Runtime Dashboard", "", f"Generated: {payload.get('generated_at')}", "", "Advisory only: this dashboard does not launch workers, consume Codex seats, or schedule work.", "", "## Summary", f"- Providers observed: {s.get('provider_count', 0)}", f"- Cloud Codex seats: {s.get('cloud_codex_seat_count', 0)}", f"- Constrained Cloud Codex seats: {s.get('constrained_cloud_codex_seat_count', 0)}", f"- Local worker providers: {s.get('local_worker_provider_count', 0)}", f"- Workers observed: {s.get('worker_count', 0)}", f"- Idle workers: {s.get('idle_worker_count', 0)}", f"- Blocked workers: {s.get('blocked_worker_count', 0)}", f"- Worker warnings: {s.get('worker_warning_count', 0)}", f"- Recommended next action: {s.get('recommended_next_action')}", "", "## Cloud Codex Seat Fuel Gauges"]
    if not payload.get("cloud_codex_seats"):
        lines.append("- No cloud Codex seat provider evidence found.")
    for p in payload.get("cloud_codex_seats") or []:
        gauge = p.get("fuel_gauge") or {}
        lines.append(f"- {p.get('provider_id')}: {p.get('health_status')} / {p.get('capacity_state')}; fuel={gauge.get('percent') if gauge.get('percent') is not None else 'unknown'}%; queue={p.get('queue_depth')}")
    lines += ["", "## Local Worker Runtime"]
    if not payload.get("workers"):
        lines.append("- No worker runtime evidence found.")
    for w in payload.get("workers") or []:
        lines.append(f"- {w.get('worker_id')}: {w.get('status')} / {w.get('health')}; assignment={(w.get('current_assignment') or {}).get('work_package_id') or 'none'}; next={w.get('recommended_next_action')}")
    return "\n".join(lines).rstrip() + "\n"
