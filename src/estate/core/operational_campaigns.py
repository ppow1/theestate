"""Governed operational campaign model.

A campaign is an approved, bounded multi-step initiative.  This module only
models authority, phase eligibility, state, and audit history; execution remains
with Traffic Controller decisions, dispatch, provider recommendation, scheduler,
and validation seams.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

CAMPAIGN_STATES = {"Draft", "Ready", "Running", "Paused", "Blocked", "Cancelled", "Completed"}
PHASE_STATES = {"Pending", "Ready", "Running", "Blocked", "Completed", "Cancelled"}
EVENT_TYPES = {
    "campaign_started", "campaign_paused", "campaign_resumed", "campaign_advanced",
    "campaign_blocked", "campaign_cancelled", "campaign_completed", "campaign_escalated",
    "phase_dispatched", "phase_completed",
}
TERMINAL_CAMPAIGN_STATES = {"Cancelled", "Completed"}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in value]
    if isinstance(value, tuple):
        return [str(v) for v in value]
    return [str(value)]


@dataclass
class CampaignAuthority:
    approved_by: str
    approved_at: str
    allowed_directors: list[str] = field(default_factory=lambda: ["Operations Manager"])
    allowed_actions: list[str] = field(default_factory=lambda: ["start", "pause", "resume", "advance", "block", "cancel", "complete"])
    allowed_phase_ids: list[str] = field(default_factory=list)
    max_routine_advances_per_cycle: int = 1
    requires_steward_for_acceptance: bool = True
    notes: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CampaignAuthority":
        return cls(
            approved_by=str(data.get("approved_by") or "Steward"),
            approved_at=str(data.get("approved_at") or utc_now_iso()),
            allowed_directors=_list(data.get("allowed_directors") or ["Operations Manager"]),
            allowed_actions=_list(data.get("allowed_actions") or ["start", "pause", "resume", "advance", "block", "cancel", "complete"]),
            allowed_phase_ids=_list(data.get("allowed_phase_ids")),
            max_routine_advances_per_cycle=int(data.get("max_routine_advances_per_cycle") or 1),
            requires_steward_for_acceptance=bool(data.get("requires_steward_for_acceptance", True)),
            notes=data.get("notes"),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CampaignPhase:
    phase_id: str
    title: str
    goals: list[str]
    dependencies: list[str] = field(default_factory=list)
    entry_criteria: list[str] = field(default_factory=list)
    exit_criteria: list[str] = field(default_factory=list)
    evidence_requirements: list[str] = field(default_factory=list)
    delegated_authority: list[str] = field(default_factory=list)
    escalation_conditions: list[str] = field(default_factory=list)
    work_package_id: str | None = None
    provider: str | None = None
    validation_commands: list[str] = field(default_factory=list)
    routine: bool = True
    state: str = "Pending"
    dispatch_id: str | None = None
    blockers: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CampaignPhase":
        return cls(
            phase_id=str(data["phase_id"]), title=str(data.get("title") or data["phase_id"]), goals=_list(data.get("goals")),
            dependencies=_list(data.get("dependencies")), entry_criteria=_list(data.get("entry_criteria")),
            exit_criteria=_list(data.get("exit_criteria")), evidence_requirements=_list(data.get("evidence_requirements")),
            delegated_authority=_list(data.get("delegated_authority")), escalation_conditions=_list(data.get("escalation_conditions")),
            work_package_id=data.get("work_package_id"), provider=data.get("provider"), validation_commands=_list(data.get("validation_commands")),
            routine=bool(data.get("routine", True)), state=str(data.get("state") or "Pending"), dispatch_id=data.get("dispatch_id"),
            blockers=_list(data.get("blockers")), evidence=_list(data.get("evidence")),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class OperationalCampaign:
    campaign_id: str
    title: str
    goals: list[str]
    authority: CampaignAuthority
    phases: list[CampaignPhase]
    state: str = "Ready"
    holds: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    tempo: str = "routine"
    created_at: str = field(default_factory=utc_now_iso)
    updated_at: str = field(default_factory=utc_now_iso)
    completed_at: str | None = None
    institutional_acceptance: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(cls, *, title: str, goals: list[str], authority: CampaignAuthority, phases: list[CampaignPhase], campaign_id: str | None = None, **kwargs: Any) -> "OperationalCampaign":
        return cls(campaign_id=campaign_id or f"camp-{uuid4().hex[:12]}", title=title, goals=goals, authority=authority, phases=phases, **kwargs)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "OperationalCampaign":
        return cls(
            campaign_id=str(data["campaign_id"]), title=str(data.get("title") or data["campaign_id"]), goals=_list(data.get("goals")),
            authority=CampaignAuthority.from_dict(data.get("authority") or {}), phases=[CampaignPhase.from_dict(p) for p in data.get("phases", [])],
            state=str(data.get("state") or "Ready"), holds=_list(data.get("holds")), blockers=_list(data.get("blockers")), tempo=str(data.get("tempo") or "routine"),
            created_at=str(data.get("created_at") or utc_now_iso()), updated_at=str(data.get("updated_at") or utc_now_iso()), completed_at=data.get("completed_at"),
            institutional_acceptance=bool(data.get("institutional_acceptance", False)), metadata=dict(data.get("metadata") or {}),
        )

    def validate(self) -> None:
        if self.state not in CAMPAIGN_STATES: raise ValueError(f"unknown campaign state {self.state}")
        ids = [p.phase_id for p in self.phases]
        if len(ids) != len(set(ids)): raise ValueError("phase_id values must be unique")
        for phase in self.phases:
            if phase.state not in PHASE_STATES: raise ValueError(f"unknown phase state {phase.state}")
            missing = [dep for dep in phase.dependencies if dep not in ids]
            if missing: raise ValueError(f"phase {phase.phase_id} has unknown dependencies: {missing}")
        if self.authority.allowed_phase_ids:
            unknown = [pid for pid in self.authority.allowed_phase_ids if pid not in ids]
            if unknown: raise ValueError(f"authority references unknown phases: {unknown}")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        data = asdict(self)
        data["authority"] = self.authority.to_dict()
        data["phases"] = [p.to_dict() for p in self.phases]
        return data

    def phase(self, phase_id: str) -> CampaignPhase:
        for phase in self.phases:
            if phase.phase_id == phase_id: return phase
        raise KeyError(f"unknown campaign phase {phase_id}")


def campaign_event(campaign: OperationalCampaign, event_type: str, summary: str, **metadata: Any) -> dict[str, Any]:
    if event_type not in EVENT_TYPES: raise ValueError(f"unsupported campaign event {event_type}")
    return {"event_id": f"{campaign.campaign_id}-{uuid4().hex[:10]}", "event_type": event_type, "campaign_id": campaign.campaign_id, "campaign_state": campaign.state, "summary": summary, "created_at": utc_now_iso(), "metadata": metadata}
