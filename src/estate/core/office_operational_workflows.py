from __future__ import annotations

import copy
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Mapping

TERMINAL_STATES = {"completed", "failed", "blocked", "cancelled"}


@dataclass(frozen=True)
class OperationalStep:
    id: str
    title: str
    guidance: str
    handler: str
    required_inputs: tuple[str, ...] = ()
    required_confirmations: tuple[str, ...] = ()
    preconditions: tuple[str, ...] = ()
    evidence_required: bool = True
    irreversible: bool = False
    rollback_guidance: str | None = None


@dataclass(frozen=True)
class OperationalWorkflow:
    id: str
    title: str
    family: str
    authority_gate: str
    canonical_handlers: tuple[str, ...]
    steps: tuple[OperationalStep, ...]


@dataclass
class OperationalWorkflowSession:
    workflow: OperationalWorkflow
    session_id: str
    current_step_index: int = 0
    status: str = "not_started"
    inputs: dict[str, Any] = field(default_factory=dict)
    confirmations: set[str] = field(default_factory=set)
    satisfied_preconditions: set[str] = field(default_factory=set)
    evidence: list[dict[str, Any]] = field(default_factory=list)
    generated_artifacts: list[dict[str, Any]] = field(default_factory=list)
    audit_log: list[dict[str, Any]] = field(default_factory=list)
    completed_steps: list[str] = field(default_factory=list)
    blocked_reason: str | None = None
    failure_reason: str | None = None
    cancellation_reason: str | None = None

    def to_snapshot(self) -> dict[str, Any]:
        return {
            "schema": "estate.operational_workflow_session.v1",
            "installed_by_wp_0531": True,
            "session_id": self.session_id,
            "workflow": workflow_to_dict(self.workflow),
            "current_step_index": self.current_step_index,
            "status": self.status,
            "inputs": copy.deepcopy(self.inputs),
            "confirmations": sorted(self.confirmations),
            "satisfied_preconditions": sorted(self.satisfied_preconditions),
            "evidence": copy.deepcopy(self.evidence),
            "generated_artifacts": copy.deepcopy(self.generated_artifacts),
            "audit_log": copy.deepcopy(self.audit_log),
            "completed_steps": list(self.completed_steps),
            "blocked_reason": self.blocked_reason,
            "failure_reason": self.failure_reason,
            "cancellation_reason": self.cancellation_reason,
        }

    @classmethod
    def from_snapshot(cls, snapshot: Mapping[str, Any]) -> "OperationalWorkflowSession":
        return cls(
            workflow=workflow_from_dict(snapshot["workflow"]),
            session_id=str(snapshot["session_id"]),
            current_step_index=int(snapshot.get("current_step_index", 0)),
            status=str(snapshot.get("status", "not_started")),
            inputs=copy.deepcopy(dict(snapshot.get("inputs", {}))),
            confirmations=set(snapshot.get("confirmations", [])),
            satisfied_preconditions=set(snapshot.get("satisfied_preconditions", [])),
            evidence=copy.deepcopy(list(snapshot.get("evidence", []))),
            generated_artifacts=copy.deepcopy(list(snapshot.get("generated_artifacts", []))),
            audit_log=copy.deepcopy(list(snapshot.get("audit_log", []))),
            completed_steps=list(snapshot.get("completed_steps", [])),
            blocked_reason=snapshot.get("blocked_reason"),
            failure_reason=snapshot.get("failure_reason"),
            cancellation_reason=snapshot.get("cancellation_reason"),
        )


Handler = Callable[[OperationalWorkflowSession, OperationalStep], Mapping[str, Any]]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def workflow_to_dict(workflow: OperationalWorkflow) -> dict[str, Any]:
    return {
        "id": workflow.id,
        "title": workflow.title,
        "family": workflow.family,
        "authority_gate": workflow.authority_gate,
        "canonical_handlers": list(workflow.canonical_handlers),
        "steps": [
            {
                "id": s.id,
                "title": s.title,
                "guidance": s.guidance,
                "handler": s.handler,
                "required_inputs": list(s.required_inputs),
                "required_confirmations": list(s.required_confirmations),
                "preconditions": list(s.preconditions),
                "evidence_required": s.evidence_required,
                "irreversible": s.irreversible,
                "rollback_guidance": s.rollback_guidance,
            }
            for s in workflow.steps
        ],
    }


