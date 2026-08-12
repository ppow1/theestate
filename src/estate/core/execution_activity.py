"""Shared execution activity surface.

This module normalizes local execution-provider lifecycle records into one
Office-readable current activity snapshot. It does not dispatch work, schedule
workers, or call live providers.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from estate.core.paths import ESTATE_ROOT

RUNTIME_DIR = Path("runtime/execution_activity")
EVENTS_OUTPUT = RUNTIME_DIR / "events.jsonl"
CURRENT_OUTPUT = RUNTIME_DIR / "current.json"
REPORT_OUTPUT = RUNTIME_DIR / "report.md"

CODEX_BRIDGE_DIR = Path("runtime/codex_bridge")
CODEX_BRIDGE_EVENT_OUTPUT = CODEX_BRIDGE_DIR / "events.jsonl"
CODEX_BRIDGE_CURRENT_OUTPUT = CODEX_BRIDGE_DIR / "current.json"
CODEX_BRIDGE_CURRENT_STATUS_OUTPUT = CODEX_BRIDGE_DIR / "current_status.json"

REQUIRED_EVENT_TYPES = {
    "job_accepted",
    "execution_started",
    "checkpoint_reached",
    "waiting_for_approval",
    "validation_started",
    "validation_passed",
    "validation_failed",
    "commit_created",
    "result_returned",
    "execution_complete",
    "execution_failed",
    "policy_denied",
}

ACTIVE_EVENT_TYPES = {
    "job_accepted",
    "execution_started",
    "checkpoint_reached",
    "validation_started",
}
BLOCKED_EVENT_TYPES = {"waiting_for_approval", "policy_denied"}
FAILED_EVENT_TYPES = {"execution_failed", "validation_failed"}
COMPLETED_EVENT_TYPES = {"execution_complete", "commit_created"}

ACTIVE_STATES = {"accepted", "active", "in_progress", "planning", "reviewing", "running", "validation", "waiting"}
BLOCKED_STATES = {"awaiting approval", "blocked", "policy denied", "waiting for approval"}
FAILED_STATES = {"error", "failed", "failure"}
COMPLETED_STATES = {"complete", "completed", "done", "succeeded", "success"}

SECRET_PATTERNS = [
    re.compile(r"(?<![A-Za-z0-9])sk-[A-Za-z0-9_-]{10,}"),
    re.compile(r"(Bearer\s+)[A-Za-z0-9._~+/=-]{12,}", re.IGNORECASE),
    re.compile(r"((?:api[_-]?key|token|password|secret)\s*[:=]\s*)[^\s,;]+", re.IGNORECASE),
]
AUTH_PATH_PATTERN = re.compile(
    r"(?i)(?:[A-Z]:[\\/][^\s,;]*|~?[\\/][^\s,;]*|\b[^\s,;]*)(?:\.codex|auth\.json|\.env|CODEX_HOME)[^\s,;]*"
)
SENSITIVE_METADATA_KEYS = {
    "api_key",
    "apikey",
    "auth",
    "auth_path",
    "codex_home",
    "credential",
    "credentials",
    "password",
    "prompt",
    "raw_prompt",
    "raw_stderr",
    "raw_stdout",
    "secret",
    "stderr",
    "stdout",
    "token",
}


@dataclass
class ExecutionActivityEvent:
    event_id: str | None = None
    request_id: str | None = None
    work_package_id: str | None = None
    source: str = "execution_activity"
    worker_label: str | None = None
    provider: str | None = None
    profile_label: str | None = None
    state: str | None = None
    event_type: str = "unknown"
    timestamp: str | None = None
    elapsed_seconds: float | None = None
    classification: str | None = None
    budget_source: str | None = None
    validation_status: str | None = None
    attention_required: bool = False
    summary: str | None = None
    current_assignment: str | None = None
    estimated_completion: str | None = None
    compute_resource_id: str | None = None
    gpu_uuid: str | None = None
    actual_runtime_resource_id: str | None = None
    actual_runtime_gpu_uuid: str | None = None
    placement_match: bool | None = None
    runtime_lane_id: str | None = None
    model_identity: str | None = None
    reservation_reference: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        if not data["metadata"]:
            data.pop("metadata")
        return data


@dataclass
class ActivityItem:
    request_id: str | None
    work_package_id: str | None
    worker_label: str | None
    provider: str | None
    profile_label: str | None
    current_assignment: str | None
    current_state: str | None
    elapsed_seconds: float | None
    estimated_completion: str | None
    budget_source: str | None
    classification: str | None
    validation_status: str | None
    last_event: dict[str, Any]
    attention_required: bool
    summary: str | None
    updated_at: str | None
    compute_resource_id: str | None = None
    gpu_uuid: str | None = None
    actual_runtime_resource_id: str | None = None
    actual_runtime_gpu_uuid: str | None = None
    placement_match: bool | None = None
    runtime_lane_id: str | None = None
    model_identity: str | None = None
    reservation_reference: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _root(root: str | Path | None = None) -> Path:
    if root is not None:
        return Path(root)
    return ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def _clean_text(value: Any) -> Any:
    if isinstance(value, str):
        text = AUTH_PATH_PATTERN.sub("[REDACTED_AUTH_PATH]", value)
        for pattern in SECRET_PATTERNS:
            if pattern.groups:
                text = pattern.sub(r"\1[REDACTED_SECRET]", text)
            else:
                text = pattern.sub("[REDACTED_SECRET]", text)
        return text
    if isinstance(value, dict):
        return {str(k): _clean_text(v) for k, v in value.items() if not _is_sensitive_key(str(k))}
    if isinstance(value, list):
        return [_clean_text(v) for v in value]
    return value


def _is_sensitive_key(key: str) -> bool:
    lower = key.lower().replace("-", "_")
    return lower in SENSITIVE_METADATA_KEYS or any(part in lower for part in SENSITIVE_METADATA_KEYS)


def _first(data: dict[str, Any], *names: str) -> Any:
    for name in names:
        if name in data and data[name] is not None:
            return data[name]
    return None


def _coerce_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _coerce_bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    return str(value).strip().lower() in {"1", "true", "yes", "y", "attention", "required"}


def _string_or_none(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return _clean_text(text) if text else None


def _metadata(data: dict[str, Any], mapped_keys: set[str]) -> dict[str, Any]:
    meta = {}
    for key, value in data.items():
        if key in mapped_keys or _is_sensitive_key(key):
            continue
        if isinstance(value, (str, int, float, bool, list, dict)) or value is None:
            meta[str(key)] = _clean_text(value)
    return meta


def normalize_activity_event(data: dict[str, Any], *, source: str = "execution_activity") -> ExecutionActivityEvent:
    """Normalize a provider or shared event record.

    Unknown event types are preserved as-is. Unknown extra fields are retained
    in sanitized metadata, except raw prompt/output/auth material.
    """

    if not isinstance(data, dict):
        raise ValueError("activity event must be a JSON object")
    last_event = data.get("last_event") if isinstance(data.get("last_event"), dict) else {}
    event_type = _string_or_none(
        _first(data, "event_type", "type", "kind") or last_event.get("event_type")
    ) or "unknown"
    state = _string_or_none(_first(data, "state", "current_state", "status"))
    attention_default = event_type in BLOCKED_EVENT_TYPES | FAILED_EVENT_TYPES
    mapped_keys = {
        "attention_required",
        "budget_source",
        "classification",
        "compute_resource_id",
        "actual_runtime_resource_id",
        "actual_runtime_gpu_uuid",
        "placement_match",
        "current_assignment",
        "current_state",
        "elapsed_seconds",
        "estimated_completion",
        "event_id",
        "event_type",
        "human_attention_required",
        "gpu_uuid",
        "kind",
        "last_event",
        "model_identity",
        "profile_label",
        "provider",
        "request_id",
        "reservation_reference",
        "runtime_lane_id",
        "security_classification",
        "source",
        "state",
        "status",
        "summary",
        "timestamp",
        "type",
        "updated_at",
        "validation_status",
        "work_package_id",
        "worker",
        "worker_label",
    }
    return ExecutionActivityEvent(
        event_id=_string_or_none(_first(data, "event_id") or last_event.get("event_id")),
        request_id=_string_or_none(_first(data, "request_id")),
        work_package_id=_string_or_none(_first(data, "work_package_id")),
        source=_string_or_none(_first(data, "source")) or source,
        worker_label=_string_or_none(_first(data, "worker_label", "worker")),
        provider=_string_or_none(_first(data, "provider")),
        profile_label=_string_or_none(_first(data, "profile_label")),
        state=state,
        event_type=event_type,
        timestamp=_string_or_none(_first(data, "timestamp", "updated_at")),
        elapsed_seconds=_coerce_float(_first(data, "elapsed_seconds")),
        classification=_string_or_none(_first(data, "classification", "security_classification")),
        budget_source=_string_or_none(_first(data, "budget_source")),
        validation_status=_string_or_none(_first(data, "validation_status")),
        attention_required=_coerce_bool(
            _first(data, "attention_required", "human_attention_required"),
            default=attention_default,
        ),
        summary=_string_or_none(_first(data, "summary") or last_event.get("summary")),
        current_assignment=_string_or_none(_first(data, "current_assignment")),
        estimated_completion=_string_or_none(_first(data, "estimated_completion")),
        compute_resource_id=_string_or_none(_first(data, "compute_resource_id")),
        gpu_uuid=_string_or_none(_first(data, "gpu_uuid")),
        actual_runtime_resource_id=_string_or_none(_first(data, "actual_runtime_resource_id")),
        actual_runtime_gpu_uuid=_string_or_none(_first(data, "actual_runtime_gpu_uuid")),
        placement_match=_coerce_bool(_first(data, "placement_match"), default=False) if _first(data, "placement_match") is not None else None,
        runtime_lane_id=_string_or_none(_first(data, "runtime_lane_id")),
        model_identity=_string_or_none(_first(data, "model_identity")),
        reservation_reference=_string_or_none(_first(data, "reservation_reference")),
        metadata=_metadata(data, mapped_keys),
    )


def _snapshot_event(snapshot: dict[str, Any], *, source: str) -> ExecutionActivityEvent:
    last_event = snapshot.get("last_event") if isinstance(snapshot.get("last_event"), dict) else {}
    data = dict(snapshot)
    data["source"] = source
    data["event_type"] = last_event.get("event_type") or data.get("event_type") or "snapshot_observed"
    data["event_id"] = last_event.get("event_id") or data.get("event_id") or f"snapshot-{data.get('request_id') or source}"
    data["timestamp"] = data.get("updated_at") or data.get("generated_at") or data.get("timestamp")
    data["summary"] = last_event.get("summary") or data.get("summary") or f"Snapshot reports {data.get('current_state') or 'unknown'}."
    return normalize_activity_event(data, source=source)


def parse_activity_jsonl(path: str | Path, *, source: str = "execution_activity") -> tuple[list[ExecutionActivityEvent], list[dict[str, str]]]:
    path = Path(path)
    events: list[ExecutionActivityEvent] = []
    warnings: list[dict[str, str]] = []
    if not path.exists():
        warnings.append({"type": "missing_runtime_file", "path": str(path), "message": "Runtime activity source is not available yet."})
        return events, warnings
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        warnings.append({"type": "read_error", "path": str(path), "message": str(exc)})
        return events, warnings
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            raw = json.loads(line)
            events.append(normalize_activity_event(raw, source=source))
        except (json.JSONDecodeError, ValueError) as exc:
            warnings.append({
                "type": "malformed_jsonl",
                "path": str(path),
                "message": f"line {line_number}: {exc}",
            })
    return events, warnings


def _read_snapshot(path: Path, *, source: str) -> tuple[list[ExecutionActivityEvent], list[dict[str, str]]]:
    if not path.exists():
        return [], [{"type": "missing_runtime_file", "path": str(path), "message": "Runtime current-status source is not available yet."}]
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [], [{"type": "read_error", "path": str(path), "message": str(exc)}]
    if isinstance(raw, dict) and isinstance(raw.get("active"), list):
        events = []
        for item in raw.get("active", []) + raw.get("blocked", []) + raw.get("attention_required", []) + raw.get("failed", []) + raw.get("recently_completed", []):
            if isinstance(item, dict):
                events.append(_snapshot_event(item, source=source))
        return events, []
    if isinstance(raw, dict):
        return [_snapshot_event(raw, source=source)], []
    return [], [{"type": "unsupported_snapshot", "path": str(path), "message": "Current-status source was not a JSON object."}]


def _codex_bridge_event_paths(root: Path) -> list[Path]:
    paths = [root / CODEX_BRIDGE_EVENT_OUTPUT]
    bridge_dir = root / CODEX_BRIDGE_DIR
    if bridge_dir.exists():
        paths.extend(sorted(path for path in bridge_dir.glob("*/events.jsonl") if path.is_file()))
    return paths


def load_activity_events(root: str | Path | None = None) -> tuple[list[ExecutionActivityEvent], list[dict[str, str]], list[str]]:
    base = _root(root)
    events: list[ExecutionActivityEvent] = []
    warnings: list[dict[str, str]] = []
    sources: list[str] = []

    normalized_path = base / EVENTS_OUTPUT
    parsed, source_warnings = parse_activity_jsonl(normalized_path, source="execution_activity")
    events.extend(parsed)
    warnings.extend(source_warnings)
    sources.append(_rel(normalized_path, base))

    for path in _codex_bridge_event_paths(base):
        parsed, source_warnings = parse_activity_jsonl(path, source="codex_bridge")
        events.extend(parsed)
        warnings.extend(source_warnings)
        sources.append(_rel(path, base))

    for rel_path, source in (
        (CODEX_BRIDGE_CURRENT_OUTPUT, "codex_bridge_current"),
        (CODEX_BRIDGE_CURRENT_STATUS_OUTPUT, "codex_bridge_current_status"),
    ):
        path = base / rel_path
        parsed, source_warnings = _read_snapshot(path, source=source)
        events.extend(parsed)
        warnings.extend(source_warnings)
        sources.append(_rel(path, base))

    return _dedupe_events(events), warnings, sources


def _event_sort_key(event: ExecutionActivityEvent) -> tuple[str, str, str]:
    return (event.timestamp or "", event.request_id or "", event.event_id or event.event_type)


def _dedupe_events(events: list[ExecutionActivityEvent]) -> list[ExecutionActivityEvent]:
    by_key: dict[str, ExecutionActivityEvent] = {}
    for event in sorted(events, key=_event_sort_key):
        key = event.event_id or f"{event.source}:{event.request_id}:{event.event_type}:{event.timestamp}"
        by_key[key] = event
    return sorted(by_key.values(), key=_event_sort_key)


def _item_from_events(request_id: str | None, events: list[ExecutionActivityEvent]) -> ActivityItem:
    latest = sorted(events, key=_event_sort_key)[-1]
    return ActivityItem(
        request_id=request_id or latest.request_id,
        work_package_id=latest.work_package_id,
        worker_label=latest.worker_label,
        provider=latest.provider,
        profile_label=latest.profile_label,
        current_assignment=latest.current_assignment or latest.work_package_id or latest.request_id,
        current_state=latest.state,
        elapsed_seconds=latest.elapsed_seconds,
        estimated_completion=latest.estimated_completion,
        budget_source=latest.budget_source,
        classification=latest.classification,
        validation_status=latest.validation_status,
        last_event={
            "event_id": latest.event_id,
            "event_type": latest.event_type,
            "timestamp": latest.timestamp,
            "summary": latest.summary,
        },
        attention_required=latest.attention_required,
        summary=latest.summary,
        updated_at=latest.timestamp,
        compute_resource_id=latest.compute_resource_id,
        gpu_uuid=latest.gpu_uuid,
        actual_runtime_resource_id=latest.actual_runtime_resource_id,
        actual_runtime_gpu_uuid=latest.actual_runtime_gpu_uuid,
        placement_match=latest.placement_match,
        runtime_lane_id=latest.runtime_lane_id,
        model_identity=latest.model_identity,
        reservation_reference=latest.reservation_reference,
    )


def _state_key(item: ActivityItem) -> str:
    return str(item.current_state or "").strip().lower()


def _item_event_type(item: ActivityItem) -> str:
    return str((item.last_event or {}).get("event_type") or "")


def _is_blocked(item: ActivityItem) -> bool:
    return _item_event_type(item) in BLOCKED_EVENT_TYPES or _state_key(item) in BLOCKED_STATES


def _is_failed(item: ActivityItem) -> bool:
    return _item_event_type(item) in FAILED_EVENT_TYPES or _state_key(item) in FAILED_STATES


def _is_completed(item: ActivityItem) -> bool:
    return _item_event_type(item) in COMPLETED_EVENT_TYPES or _state_key(item) in COMPLETED_STATES


def _is_active(item: ActivityItem) -> bool:
    if _is_blocked(item) or _is_failed(item) or _is_completed(item):
        return False
    return _item_event_type(item) in ACTIVE_EVENT_TYPES or _state_key(item) in ACTIVE_STATES


def _sort_items(items: list[ActivityItem]) -> list[dict[str, Any]]:
    return [
        item.to_dict()
        for item in sorted(
            items,
            key=lambda i: (str(i.updated_at or ""), str(i.worker_label or ""), str(i.request_id or "")),
            reverse=True,
        )
    ]


def _provider_summaries(items: list[ActivityItem]) -> list[dict[str, Any]]:
    buckets: dict[str, list[ActivityItem]] = {}
    for item in items:
        buckets.setdefault(item.provider or "unknown", []).append(item)
    providers = []
    for provider, bucket in buckets.items():
        state_counts: dict[str, int] = {}
        for item in bucket:
            state = item.current_state or "unknown"
            state_counts[state] = state_counts.get(state, 0) + 1
        active_count = sum(1 for item in bucket if _is_active(item))
        blocked_count = sum(1 for item in bucket if _is_blocked(item))
        failed_count = sum(1 for item in bucket if _is_failed(item))
        completed_count = sum(1 for item in bucket if _is_completed(item))
        if active_count:
            known_state = "active"
        elif blocked_count:
            known_state = "blocked"
        elif failed_count:
            known_state = "failed"
        elif completed_count:
            known_state = "idle_or_recently_completed"
        else:
            known_state = "unknown"
        providers.append({
            "provider": provider,
            "worker_labels": sorted({item.worker_label for item in bucket if item.worker_label}),
            "profile_labels": sorted({item.profile_label for item in bucket if item.profile_label}),
            "state_counts": dict(sorted(state_counts.items())),
            "active_count": active_count,
            "blocked_count": blocked_count,
            "failed_count": failed_count,
            "attention_required_count": sum(1 for item in bucket if item.attention_required),
            "recently_completed_count": completed_count,
            "capacity_known": False,
            "saturation_status": "unknown",
            "known_state": known_state,
        })
    return sorted(providers, key=lambda item: item["provider"])


def build_current_activity_snapshot(
    events: list[ExecutionActivityEvent],
    *,
    generated_at: str | None = None,
    source: str = str(EVENTS_OUTPUT).replace("\\", "/"),
    warnings: list[dict[str, str]] | None = None,
    sources: list[str] | None = None,
) -> dict[str, Any]:
    grouped: dict[str | None, list[ExecutionActivityEvent]] = {}
    for event in events:
        grouped.setdefault(event.request_id or event.event_id, []).append(event)
    items = [_item_from_events(request_id, grouped_events) for request_id, grouped_events in grouped.items()]
    active = [item for item in items if _is_active(item)]
    blocked = [item for item in items if _is_blocked(item)]
    attention = [item for item in items if item.attention_required]
    failed = [item for item in items if _is_failed(item)]
    completed = [item for item in items if _is_completed(item)]
    snapshot = {
        "version": 1,
        "generated_at": generated_at or _now(),
        "source": source,
        "sources": list(dict.fromkeys(sources or [source])),
        "active": _sort_items(active),
        "blocked": _sort_items(blocked),
        "attention_required": _sort_items(attention),
        "recently_completed": _sort_items(completed),
        "failed": _sort_items(failed),
        "providers": _provider_summaries(items),
        "warnings": warnings or [],
        "summary": {
            "event_count": len(events),
            "request_count": len(items),
            "active_count": len(active),
            "blocked_count": len(blocked),
            "attention_required_count": len(attention),
            "recently_completed_count": len(completed),
            "failed_count": len(failed),
            "provider_count": len({item.provider or "unknown" for item in items}),
            "warning_count": len(warnings or []),
        },
        "office_integration": {
            "current_json_path": str(CURRENT_OUTPUT).replace("\\", "/"),
            "report_path": str(REPORT_OUTPUT).replace("\\", "/"),
            "cli_json_command": "python -m estate.cli.main execution-activity --json",
            "cli_report_command": "python -m estate.cli.main execution-activity-report",
            "local_only": True,
            "does_not_dispatch_work": True,
        },
    }
    return _clean_text(snapshot)


def format_execution_activity_report(snapshot: dict[str, Any]) -> str:
    summary = snapshot.get("summary") or {}
    lines = [
        "# Execution Activity Surface",
        "",
        f"Generated: {snapshot.get('generated_at')}",
        f"Source: `{snapshot.get('source')}`",
        "",
        "## Summary",
        f"- Events: {summary.get('event_count', 0)}",
        f"- Requests: {summary.get('request_count', 0)}",
        f"- Active: {summary.get('active_count', 0)}",
        f"- Blocked: {summary.get('blocked_count', 0)}",
        f"- Attention required: {summary.get('attention_required_count', 0)}",
        f"- Failed: {summary.get('failed_count', 0)}",
        f"- Recently completed: {summary.get('recently_completed_count', 0)}",
        "",
    ]
    for key, title in (
        ("active", "Currently Running"),
        ("blocked", "Blocked"),
        ("attention_required", "Requires Steward Attention"),
        ("failed", "Failed"),
        ("recently_completed", "Recently Completed"),
    ):
        lines.extend([f"## {title}"])
        items = snapshot.get(key) or []
        if not items:
            lines.append("- None currently visible.")
        for item in items:
            last = item.get("last_event") or {}
            lines.append(
                "- "
                f"{item.get('request_id') or 'unknown request'} | "
                f"{item.get('work_package_id') or 'unassigned'} | "
                f"{item.get('worker_label') or 'unknown worker'} | "
                f"{item.get('provider') or 'unknown provider'} | "
                f"{item.get('profile_label') or 'no profile'} | "
                f"{item.get('runtime_lane_id') or 'no runtime lane'} | "
                f"{item.get('model_identity') or 'no model'} | "
                f"{item.get('compute_resource_id') or 'no physical resource'} | "
                f"{item.get('current_state') or 'unknown'} | "
                f"{last.get('event_type') or 'unknown'} | "
                f"{item.get('summary') or 'No summary.'}"
            )
        lines.append("")
    lines.extend(["## Providers"])
    providers = snapshot.get("providers") or []
    if not providers:
        lines.append("- No providers are visible yet.")
    for provider in providers:
        lines.append(
            "- "
            f"{provider.get('provider')}: state={provider.get('known_state')}, "
            f"active={provider.get('active_count')}, blocked={provider.get('blocked_count')}, "
            f"failed={provider.get('failed_count')}, saturation={provider.get('saturation_status')}"
        )
    lines.extend(["", "## Warnings"])
    warnings = snapshot.get("warnings") or []
    if not warnings:
        lines.append("- None.")
    for warning in warnings:
        if isinstance(warning, dict):
            lines.append(f"- {warning.get('type')}: {warning.get('path')} - {warning.get('message')}")
        else:
            lines.append(f"- {warning}")
    lines.extend([
        "",
        "## Boundary Notes",
        "- This surface reads local runtime artifacts only.",
        "- It does not schedule work, dispatch providers, or read provider auth stores.",
        "- Provider saturation remains unknown until provider-specific quota reporting exists.",
    ])
    return "\n".join(lines)


def generate_execution_activity_surface(
    root: str | Path | None = None,
    *,
    write: bool = True,
    generated_at: str | None = None,
) -> dict[str, Any]:
    base = _root(root)
    events, warnings, sources = load_activity_events(base)
    snapshot = build_current_activity_snapshot(events, generated_at=generated_at, warnings=warnings, sources=sources)
    if write:
        output_dir = base / RUNTIME_DIR
        output_dir.mkdir(parents=True, exist_ok=True)
        (base / EVENTS_OUTPUT).write_text(
            "".join(json.dumps(event.to_dict(), sort_keys=True) + "\n" for event in events),
            encoding="utf-8",
        )
        (base / CURRENT_OUTPUT).write_text(json.dumps(snapshot, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        (base / REPORT_OUTPUT).write_text(format_execution_activity_report(snapshot) + "\n", encoding="utf-8")
    return snapshot


def format_execution_activity_summary(snapshot: dict[str, Any]) -> str:
    summary = snapshot.get("summary") or {}
    return "\n".join([
        "Execution Activity Surface",
        f"Generated: {snapshot.get('generated_at')}",
        f"Active: {summary.get('active_count', 0)}",
        f"Blocked: {summary.get('blocked_count', 0)}",
        f"Attention required: {summary.get('attention_required_count', 0)}",
        f"Failed: {summary.get('failed_count', 0)}",
        f"Recently completed: {summary.get('recently_completed_count', 0)}",
        f"Current JSON: {CURRENT_OUTPUT}",
        f"Report: {REPORT_OUTPUT}",
    ])
