from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any
from uuid import uuid4

from estate.core.execution_dispatch import DispatchRequest, enqueue_dispatch_request
from estate.core.operational_events import utc_now_iso, validate_iso_timestamp
from estate.core.operational_status import record_operational_event
from estate.core.paths import ESTATE_ROOT
from estate.core.traffic_controller import RecommendedAction, redact_summary
from estate.core.worker_assignments import ALLOWED_CLASSIFICATIONS, ALLOWED_PRIORITIES
from estate.core.operations_manager import OperationsDecision
from estate.core.operations_control_runtime import OperationsControlRuntime

GRACE_ROOT = Path("runtime/operations/grace")
OBJECTIVES_DIR = GRACE_ROOT / "objectives"
ACTIONS_DIR = GRACE_ROOT / "actions"
ESCALATIONS_DIR = GRACE_ROOT / "escalations"
CLOSURES_DIR = GRACE_ROOT / "closures"
STATUS_DIR = GRACE_ROOT / "status"

ALLOWED_AUTHORITY = {"delegated", "requires_steward", "unauthorized"}
ALLOWED_STATES = {"proposed", "ready", "blocked", "awaiting_approval", "dispatch_requested", "escalated", "closed"}


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _require_str(data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} is required")
    return value


def _optional_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, str):
        return [value] if value.strip() else []
    raise ValueError("expected a list")


@dataclass
class GraceObjective:
    objective_id: str
    created_at: str
    requested_by: str
    title: str
    summary: str
    classification: str = "Estate Internal"
    priority: str = "normal"
    work_package_id: str | None = None
    authority: str = "delegated"
    dependencies: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    owner: str | None = None
    checkpoint: str | None = None
    evidence: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(cls, *, requested_by: str, title: str, summary: str, **kwargs: Any) -> "GraceObjective":
        return cls(objective_id=f"grace-obj-{uuid4().hex[:12]}", created_at=utc_now_iso(), requested_by=requested_by, title=title, summary=summary, **kwargs)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GraceObjective":
        obj = cls(objective_id=_require_str(data, "objective_id"), created_at=_require_str(data, "created_at"), requested_by=_require_str(data, "requested_by"), title=_require_str(data, "title"), summary=_require_str(data, "summary"), classification=data.get("classification") or "Estate Internal", priority=data.get("priority") or "normal", work_package_id=data.get("work_package_id"), authority=data.get("authority") or "delegated", dependencies=_optional_list(data.get("dependencies")), blockers=_optional_list(data.get("blockers")), owner=data.get("owner"), checkpoint=data.get("checkpoint"), evidence=_optional_list(data.get("evidence")), metadata=data.get("metadata") or {})
        obj.validate(); return obj

    def validate(self) -> None:
        validate_iso_timestamp(self.created_at, "created_at")
        if self.classification not in ALLOWED_CLASSIFICATIONS: raise ValueError(f"unknown classification '{self.classification}'")
        if self.priority not in ALLOWED_PRIORITIES: raise ValueError(f"unknown priority '{self.priority}'")
        if self.authority not in ALLOWED_AUTHORITY: raise ValueError(f"unknown authority '{self.authority}'")
        if not isinstance(self.metadata, dict): raise ValueError("metadata must be an object")

    def to_dict(self) -> dict[str, Any]:
        self.validate(); return asdict(self)


@dataclass
class GraceNextAction:
    action_id: str
    objective_id: str
    created_at: str
    state: str
    proposal: str
    owner: str
    checkpoint: str
    traffic_controller_request: dict[str, Any]
    classification: str = "Estate Internal"
    priority: str = "normal"
    dependencies: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    dispatch_handoff_request: dict[str, Any] | None = None
    escalation: dict[str, Any] | None = None
    evidence: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        validate_iso_timestamp(self.created_at, "created_at")
        if self.state not in ALLOWED_STATES: raise ValueError(f"unknown state '{self.state}'")
        if self.classification not in ALLOWED_CLASSIFICATIONS: raise ValueError(f"unknown classification '{self.classification}'")
        if self.priority not in ALLOWED_PRIORITIES: raise ValueError(f"unknown priority '{self.priority}'")
        if not self.traffic_controller_request: raise ValueError("traffic_controller_request is required")

    def to_dict(self) -> dict[str, Any]:
        self.validate(); return asdict(self)


