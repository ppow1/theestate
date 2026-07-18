from dataclasses import replace

import pytest

from estate.core.operational_action_taxonomy import (
    ACTION_CLASSES,
    ActionEvaluationContext,
    EXPECTED_MECHANISMS,
    EXPECTED_SIDE_EFFECTS,
    OperationalActionDescriptor,
    evaluate_action,
    evaluate_for_mechanism,
)


def descriptor(action_class="observe", role="grace", scope="operational_observation", **changes):
    item = OperationalActionDescriptor(
        action_id=f"action-{action_class}",
        action_class=action_class,
        proposed_actor_id=f"employee:{role}",
        institutional_role=role,
        identity_evidence=("data/registry/personnel.json",),
        source_refs=("collaboration/work_packages/completions/WP-0689_completion_receipt.md",),
        target_ref="CAMPAIGN-0681/WP-0690",
        target_mechanism=EXPECTED_MECHANISMS[action_class],
        authority_scope=scope,
        required_authority="named canonical owner",
        authority_evidence=("docs/architecture/estate_operational_authority_map.md",),
        readiness_prerequisites=("ready",),
        validation_requirements=("validated",),
        evidence_requirements=("source-linked",),
        side_effect=EXPECTED_SIDE_EFFECTS[action_class],
        protected_surfaces=(),
        idempotency_key=f"CAMPAIGN-0681:{action_class}:1",
        retry_policy="bounded_idempotent",
        stop_conditions=("authority missing",),
        escalation_conditions=("protected surface",),
    )
    return replace(item, **changes)


def context(**changes):
    item = ActionEvaluationContext(
        satisfied_readiness=("ready",),
        satisfied_validation=("validated",),
        available_evidence=("source-linked",),
    )
    return replace(item, **changes)


def test_all_required_action_classes_are_distinct_and_machine_checkable():
    assert ACTION_CLASSES == {"observe", "recommend", "coordinate", "request_execution", "mechanical_action", "office_decision", "protected_decision", "acceptance"}
    assert len(set(EXPECTED_MECHANISMS.values())) == len(ACTION_CLASSES)


def test_ambiguous_identity_and_conflicting_authority_fail_closed():
    result = evaluate_action(descriptor(identity_evidence=()), context())
    assert result.disposition == "requires_review"
    assert "identity_evidence" in result.missing_prerequisites
    conflict = evaluate_action(descriptor(), context(conflicting_authority=True))
    assert conflict.must_stop_and_escalate is True


def test_canonical_mechanism_and_side_effect_cannot_be_bypassed():
    bypass = evaluate_action(descriptor(target_mechanism="execution_dispatch"), context())
    assert bypass.disposition == "denied"
    disguised = evaluate_action(descriptor(side_effect="decision_record"), context())
    assert disguised.disposition == "denied"


@pytest.mark.parametrize(
    "role,scope",
    [
        ("grace", "operational_coordination"),
        ("helen", "staffing"),
        ("alfred", "communication_routing"),
        ("chief_architect", "engineering_coordination"),
        ("steward", "institutional"),
    ],
)
def test_named_offices_coordinate_only_inside_their_evidence_bound_scope(role, scope):
    result = evaluate_action(descriptor("coordinate", role, scope), context())
    assert result.disposition == "allowed"
    assert result.must_stop_and_escalate is False


def test_grace_cannot_take_architecture_or_engineering_acceptance_authority():
    item = descriptor("office_decision", "grace", "engineering_architecture", protected_surfaces=("engineering_architecture",))
    result = evaluate_action(item, context())
    assert result.disposition == "denied"
    assert result.required_decision_owner == "Chief Architect"


def test_helen_cannot_set_engineering_priority_or_acceptance():
    item = descriptor("office_decision", "helen", "engineering_acceptance", protected_surfaces=("engineering_acceptance",))
    result = evaluate_action(item, context())
    assert result.disposition == "denied"
    assert result.required_decision_owner == "Chief Architect"


def test_alfred_routing_does_not_become_execution():
    item = descriptor("request_execution", "alfred", "communication_routing")
    result = evaluate_action(item, context())
    assert result.disposition == "denied"


def test_execution_provider_is_not_an_office_or_decision_authority():
    item = descriptor("office_decision", "execution_provider", "bounded_execution")
    result = evaluate_action(item, context())
    assert result.disposition == "denied"


def test_recommendation_is_advisory_not_a_decision():
    result = evaluate_action(descriptor("recommend", "grace", "operational_observation"), context())
    assert result.disposition == "allowed"
    assert result.required_mechanism == "office_decision_support"
    assert "advisory" in result.explanation


def test_mechanical_action_requires_explicit_delegation():
    item = descriptor("mechanical_action", "execution_provider", "bounded_execution")
    stopped = evaluate_action(item, context())
    assert stopped.disposition == "requires_review"
    allowed = evaluate_action(item, context(explicit_delegation_refs=("dispatch:handoff:1",)))
    assert allowed.disposition == "allowed"
    assert "non-decisional" in allowed.explanation


@pytest.mark.parametrize(
    "surface,owner",
    [("budget", "Steward or explicitly named budget authority"), ("engineering_architecture", "Chief Architect"), ("staffing", "Helen or explicitly named protected staffing authority")],
)
def test_protected_actions_stop_for_correct_authority(surface, owner):
    item = descriptor("protected_decision", "steward", "institutional", protected_surfaces=(surface,))
    result = evaluate_action(item, context(protected_decision_refs=("decision-request:1",)))
    assert result.disposition == "requires_review"
    assert result.required_decision_owner == owner
    assert result.must_stop_and_escalate is True


def test_acceptance_cannot_be_inferred_from_execution_success():
    item = descriptor(
        "acceptance",
        "chief_architect",
        "engineering_acceptance",
        protected_surfaces=("engineering_acceptance",),
        decision_or_execution_evidence=("execution:success",),
    )
    missing = evaluate_action(item, context())
    assert missing.disposition == "requires_review"
    assert "canonical_acceptance_refs" in missing.missing_prerequisites
    still_stopped = evaluate_action(item, context(acceptance_refs=("acceptance:request:1",)))
    assert still_stopped.disposition == "requires_review"


def test_missing_readiness_validation_or_evidence_is_explained():
    result = evaluate_action(descriptor(), ActionEvaluationContext())
    assert result.disposition == "requires_review"
    assert result.missing_prerequisites == ("readiness:ready", "validation:validated", "evidence:source-linked")
    assert result.evidence_to_produce == ("validated", "source-linked")


def test_narrow_adapter_rejects_caller_mechanism_mismatch():
    item = descriptor()
    result = evaluate_for_mechanism(item, context(), "execution_dispatch")
    assert result.disposition == "denied"
