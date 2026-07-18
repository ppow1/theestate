"""Authority-aware classification for proposed operational actions.

This module evaluates descriptors; it does not execute actions, resolve identities,
grant authority, or persist decisions.  Callers must supply canonical evidence.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

SCHEMA_VERSION = "estate.operational.action.v1"

ACTION_CLASSES = {
    "observe", "recommend", "coordinate", "request_execution",
    "mechanical_action", "office_decision", "protected_decision", "acceptance",
}
DISPOSITIONS = {"proposed", "evaluated", "denied", "requires_review", "disposed"}
SIDE_EFFECTS = {
    "none", "advisory", "routing", "execution_request", "bounded_write",
    "decision_record", "protected_record", "acceptance_record",
}
RETRY_POLICIES = {"never", "manual", "bounded_idempotent"}

EXPECTED_MECHANISMS = {
    "observe": "canonical_source_read",
    "recommend": "office_decision_support",
    "coordinate": "office_runtime_or_repository_message",
    "request_execution": "execution_dispatch",
    "mechanical_action": "delegated_target_adapter",
    "office_decision": "canonical_office_record",
    "protected_decision": "protected_authority_record",
    "acceptance": "existing_acceptance_lane",
}

EXPECTED_SIDE_EFFECTS = {
    "observe": "none",
    "recommend": "advisory",
    "coordinate": "routing",
    "request_execution": "execution_request",
    "mechanical_action": "bounded_write",
    "office_decision": "decision_record",
    "protected_decision": "protected_record",
    "acceptance": "acceptance_record",
}

# This is a fail-closed boundary policy derived from canonical records, not an
# identity or authority registry.  Evidence supplied for a real actor controls.
ROLE_SCOPES = {
    "steward": {"institutional", "strategic_priority", "budget", "privacy", "constitutional", "final_acceptance"},
    "chief_architect": {"engineering_architecture", "engineering_coordination", "engineering_acceptance", "integration"},
    "grace": {"operational_observation", "operational_coordination", "recovery_coordination"},
    "helen": {"staffing", "capability", "workforce"},
    "alfred": {"communication_routing", "chief_of_staff_coordination"},
    "engineering_worker": {"bounded_engineering_execution"},
    "execution_provider": {"bounded_execution"},
}

COORDINATION_ROLES = {"steward", "chief_architect", "grace", "helen", "alfred"}
EXECUTION_REQUEST_ROLES = {"steward", "chief_architect", "grace", "engineering_worker"}
MECHANICAL_ROLES = {"engineering_worker", "execution_provider"}
OFFICE_DECISION_ROLES = {"steward", "chief_architect", "grace", "helen", "alfred"}

PROTECTED_OWNERS = {
    "engineering_architecture": "Chief Architect",
    "engineering_acceptance": "Chief Architect",
    "staffing": "Helen or explicitly named protected staffing authority",
    "budget": "Steward or explicitly named budget authority",
    "spending": "Steward or explicitly named spending authority",
    "privacy": "Steward or explicitly named privacy authority",
    "constitutional": "Steward",
    "final_acceptance": "Steward",
    "merge": "explicit merge authority",
    "deployment": "explicit deployment authority",
    "disclosure": "explicit disclosure authority",
}

AUTHORITY_BASIS = {
    "steward": "docs/governance/Estate_Manual.md",
    "chief_architect": "operations/departments/engineering/engineering_department_charter.md",
    "grace": "runtime/onboarding/grace/steward_appointment_decision.json",
    "helen": "docs/architecture/estate_operations_center_continuous_momentum_engine_architectural_charter.md",
    "alfred": "docs/governance/Estate_Vision_and_Architecture.md",
    "engineering_worker": "docs/architecture/engineering_campaign_intake_contract.md",
    "execution_provider": "docs/architecture/engineering_execution_lane_and_provider_routing_contract.md",
}


def _text(value: Any, name: str, missing: list[str]) -> None:
    if not isinstance(value, str) or not value.strip():
        missing.append(name)


@dataclass(frozen=True)
class OperationalActionDescriptor:
    action_id: str
    action_class: str
    proposed_actor_id: str
    institutional_role: str
    identity_evidence: tuple[str, ...]
    source_refs: tuple[str, ...]
    target_ref: str
    target_mechanism: str
    authority_scope: str
    required_authority: str
    authority_evidence: tuple[str, ...]
    readiness_prerequisites: tuple[str, ...]
    validation_requirements: tuple[str, ...]
    evidence_requirements: tuple[str, ...]
    side_effect: str
    protected_surfaces: tuple[str, ...]
    idempotency_key: str
    retry_policy: str
    stop_conditions: tuple[str, ...]
    escalation_conditions: tuple[str, ...]
    disposition_state: str = "proposed"
    decision_or_execution_evidence: tuple[str, ...] = ()
    schema_version: str = SCHEMA_VERSION
    metadata: dict[str, Any] = field(default_factory=dict, compare=False)

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "OperationalActionDescriptor":
        payload = dict(value)
        tuple_fields = {
            "identity_evidence", "source_refs", "authority_evidence",
            "readiness_prerequisites", "validation_requirements",
            "evidence_requirements", "protected_surfaces", "stop_conditions",
            "escalation_conditions", "decision_or_execution_evidence",
        }
        for name in tuple_fields:
            item = payload.get(name, ())
            if not isinstance(item, (list, tuple)):
                raise ValueError(f"{name} must be an array")
            payload[name] = tuple(item)
        return cls(**payload)

    def missing_or_ambiguous(self) -> tuple[str, ...]:
        missing: list[str] = []
        for name in (
            "action_id", "proposed_actor_id", "institutional_role", "target_ref",
            "target_mechanism", "authority_scope", "required_authority",
            "idempotency_key",
        ):
            _text(getattr(self, name), name, missing)
        if self.action_class not in ACTION_CLASSES:
            missing.append("known action_class")
        if self.institutional_role not in ROLE_SCOPES:
            missing.append("recognized evidence-bound institutional_role")
        if not self.identity_evidence:
            missing.append("identity_evidence")
        if not self.source_refs:
            missing.append("source_refs")
        if not self.evidence_requirements:
            missing.append("evidence_requirements")
        if not self.stop_conditions:
            missing.append("stop_conditions")
        if not self.escalation_conditions:
            missing.append("escalation_conditions")
        if self.side_effect not in SIDE_EFFECTS:
            missing.append("known side_effect")
        if self.retry_policy not in RETRY_POLICIES:
            missing.append("known retry_policy")
        if self.disposition_state not in DISPOSITIONS:
            missing.append("known disposition_state")
        if self.schema_version != SCHEMA_VERSION:
            missing.append("supported schema_version")
        if not isinstance(self.metadata, dict):
            missing.append("metadata object")
        return tuple(dict.fromkeys(missing))


@dataclass(frozen=True)
class ActionEvaluationContext:
    satisfied_readiness: tuple[str, ...] = ()
    satisfied_validation: tuple[str, ...] = ()
    available_evidence: tuple[str, ...] = ()
    explicit_delegation_refs: tuple[str, ...] = ()
    protected_decision_refs: tuple[str, ...] = ()
    acceptance_refs: tuple[str, ...] = ()
    conflicting_authority: bool = False


@dataclass(frozen=True)
class AuthorityEvaluation:
    action_id: str
    classification: str
    disposition: str
    authoritative_basis: tuple[str, ...]
    missing_prerequisites: tuple[str, ...]
    required_mechanism: str
    required_decision_owner: str
    must_stop_and_escalate: bool
    next_safe_action: str
    evidence_to_produce: tuple[str, ...]
    explanation: str


def _owner(descriptor: OperationalActionDescriptor) -> str:
    for surface in descriptor.protected_surfaces:
        if surface in PROTECTED_OWNERS:
            return PROTECTED_OWNERS[surface]
    if descriptor.authority_scope in PROTECTED_OWNERS:
        return PROTECTED_OWNERS[descriptor.authority_scope]
    return descriptor.required_authority or "named canonical authority"


def _result(
    descriptor: OperationalActionDescriptor,
    disposition: str,
    missing: tuple[str, ...],
    owner: str,
    explanation: str,
) -> AuthorityEvaluation:
    mechanism = EXPECTED_MECHANISMS.get(descriptor.action_class, descriptor.target_mechanism or "unresolved")
    stop = disposition != "allowed"
    next_action = (
        f"Use {mechanism} and produce the declared validation and evidence records."
        if not stop
        else f"Do not execute; route the descriptor and missing evidence to {owner}."
    )
    basis = tuple(dict.fromkeys((*descriptor.identity_evidence, *descriptor.authority_evidence, AUTHORITY_BASIS.get(descriptor.institutional_role, ""))))
    return AuthorityEvaluation(
        descriptor.action_id,
        descriptor.action_class,
        disposition,
        tuple(item for item in basis if item),
        missing,
        mechanism,
        owner,
        stop,
        next_action,
        tuple(dict.fromkeys((*descriptor.validation_requirements, *descriptor.evidence_requirements))),
        explanation,
    )


def evaluate_action(descriptor: OperationalActionDescriptor, context: ActionEvaluationContext) -> AuthorityEvaluation:
    """Evaluate a proposed action without performing or approving it."""
    ambiguous = descriptor.missing_or_ambiguous()
    owner = _owner(descriptor)
    if ambiguous or context.conflicting_authority:
        missing = ambiguous + (("conflicting_authority",) if context.conflicting_authority else ())
        return _result(descriptor, "requires_review", missing, owner, "Identity, scope, authority, or descriptor evidence is ambiguous; evaluation fails closed.")

    expected_mechanism = EXPECTED_MECHANISMS[descriptor.action_class]
    if descriptor.target_mechanism != expected_mechanism:
        return _result(descriptor, "denied", (f"canonical mechanism {expected_mechanism}",), owner, "The proposed mechanism would bypass the canonical action lane.")
    expected_effect = EXPECTED_SIDE_EFFECTS[descriptor.action_class]
    if descriptor.side_effect != expected_effect:
        return _result(descriptor, "denied", (f"side_effect {expected_effect}",), owner, "The side effect does not match the declared action class.")

    missing = []
    for required, available, label in (
        (descriptor.readiness_prerequisites, context.satisfied_readiness, "readiness"),
        (descriptor.validation_requirements, context.satisfied_validation, "validation"),
        (descriptor.evidence_requirements, context.available_evidence, "evidence"),
    ):
        missing.extend(f"{label}:{item}" for item in required if item not in available)
    if missing:
        return _result(descriptor, "requires_review", tuple(missing), owner, "Declared readiness, validation, or evidence prerequisites are incomplete.")

    role = descriptor.institutional_role
    scope_allowed = descriptor.authority_scope in ROLE_SCOPES[role]
    if descriptor.action_class in {"observe", "recommend"}:
        # Access/classification policy remains a caller prerequisite. These classes
        # never authorize mutation or a decision.
        return _result(descriptor, "allowed", (), descriptor.required_authority, "The action is read-only or advisory and remains bound to its canonical evidence and decision owner.")
    if not descriptor.authority_evidence:
        return _result(descriptor, "requires_review", ("authority_evidence",), owner, "A role label or technical capability is not authority evidence.")
    if descriptor.action_class == "coordinate":
        if role not in COORDINATION_ROLES or not scope_allowed:
            return _result(descriptor, "denied", ("office coordination authority",), owner, "The actor is outside the requested office coordination scope.")
        return _result(descriptor, "allowed", (), descriptor.required_authority, "Coordination is allowed only within the evidence-bound office scope.")
    if descriptor.action_class == "request_execution":
        if role not in EXECUTION_REQUEST_ROLES or not scope_allowed:
            return _result(descriptor, "denied", ("execution-request authority",), owner, "The actor may not submit this Dispatch request.")
        return _result(descriptor, "allowed", (), descriptor.required_authority, "The request may enter Dispatch; it is not execution, approval, or acceptance.")
    if descriptor.action_class == "mechanical_action":
        if role not in MECHANICAL_ROLES or not scope_allowed:
            return _result(descriptor, "denied", ("bounded execution role and scope",), owner, "The actor is not an authorized mechanical execution provider for this scope.")
        if not context.explicit_delegation_refs:
            return _result(descriptor, "requires_review", ("explicit_delegation_refs",), owner, "Mechanical capability without explicit delegation fails closed.")
        return _result(descriptor, "allowed", (), descriptor.required_authority, "The bounded, idempotent mechanical action is explicitly delegated; outcome evidence remains non-decisional.")
    if descriptor.action_class == "office_decision":
        if role not in OFFICE_DECISION_ROLES or not scope_allowed:
            return _result(descriptor, "denied", ("office decision scope",), owner, "The proposed actor does not own this office decision scope.")
        return _result(descriptor, "allowed", (), descriptor.required_authority, "The named office may record this bounded decision in its canonical lane; no broader authority is implied.")
    if descriptor.action_class == "protected_decision":
        missing_refs = () if context.protected_decision_refs else ("protected_decision_refs",)
        return _result(descriptor, "requires_review", missing_refs, owner, "Protected decisions always stop for the named authority; this evaluator cannot perform or infer them.")
    if descriptor.action_class == "acceptance":
        missing_refs = () if context.acceptance_refs else ("canonical_acceptance_refs",)
        return _result(descriptor, "requires_review", missing_refs, owner, "Acceptance is a distinct protected lane and cannot be inferred from execution, validation, or completion.")
    return _result(descriptor, "requires_review", ("recognized action policy",), owner, "No safe policy matched the proposed action.")


def evaluate_for_mechanism(
    descriptor: OperationalActionDescriptor,
    context: ActionEvaluationContext,
    mechanism: str,
) -> AuthorityEvaluation:
    """Narrow preflight adapter for PTM, Dispatch, mail, and decision callers."""
    if mechanism != descriptor.target_mechanism:
        return _result(descriptor, "denied", (f"descriptor target mechanism {descriptor.target_mechanism}",), _owner(descriptor), "The caller mechanism does not match the evaluated descriptor.")
    return evaluate_action(descriptor, context)