def workflow_from_dict(data: Mapping[str, Any]) -> OperationalWorkflow:
    return OperationalWorkflow(
        id=str(data["id"]),
        title=str(data["title"]),
        family=str(data["family"]),
        authority_gate=str(data["authority_gate"]),
        canonical_handlers=tuple(data.get("canonical_handlers", ())),
        steps=tuple(
            OperationalStep(
                id=str(s["id"]), title=str(s["title"]), guidance=str(s["guidance"]), handler=str(s["handler"]),
                required_inputs=tuple(s.get("required_inputs", ())), required_confirmations=tuple(s.get("required_confirmations", ())),
                preconditions=tuple(s.get("preconditions", ())), evidence_required=bool(s.get("evidence_required", True)),
                irreversible=bool(s.get("irreversible", False)), rollback_guidance=s.get("rollback_guidance"),
            ) for s in data.get("steps", ())
        ),
    )


def workflow_catalog() -> dict[str, OperationalWorkflow]:
    gate = "existing_office_authority_gate_required_for_each_step"
    return {w.id: w for w in [
        OperationalWorkflow("ops.work_package_review_promotion.v1", "Work-package review and promotion", "work-package review and promotion", gate, ("canonical_work_package_review", "canonical_promotion_request"), (
            OperationalStep("review", "Review work-package evidence", "Collect package path, validation evidence, and reviewer disposition.", "canonical_work_package_review", ("work_package_path",), (), ("workspace_clean",), True, False, "Return package to pending with review notes."),
            OperationalStep("promote", "Promote only after explicit approval", "Record steward approval before invoking canonical promotion.", "canonical_promotion_request", (), ("steward_promotion_approval",), ("review.completed",), True, True, "If unsupported, create a rollback request rather than auto-reverting."),
        )),
        OperationalWorkflow("ops.validation_evidence_next_action.v1", "Validation request, evidence review, and next action", "validation request, evidence review, and next action", gate, ("canonical_validation_request", "canonical_evidence_review", "canonical_next_action"), (
            OperationalStep("request_validation", "Request validation", "Capture validation scope and requested checks.", "canonical_validation_request", ("validation_scope",), (), (), True),
            OperationalStep("review_evidence", "Review evidence", "Attach evidence links and disposition.", "canonical_evidence_review", ("evidence_link",), ("reviewer_accepts_evidence",), ("request_validation.completed",), True),
            OperationalStep("select_next_action", "Record next action", "Record the operator-selected next action; never auto-select providers or retries.", "canonical_next_action", ("next_action",), ("operator_confirms_next_action",), ("review_evidence.completed",), True),
        )),
        OperationalWorkflow("ops.resident_onboarding_preparation.v1", "Resident onboarding preparation", "resident onboarding preparation", gate, ("canonical_resident_onboarding_prepare",), (
            OperationalStep("prepare_packet", "Prepare onboarding packet", "Gather resident id, charter links, and readiness evidence.", "canonical_resident_onboarding_prepare", ("resident_id", "charter_link"), (), ("resident_registry_available",), True),
            OperationalStep("confirm_handoff", "Confirm onboarding handoff", "Confirm handoff without activating unapproved runtime.", "canonical_resident_onboarding_prepare", (), ("operator_confirms_onboarding_packet",), ("prepare_packet.completed",), True),
        )),
        OperationalWorkflow("ops.project_intake_assignment.v1", "Project intake and assignment", "project intake and assignment", gate, ("canonical_project_intake", "canonical_assignment"), (
            OperationalStep("intake", "Capture project intake", "Capture goal, owner, constraints, and evidence.", "canonical_project_intake", ("project_goal", "requestor"), (), (), True),
            OperationalStep("assign", "Assign explicitly", "Assign only to the named approved assignee.", "canonical_assignment", ("assignee",), ("operator_confirms_assignment",), ("intake.completed",), True),
        )),
        OperationalWorkflow("ops.local_service_ready_launch.v1", "Local service readiness and approved launch", "local service readiness and approved launch", gate, ("canonical_service_readiness", "canonical_approved_launch"), (
            OperationalStep("readiness", "Check service readiness", "Verify service configuration, dependencies, and rollback notes.", "canonical_service_readiness", ("service_id",), (), ("workspace_clean",), True),
            OperationalStep("launch", "Launch after approval", "Launch only after explicit approval; do not select providers automatically.", "canonical_approved_launch", (), ("operator_approved_launch",), ("readiness.completed",), True, True, "Stop service or follow service-specific rollback runbook."),
        )),
        OperationalWorkflow("ops.incident_failure_triage.v1", "Incident or failure triage", "incident or failure triage", gate, ("canonical_incident_triage", "canonical_recovery_guidance"), (
            OperationalStep("triage", "Triage incident", "Capture symptoms, impact, and evidence.", "canonical_incident_triage", ("incident_summary", "impact"), (), (), True),
            OperationalStep("recovery", "Record recovery guidance", "Record supported recovery only; no automatic retry.", "canonical_recovery_guidance", ("recovery_plan",), ("operator_confirms_recovery_plan",), ("triage.completed",), True, False, "Escalate if the recovery handler reports unsupported rollback."),
        )),
        OperationalWorkflow("ops.operational_handoff_followup.v1", "Operational handoff and follow-up", "operational handoff and follow-up", gate, ("canonical_handoff", "canonical_followup"), (
            OperationalStep("handoff", "Prepare handoff", "Capture recipient, open items, and evidence.", "canonical_handoff", ("recipient", "open_items"), (), (), True),
            OperationalStep("followup", "Schedule follow-up", "Confirm follow-up owner and artifact links.", "canonical_followup", ("followup_owner",), ("operator_confirms_followup",), ("handoff.completed",), True),
        )),
    ]}


