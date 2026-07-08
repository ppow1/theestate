from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from estate.core.operational_status import SENSITIVE_CLASSIFICATIONS, summary_message
from estate.core.paths import ESTATE_ROOT
from estate.core.orchestrator_intake_decisions import load_office_intake_decision_surface

STATUS_FILES = {
    "latest": "runtime/operations/status/latest.json",
    "active": "runtime/operations/status/active.json",
    "recent": "runtime/operations/status/recent.json",
    "summary": "runtime/operations/status/summary.md",
}
ACTIVE_STALE_SECONDS = 15 * 60
RECENT_STALE_SECONDS = 24 * 60 * 60
GROUPS = [
    ("active", "Active"),
    ("awaiting_approval", "Awaiting Approval"),
    ("blocked_attention", "Blocked / Attention Required"),
    ("validation", "Validation"),
    ("recently_completed", "Recently Completed"),
    ("failed_cancelled", "Failed / Cancelled"),
]


def _root(root: Path | None = None) -> Path:
    return Path(root) if root is not None else ESTATE_ROOT


def _rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _age_info(updated_at: Any, threshold_seconds: int, now: datetime) -> dict[str, Any]:
    parsed = _parse_timestamp(updated_at)
    if parsed is None:
        return {"state": "uncertain", "is_stale": True, "age_seconds": None, "message": "Timestamp could not be parsed; freshness is uncertain."}
    age = max(0.0, (now - parsed).total_seconds())
    if age > threshold_seconds:
        return {"state": "stale", "is_stale": True, "age_seconds": age, "message": f"Status is stale; last updated {parsed.isoformat(timespec='seconds')}."}
    return {"state": "fresh", "is_stale": False, "age_seconds": age, "message": f"Last updated {parsed.isoformat(timespec='seconds')}."}


def _read_json_artifact(path: Path, root: Path) -> dict[str, Any]:
    rel = _rel(path, root)
    if not path.exists():
        return {"available": False, "path": rel, "error": None, "data": None}
    try:
        return {"available": True, "path": rel, "error": None, "data": json.loads(path.read_text(encoding="utf-8"))}
    except Exception as exc:
        return {"available": False, "path": rel, "error": f"Malformed JSON: {exc}", "data": None}


def _read_text_artifact(path: Path, root: Path) -> dict[str, Any]:
    rel = _rel(path, root)
    if not path.exists():
        return {"available": False, "path": rel, "error": None, "text": None}
    try:
        return {"available": True, "path": rel, "error": None, "text": path.read_text(encoding="utf-8")}
    except Exception as exc:
        return {"available": False, "path": rel, "error": f"Unreadable text artifact: {exc}", "text": None}


def _normalize_status(item: Any, *, source: str, freshness_threshold: int, now: datetime) -> dict[str, Any] | None:
    if not isinstance(item, dict):
        return None
    status = dict(item.get("status") if isinstance(item.get("status"), dict) else item)
    updated_at = status.get("updated_at") or status.get("created_at") or status.get("started_at")
    classification = status.get("classification") or "Estate Internal"
    metadata = status.get("metadata") if isinstance(status.get("metadata"), dict) else {}
    display = dict(status)
    display["source"] = source
    display["display_message"] = summary_message(status)
    display["message_redacted"] = classification in SENSITIVE_CLASSIFICATIONS and not metadata.get("summary_safe") is True
    display["freshness"] = _age_info(updated_at, freshness_threshold, now)
    display.setdefault("current_state", status.get("state") or "unknown")
    display.setdefault("last_message", status.get("message") or "")
    display.setdefault("activity_id", status.get("request_id") or status.get("assignment_id") or status.get("work_package_id") or status.get("worker_id") or "unknown")
    display.setdefault("artifact_paths", [])
    return display


