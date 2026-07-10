from __future__ import annotations

import copy
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Mapping

TERMINAL_STATES = {"completed", "failed", "blocked", "cancelled"}
ACTIVE_STATES = {"not_started", "awaiting_input", "awaiting_confirmation", "ready", "running"}


@dataclass(frozen=True)
class WorkflowStep:
    id: str
    title: str
    handler: str
    required_inputs: tuple[str, ...] = ()
    required_confirmations: tuple[str, ...] = ()
    preconditions: tuple[str, ...] = ()
    evidence_required: bool = True
    irreversible: bool = False


@dataclass(frozen=True)
class GuidedWorkflow:
    id: str
    title: str
    authority_gate: str
    steps: tuple[WorkflowStep, ...]


@dataclass
class GuidedActionSession:
    workflow: GuidedWorkflow
    session_id: str
    current_step_index: int = 0
    status: str = "not_started"
    inputs: dict[str, Any] = field(default_factory=dict)
    confirmations: set[str] = field(default_factory=set)
    satisfied_preconditions: set[str] = field(default_factory=set)
    evidence: list[dict[str, Any]] = field(default_factory=list)
    audit_log: list[dict[str, Any]] = field(default_factory=list)
    completed_steps: list[str] = field(default_factory=list)
    blocked_reason: str | None = None
    failure_reason: str | None = None
    cancellation_reason: str | None = None

    def to_snapshot(self) -> dict[str, Any]:
        return {
            "schema": "estate.guided_action_session.v1",
            "session_id": self.session_id,
            "workflow": workflow_to_dict(self.workflow),
            "current_step_index": self.current_step_index,
            "status": self.status,
            "inputs": copy.deepcopy(self.inputs),
            "confirmations": sorted(self.confirmations),
            "satisfied_preconditions": sorted(self.satisfied_preconditions),
            "evidence": copy.deepcopy(self.evidence),
            "audit_log": copy.deepcopy(self.audit_log),
            "completed_steps": list(self.completed_steps),
            "blocked_reason": self.blocked_reason,
            "failure_reason": self.failure_reason,
            "cancellation_reason": self.cancellation_reason,
            "staged_not_installed": True,
        }

    @classmethod
    def from_snapshot(cls, snapshot: Mapping[str, Any]) -> "GuidedActionSession":
        session = cls(
            workflow=workflow_from_dict(snapshot["workflow"]),
            session_id=str(snapshot["session_id"]),
            current_step_index=int(snapshot.get("current_step_index", 0)),
            status=str(snapshot.get("status", "not_started")),
            inputs=copy.deepcopy(dict(snapshot.get("inputs", {}))),
            confirmations=set(snapshot.get("confirmations", [])),
            satisfied_preconditions=set(snapshot.get("satisfied_preconditions", [])),
            evidence=copy.deepcopy(list(snapshot.get("evidence", []))),
            audit_log=copy.deepcopy(list(snapshot.get("audit_log", []))),
            completed_steps=list(snapshot.get("completed_steps", [])),
            blocked_reason=snapshot.get("blocked_reason"),
            failure_reason=snapshot.get("failure_reason"),
            cancellation_reason=snapshot.get("cancellation_reason"),
        )
        return session


Handler = Callable[[GuidedActionSession, WorkflowStep], Mapping[str, Any]]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def workflow_to_dict(workflow: GuidedWorkflow) -> dict[str, Any]:
    return {
        "id": workflow.id,
        "title": workflow.title,
        "authority_gate": workflow.authority_gate,
        "steps": [step.__dict__ | {"required_inputs": list(step.required_inputs), "required_confirmations": list(step.required_confirmations), "preconditions": list(step.preconditions)} for step in workflow.steps],
    }


def workflow_from_dict(data: Mapping[str, Any]) -> GuidedWorkflow:
    return GuidedWorkflow(
        id=str(data["id"]),
        title=str(data["title"]),
        authority_gate=str(data["authority_gate"]),
        steps=tuple(WorkflowStep(id=str(s["id"]), title=str(s["title"]), handler=str(s["handler"]), required_inputs=tuple(s.get("required_inputs", ())), required_confirmations=tuple(s.get("required_confirmations", ())), preconditions=tuple(s.get("preconditions", ())), evidence_required=bool(s.get("evidence_required", True)), irreversible=bool(s.get("irreversible", False))) for s in data.get("steps", ())),
    )


def create_validate_review_promote_workflow() -> GuidedWorkflow:
    return GuidedWorkflow(
        id="office.validate_review_promote.v1",
        title="Validate, Review, Promote",
        authority_gate="existing_office_authority_gate_required_for_each_step",
        steps=(
            WorkflowStep("validate", "Validate staged evidence", "validate", required_inputs=("artifact",), preconditions=("workspace_clean",)),
            WorkflowStep("review", "Review validation evidence", "review", required_confirmations=("reviewer_accepts_evidence",), preconditions=("validate.completed",)),
            WorkflowStep("promote", "Promote after explicit approval", "promote", required_confirmations=("steward_promote_approval",), preconditions=("review.completed",), irreversible=True),
        ),
    )


def start_session(workflow: GuidedWorkflow, session_id: str) -> GuidedActionSession:
    session = GuidedActionSession(workflow=workflow, session_id=session_id)
    _audit(session, "session_started", "Guided workflow session created; no authorization is implied.")
    return session


def provide_input(session: GuidedActionSession, name: str, value: Any) -> None:
    session.inputs[name] = value
    _audit(session, "input_provided", f"Input provided: {name}", input=name)


def confirm(session: GuidedActionSession, confirmation_id: str) -> None:
    session.confirmations.add(confirmation_id)
    _audit(session, "confirmation_recorded", f"Explicit confirmation recorded: {confirmation_id}", confirmation=confirmation_id)


