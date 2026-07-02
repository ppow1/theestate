"""Worker Runtime Heartbeat service.

Records local evidence about Estate worker runtime health without scheduling,
remote monitoring, or invented state transitions.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from estate.core.paths import ESTATE_ROOT

VALID_STATUSES = {"idle", "active", "blocked", "offline"}
RUNTIME_DIR = "runtime/workers"
HEARTBEAT_DIR = "runtime/workers/heartbeats"
SUMMARY_JSON = "runtime/workers/worker_runtime_heartbeat.json"
SUMMARY_MARKDOWN = "operations/workers/runtime_heartbeat.md"
DEFAULT_STALE_AFTER_MINUTES = 60


def estate_root(root: str | Path | None = None) -> Path:
    return Path(root) if root is not None else (ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd())


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime | None = None) -> str:
    return (dt or _now()).astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        normalized = value.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(normalized)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except ValueError:
        return None


def _safe_worker_id(worker_id: str) -> str:
    safe = "".join(ch if ch.isalnum() or ch in {"-", "_", "."} else "_" for ch in worker_id.strip())
    if not safe:
        raise ValueError("worker_id is required")
    return safe


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def create_worker_heartbeat(
    worker_id: str,
    *,
    activity: str,
    status: str,
    last_completed_work_package: str | None = None,
    blocking_reason: str | None = None,
    identity: dict[str, Any] | None = None,
    root: str | Path | None = None,
    observed_at: str | None = None,
) -> dict[str, Any]:
    """Record a single worker heartbeat as local evidence."""
    if status not in VALID_STATUSES:
        raise ValueError(f"status must be one of {sorted(VALID_STATUSES)}")
    if status == "blocked" and not blocking_reason:
        raise ValueError("blocked heartbeats require a blocking_reason")
    if status != "blocked" and blocking_reason:
        raise ValueError("blocking_reason is only allowed for blocked heartbeats")

    root_path = estate_root(root)
    safe_id = _safe_worker_id(worker_id)
    heartbeat = {
        "version": 1,
        "worker_id": worker_id,
        "identity": identity or {"id": worker_id},
        "last_heartbeat": observed_at or _iso(),
        "current_activity": activity,
        "last_completed_work_package": last_completed_work_package,
        "status": status,
        "blocking_reason": blocking_reason,
        "evidence": "worker_reported_heartbeat",
    }
    _write_json(root_path / HEARTBEAT_DIR / f"{safe_id}.json", heartbeat)
    return heartbeat


def _load_heartbeats(root: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    directory = root / HEARTBEAT_DIR
    warnings: list[dict[str, Any]] = []
    workers: list[dict[str, Any]] = []
    if not directory.exists():
        return workers, warnings
    for path in sorted(directory.glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:  # malformed local evidence should not stop summary
            warnings.append({"type": "malformed_heartbeat", "path": str(path.relative_to(root)), "message": str(exc)})
            continue
        payload["source_path"] = str(path.relative_to(root))
        workers.append(payload)
    return workers, warnings


def generate_worker_runtime_summary(
    *,
    root: str | Path | None = None,
    stale_after_minutes: int = DEFAULT_STALE_AFTER_MINUTES,
    write: bool = True,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Summarize local worker heartbeat evidence and stale-heartbeat flags."""
    root_path = estate_root(root)
    current_time = (now or _now()).astimezone(timezone.utc)
    workers, warnings = _load_heartbeats(root_path)
    stale_cutoff = current_time - timedelta(minutes=stale_after_minutes)

    enriched: list[dict[str, Any]] = []
    counts = {status: 0 for status in sorted(VALID_STATUSES)}
    stale_count = 0
    for worker in workers:
        status = worker.get("status")
        if status in counts:
            counts[status] += 1
        else:
            warnings.append({"type": "unknown_status", "worker_id": worker.get("worker_id"), "status": status})
        parsed = _parse_time(worker.get("last_heartbeat"))
        is_stale = parsed is None or parsed < stale_cutoff
        if is_stale:
            stale_count += 1
        enriched.append({
            "worker_id": worker.get("worker_id"),
            "identity": worker.get("identity", {}),
            "last_heartbeat": worker.get("last_heartbeat"),
            "current_activity": worker.get("current_activity"),
            "last_completed_work_package": worker.get("last_completed_work_package"),
            "status": status,
            "blocking_reason": worker.get("blocking_reason"),
            "stale": is_stale,
            "stale_after_minutes": stale_after_minutes,
            "source_path": worker.get("source_path"),
            "state_basis": "reported_status_only; stale flag derives from recorded heartbeat age",
        })

    summary = {
        "version": 1,
        "generated_at": _iso(current_time),
        "constraints": {
            "scheduling_engine": False,
            "remote_monitoring": False,
            "state_inference_without_evidence": False,
        },
        "summary": {"worker_count": len(enriched), "stale_worker_count": stale_count, "status_counts": counts, "warning_count": len(warnings)},
        "workers": enriched,
        "warnings": warnings,
    }
    if write:
        _write_json(root_path / SUMMARY_JSON, summary)
        md = format_worker_runtime_summary(summary)
        path = root_path / SUMMARY_MARKDOWN
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(md, encoding="utf-8")
    return summary


def format_worker_runtime_summary(payload: dict[str, Any]) -> str:
    lines = [
        "# Worker Runtime Heartbeat",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        "This summary reflects local worker heartbeat evidence only. It does not run a scheduler, perform remote monitoring, or infer worker state without evidence.",
        "",
        "## Summary",
        f"- Workers with heartbeat evidence: {payload['summary']['worker_count']}",
        f"- Stale heartbeat records: {payload['summary']['stale_worker_count']}",
        f"- Warnings: {payload['summary']['warning_count']}",
        "",
        "## Workers",
    ]
    if not payload.get("workers"):
        lines.append("- No worker heartbeat evidence found.")
    for worker in payload.get("workers", []):
        blocked = f"; blocking reason: {worker['blocking_reason']}" if worker.get("blocking_reason") else ""
        stale = "stale" if worker.get("stale") else "fresh"
        lines.append(
            f"- {worker.get('worker_id')}: {worker.get('status')} ({stale}); activity: {worker.get('current_activity')}; "
            f"last completed: {worker.get('last_completed_work_package') or 'none'}{blocked}"
        )
    return "\n".join(lines) + "\n"