def load_office_operational_activity(root: Path | None = None, *, now: datetime | None = None) -> dict[str, Any]:
    root = _root(root)
    now = now or _now()
    status_dir = root / "runtime" / "operations" / "status"
    artifacts = {
        "latest": _read_json_artifact(root / STATUS_FILES["latest"], root),
        "active": _read_json_artifact(root / STATUS_FILES["active"], root),
        "recent": _read_json_artifact(root / STATUS_FILES["recent"], root),
        "summary": _read_text_artifact(root / STATUS_FILES["summary"], root),
    }
    errors = [{"path": a["path"], "message": a["error"]} for a in artifacts.values() if a.get("error")]
    groups = {key: [] for key, _ in GROUPS}
    active_data = artifacts["active"].get("data") if artifacts["active"].get("available") else []
    recent_data = artifacts["recent"].get("data") if artifacts["recent"].get("available") else []
    latest_data = artifacts["latest"].get("data") if artifacts["latest"].get("available") else None

    items = []
    if isinstance(active_data, list):
        items.extend(_normalize_status(item, source=artifacts["active"]["path"], freshness_threshold=ACTIVE_STALE_SECONDS, now=now) for item in active_data)
    elif active_data is not None:
        errors.append({"path": artifacts["active"]["path"], "message": "Expected active.json to contain a list."})
    if isinstance(recent_data, list):
        items.extend(_normalize_status(item, source=artifacts["recent"]["path"], freshness_threshold=RECENT_STALE_SECONDS, now=now) for item in recent_data)
    elif recent_data is not None:
        errors.append({"path": artifacts["recent"]["path"], "message": "Expected recent.json to contain a list."})
    if isinstance(latest_data, dict) and latest_data.get("status"):
        latest_status = _normalize_status(latest_data.get("status"), source=artifacts["latest"]["path"], freshness_threshold=ACTIVE_STALE_SECONDS, now=now)
    else:
        latest_status = None
    seen = set()
    for item in [i for i in items if i]:
        key = (item.get("activity_id"), item.get("source"))
        if key in seen:
            continue
        seen.add(key)
        state = str(item.get("current_state") or "").lower()
        attention = bool(item.get("requires_attention"))
        validation = str(item.get("validation_status") or "").lower()
        if state == "awaiting approval":
            groups["awaiting_approval"].append(item)
        elif state == "validation" or validation not in {"", "not_validated", "not validated"}:
            groups["validation"].append(item)
        elif state in {"blocked"} or attention:
            groups["blocked_attention"].append(item)
        elif state == "completed":
            groups["recently_completed"].append(item)
        elif state in {"failed", "cancelled"}:
            groups["failed_cancelled"].append(item)
        elif state in {"planning", "waiting", "running", "reviewing", "deferred"}:
            groups["active"].append(item)
        else:
            groups["active"].append(item)
    any_available = any(artifacts[k].get("available") for k in ("latest", "active", "recent", "summary"))
    intake_surface = load_office_intake_decision_surface(root)
    return {
        "available": any_available or bool((intake_surface.get("items") or [])),
        "runtime_directory_accessible": status_dir.exists() and status_dir.is_dir(),
        "path": "; ".join(STATUS_FILES.values()),
        "kind": "office_operational_activity",
        "summary": {"status_artifact_found": any_available, "error_count": len(errors), "activity_count": sum(len(v) for v in groups.values()), "latest_status_available": latest_status is not None},
        "latest_status": latest_status,
        "groups": groups,
        "group_order": GROUPS,
        "artifacts": artifacts,
        "errors": errors,
        "empty_state": "No active operational status found.",
        "expected_status_artifact_paths": list(STATUS_FILES.values()),
        "stale_thresholds": {"active_seconds": ACTIVE_STALE_SECONDS, "recent_terminal_seconds": RECENT_STALE_SECONDS},
        "classification_behavior": "Restricted, Steward Only, and Local Only messages are redacted unless metadata.summary_safe is true.",
        "orchestrator_intake_decisions": intake_surface,
    }
