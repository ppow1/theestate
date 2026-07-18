from copy import deepcopy

from estate.core.operational_guardrails import evaluate_guardrails

NOW = "2026-07-18T12:00:00Z"


def proposal(**extra):
    value = {"action_id": "a1", "action_class": "coordinate", "authority_scope": "operational_coordination", "target_mechanism": "office_runtime_or_repository_message", "source_refs": ["evidence/a1.json"], "permission": "recommendation", "protected_surfaces": []}
    value.update(extra)
    return value


def rule(rule_id, disposition, kind="campaign", **extra):
    value = {"rule_id": rule_id, "disposition": disposition, "policy_kind": kind, "authority_source": f"policy/{rule_id}.md", "decision_owner": "Chief Architect", "effective_from": "2026-07-18T00:00:00Z", "scope": {"action_class": "coordinate"}}
    value.update(extra)
    return value


def test_current_canonical_rule_allows_only_progress_to_existing_lane():
    result = evaluate_guardrails(proposal(), [rule("campaign-allow", "allow")], evaluated_at=NOW)
    assert result["disposition"] == "allow"
    assert result["action_may_proceed_to_existing_authorization_lane"] is True
    assert result["authorizes_action"] is False


def test_constitutional_deny_outranks_delegation_allow():
    result = evaluate_guardrails(proposal(), [rule("delegation", "allow", "delegation"), rule("constitution", "deny", "constitutional")], evaluated_at=NOW)
    assert result["disposition"] == "deny"
    assert result["controlling_rule_ids"] == ["constitution"]


def test_equal_precedence_conflict_escalates():
    result = evaluate_guardrails(proposal(), [rule("allow", "allow", "office"), rule("deny", "deny", "office")], evaluated_at=NOW)
    assert result["disposition"] == "escalate"
    assert "conflict" in " ".join(result["missing_or_conflicting_evidence"])


def test_missing_and_stale_policy_defer_without_inferring_permission():
    missing = evaluate_guardrails(proposal(), [], evaluated_at=NOW)
    stale = evaluate_guardrails(proposal(), [rule("old", "allow", effective_until="2026-07-17T00:00:00Z")], evaluated_at=NOW)
    assert missing["disposition"] == "defer"
    assert stale["disposition"] == "defer"
    assert stale["missing_or_conflicting_evidence"]


def test_protected_and_prohibited_actions_cannot_be_allowed_by_guardrail():
    protected = evaluate_guardrails(proposal(permission="protected"), [rule("allow", "allow")], evaluated_at=NOW)
    prohibited = evaluate_guardrails(proposal(permission="prohibited"), [rule("allow", "allow")], evaluated_at=NOW)
    assert protected["disposition"] == "escalate"
    assert prohibited["disposition"] == "deny"


def test_scope_mismatch_and_ambiguous_proposal_fail_closed_without_mutation():
    item = proposal(action_id="")
    before = deepcopy(item)
    result = evaluate_guardrails(item, [rule("execution", "allow", scope={"action_class": "mechanical_action"})], evaluated_at=NOW)
    assert result["disposition"] == "escalate"
    assert item == before


def test_all_four_policy_dispositions_are_explicit_and_audited():
    outcomes = {outcome: evaluate_guardrails(proposal(), [rule(outcome, outcome)], evaluated_at=NOW) for outcome in ("allow", "deny", "defer", "escalate")}
    assert set(result["disposition"] for result in outcomes.values()) == {"allow", "deny", "defer", "escalate"}
    assert all(result["audit_record"]["disposition"] == result["disposition"] for result in outcomes.values())
