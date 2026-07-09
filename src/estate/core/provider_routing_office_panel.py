"""Office-facing provider routing recommendation panel payloads.

The panel displays advisory recommendation evidence only. It does not schedule,
dispatch, assign, approve, or execute provider work.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

from estate.core.paths import ESTATE_ROOT

ROOT = ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd()
DEFAULT_LATEST_ARTIFACT = ROOT / "runtime" / "provider_routing" / "status" / "latest.json"
OFFICE_PANEL_BASE = ROOT / "runtime" / "provider_routing" / "office_panel"

ADVISORY_MESSAGE = (
    "Advisory provider-routing evidence only; this is not a movement decision. "
    "Traffic Controller / Operations Manager decides movement."
)
SENSITIVE_CLASSIFICATIONS = {"Sensitive", "Private", "Restricted", "Steward Only", "Local Only"}
STALE_AFTER = timedelta(hours=24)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def _iso_now() -> str:
    return _utc_now().isoformat().replace("+00:00", "Z")


def _parse_timestamp(value: Any) -> datetime | None:
    if not value:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if not isinstance(value, str):
        return None
    try:
        normalized = value.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(normalized)
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def _safe_text(value: Any, *, limit: int = 280) -> str:
    text = " ".join(str(value or "").split())
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def _classification_safe_summary(payload: dict[str, Any]) -> str:
    classification = str(payload.get("classification") or payload.get("metadata", {}).get("classification") or "Estate Internal")
    work_package_id = str(payload.get("work_package_id") or payload.get("metadata", {}).get("work_package_id") or "unknown work package")
    provider = str(payload.get("recommended_provider") or "unknown provider")
    if classification in SENSITIVE_CLASSIFICATIONS:
        return f"{classification} recommendation metadata for {work_package_id}; rationale redacted for Office-safe summary. Recommended provider: {provider}."
    rationale = _safe_text(payload.get("provider_rationale"), limit=220)
    return f"{classification} recommendation metadata for {work_package_id}. Recommended provider: {provider}. {rationale}".strip()


def unavailable_panel(reason: str, *, source_artifact: str = "", error: str | None = None) -> dict[str, Any]:
    errors = [error or reason]
    return {
        "available": False,
        "stale": False,
        "advisory_only": True,
        "latest_recommendation_id": "",
        "recommended_provider": "",
        "alternate_providers": [],
        "provider_rationale": "",
        "capacity_note": ADVISORY_MESSAGE,
        "local_runtime_required": False,
        "human_review_required": False,
        "boundary_review_required": False,
        "validation_rings_required": [],
        "not_recommended": {},
        "source_artifact": source_artifact,
        "work_package_id": "",
        "classification": "Estate Internal",
        "safe_summary": f"Provider routing recommendation panel unavailable: {reason}.",
        "warnings": [ADVISORY_MESSAGE],
        "errors": errors,
        "updated_at": _iso_now(),
    }


def build_office_panel_payload(payload: dict[str, Any], *, source_artifact: str = "", stale_after: timedelta = STALE_AFTER, now: datetime | None = None) -> dict[str, Any]:
    """Build a classification-aware Office panel payload from a recommendation artifact."""
    now = now or _utc_now()
    metadata = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
    updated_at = payload.get("updated_at") or payload.get("created_at") or metadata.get("created_at") or _iso_now()
    timestamp = _parse_timestamp(updated_at)
    stale = bool(timestamp and now - timestamp > stale_after)
    warnings = [ADVISORY_MESSAGE]
    if stale:
        warnings.append("Recommendation artifact is stale; Traffic Controller / Operations Manager should request fresh evidence before movement decisions.")
    local_runtime_required = bool(payload.get("local_runtime_required"))
    if local_runtime_required:
        warnings.append("Local runtime is required; avoid cloud-only movement until local-runtime constraints are reviewed.")
    if not payload.get("recommendation_id"):
        warnings.append("Recommendation artifact is missing a recommendation_id.")

    return {
        "available": True,
        "stale": stale,
        "advisory_only": True,
        "latest_recommendation_id": str(payload.get("recommendation_id") or ""),
        "recommended_provider": str(payload.get("recommended_provider") or ""),
        "alternate_providers": [str(item) for item in _as_list(payload.get("alternate_providers"))],
        "provider_rationale": _safe_text(payload.get("provider_rationale"), limit=500),
        "capacity_note": _safe_text(payload.get("capacity_note") or ADVISORY_MESSAGE, limit=500),
        "local_runtime_required": local_runtime_required,
        "human_review_required": bool(payload.get("human_review_required")),
        "boundary_review_required": bool(payload.get("boundary_review_required")),
        "validation_rings_required": [str(item) for item in _as_list(payload.get("validation_rings_required"))],
        "not_recommended": dict(payload.get("not_recommended") or {}),
        "source_artifact": source_artifact or str(payload.get("source_artifact") or metadata.get("source_artifact") or ""),
        "work_package_id": str(payload.get("work_package_id") or metadata.get("work_package_id") or ""),
        "classification": str(payload.get("classification") or metadata.get("classification") or "Estate Internal"),
        "safe_summary": _classification_safe_summary(payload),
        "warnings": warnings,
        "errors": [],
        "updated_at": str(updated_at),
    }


def load_latest_office_panel_payload(latest_path: str | Path = DEFAULT_LATEST_ARTIFACT, *, stale_after_hours: int = 24) -> dict[str, Any]:
    """Load latest provider recommendation evidence for the Office panel."""
    path = Path(latest_path)
    if not path.is_file():
        return unavailable_panel("latest recommendation artifact missing", source_artifact=str(path))
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return unavailable_panel("latest recommendation artifact malformed", source_artifact=str(path), error=str(exc))
    if not isinstance(payload, dict):
        return unavailable_panel("latest recommendation artifact is not an object", source_artifact=str(path))
    if not payload:
        return unavailable_panel("latest recommendation artifact empty", source_artifact=str(path))
    return build_office_panel_payload(payload, source_artifact=str(path), stale_after=timedelta(hours=stale_after_hours))


def write_office_panel_artifacts(panel: dict[str, Any], *, base: str | Path = OFFICE_PANEL_BASE) -> dict[str, Any]:
    """Write optional local panel summary artifacts; no live provider calls occur."""
    base_path = Path(base)
    base_path.mkdir(parents=True, exist_ok=True)
    latest = base_path / "latest.json"
    summary = base_path / "summary.json"
    latest.write_text(json.dumps(panel, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary_payload = {
        "available": panel.get("available", False),
        "stale": panel.get("stale", False),
        "advisory_only": True,
        "latest_recommendation_id": panel.get("latest_recommendation_id", ""),
        "recommended_provider": panel.get("recommended_provider", ""),
        "human_review_required": panel.get("human_review_required", False),
        "boundary_review_required": panel.get("boundary_review_required", False),
        "updated_at": panel.get("updated_at", _iso_now()),
    }
    summary.write_text(json.dumps(summary_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    result = dict(panel)
    result["office_panel_latest_path"] = str(latest.relative_to(ROOT)) if latest.is_relative_to(ROOT) else str(latest)
    result["office_panel_summary_path"] = str(summary.relative_to(ROOT)) if summary.is_relative_to(ROOT) else str(summary)
    return result