def start_session(workflow: OperationalWorkflow, session_id: str) -> OperationalWorkflowSession:
    session = OperationalWorkflowSession(workflow=workflow, session_id=session_id)
    _audit(session, "session_started", "Staged operational workflow created; no authorization is implied.")
    return session


def provide_input(session: OperationalWorkflowSession, name: str, value: Any) -> None:
    session.inputs[name] = value
    _audit(session, "input_provided", f"Input provided: {name}", input=name)


def confirm(session: OperationalWorkflowSession, confirmation_id: str) -> None:
    session.confirmations.add(confirmation_id)
    _audit(session, "confirmation_recorded", f"Explicit confirmation recorded: {confirmation_id}", confirmation=confirmation_id)


def satisfy_precondition(session: OperationalWorkflowSession, precondition_id: str, evidence_link: str | None = None) -> None:
    session.satisfied_preconditions.add(precondition_id)
    _audit(session, "precondition_satisfied", f"Precondition satisfied: {precondition_id}", precondition=precondition_id, evidence_link=evidence_link)


def current_step(session: OperationalWorkflowSession) -> OperationalStep | None:
    return None if session.current_step_index >= len(session.workflow.steps) else session.workflow.steps[session.current_step_index]


def evaluate_readiness(session: OperationalWorkflowSession) -> dict[str, Any]:
    step = current_step(session)
    if step is None:
        return {"state": "completed", "step_id": None, "missing_inputs": [], "missing_confirmations": [], "missing_preconditions": []}
    missing_inputs = [x for x in step.required_inputs if x not in session.inputs]
    missing_confirmations = [x for x in step.required_confirmations if x not in session.confirmations]
    missing_preconditions = [x for x in step.preconditions if x not in session.satisfied_preconditions]
    state = "ready" if not (missing_inputs or missing_confirmations or missing_preconditions) else "awaiting_input"
    if missing_confirmations and not missing_inputs and not missing_preconditions:
        state = "awaiting_confirmation"
    return {"state": state, "step_id": step.id, "guidance": step.guidance, "missing_inputs": missing_inputs, "missing_confirmations": missing_confirmations, "missing_preconditions": missing_preconditions, "irreversible": step.irreversible, "rollback_guidance": step.rollback_guidance}


