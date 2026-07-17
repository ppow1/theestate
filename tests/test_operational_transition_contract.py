import json
from dataclasses import replace
from pathlib import Path

import pytest

from estate.core.operational_transition_contract import (
    ContractViolation,
    NormalizedOperationalEvent,
    TransitionContext,
    replay_projection,
    validate_transition,
)

FIXTURES = Path(__file__).parent / "fixtures" / "campaign_0681"


def load(name):
    return NormalizedOperationalEvent.from_dict(json.loads((FIXTURES / name).read_text(encoding="utf-8")))


def event(**changes):
    base = load("operational_event_valid.json")
    return replace(base, **changes)


def ready_context(**changes):
    base = TransitionContext(
        dependencies_ready=True,
        readiness_confirmed=True,
        staffing_confirmed=True,
        evidence_complete=True,
        health_status="healthy",
        authority_refs=("collaboration/campaigns/CAMPAIGN_0681_WP_0691_REPAIR_SUPERSEDING_LAUNCH_AUTHORIZATION.md",),
    )
    return replace(base, **changes)


def test_fixture_references_canonical_identity_and_path():
    item = load("operational_event_valid.json")
    assert item.subject.subject_id == "WP-0689"
    assert item.subject.canonical_path.startswith("collaboration/work_packages/pending/")
    validate_transition("pending", item, ready_context())


def test_projection_is_rebuildable_and_non_authoritative():
    item = load("operational_event_valid.json")
    projection = replay_projection([item], {item.event_id: ready_context()}, initial_state="pending")
    assert projection.state == "ready"
    assert projection.authoritative is False
    assert projection.rebuildable is True
    assert projection.evidence_refs == item.evidence_refs


def test_missing_canonical_path_fails_closed():
    item = event(subject=replace(load("operational_event_valid.json").subject, canonical_path=""))
    with pytest.raises(ContractViolation, match="canonical_path"):
        item.validate()


@pytest.mark.parametrize("missing", ["dependencies_ready", "readiness_confirmed", "staffing_confirmed"])
def test_readiness_prerequisites_fail_closed(missing):
    item = load("operational_event_valid.json")
    with pytest.raises(ContractViolation, match="prerequisites"):
        validate_transition("pending", item, replace(ready_context(), **{missing: False}))


def test_unavailable_or_unknown_health_cannot_become_ready():
    item = load("operational_event_valid.json")
    for health in ("unavailable", "stale", "unknown"):
        with pytest.raises(ContractViolation, match="health"):
            validate_transition("pending", item, ready_context(health_status=health))


def test_recommendation_and_execution_request_do_not_change_state():
    for classification in ("recommendation", "execution_request"):
        proposed = event(authority_classification=classification)
        with pytest.raises(ContractViolation, match="cannot change"):
            validate_transition("pending", proposed, ready_context())


def test_execution_requires_explicit_delegation_and_authority_evidence():
    proposed = event(prior_state="eligible", new_state="executing", authority_classification="delegated_mechanical")
    with pytest.raises(ContractViolation, match="authority evidence"):
        validate_transition("eligible", proposed, ready_context(authority_refs=()))
    validate_transition("eligible", proposed, ready_context())


def test_completion_does_not_imply_review_or_acceptance():
    completed = event(prior_state="executing", new_state="complete", authority_classification="delegated_mechanical")
    validate_transition("executing", completed, ready_context())
    invalid = load("operational_event_invalid_acceptance.json")
    with pytest.raises(ContractViolation, match="distinct acceptance"):
        validate_transition("complete", invalid, ready_context(canonical_acceptance_ref="acceptance.md"))


def test_acceptance_requires_canonical_record_and_authority():
    accepted = event(prior_state="review_required", new_state="accepted", authority_classification="acceptance")
    with pytest.raises(ContractViolation, match="canonical acceptance"):
        validate_transition("review_required", accepted, ready_context())
    validate_transition("review_required", accepted, ready_context(canonical_acceptance_ref="collaboration/acceptance/WP-0689.md"))


def test_protected_transition_requires_explicit_approval():
    protected = event(prior_state="waiting_for_authority", new_state="executing", authority_classification="protected_decision")
    with pytest.raises(ContractViolation, match="protected approval"):
        validate_transition("waiting_for_authority", protected, ready_context())
    validate_transition("waiting_for_authority", protected, ready_context(protected_approval_refs=("decision:steward:1",)))


def test_stale_and_conflicting_evidence_fail_closed():
    item = load("operational_event_valid.json")
    stale = ready_context(evidence_observed_at="2026-07-17T18:00:00Z", max_evidence_age_seconds=60)
    with pytest.raises(ContractViolation, match="stale"):
        validate_transition("pending", item, stale)
    with pytest.raises(ContractViolation, match="conflicting"):
        validate_transition("pending", item, ready_context(conflicting_evidence=True))


def test_exact_duplicate_is_idempotent_but_conflicting_duplicate_fails():
    item = load("operational_event_valid.json")
    contexts = {item.event_id: ready_context()}
    projection = replay_projection([item, item], contexts, initial_state="pending")
    assert projection.applied_event_ids == (item.event_id,)
    assert projection.duplicate_event_ids == (item.event_id,)
    conflict = replace(item, event_id="other-id", new_state="blocked")
    with pytest.raises(ContractViolation, match="conflicting content"):
        replay_projection([item, conflict], {**contexts, "other-id": ready_context()}, initial_state="pending")


def test_out_of_order_and_prior_state_mismatch_fail_closed():
    first = load("operational_event_valid.json")
    second = event(
        event_id="opn-older",
        idempotency_key="older",
        prior_state="ready",
        new_state="blocked",
        observed_at="2026-07-17T19:58:00Z",
        effective_at="2026-07-17T19:58:00Z",
    )
    with pytest.raises(ContractViolation, match="out-of-order"):
        replay_projection([first, second], {first.event_id: ready_context(), second.event_id: ready_context()}, initial_state="pending")
    with pytest.raises(ContractViolation, match="does not match"):
        validate_transition("observed", first, ready_context())
