"""Governed cross-department operational coordination model.

The model records coordination facts for approved operational work without
moving authority away from departments, the Traffic Controller, Steward, or
execution providers.  Operations can sequence routine work inside delegated
authority; unresolved contention and authority conflicts are surfaced as
escalations.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

REQUEST_STATES = {"Draft", "Requested", "Acknowledged", "Ready", "Blocked", "In Progress", "Completed", "Escalated", "Cancelled"}
ACK_STATES = {"Pending", "Acknowledged", "Rejected"}
BLOCKER_STATES = {"Open", "Resolved", "Escalated"}
HANDOFF_STATES = {"Pending", "Ready", "Delivered", "Accepted", "Blocked"}
DEPENDENCY_STATES = {"Waiting", "Released", "Blocked"}
EVENT_TYPES = {
    "coordination_created", "request_added", "request_acknowledged", "request_blocked",
    "blocker_resolved", "handoff_delivered", "handoff_accepted", "dependency_released",
    "work_sequenced", "request_completed", "coordination_escalated",
}
ROUTINE_SEQUENCE_ACTIONS = {"sequence", "release_dependency", "resolve_blocker", "deliver_handoff", "accept_handoff"}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return [str(v) for v in value]
    return [str(value)]


@dataclass
class DepartmentAuthority:
    """Delegated authority envelope for an operational coordination."""

    approved_by: str
    approved_at: str
    operations_manager: str = "Operations Manager"
    allowed_departments: list[str] = field(default_factory=list)
    allowed_actions: list[str] = field(default_factory=lambda: sorted(ROUTINE_SEQUENCE_ACTIONS))
    requires_steward_for_acceptance: bool = True
    notes: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DepartmentAuthority":
        return cls(
            approved_by=str(data.get("approved_by") or "Steward"),
            approved_at=str(data.get("approved_at") or utc_now_iso()),
            operations_manager=str(data.get("operations_manager") or "Operations Manager"),
            allowed_departments=_list(data.get("allowed_departments")),
            allowed_actions=_list(data.get("allowed_actions") or sorted(ROUTINE_SEQUENCE_ACTIONS)),
            requires_steward_for_acceptance=bool(data.get("requires_steward_for_acceptance", True)),
            notes=data.get("notes"),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ServiceLevelExpectation:
    response_due: str | None = None
    commitment_due: str | None = None
    completion_due: str | None = None
    priority: str = "Normal"
    escalation_after: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "ServiceLevelExpectation":
        data = data or {}
        return cls(data.get("response_due"), data.get("commitment_due"), data.get("completion_due"), str(data.get("priority") or "Normal"), data.get("escalation_after"))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DepartmentDependency:
    dependency_id: str
    upstream_request_id: str
    description: str
    state: str = "Waiting"
    released_at: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DepartmentDependency":
        return cls(str(data["dependency_id"]), str(data["upstream_request_id"]), str(data.get("description") or data["dependency_id"]), str(data.get("state") or "Waiting"), data.get("released_at"))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DepartmentHandoff:
    handoff_id: str
    from_department: str
    to_department: str
    description: str
    state: str = "Pending"
    evidence: list[str] = field(default_factory=list)
    delivered_at: str | None = None
    accepted_at: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DepartmentHandoff":
        return cls(str(data["handoff_id"]), str(data["from_department"]), str(data["to_department"]), str(data.get("description") or data["handoff_id"]), str(data.get("state") or "Pending"), _list(data.get("evidence")), data.get("delivered_at"), data.get("accepted_at"))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DepartmentBlocker:
    blocker_id: str
    description: str
    owner_department: str
    state: str = "Open"
    escalation_required: bool = False
    resolved_at: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DepartmentBlocker":
        return cls(str(data["blocker_id"]), str(data.get("description") or data["blocker_id"]), str(data["owner_department"]), str(data.get("state") or "Open"), bool(data.get("escalation_required", False)), data.get("resolved_at"))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DepartmentRequest:
    request_id: str
    department: str
    title: str
    requested_by: str
    commitment: str
    execution_provider: str | None = None
    state: str = "Requested"
    dependencies: list[DepartmentDependency] = field(default_factory=list)
    handoffs: list[DepartmentHandoff] = field(default_factory=list)
    blockers: list[DepartmentBlocker] = field(default_factory=list)
    service_level: ServiceLevelExpectation = field(default_factory=ServiceLevelExpectation)
    acknowledgement_state: str = "Pending"
    acknowledged_by: str | None = None
    acknowledged_at: str | None = None
    sequence: int | None = None
    evidence: list[str] = field(default_factory=list)

    @classmethod
    def create(cls, *, department: str, title: str, requested_by: str, commitment: str, request_id: str | None = None, **kwargs: Any) -> "DepartmentRequest":
        return cls(request_id or f"dreq-{uuid4().hex[:10]}", department, title, requested_by, commitment, **kwargs)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DepartmentRequest":
        return cls(
            request_id=str(data["request_id"]), department=str(data["department"]), title=str(data.get("title") or data["request_id"]), requested_by=str(data.get("requested_by") or "Operations"), commitment=str(data.get("commitment") or "Coordinate approved work"), execution_provider=data.get("execution_provider"), state=str(data.get("state") or "Requested"), dependencies=[DepartmentDependency.from_dict(x) for x in data.get("dependencies", [])], handoffs=[DepartmentHandoff.from_dict(x) for x in data.get("handoffs", [])], blockers=[DepartmentBlocker.from_dict(x) for x in data.get("blockers", [])], service_level=ServiceLevelExpectation.from_dict(data.get("service_level")), acknowledgement_state=str(data.get("acknowledgement_state") or "Pending"), acknowledged_by=data.get("acknowledged_by"), acknowledged_at=data.get("acknowledged_at"), sequence=data.get("sequence"), evidence=_list(data.get("evidence")),
        )

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        data = asdict(self)
        data["dependencies"] = [d.to_dict() for d in self.dependencies]
        data["handoffs"] = [h.to_dict() for h in self.handoffs]
        data["blockers"] = [b.to_dict() for b in self.blockers]
        data["service_level"] = self.service_level.to_dict()
        return data

    def validate(self) -> None:
        if self.state not in REQUEST_STATES: raise ValueError(f"unknown request state {self.state}")
        if self.acknowledgement_state not in ACK_STATES: raise ValueError(f"unknown acknowledgement state {self.acknowledgement_state}")
        for dep in self.dependencies:
            if dep.state not in DEPENDENCY_STATES: raise ValueError(f"unknown dependency state {dep.state}")
        for handoff in self.handoffs:
            if handoff.state not in HANDOFF_STATES: raise ValueError(f"unknown handoff state {handoff.state}")
        for blocker in self.blockers:
            if blocker.state not in BLOCKER_STATES: raise ValueError(f"unknown blocker state {blocker.state}")

    @property
    def ready(self) -> bool:
        return self.acknowledgement_state == "Acknowledged" and not [d for d in self.dependencies if d.state != "Released"] and not [b for b in self.blockers if b.state == "Open"]


@dataclass
class DepartmentCoordination:
    coordination_id: str
    campaign_id: str
    title: str
    authority: DepartmentAuthority
    requests: list[DepartmentRequest]
    state: str = "Open"
    created_at: str = field(default_factory=utc_now_iso)
    updated_at: str = field(default_factory=utc_now_iso)
    escalations: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(cls, *, campaign_id: str, title: str, authority: DepartmentAuthority, requests: list[DepartmentRequest], coordination_id: str | None = None, **kwargs: Any) -> "DepartmentCoordination":
        return cls(coordination_id or f"coord-{uuid4().hex[:12]}", campaign_id, title, authority, requests, **kwargs)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DepartmentCoordination":
        return cls(str(data["coordination_id"]), str(data["campaign_id"]), str(data.get("title") or data["coordination_id"]), DepartmentAuthority.from_dict(data.get("authority") or {}), [DepartmentRequest.from_dict(x) for x in data.get("requests", [])], str(data.get("state") or "Open"), str(data.get("created_at") or utc_now_iso()), str(data.get("updated_at") or utc_now_iso()), list(data.get("escalations") or []), dict(data.get("metadata") or {}))

    def validate(self) -> None:
        ids = [r.request_id for r in self.requests]
        if len(ids) != len(set(ids)): raise ValueError("request_id values must be unique")
        departments = {r.department for r in self.requests}
        if self.authority.allowed_departments:
            outside = sorted(departments.difference(self.authority.allowed_departments))
            if outside: raise PermissionError(f"departments outside delegated authority: {outside}")
        for request in self.requests:
            request.validate()
            for dep in request.dependencies:
                if dep.upstream_request_id not in ids: raise ValueError(f"request {request.request_id} depends on unknown request {dep.upstream_request_id}")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return {"coordination_id": self.coordination_id, "campaign_id": self.campaign_id, "title": self.title, "authority": self.authority.to_dict(), "requests": [r.to_dict() for r in self.requests], "state": self.state, "created_at": self.created_at, "updated_at": self.updated_at, "escalations": self.escalations, "metadata": self.metadata}

    def request(self, request_id: str) -> DepartmentRequest:
        for request in self.requests:
            if request.request_id == request_id: return request
        raise KeyError(f"unknown department request {request_id}")


def coordination_event(coordination: DepartmentCoordination, event_type: str, summary: str, **metadata: Any) -> dict[str, Any]:
    if event_type not in EVENT_TYPES: raise ValueError(f"unsupported coordination event {event_type}")
    return {"event_id": f"{coordination.coordination_id}-{uuid4().hex[:10]}", "event_type": event_type, "coordination_id": coordination.coordination_id, "campaign_id": coordination.campaign_id, "state": coordination.state, "summary": summary, "created_at": utc_now_iso(), "metadata": metadata}
