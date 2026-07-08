from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from estate.core.operational_events import utc_now_iso, validate_iso_timestamp

ALLOWED_ORCHESTRATOR_MODES = {"dry_run", "single_cycle"}
ALLOWED_ORCHESTRATOR_STATES = {"idle", "running", "completed", "completed_with_warnings", "failed"}


@dataclass
class OrchestratorRuntimeState:
    cycle_id: str
    started_at: str
    mode: str
    state: str
    orchestrator_id: str = "estate.orchestrator.local"
    finished_at: str | None = None
    items_evaluated: int = 0
    dispatches_created: int = 0
    items_blocked: int = 0
    items_deferred: int = 0
    events_emitted: int = 0
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(cls, *, cycle_id: str, mode: str) -> "OrchestratorRuntimeState":
        rec = cls(cycle_id=cycle_id, started_at=utc_now_iso(), mode=mode, state="running")
        rec.validate(); return rec

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "OrchestratorRuntimeState":
        rec = cls(**{**data, "orchestrator_id": data.get("orchestrator_id") or "estate.orchestrator.local", "errors": data.get("errors") or [], "warnings": data.get("warnings") or [], "metadata": data.get("metadata") or {}})
        rec.validate(); return rec

    def finish(self) -> None:
        self.finished_at = utc_now_iso()
        self.state = "failed" if self.errors else "completed_with_warnings" if self.warnings else "completed"

    def validate(self) -> None:
        if not self.cycle_id: raise ValueError("cycle_id is required")
        validate_iso_timestamp(self.started_at, "started_at")
        if self.finished_at: validate_iso_timestamp(self.finished_at, "finished_at")
        if self.mode not in ALLOWED_ORCHESTRATOR_MODES: raise ValueError(f"unknown mode '{self.mode}'")
        if self.state not in ALLOWED_ORCHESTRATOR_STATES: raise ValueError(f"unknown state '{self.state}'")
        for key in ["items_evaluated", "dispatches_created", "items_blocked", "items_deferred", "events_emitted"]:
            if getattr(self, key) < 0: raise ValueError(f"{key} must be non-negative")
        if not isinstance(self.metadata, dict): raise ValueError("metadata must be an object")

    def to_dict(self) -> dict[str, Any]:
        self.validate(); return asdict(self)
