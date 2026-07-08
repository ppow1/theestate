from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from estate.core.operational_events import OperationalEvent, append_event_artifact
from estate.core.paths import ESTATE_ROOT

RUNTIME_STATUS_RELATIVE_DIR = Path("runtime/operations/status")
ACTIVE_STATES = {"Planning", "Waiting", "Running", "Reviewing", "Blocked", "Awaiting Approval", "Validation", "Deferred"}
TERMINAL_STATES = {"Completed", "Failed", "Cancelled"}
SENSITIVE_CLASSIFICATIONS = {"Restricted", "Steward Only", "Local Only"}


def _parse_ts(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _now() -> datetime:
    return datetime.now(timezone.utc)


def derive_activity_id(event: OperationalEvent) -> str:
    return event.request_id or event.assignment_id or event.work_package_id or event.worker_id or f"activity-{uuid4().hex}"


def summary_message(event_or_status: Any) -> str:
    classification = getattr(event_or_status, "classification", None) if not isinstance(event_or_status, dict) else event_or_status.get("classification")
    metadata = getattr(event_or_status, "metadata", {}) if not isinstance(event_or_status, dict) else event_or_status.get("metadata", {})
    message = getattr(event_or_status, "message", None) or getattr(event_or_status, "last_message", None) if not isinstance(event_or_status, dict) else event_or_status.get("last_message") or event_or_status.get("message")
    if classification in SENSITIVE_CLASSIFICATIONS and not (isinstance(metadata, dict) and metadata.get("summary_safe") is True):
        return "Sensitive operational message redacted."
    return message or ""


@dataclass
class ActivityStatus:
    activity_id: str
    current_state: str
    last_event_type: str
    last_message: str
    started_at: str
    updated_at: str
    elapsed_seconds: float
    worker_id: str | None = None
    worker_role: str | None = None
    provider_id: str | None = None
    provider_type: str | None = None
    assignment_id: str | None = None
    work_package_id: str | None = None
    request_id: str | None = None
    classification: str = "Estate Internal"
    budget_source: str | None = None
    validation_status: str = "not_validated"
    requires_attention: bool = False
    artifact_paths: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_event(cls, event: OperationalEvent, previous: "ActivityStatus | None" = None) -> "ActivityStatus":
        started_at = previous.started_at if previous else event.created_at
        updated_at = event.updated_at or event.created_at
        elapsed = max(0.0, (_parse_ts(updated_at) - _parse_ts(started_at)).total_seconds())
        return cls(
            activity_id=previous.activity_id if previous else derive_activity_id(event),
            current_state=event.state,
            last_event_type=event.event_type,
            last_message=event.message,
            started_at=started_at,
            updated_at=updated_at,
            elapsed_seconds=elapsed,
            worker_id=event.worker_id,
            worker_role=event.worker_role,
            provider_id=event.provider_id,
            provider_type=event.provider_type,
            assignment_id=event.assignment_id,
            work_package_id=event.work_package_id,
            request_id=event.request_id,
            classification=event.classification,
            budget_source=event.budget_source,
            validation_status=event.validation_status,
            requires_attention=event.requires_attention or event.state in {"Blocked", "Awaiting Approval", "Failed"},
            artifact_paths=event.artifact_paths,
            metadata=event.metadata,
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _load_list(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def update_status_files(event: OperationalEvent, root: Path | None = None, *, allow_extension_event_types: bool = False) -> dict[str, Path]:
    root = root or ESTATE_ROOT
    status_dir = root / RUNTIME_STATUS_RELATIVE_DIR
    status_dir.mkdir(parents=True, exist_ok=True)
    active_path, recent_path, latest_path, summary_path = (status_dir / n for n in ["active.json", "recent.json", "latest.json", "summary.md"])
    active = _load_list(active_path)
    recent = _load_list(recent_path)
    activity_id = derive_activity_id(event)
    previous_data = next((item for item in active + recent if item.get("activity_id") == activity_id), None)
    previous = ActivityStatus(**previous_data) if previous_data else None
    status = ActivityStatus.from_event(event, previous)
    active = [item for item in active if item.get("activity_id") != status.activity_id]
    recent = [item for item in recent if item.get("activity_id") != status.activity_id]
    target = active if status.current_state in ACTIVE_STATES else recent
    target.append(status.to_dict())
    active_path.write_text(json.dumps(active, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    recent_path.write_text(json.dumps(recent[-25:], indent=2, sort_keys=True) + "\n", encoding="utf-8")
    latest_path.write_text(json.dumps({"event": event.to_dict(allow_extension_event_types=allow_extension_event_types), "status": status.to_dict()}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary_path.write_text(generate_summary_markdown(root=root), encoding="utf-8")
    return {"active": active_path, "recent": recent_path, "latest": latest_path, "summary": summary_path}


def record_operational_event(event: OperationalEvent, root: Path | None = None, *, allow_extension_event_types: bool = False) -> dict[str, Path]:
    event_path = append_event_artifact(event, root=root, allow_extension_event_types=allow_extension_event_types)
    paths = update_status_files(event, root=root, allow_extension_event_types=allow_extension_event_types)
    paths["event_log"] = event_path
    return paths


def generate_summary_markdown(root: Path | None = None) -> str:
    status_dir = (root or ESTATE_ROOT) / RUNTIME_STATUS_RELATIVE_DIR
    active = _load_list(status_dir / "active.json") if (status_dir / "active.json").exists() else []
    recent = _load_list(status_dir / "recent.json") if (status_dir / "recent.json").exists() else []
    lines = ["# Operational Activity Summary", ""]
    if not active and not recent:
        lines.append("No operational activity recorded.")
        return "\n".join(lines) + "\n"
    sections = [("Active", active), ("Blocked", [a for a in active if a.get("current_state") == "Blocked"]), ("Awaiting Approval", [a for a in active if a.get("current_state") == "Awaiting Approval"]), ("Failed", [r for r in recent if r.get("current_state") == "Failed"]), ("Recent Completed", [r for r in recent if r.get("current_state") == "Completed"])]
    for title, items in sections:
        lines += [f"## {title}"]
        if not items:
            lines.append("- None")
        for item in items:
            lines.append(f"- {item.get('activity_id')} | {item.get('current_state')} | {summary_message(item)}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def format_summary_for_cli(root: Path | None = None) -> str:
    return generate_summary_markdown(root=root)
