from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any
from uuid import uuid4

from estate.core.operational_events import OperationalEvent, utc_now_iso, validate_iso_timestamp
from estate.core.operational_status import record_operational_event
from estate.core.orchestrator_intake import ALLOWED_CLASSIFICATIONS, OrchestratorIntakeStatus
from estate.core.orchestrator_intake_runtime import RUNTIME_RELATIVE_ROOT, SENSITIVE_CLASSIFICATIONS, OrchestratorIntakeRuntime, safe_summary
from estate.core.paths import ESTATE_ROOT

ALLOWED_DECISIONS = {"approve", "reject", "defer", "request_boundary_review", "mark_needs_revision"}
ALLOWED_NEXT_STATES = {"approved", "rejected", "deferred", "blocked", "needs_revision"}
DECISION_NEXT_STATE = {
    "approve": "approved",
    "reject": "rejected",
    "defer": "deferred",
    "request_boundary_review": "blocked",
    "mark_needs_revision": "needs_revision",
}
DECISION_EVENT = {
    "approve": ("Checkpoint Reached", "Completed"),
    "reject": ("Result Returned", "Completed"),
    "defer": ("Checkpoint Reached", "Deferred"),
    "request_boundary_review": ("Boundary Review Required", "Blocked"),
    "mark_needs_revision": ("Waiting for Approval", "Awaiting Approval"),
}


@dataclass
class OrchestratorIntakeDecision:
    decision_id: str
    intake_id: str
    decision: str
    decided_by: str
    decided_at: str
    classification: str
    next_state: str
    reason: str | None = None
    summary_safe: bool = False
    requires_boundary_review: bool = False
    requires_revision: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(cls, *, intake_id: str, decision: str, decided_by: str, classification: str, reason: str | None = None, metadata: dict[str, Any] | None = None) -> "OrchestratorIntakeDecision":
        if decision not in ALLOWED_DECISIONS:
            raise ValueError(f"unknown decision '{decision}'")
        return cls(
            decision_id=f"oid-{uuid4().hex}",
            intake_id=intake_id,
            decision=decision,
            decided_by=decided_by,
            decided_at=utc_now_iso(),
            classification=classification,
            next_state=DECISION_NEXT_STATE[decision],
            reason=reason,
            summary_safe=bool((metadata or {}).get("summary_safe", False)),
            requires_boundary_review=decision == "request_boundary_review",
            requires_revision=decision == "mark_needs_revision",
            metadata=metadata or {},
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "OrchestratorIntakeDecision":
        if not isinstance(data, dict):
            raise ValueError("decision artifact must be a JSON object")
        artifact = cls(
            decision_id=_require_str(data, "decision_id"),
            intake_id=_require_str(data, "intake_id"),
            decision=_require_str(data, "decision"),
            decided_by=_require_str(data, "decided_by"),
            decided_at=_require_str(data, "decided_at"),
            classification=_require_str(data, "classification"),
            next_state=_require_str(data, "next_state"),
            reason=data.get("reason"),
            summary_safe=bool(data.get("summary_safe", False)),
            requires_boundary_review=bool(data.get("requires_boundary_review", False)),
            requires_revision=bool(data.get("requires_revision", False)),
            metadata=data.get("metadata") or {},
        )
        artifact.validate()
        return artifact

    def validate(self) -> None:
        for key in ["decision_id", "intake_id", "decision", "decided_by", "decided_at", "classification", "next_state"]:
            if not isinstance(getattr(self, key), str) or not getattr(self, key).strip():
                raise ValueError(f"{key} is required")
        if self.decision not in ALLOWED_DECISIONS:
            raise ValueError(f"unknown decision '{self.decision}'")
        if self.next_state not in ALLOWED_NEXT_STATES:
            raise ValueError(f"unknown next_state '{self.next_state}'")
        if self.classification not in ALLOWED_CLASSIFICATIONS:
            raise ValueError(f"unknown classification '{self.classification}'")
        validate_iso_timestamp(self.decided_at, "decided_at")
        if self.reason is not None and not isinstance(self.reason, str):
            raise ValueError("reason must be a string")
        if not isinstance(self.summary_safe, bool) or not isinstance(self.requires_boundary_review, bool) or not isinstance(self.requires_revision, bool):
            raise ValueError("decision booleans must be boolean")
        if not isinstance(self.metadata, dict):
            raise ValueError("metadata must be an object")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)


def _require_str(data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} is required")
    return value


