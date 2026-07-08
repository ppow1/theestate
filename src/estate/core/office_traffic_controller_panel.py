from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from estate.core.paths import ESTATE_ROOT
from estate.core.traffic_controller import redact_summary

STATUS_FILES = {
    "latest": "runtime/operations/control/status/latest.json",
    "summary_json": "runtime/operations/control/status/summary.json",
    "summary_md": "runtime/operations/control/status/summary.md",
}
REVIEWS_DIR = "runtime/operations/control/reviews"
DECISIONS_DIR = "runtime/operations/control/decisions"
ACTIVE_STALE_SECONDS = 15 * 60
HISTORICAL_STALE_SECONDS = 24 * 60 * 60
SUPPORTED_CONTROLS = {"assign", "reprioritize", "hold", "release", "defer", "cancel", "escalate", "request_boundary_review", "request_revision", "request_validation"}


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


def _freshness(value: Any, threshold: int, now: datetime) -> dict[str, Any]:
    parsed = _parse_timestamp(value)
    if parsed is None:
        return {"state": "uncertain", "is_stale": True, "age_seconds": None, "message": "Timestamp could not be parsed; freshness is uncertain."}
    age = max(0.0, (now - parsed).total_seconds())
    if age > threshold:
        return {"state": "stale", "is_stale": True, "age_seconds": age, "message": f"Operations review is stale; last updated {parsed.isoformat(timespec='seconds')}."}
    return {"state": "fresh", "is_stale": False, "age_seconds": age, "message": f"Operations review updated {parsed.isoformat(timespec='seconds')}."}


def _read_json(path: Path, root: Path) -> dict[str, Any]:
    rel = _rel(path, root)
    if not path.exists():
        return {"available": False, "path": rel, "error": None, "data": None}
    try:
        return {"available": True, "path": rel, "error": None, "data": json.loads(path.read_text(encoding="utf-8"))}
    except Exception as exc:
        return {"available": False, "path": rel, "error": f"Malformed JSON: {exc}", "data": None}


def _redact(classification: str, text: Any, metadata: dict[str, Any] | None = None) -> tuple[str, bool]:
    original = "" if text is None else str(text)
    redacted = redact_summary(classification or "Estate Internal", original, metadata or {})
    return redacted, redacted != original


def _action_summary(action: Any) -> dict[str, Any] | None:
    if not isinstance(action, dict):
        return None
    classification = str(action.get("classification") or "Estate Internal")
    metadata = action.get("metadata") if isinstance(action.get("metadata"), dict) else {}
    text, was_redacted = _redact(classification, action.get("safe_summary") or action.get("reason") or "", metadata | {"summary_safe": action.get("summary_safe", metadata.get("summary_safe"))})
    action_type = str(action.get("action_type") or action.get("decision_type") or "unknown")
    supported = action_type in SUPPORTED_CONTROLS
    return {
        "action_type": action_type,
        "target_type": action.get("target_type") or "system",
        "target_id": action.get("target_id"),
        "priority": action.get("priority") or "normal",
        "summary": text,
        "summary_redacted": was_redacted,
        "requires_steward_approval": bool(action.get("requires_steward_approval") or action.get("requires_steward_attention")),
        "requires_boundary_review": bool(action.get("requires_boundary_review")),
        "control": {"available": supported, "action_id": "operations_control.record_decision" if supported else None, "decision_type": action_type if supported else None, "unavailable_reason": None if supported else f"No safe Office handler is registered for {action_type}."},
    }


def _decision_summary(decision: Any) -> dict[str, Any] | None:
    if not isinstance(decision, dict):
        return None
    classification = str(decision.get("classification") or "Estate Internal")
    reason, redacted = _redact(classification, decision.get("reason") or "", {"summary_safe": decision.get("summary_safe")})
    return {**decision, "safe_reason": reason, "reason_redacted": redacted}


