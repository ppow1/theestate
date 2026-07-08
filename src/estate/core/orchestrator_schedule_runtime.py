from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from estate.core.operational_events import OperationalEvent
from estate.core.operational_status import record_operational_event
from estate.core.orchestrator_intake_runtime import RUNTIME_RELATIVE_ROOT as INTAKE_ROOT, SENSITIVE_CLASSIFICATIONS, safe_summary
from estate.core.orchestrator_scheduler import OrchestratorScheduleRecord, determine_schedule_outcome
from estate.core.paths import ESTATE_ROOT
from estate.core.provider_catalog import load_provider_catalog

SCHEDULE_RUNTIME_RELATIVE_ROOT = Path("runtime/orchestrator/schedule")


class OrchestratorScheduleRuntime:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root or ESTATE_ROOT
        self.runtime_root = self.root / SCHEDULE_RUNTIME_RELATIVE_ROOT
        self.scheduled_dir = self.runtime_root / "scheduled"
        self.deferred_dir = self.runtime_root / "deferred"
        self.blocked_dir = self.runtime_root / "blocked"
        self.status_dir = self.runtime_root / "status"

    def ensure_dirs(self) -> None:
        for path in [self.scheduled_dir, self.deferred_dir, self.blocked_dir, self.status_dir]:
            path.mkdir(parents=True, exist_ok=True)

    def schedule(self, *, intake_id: str | None = None, request_path: Path | None = None, scheduled_by: str = "orchestrator", defer_if_provider_unavailable: bool = True, explicit_defer: bool = False) -> tuple[OrchestratorScheduleRecord, dict[str, str]]:
        self.ensure_dirs()
        intake = self._load_intake(intake_id, request_path)
        try:
            catalog = load_provider_catalog(self.root / "config" / "providers" / "catalog.json")
        except Exception:
            catalog = None
        state, reason = determine_schedule_outcome(intake, catalog=catalog, defer_if_provider_unavailable=defer_if_provider_unavailable, explicit_defer=explicit_defer)
        if intake is None:
            intake = {"intake_id": intake_id or "missing", "classification": "Estate Internal", "priority": "normal", "metadata": {}}
        record = OrchestratorScheduleRecord.create(intake=intake, state=state, scheduled_by=scheduled_by, blocked_reason=reason if state == "blocked" else None, metadata={"deferred_reason": reason} if state == "deferred" and reason else None)
        directory = {"scheduled": self.scheduled_dir, "deferred": self.deferred_dir, "blocked": self.blocked_dir}[record.state]
        artifact_path = directory / f"{record.schedule_id}.json"
        record.artifact_paths = [str(artifact_path)]
        artifact_path.write_text(json.dumps(record.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        event = self._event_for(record)
        try:
            event_paths = record_operational_event(event, root=self.root)
        except Exception as exc:
            event_paths = {}
            record.metadata = {**record.metadata, "operational_event_warning": str(exc)}
            artifact_path.write_text(json.dumps(record.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        latest_path = self.status_dir / "latest.json"
        queue_path = self.status_dir / "queue.json"
        latest_path.write_text(json.dumps(record.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        self._write_queue(queue_path)
        paths = {"artifact": str(artifact_path), "latest": str(latest_path), "queue": str(queue_path)}
        paths.update({f"operations_{k}": str(v) for k, v in event_paths.items()})
        return record, paths

    def _load_intake(self, intake_id: str | None, request_path: Path | None) -> dict[str, Any] | None:
        if request_path:
            return json.loads(request_path.read_text(encoding="utf-8"))
        if not intake_id:
            raise ValueError("--intake-id or --request is required")
        queue_path = self.root / INTAKE_ROOT / "status" / "queue.json"
        if queue_path.exists():
            queue = json.loads(queue_path.read_text(encoding="utf-8"))
            for item in [*(queue.get("pending") or []), *(queue.get("blocked") or [])]:
                if item.get("intake_id") == intake_id:
                    return self._hydrate_intake(item)
        latest_path = self.root / INTAKE_ROOT / "status" / "latest.json"
        if latest_path.exists():
            latest = json.loads(latest_path.read_text(encoding="utf-8"))
            if latest.get("intake_id") == intake_id:
                return self._hydrate_intake(latest)
        return None

    def _hydrate_intake(self, status: dict[str, Any]) -> dict[str, Any]:
        for artifact in status.get("artifact_paths") or []:
            path = Path(artifact)
            if path.exists() and path.name.endswith(".json") and "decisions" not in path.parts:
                try:
                    original = json.loads(path.read_text(encoding="utf-8"))
                    merged = {**original, **status}
                    merged.setdefault("required_capabilities", original.get("required_capabilities") or [])
                    merged.setdefault("allowed_paths", original.get("allowed_paths") or [])
                    merged.setdefault("forbidden_paths", original.get("forbidden_paths") or [])
                    merged.setdefault("expected_outputs", original.get("expected_outputs") or [])
                    return merged
                except Exception:
                    pass
        return status

    def _event_for(self, record: OrchestratorScheduleRecord) -> OperationalEvent:
        if record.state == "scheduled":
            event_type, state, message, attention = "Job Accepted", "Waiting", "Orchestrator scheduled approved intake; no provider execution was invoked.", False
        elif record.state == "deferred":
            event_type, state, message, attention = "Checkpoint Reached", "Deferred", record.metadata.get("deferred_reason") or "Scheduling deferred.", False
        else:
            if record.boundary_review_required:
                event_type, state = "Boundary Review Required", "Blocked"
            elif "Approval" in (record.blocked_reason or ""):
                event_type, state = "Waiting for Approval", "Awaiting Approval"
            else:
                event_type, state = "Worker Blocked", "Blocked"
            message, attention = record.blocked_reason or "Scheduling blocked.", True
        return OperationalEvent.create(event_type=event_type, state=state, classification=record.classification, message=message, provider_id=record.provider_id, provider_type=record.provider_type, assignment_id=record.assignment_id, work_package_id=record.work_package_id, request_id=record.intake_id, validation_status="not_validated" if record.validation_required else "not_required", requires_attention=attention, artifact_paths=record.artifact_paths, metadata={"schedule_id": record.schedule_id, "schedule_state": record.state})

    def _load_records(self) -> list[dict[str, Any]]:
        records = []
        for directory in [self.scheduled_dir, self.deferred_dir, self.blocked_dir]:
            if not directory.exists(): continue
            for path in sorted(directory.glob("*.json")):
                records.append(OrchestratorScheduleRecord.from_dict(json.loads(path.read_text(encoding="utf-8"))).to_dict())
        return records

    def _write_queue(self, queue_path: Path) -> None:
        records = self._load_records()
        payload = {"scheduled": [r for r in records if r["state"] == "scheduled"], "deferred": [r for r in records if r["state"] == "deferred"], "blocked": [r for r in records if r["state"] == "blocked"]}
        queue_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def queue_state(self) -> dict[str, Any]:
        self.ensure_dirs(); queue_path = self.status_dir / "queue.json"
        if not queue_path.exists(): self._write_queue(queue_path)
        return json.loads(queue_path.read_text(encoding="utf-8"))


def safe_schedule_summary(record: dict[str, Any]) -> str:
    if record.get("classification") in SENSITIVE_CLASSIFICATIONS and not (record.get("metadata") or {}).get("summary_safe"):
        return "Sensitive summary redacted."
    return record.get("metadata", {}).get("summary") or record.get("intake_id") or ""


def format_schedule_queue_for_cli(queue: dict[str, Any]) -> str:
    lines = ["Orchestrator Schedule Queue"]
    for label in ["scheduled", "deferred", "blocked"]:
        lines.append(label.upper())
        items = queue.get(label, [])
        if not items: lines.append("- None")
        for item in items:
            reason = item.get("blocked_reason") or (item.get("metadata") or {}).get("deferred_reason") or ""
            suffix = f" | {reason}" if reason else ""
            lines.append(f"- {item.get('schedule_id')} | intake={item.get('intake_id')} | {item.get('priority')}{suffix}")
    return "\n".join(lines)