def satisfy_precondition(session: GuidedActionSession, precondition_id: str, evidence_link: str | None = None) -> None:
    session.satisfied_preconditions.add(precondition_id)
    _audit(session, "precondition_satisfied", f"Precondition satisfied: {precondition_id}", precondition=precondition_id, evidence_link=evidence_link)


def current_step(session: GuidedActionSession) -> WorkflowStep | None:
    if session.current_step_index >= len(session.workflow.steps):
        return None
    return session.workflow.steps[session.current_step_index]


def evaluate_readiness(session: GuidedActionSession) -> dict[str, Any]:
    step = current_step(session)
    if step is None:
        return {"state": "completed", "missing_inputs": [], "missing_confirmations": [], "missing_preconditions": [], "step_id": None}
    missing_inputs = [name for name in step.required_inputs if name not in session.inputs]
    missing_confirmations = [name for name in step.required_confirmations if name not in session.confirmations]
    missing_preconditions = [name for name in step.preconditions if name not in session.satisfied_preconditions]
    state = "ready" if not (missing_inputs or missing_confirmations or missing_preconditions) else "awaiting_input"
    if missing_confirmations and not missing_inputs and not missing_preconditions:
        state = "awaiting_confirmation"
    return {"state": state, "step_id": step.id, "missing_inputs": missing_inputs, "missing_confirmations": missing_confirmations, "missing_preconditions": missing_preconditions, "irreversible": step.irreversible}


def advance(session: GuidedActionSession, handlers: Mapping[str, Handler]) -> dict[str, Any]:
    if session.status in TERMINAL_STATES:
        _audit(session, "advance_ignored", f"Cannot advance terminal session state: {session.status}")
        return {"state": session.status, "advanced": False}
    readiness = evaluate_readiness(session)
    if readiness["state"] != "ready":
        session.status = readiness["state"]
        _audit(session, "advance_blocked", "Step requirements are not satisfied.", readiness=readiness)
        return readiness | {"advanced": False}
    step = current_step(session)
    assert step is not None
    handler = handlers.get(step.handler)
    if handler is None:
        session.status = "blocked"
        session.blocked_reason = f"No handler registered for {step.handler}"
        _audit(session, "blocked", session.blocked_reason, step_id=step.id)
        return {"state": "blocked", "advanced": False, "reason": session.blocked_reason}
    session.status = "running"
    _audit(session, "step_started", f"Started step: {step.id}", step_id=step.id, authority_gate=session.workflow.authority_gate)
    try:
        result = dict(handler(session, step))
    except Exception as exc:  # handler failure is state, not hidden success
        session.status = "failed"
        session.failure_reason = f"{type(exc).__name__}: {exc}"
        _audit(session, "failed", session.failure_reason, step_id=step.id)
        return {"state": "failed", "advanced": False, "reason": session.failure_reason}
    if result.get("blocked"):
        session.status = "blocked"
        session.blocked_reason = str(result.get("reason", "handler reported blocked"))
        _audit(session, "blocked", session.blocked_reason, step_id=step.id)
        return {"state": "blocked", "advanced": False, "reason": session.blocked_reason}
    evidence_link = result.get("evidence_link")
    if step.evidence_required and not evidence_link:
        session.status = "failed"
        session.failure_reason = "Step completed without required evidence link."
        _audit(session, "failed", session.failure_reason, step_id=step.id)
        return {"state": "failed", "advanced": False, "reason": session.failure_reason}
    session.evidence.append({"step_id": step.id, "handler": step.handler, "evidence_link": evidence_link, "summary": result.get("summary", "completed"), "created_at": utc_now()})
    session.completed_steps.append(step.id)
    session.satisfied_preconditions.add(f"{step.id}.completed")
    session.current_step_index += 1
    session.status = "completed" if current_step(session) is None else "not_started"
    _audit(session, "step_completed", f"Completed step: {step.id}", step_id=step.id, evidence_link=evidence_link)
    return {"state": session.status, "advanced": True, "completed_step": step.id, "evidence_link": evidence_link}


def cancel(session: GuidedActionSession, reason: str) -> dict[str, Any]:
    step = current_step(session)
    if session.status in TERMINAL_STATES:
        _audit(session, "cancel_ignored", f"Cannot cancel terminal session state: {session.status}")
        return {"state": session.status, "cancelled": False}
    if step and step.irreversible and evaluate_readiness(session)["state"] == "ready":
        session.status = "blocked"
        session.blocked_reason = "Cancellation blocked because the irreversible step is ready; require explicit Office disposition."
        _audit(session, "cancellation_blocked", session.blocked_reason, step_id=step.id)
        return {"state": "blocked", "cancelled": False, "reason": session.blocked_reason}
    session.status = "cancelled"
    session.cancellation_reason = reason
    _audit(session, "cancelled", reason, step_id=None if step is None else step.id)
    return {"state": "cancelled", "cancelled": True}


def browser_contract(session: GuidedActionSession) -> dict[str, Any]:
    return {"kind": "estate.guided_action.browser_contract.v1", "staged_not_installed": True, "session": session.to_snapshot(), "current_step": None if current_step(session) is None else current_step(session).__dict__, "readiness": evaluate_readiness(session), "allowed_actions": ["provide_input", "confirm", "satisfy_precondition", "advance", "cancel"], "authority": {"no_hidden_authorization": True, "automatic_approval": False, "authority_gate": session.workflow.authority_gate}}


def _audit(session: GuidedActionSession, event: str, message: str, **extra: Any) -> None:
    session.audit_log.append({"at": utc_now(), "event": event, "message": message, **{k: v for k, v in extra.items() if v is not None}})