class GraceOperationsRuntime:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root or ESTATE_ROOT

    def intake_objective(self, objective: GraceObjective) -> dict[str, str]:
        objective.validate()
        path = self.root / OBJECTIVES_DIR / f"{objective.created_at[:10]}_{objective.objective_id}.json"
        _write_json(path, objective.to_dict())
        self._write_status(objective=objective)
        return {"objective": str(path), "status": str(self.root / STATUS_DIR / "latest.json")}

    def propose_next_action(self, objective: GraceObjective) -> GraceNextAction:
        blocked = bool(objective.blockers) or objective.authority != "delegated"
        state = "blocked" if objective.blockers else ("awaiting_approval" if objective.authority != "delegated" else "ready")
        owner = objective.owner or "Operations"
        checkpoint = objective.checkpoint or "Steward/Chief Architect checkpoint before closure."
        tc_action = "hold" if blocked else "assign"
        traffic_request = RecommendedAction.create(action_type=tc_action, target_type="work_package", target_id=objective.work_package_id, priority=objective.priority, reason=objective.summary, safe_summary=objective.title, requires_steward_approval=objective.authority != "delegated", requires_boundary_review=objective.authority == "unauthorized", metadata={"requested_by": "Grace", "objective_id": objective.objective_id}).to_dict()
        dispatch = None if blocked else {"request_type": "dispatch_handoff", "work_package_id": objective.work_package_id, "title": objective.title, "requested_by": "Grace", "owner": owner, "checkpoint": checkpoint, "provider_execution_must_remain_behind_dispatch": True}
        escalation = None if not blocked else {"reason": "; ".join(objective.blockers) if objective.blockers else f"Authority is {objective.authority}.", "escalate_to": "Steward", "grace_may_not_override_traffic_controller": True}
        action = GraceNextAction(action_id=f"grace-act-{uuid4().hex[:12]}", objective_id=objective.objective_id, created_at=utc_now_iso(), state=state, proposal=objective.summary, owner=owner, checkpoint=checkpoint, traffic_controller_request=traffic_request, classification=objective.classification, priority=objective.priority, dependencies=list(objective.dependencies), blockers=list(objective.blockers), dispatch_handoff_request=dispatch, escalation=escalation, evidence=list(objective.evidence), metadata={"authority": objective.authority, "technical_design_owner": "Engineering", "workforce_assessment_owner": "Helen", "privacy_classification_owner": "Ingrid", "institutional_acceptance_owner": "Chief Architect and Steward"})
        return action

    def conduct_objective(self, objective: GraceObjective, *, request_dispatch: bool = False) -> tuple[GraceNextAction, dict[str, str]]:
        self.intake_objective(objective)
        action = self.propose_next_action(objective)
        paths: dict[str, str] = {}
        action_path = self.root / ACTIONS_DIR / f"{action.created_at[:10]}_{action.action_id}.json"
        _write_json(action_path, action.to_dict()); paths["action"] = str(action_path)
        decision = OperationsDecision.create(decided_by="Grace", decision_type="request_boundary_review" if action.state == "awaiting_approval" else ("hold" if action.state == "blocked" else "assign"), target_type="work_package", target_id=objective.work_package_id, priority=objective.priority, classification=objective.classification, reason=action.proposal, assignment_label=action.owner, requires_boundary_review=objective.authority == "unauthorized", requires_steward_attention=action.state in {"blocked", "awaiting_approval"}, summary_safe=objective.metadata.get("summary_safe") is True, metadata={"grace_action_id": action.action_id, "checkpoint": action.checkpoint})
        paths.update(OperationsControlRuntime(self.root).record_decision(decision))
        if action.escalation:
            esc_path = self.root / ESCALATIONS_DIR / f"{action.created_at[:10]}_{action.action_id}.json"
            _write_json(esc_path, action.escalation); paths["escalation"] = str(esc_path)
        elif request_dispatch and action.dispatch_handoff_request:
            dispatch_request = DispatchRequest(work_package_id=objective.work_package_id, title=objective.title, requested_by="Grace", assigned_worker=action.owner, classification=objective.classification, priority=objective.priority.title(), state="Queued", dependencies=objective.dependencies, provider_metadata={"grace_action_id": action.action_id, "checkpoint": action.checkpoint})
            item = enqueue_dispatch_request(dispatch_request, root=self.root)
            action.state = "dispatch_requested"
            action.dispatch_handoff_request["dispatch_id"] = item.dispatch_id
            _write_json(action_path, action.to_dict())
            paths["dispatch_queue"] = str(self.root / "runtime/execution_dispatch/queue.json")
        self._write_status(objective=objective, action=action, paths=paths)
        return action, paths

    def close_objective(self, objective_id: str, *, reviewed_by: str, result: str, accepted: bool = False) -> dict[str, str]:
        payload = {"closure_id": f"grace-close-{uuid4().hex[:12]}", "objective_id": objective_id, "created_at": utc_now_iso(), "reviewed_by": reviewed_by, "result": result, "accepted": accepted, "note": "Grace records reconciliation evidence only; institutional acceptance remains with authorized Chief Architect and Steward layers."}
        path = self.root / CLOSURES_DIR / f"{payload['created_at'][:10]}_{payload['closure_id']}.json"
        _write_json(path, payload)
        self._write_status(closure=payload)
        return {"closure": str(path), "status": str(self.root / STATUS_DIR / "latest.json")}

    def status(self) -> dict[str, Any]:
        path = self.root / STATUS_DIR / "latest.json"
        return _read_json(path) if path.exists() else {"available": False, "kind": "grace_operations_status", "message": "No Grace operational runtime status found."}

    def _write_status(self, **kwargs: Any) -> None:
        clean_kwargs = {key: (value.to_dict() if hasattr(value, "to_dict") else value) for key, value in kwargs.items()}
        payload = {"available": True, "kind": "grace_operations_status", "updated_at": utc_now_iso(), "role": "governed operational executive", "authority_boundaries": ["Recommendations, runtime state, and validation are evidence, not authority.", "Provider execution remains behind Dispatch and adapters.", "Grace cannot merge code, appoint personnel, override Traffic Controller, or declare institutional acceptance."], **clean_kwargs}
        _write_json(self.root / STATUS_DIR / "latest.json", payload)
        lines = ["# Grace Operations Status", "", f"Updated: {payload['updated_at']}", "Role: governed operational executive", "", "## Boundaries"] + [f"- {item}" for item in payload["authority_boundaries"]]
        (self.root / STATUS_DIR / "latest.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def format_grace_action(action: GraceNextAction, paths: dict[str, str] | None = None) -> str:
    lines = ["Grace next action", f"Action: {action.action_id}", f"State: {action.state}", f"Owner: {action.owner}", f"Checkpoint: {action.checkpoint}", f"Traffic Controller request: {action.traffic_controller_request['action_type']}"]
    if action.blockers: lines.append("Blockers: " + "; ".join(action.blockers))
    if paths:
        for label, path in paths.items(): lines.append(f"{label}: {path}")
    return "\n".join(lines)