def advance(session: OperationalWorkflowSession, handlers: Mapping[str, Handler]) -> dict[str, Any]:
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
        session.status = "blocked"; session.blocked_reason = f"No canonical handler registered for {step.handler}"
        _audit(session, "blocked", session.blocked_reason, step_id=step.id)
        return {"state": "blocked", "advanced": False, "reason": session.blocked_reason}
    session.status = "running"
    _audit(session, "step_started", f"Invoking canonical handler: {step.handler}", step_id=step.id, handler=step.handler, authority_gate=session.workflow.authority_gate)
    try:
        result = dict(handler(session, step))
    except Exception as exc:
        session.status = "failed"; session.failure_reason = f"{type(exc).__name__}: {exc}"
        _audit(session, "failed", session.failure_reason, step_id=step.id)
        return {"state": "failed", "advanced": False, "reason": session.failure_reason}
    if result.get("blocked"):
        session.status = "blocked"; session.blocked_reason = str(result.get("reason", "handler reported blocked"))
        _audit(session, "blocked", session.blocked_reason, step_id=step.id)
        return {"state": "blocked", "advanced": False, "reason": session.blocked_reason, "rollback_guidance": step.rollback_guidance}
    evidence_link = result.get("evidence_link")
    if step.evidence_required and not evidence_link:
        session.status = "failed"; session.failure_reason = "Step completed without required evidence link."
        _audit(session, "failed", session.failure_reason, step_id=step.id)
        return {"state": "failed", "advanced": False, "reason": session.failure_reason}
    session.evidence.append({"step_id": step.id, "handler": step.handler, "evidence_link": evidence_link, "summary": result.get("summary", "completed"), "created_at": utc_now()})
    for artifact in result.get("generated_artifacts", []):
        session.generated_artifacts.append(dict(artifact) | {"step_id": step.id})
    session.completed_steps.append(step.id)
    session.satisfied_preconditions.add(f"{step.id}.completed")
    session.current_step_index += 1
    session.status = "completed" if current_step(session) is None else "not_started"
    _audit(session, "step_completed", f"Completed step: {step.id}", step_id=step.id, evidence_link=evidence_link)
    return {"state": session.status, "advanced": True, "completed_step": step.id, "evidence_link": evidence_link}


def recovery_guidance(session: OperationalWorkflowSession) -> dict[str, Any]:
    step = current_step(session)
    return {"supported": bool(step and step.rollback_guidance), "guidance": None if step is None else step.rollback_guidance, "no_automatic_retry": True, "no_automatic_provider_selection": True}


def browser_contract(session: OperationalWorkflowSession) -> dict[str, Any]:
    return {"kind": "estate.operational_workflow.browser_contract.v1", "installed_by_wp_0531": True, "session": session.to_snapshot(), "current_step": None if current_step(session) is None else workflow_to_dict(session.workflow)["steps"][session.current_step_index], "readiness": evaluate_readiness(session), "allowed_actions": ["provide_input", "confirm", "satisfy_precondition", "advance", "save", "resume"], "authority": {"authority_gate": session.workflow.authority_gate, "automatic_approval": False, "automatic_acceptance": False, "automatic_merge": False, "automatic_retry": False, "automatic_provider_selection": False}}


def _audit(session: OperationalWorkflowSession, event: str, message: str, **extra: Any) -> None:
    session.audit_log.append({"at": utc_now(), "event": event, "message": message, **{k: v for k, v in extra.items() if v is not None}})