class OrchestratorIntakeDecisionRuntime:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root or ESTATE_ROOT
        self.intake = OrchestratorIntakeRuntime(self.root)
        self.decisions_dir = self.root / RUNTIME_RELATIVE_ROOT / "decisions"

    def decide(self, *, intake_id: str, decision: str, decided_by: str, reason: str | None = None, metadata: dict[str, Any] | None = None) -> tuple[OrchestratorIntakeDecision, dict[str, str]]:
        queue = self.intake.queue_state()
        status_data = next((i for i in [*(queue.get("pending") or []), *(queue.get("blocked") or [])] if i.get("intake_id") == intake_id), None)
        if not status_data:
            raise ValueError(f"intake_id '{intake_id}' is not pending or blocked")
        artifact = OrchestratorIntakeDecision.create(intake_id=intake_id, decision=decision, decided_by=decided_by, classification=status_data.get("classification") or "Estate Internal", reason=reason, metadata=metadata)
        if decision == "approve" and status_data.get("boundary_review_required") and not ((status_data.get("metadata") or {}).get("boundary_review_completed") or (metadata or {}).get("boundary_review_completed")):
            artifact.next_state = "blocked"
            artifact.requires_boundary_review = True
            artifact.metadata = {**artifact.metadata, "approval_blocked_reason": "Boundary review must be completed before approval can proceed."}
        self.decisions_dir.mkdir(parents=True, exist_ok=True)
        decision_path = self.decisions_dir / f"{artifact.decision_id}.json"
        decision_path.write_text(json.dumps(artifact.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        updated = dict(status_data)
        updated.update({"state": artifact.next_state, "updated_at": artifact.decided_at, "latest_decision": artifact.to_dict(), "artifact_paths": [*(status_data.get("artifact_paths") or []), str(decision_path)]})
        self._write_statuses(updated)
        event = self._event_for(artifact, updated, str(decision_path))
        try:
            event_paths = record_operational_event(event, root=self.root)
        except Exception as exc:
            event_paths = {}
            artifact.metadata = {**artifact.metadata, "operational_event_warning": str(exc)}
            decision_path.write_text(json.dumps(artifact.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        paths = {"decision": str(decision_path), "latest": str(self.root / RUNTIME_RELATIVE_ROOT / "status" / "latest.json"), "queue": str(self.root / RUNTIME_RELATIVE_ROOT / "status" / "queue.json")}
        paths.update({f"operations_{k}": str(v) for k, v in event_paths.items()})
        return artifact, paths

    def _write_statuses(self, updated: dict[str, Any]) -> None:
        queue_path = self.root / RUNTIME_RELATIVE_ROOT / "status" / "queue.json"
        queue = self.intake.queue_state()
        for key in ["pending", "blocked"]:
            queue[key] = [i for i in queue.get(key, []) if i.get("intake_id") != updated["intake_id"]]
        if updated["state"] in {"pending", "blocked", "deferred", "needs_revision"}:
            target = "blocked" if updated["state"] in {"blocked", "needs_revision"} else "pending"
            queue.setdefault(target, []).append(updated)
        queue_path.write_text(json.dumps(queue, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        latest_path = self.root / RUNTIME_RELATIVE_ROOT / "status" / "latest.json"
        latest_path.write_text(json.dumps(updated, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def _event_for(self, artifact: OrchestratorIntakeDecision, status: dict[str, Any], decision_path: str) -> OperationalEvent:
        event_type, state = DECISION_EVENT[artifact.decision]
        message = f"Orchestrator intake decision recorded: {artifact.decision} -> {artifact.next_state}."
        return OperationalEvent.create(event_type=event_type, state=state, classification=artifact.classification, message=message, work_package_id=status.get("work_package_id"), request_id=artifact.intake_id, requires_attention=artifact.next_state in {"blocked", "needs_revision"}, artifact_paths=[decision_path], metadata={"decision_id": artifact.decision_id, "decision": artifact.decision, "next_state": artifact.next_state, "summary_safe": artifact.summary_safe})


def load_office_intake_decision_surface(root: Path | None = None) -> dict[str, Any]:
    runtime = OrchestratorIntakeRuntime(root)
    queue = runtime.queue_state()
    items = []
    for item in [*(queue.get("pending") or []), *(queue.get("blocked") or [])]:
        classification = item.get("classification") or "Estate Internal"
        metadata = item.get("metadata") if isinstance(item.get("metadata"), dict) else {}
        latest_decision = item.get("latest_decision") if isinstance(item.get("latest_decision"), dict) else None
        available = ["reject", "defer", "mark_needs_revision"]
        if item.get("boundary_review_required") and not metadata.get("boundary_review_completed"):
            available.insert(0, "request_boundary_review")
        else:
            available.insert(0, "approve")
        items.append({**item, "safe_summary": safe_summary(item), "summary_redacted": classification in SENSITIVE_CLASSIFICATIONS and not metadata.get("summary_safe") is True, "available_decisions": available, "latest_decision": latest_decision})
    return {"available": True, "kind": "office_intake_decision_surface", "path": "runtime/orchestrator/intake/status/queue.json", "items": items, "summary": {"item_count": len(items)}, "classification_behavior": "Sensitive summaries are redacted unless metadata.summary_safe is true."}
