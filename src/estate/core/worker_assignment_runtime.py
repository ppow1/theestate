from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from estate.core.operational_events import OperationalEvent
from estate.core.operational_status import record_operational_event
from estate.core.paths import ESTATE_ROOT
from estate.core.provider_catalog import load_provider_catalog
from estate.core.provider_health import generate_provider_health_summary, utc_now_iso
from estate.core.worker_assignments import ACTIVE_STATES, WorkerAssignmentRecord, safe_assignment_summary

ASSIGNMENT_ROOT = Path("runtime/workers/assignments")
RECORDS_DIR = ASSIGNMENT_ROOT / "records"
STATUS_DIR = ASSIGNMENT_ROOT / "status"
STATE_EVENT_MAP = {
    "assigned": ("Job Accepted", "Waiting"),
    "accepted": ("Job Accepted", "Waiting"),
    "running": ("Execution Started", "Running"),
    "blocked": ("Worker Blocked", "Blocked"),
    "awaiting_approval": ("Waiting for Approval", "Awaiting Approval"),
    "validation": ("Validation Started", "Validation"),
    "completed": ("Execution Complete", "Completed"),
    "failed": ("Worker Failed", "Failed"),
    "cancelled": ("Worker Cancelled", "Cancelled"),
}


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


class WorkerAssignmentRuntime:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root or ESTATE_ROOT
        self.records_dir = self.root / RECORDS_DIR
        self.status_dir = self.root / STATUS_DIR

    def ensure_dirs(self) -> None:
        self.records_dir.mkdir(parents=True, exist_ok=True)
        self.status_dir.mkdir(parents=True, exist_ok=True)

    def write_assignment(self, record: WorkerAssignmentRecord, *, emit_event: bool = True) -> dict[str, str]:
        self.ensure_dirs()
        self._enrich_provider(record)
        path = self.records_dir / f"{record.assignment_id}.json"
        if str(path.relative_to(self.root)) not in record.artifact_paths:
            record.artifact_paths.append(str(path.relative_to(self.root)))
        _write_json(path, record.to_dict())
        if emit_event:
            self._emit_event(record)
        latest = self.status_dir / "latest.json"
        board = self.status_dir / "board.json"
        summary = self.status_dir / "summary.md"
        _write_json(latest, record.to_dict())
        board_payload = self.generate_board(write=True)
        return {"record": str(path), "latest": str(latest), "board": str(board), "summary": str(summary)}

    def create_assignment(self, **kwargs: Any) -> tuple[WorkerAssignmentRecord, dict[str, str]]:
        rec = WorkerAssignmentRecord.create(**kwargs)
        return rec, self.write_assignment(rec)

    def load_assignment(self, assignment_id: str) -> WorkerAssignmentRecord:
        path = self.records_dir / f"{assignment_id}.json"
        if not path.exists():
            raise ValueError(f"assignment not found: {assignment_id}")
        return WorkerAssignmentRecord.from_dict(json.loads(path.read_text(encoding="utf-8")))

    def update_assignment(self, assignment_id: str, *, state: str, blocked_reason: str | None = None, requires_attention: bool | None = None, metadata: dict[str, Any] | None = None) -> tuple[WorkerAssignmentRecord, dict[str, str]]:
        rec = self.load_assignment(assignment_id)
        rec.state = state
        rec.updated_at = utc_now_iso()
        if blocked_reason is not None:
            rec.blocked_reason = blocked_reason
        if requires_attention is not None:
            rec.requires_attention = requires_attention
        elif state in {"blocked", "failed"}:
            rec.requires_attention = True
        if metadata:
            rec.metadata.update(metadata)
        rec.validate()
        return rec, self.write_assignment(rec)

    def load_assignments(self) -> list[WorkerAssignmentRecord]:
        if not self.records_dir.exists():
            return []
        return [WorkerAssignmentRecord.from_dict(json.loads(path.read_text(encoding="utf-8"))) for path in sorted(self.records_dir.glob("*.json"))]

    def generate_board(self, *, write: bool = False) -> dict[str, Any]:
        records = self.load_assignments()
        provider_health = self._provider_health_context()
        assignments = []
        for rec in records:
            item = {k: rec.to_dict().get(k) for k in ["assignment_id", "assigned_to", "assignment_label", "worker_id", "worker_role", "provider_id", "provider_type", "seat_id", "profile_id", "work_package_id", "work_package_path", "state", "priority", "classification", "mission", "validation_required", "requires_attention", "blocked_reason", "updated_at", "artifact_paths"]}
            item["safe_summary"] = safe_assignment_summary(rec)
            if rec.provider_id and rec.provider_id in provider_health:
                item["provider_health"] = provider_health[rec.provider_id]
            assignments.append(item)
        counts = Counter(r.state for r in records)
        payload = {"generated_at": utc_now_iso(), "assignment_count": len(records), "active_count": sum(1 for r in records if r.state in ACTIVE_STATES), "blocked_count": counts.get("blocked", 0), "awaiting_approval_count": counts.get("awaiting_approval", 0), "completed_count": counts.get("completed", 0), "failed_count": counts.get("failed", 0), "assignments": assignments}
        if write:
            _write_json(self.status_dir / "board.json", payload)
            (self.status_dir / "summary.md").write_text(format_assignment_board(payload), encoding="utf-8")
        return payload

    def _enrich_provider(self, rec: WorkerAssignmentRecord) -> None:
        if not rec.provider_id:
            return
        try:
            provider = load_provider_catalog(self.root / "config" / "providers" / "catalog.json").get_provider(rec.provider_id)
            rec.provider_type = rec.provider_type or provider.provider_type
        except Exception as exc:
            rec.metadata.setdefault("provider_catalog_warning", str(exc))

    def _provider_health_context(self) -> dict[str, Any]:
        try:
            return {p["provider_id"]: {"health_status": p.get("health_status"), "capacity_state": p.get("capacity_state"), "requires_attention": p.get("requires_attention")} for p in generate_provider_health_summary(root=self.root).get("providers", [])}
        except Exception:
            return {}

    def _emit_event(self, rec: WorkerAssignmentRecord) -> None:
        if rec.state not in STATE_EVENT_MAP:
            return
        event_type, state = STATE_EVENT_MAP[rec.state]
        event = OperationalEvent.create(event_type=event_type, state=state, classification=rec.classification, message=safe_assignment_summary(rec), worker_id=rec.worker_id, worker_role=rec.worker_role, provider_id=rec.provider_id, provider_type=rec.provider_type, assignment_id=rec.assignment_id, work_package_id=rec.work_package_id, request_id=rec.intake_id, validation_status="not_validated" if rec.validation_required else "not_required", requires_attention=rec.requires_attention, artifact_paths=rec.artifact_paths, metadata={"assignment_state": rec.state, "schedule_id": rec.schedule_id, "summary_safe": rec.metadata.get("summary_safe", False)})
        try:
            record_operational_event(event, root=self.root)
        except Exception as exc:
            rec.metadata.setdefault("operational_event_warning", str(exc))


def format_assignment_board(board: dict[str, Any]) -> str:
    lines = ["# Worker Assignment Board", "", f"Generated: {board.get('generated_at')}", f"Assignments: {board.get('assignment_count', 0)}", f"Active: {board.get('active_count', 0)}", f"Blocked: {board.get('blocked_count', 0)}", "", "Assignment | Assigned To | State | Priority | Work Package | Summary"]
    for item in board.get("assignments", []):
        lines.append(f"{item.get('assignment_id')} | {item.get('assigned_to')} | {item.get('state')} | {item.get('priority')} | {item.get('work_package_id') or ''} | {item.get('safe_summary')}")
    return "\n".join(lines).rstrip() + "\n"