def load_office_traffic_controller_panel(root: Path | None = None, *, now: datetime | None = None) -> dict[str, Any]:
    root = _root(root)
    now = now or _now()
    artifacts = {name: _read_json(root / rel, root) for name, rel in STATUS_FILES.items() if name != "summary_md"}
    md_path = root / STATUS_FILES["summary_md"]
    artifacts["summary_md"] = {"available": md_path.exists(), "path": _rel(md_path, root), "error": None, "data": None}
    errors = [{"path": item["path"], "message": item["error"]} for item in artifacts.values() if item.get("error")]
    latest = artifacts["latest"].get("data") if artifacts["latest"].get("available") else None
    summary = artifacts["summary_json"].get("data") if artifacts["summary_json"].get("available") else {}
    if latest is not None and not isinstance(latest, dict):
        errors.append({"path": artifacts["latest"]["path"], "message": "Expected latest operations review to be a JSON object."}); latest = None
    if not isinstance(summary, dict):
        errors.append({"path": artifacts["summary_json"]["path"], "message": "Expected summary.json to be a JSON object."}); summary = {}
    review_time = (latest or {}).get("created_at") or summary.get("generated_at")
    actions = [_action_summary(a) for a in ((latest or {}).get("recommended_actions") or summary.get("recommended_next_actions") or [])]
    actions = [a for a in actions if a]
    decisions = [_decision_summary(d) for d in (summary.get("recent_decisions") or [])]
    decisions = [d for d in decisions if d]
    blocked = summary.get("blocked_items") if isinstance(summary.get("blocked_items"), dict) else {}
    attention_count = summary.get("items_requiring_attention")
    if attention_count is None and latest:
        attention_count = int(latest.get("blocked_intake_count", 0)) + int(latest.get("assignment_blocked_count", 0)) + int(latest.get("provider_blocked_count", 0))
    available = any(item.get("available") for item in artifacts.values())
    return {
        "available": available,
        "kind": "office_traffic_controller_panel",
        "runtime_directory_accessible": (root / "runtime" / "operations" / "control").exists(),
        "path": "; ".join([*STATUS_FILES.values(), REVIEWS_DIR, DECISIONS_DIR]),
        "summary": {"artifact_found": available, "error_count": len(errors), "operational_posture": summary.get("current_operational_posture") or ("attention_required" if (latest or {}).get("requires_steward_attention") else "unknown"), "latest_review_at": review_time, "items_requiring_attention": attention_count or 0, "boundary_review_required": bool((latest or {}).get("requires_boundary_review")), "provider_capacity_warnings": summary.get("provider_capacity_warnings", (latest or {}).get("provider_saturated_count", 0)), "assignment_gaps": summary.get("assignment_gaps", 0)},
        "freshness": _freshness(review_time, ACTIVE_STALE_SECONDS, now),
        "historical_freshness": _freshness(review_time, HISTORICAL_STALE_SECONDS, now),
        "source_artifacts_inspected": (latest or {}).get("source_artifacts") or summary.get("source_artifacts_inspected") or [],
        "blocked_items": {"intake": blocked.get("intake", (latest or {}).get("blocked_intake_count", 0)), "assignments": blocked.get("assignments", (latest or {}).get("assignment_blocked_count", 0)), "providers": blocked.get("providers", (latest or {}).get("provider_blocked_count", 0))},
        "warnings": list((latest or {}).get("warnings") or summary.get("warnings") or []),
        "recommended_actions": actions,
        "recent_decisions": decisions,
        "artifacts": artifacts,
        "errors": errors,
        "expected_status_artifact_paths": [*STATUS_FILES.values(), REVIEWS_DIR, DECISIONS_DIR],
        "empty_state": "No operations-control artifacts found.",
        "classification_behavior": "Restricted, Steward Only, and Local Only summaries are redacted unless metadata.summary_safe is true.",
        "supported_controls": sorted(SUPPORTED_CONTROLS),
        "unavailable_controls_note": "Unsupported recommendations are shown unavailable rather than exposed as fake buttons.",
    }
