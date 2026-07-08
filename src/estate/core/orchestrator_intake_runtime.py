from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from estate.core.operational_events import OperationalEvent, utc_now_iso
from estate.core.operational_status import record_operational_event
from estate.core.orchestrator_intake import OrchestratorIntakeRequest, OrchestratorIntakeStatus, determine_block_reason
from estate.core.paths import ESTATE_ROOT

RUNTIME_RELATIVE_ROOT = Path("runtime/orchestrator/intake")
SENSITIVE_CLASSIFICATIONS = {"Restricted", "Steward Only", "Local Only"}


class OrchestratorIntakeRuntime:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root or ESTATE_ROOT
        self.runtime_root = self.root / RUNTIME_RELATIVE_ROOT
        self.pending_dir = self.runtime_root / "pending"
        self.accepted_dir = self.runtime_root / "accepted"
        self.blocked_dir = self.runtime_root / "blocked"
        self.status_dir = self.runtime_root / "status"
        self.events_dir = self.runtime_root / "events"

    def ensure_dirs(self) -> None:
        for path in [self.pending_dir, self.accepted_dir, self.blocked_dir, self.status_dir, self.events_dir]:
            path.mkdir(parents=True, exist_ok=True)

    def submit(self, request: OrchestratorIntakeRequest) -> tuple[OrchestratorIntakeStatus, dict[str, str]]:
        self.ensure_dirs()
        blocked_reason = determine_block_reason(request)
        state = "blocked" if blocked_reason else "pending"
        artifact_dir = self.blocked_dir if blocked_reason else self.pending_dir
        artifact_path = artifact_dir / f"{request.intake_id}.json"
        event_path = self.events_dir / f"{request.intake_id}.jsonl"
        latest_path = self.status_dir / "latest.json"
        queue_path = self.status_dir / "queue.json"
        now = utc_now_iso()
        artifact_path.write_text(json.dumps(request.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        status = OrchestratorIntakeStatus.from_request(request, state=state, updated_at=now, blocked_reason=blocked_reason, artifact_paths=[str(artifact_path)])
        event = self._event_for(request, status)
        event_path.write_text(json.dumps(event.to_dict(), sort_keys=True) + "\n", encoding="utf-8")
        try:
            record_operational_event(event, root=self.root)
        except Exception as exc:  # compatibility hook must not reject valid intake
            status.metadata = {**status.metadata, "operational_event_warning": str(exc)}
        latest_path.write_text(json.dumps(status.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        self._write_queue(queue_path)
        return status, {"artifact": str(artifact_path), "event": str(event_path), "latest": str(latest_path), "queue": str(queue_path)}

    def _event_for(self, request: OrchestratorIntakeRequest, status: OrchestratorIntakeStatus) -> OperationalEvent:
        if status.state == "blocked":
            if request.classification == "Restricted":
                event_type, state = "Boundary Review Required", "Blocked"
            elif request.classification == "Steward Only":
                event_type, state = "Waiting for Approval", "Awaiting Approval"
            else:
                event_type, state = "Worker Blocked", "Blocked"
            message = status.blocked_reason or "Intake blocked."
        else:
            event_type, state, message = "Job Accepted", "Waiting", "Orchestrator intake accepted into pending queue."
        return OperationalEvent.create(event_type=event_type, state=state, classification=request.classification, message=message, provider_id=request.requested_provider_id, provider_type=request.requested_provider_type, assignment_id=request.assignment_id, work_package_id=request.work_package_id, request_id=request.intake_id, budget_source=request.budget_source, requires_attention=status.state == "blocked", artifact_paths=status.artifact_paths, metadata={**request.metadata, "intake_state": status.state})

    def _load_statuses(self) -> list[dict[str, Any]]:
        statuses = []
        for state_dir, state in [(self.pending_dir, "pending"), (self.blocked_dir, "blocked")]:
            if not state_dir.exists():
                continue
            for path in sorted(state_dir.glob("*.json")):
                request = OrchestratorIntakeRequest.from_dict(json.loads(path.read_text(encoding="utf-8")))
                reason = determine_block_reason(request) if state == "blocked" else None
                statuses.append(OrchestratorIntakeStatus.from_request(request, state=state, updated_at=request.created_at, blocked_reason=reason, artifact_paths=[str(path)]).to_dict())
        return statuses

    def _write_queue(self, queue_path: Path) -> None:
        statuses = self._load_statuses()
        payload = {"pending": [s for s in statuses if s["state"] == "pending"], "blocked": [s for s in statuses if s["state"] == "blocked"]}
        queue_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def queue_state(self) -> dict[str, Any]:
        self.ensure_dirs()
        queue_path = self.status_dir / "queue.json"
        if not queue_path.exists():
            self._write_queue(queue_path)
        return json.loads(queue_path.read_text(encoding="utf-8"))


def safe_summary(status: dict[str, Any]) -> str:
    if status.get("classification") in SENSITIVE_CLASSIFICATIONS and not (status.get("metadata") or {}).get("summary_safe"):
        return "Sensitive summary redacted."
    return status.get("summary") or ""


def format_queue_for_cli(queue: dict[str, Any]) -> str:
    lines = ["Orchestrator Intake Queue"]
    for label in ["pending", "blocked"]:
        lines.append(label.upper())
        items = queue.get(label, [])
        if not items:
            lines.append("- None")
        for item in items:
            reason = f" | {item.get('blocked_reason')}" if item.get("blocked_reason") else ""
            lines.append(f"- {item.get('intake_id')} | {item.get('priority')} | {safe_summary(item)}{reason}")
    return "\n".join(lines)
