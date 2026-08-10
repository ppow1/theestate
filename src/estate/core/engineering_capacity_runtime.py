"""Engineering Capacity Runtime.

Combines provider capacity/health evidence with local worker runtime evidence into
an Office-readable dashboard artifact. The runtime is advisory only: it never
launches workers, consumes cloud seats, or schedules work.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from estate.core.paths import ESTATE_ROOT
from estate.core.provider_health import generate_provider_health_summary, utc_now_iso, _write_json
from estate.core.provider_capacity import load_capacity_records
from estate.core.worker_runtime_monitor import generate_worker_runtime_monitor

RUNTIME_JSON = Path("runtime/engineering_capacity/dashboard.json")
RUNTIME_MD = Path("runtime/engineering_capacity/dashboard.md")
OFFICE_HANDOFF_MD = Path("operations/engineering_capacity/runtime_dashboard.md")

CLOUD_CODEX_HINTS = ("codex", "openai", "chatgpt")
LOCAL_WORKER_HINTS = ("local", "cli", "worker", "ollama")
FUEL_STATES = {"idle": 100, "available": 85, "busy": 55, "saturated": 20, "quota_limited": 0, "unknown": None}
CODEX_SEATS = ("C1", "C2", "C3")


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


def _freshness(provider: dict[str, Any], *, stale_after_minutes: int) -> dict[str, Any]:
    observed_at = provider.get("last_checked_at")
    result = {"state": "unknown", "observed_at": observed_at, "threshold_minutes": stale_after_minutes}
    if not observed_at:
        return result
    try:
        parsed = datetime.fromisoformat(str(observed_at).replace("Z", "+00:00"))
        age = max(0.0, (datetime.now(timezone.utc) - parsed.astimezone(timezone.utc)).total_seconds())
    except (TypeError, ValueError):
        return result
    result["age_seconds"] = int(age)
    result["state"] = "stale" if age > stale_after_minutes * 60 else "current"
    return result


def _codex_seat_observations(root: Path, *, stale_after_minutes: int) -> list[dict[str, Any]]:
    """Project one logical seat per observation; never derive a percentage from absence."""
    records = {}
    for record in load_capacity_records(root):
        metadata = record.metadata if isinstance(record.metadata, dict) else {}
        seat = metadata.get("seat_id")
        if seat in CODEX_SEATS and (seat not in records or record.checked_at >= records[seat].checked_at):
            records[seat] = record
    observations = []
    for seat in CODEX_SEATS:
        record = records.get(seat)
        if record is None:
            observations.append({
                "logical_seat_id": seat,
                "execution_surface": "codex-cli",
                "source": "codex-cli-capacity-discovery",
                "observation_timestamp": None,
                "freshness": {"state": "unknown", "observed_at": None, "threshold_minutes": stale_after_minutes},
                "capacity_state": "unknown",
                "native_capacity_fields": {},
                "collection_success": False,
                "reason": "installed Codex CLI exposes no supported noninteractive capacity/usage mechanism",
            })
            continue
        metadata = record.metadata if isinstance(record.metadata, dict) else {}
        observed = {"last_checked_at": record.checked_at}
        observations.append({
            "logical_seat_id": seat,
            "execution_surface": metadata.get("execution_surface", "codex-cli"),
            "source": metadata.get("source", record.reported_by),
            "observation_timestamp": record.checked_at,
            "freshness": _freshness(observed, stale_after_minutes=stale_after_minutes),
            "capacity_state": record.capacity_state,
            "native_capacity_fields": metadata.get("native_capacity_fields", {}),
            "active_jobs": record.active_jobs,
            "max_jobs": record.max_jobs,
            "queue_depth": record.queue_depth,
            "quota_remaining": record.quota_remaining,
            "quota_resets_at": record.quota_resets_at,
            "collection_success": metadata.get("collection_success", record.capacity_state != "unknown"),
            "reason": record.message,
        })
    return observations


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
        item["engineering_provider_capacity"] = {"index": item["fuel_gauge"].get("percent"), "state": item["capacity_state"], "basis": item["fuel_gauge"].get("basis"), "freshness": _freshness(item, stale_after_minutes=stale_after_minutes)}
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
    seat_observations = _codex_seat_observations(root_path, stale_after_minutes=stale_after_minutes)

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
            "codex_seat_observation_count": len(seat_observations),
        },
        "cloud_codex_seats": cloud_seats,
        "local_worker_providers": local_providers,
        "codex_seat_observations": seat_observations,
        "providers": providers,
        "workers": workers,
        "source_artifacts": ["runtime/providers/health/status/summary.json", "runtime/workers/worker_runtime_monitor.json"],
        "freshness_contract": {"provider_observation_stale_after_minutes": stale_after_minutes, "unknown_without_observation": True},
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
    lines = ["# Engineering Provider Capacity Runtime Dashboard", "", f"Generated: {payload.get('generated_at')}", "", "Engineering Provider Capacity is an advisory provider-availability index. It is not physical GPU utilization, GPU capacity, or an Estate-wide composite resource percentage.", "", "## Summary", f"- Providers observed: {s.get('provider_count', 0)}", f"- Providers with Codex capacity: {s.get('cloud_codex_seat_count', 0)}", f"- Constrained providers: {s.get('constrained_cloud_codex_seat_count', 0)}", f"- Codex seat observations: {s.get('codex_seat_observation_count', 0)}", f"- Local worker providers: {s.get('local_worker_provider_count', 0)}", f"- Workers observed: {s.get('worker_count', 0)}", f"- Idle workers: {s.get('idle_worker_count', 0)}", f"- Blocked workers: {s.get('blocked_worker_count', 0)}", f"- Worker warnings: {s.get('worker_warning_count', 0)}", f"- Recommended next action: {s.get('recommended_next_action')}", "", "## Codex Seat Capacity Observations"]
    for observation in payload.get("codex_seat_observations") or []:
        lines.append(f"- {observation.get('logical_seat_id')}: state={observation.get('capacity_state')}; collection={'success' if observation.get('collection_success') else 'unknown/unavailable'}; freshness={(observation.get('freshness') or {}).get('state')}; observed={observation.get('observation_timestamp') or 'unknown'}; reason={observation.get('reason') or 'none'}")
    lines.append("")
    lines.append("## Engineering Provider Capacity")
    if not payload.get("providers"):
        lines.append("- No provider evidence found.")
    for p in payload.get("providers") or []:
        capacity = p.get("engineering_provider_capacity") or {}
        freshness = capacity.get("freshness") or {}
        index = capacity.get("index")
        lines.append(f"- {p.get('provider_id')}: index={index if index is not None else 'unknown'}/100; state={capacity.get('state')}; freshness={freshness.get('state')}; observed={freshness.get('observed_at') or 'unknown'}; queue={p.get('queue_depth')}")
    lines += ["", "## Local Worker Runtime"]
    if not payload.get("workers"):
        lines.append("- No worker runtime evidence found.")
    for w in payload.get("workers") or []:
        lines.append(f"- {w.get('worker_id')}: {w.get('status')} / {w.get('health')}; assignment={(w.get('current_assignment') or {}).get('work_package_id') or 'none'}; next={w.get('recommended_next_action')}")
    return "\n".join(lines).rstrip() + "\n"
