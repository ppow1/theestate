from copy import deepcopy

from estate.core.continuous_momentum_engine import run_momentum_cycle

NOW = "2026-07-18T12:00:00Z"


def projection(state="ready", **extra):
    value = {"state": state, "authorizes_action": False, "evidence_references": ["evidence/state.json"], "warnings": []}
    value.update(extra)
    return value


def candidate(permission="recommendation", priority=10, **extra):
    value = {
        "action_id": f"action-{permission}", "permission": permission, "priority": priority,
        "idempotency_key": f"key-{permission}", "source_refs": ["evidence/action.json"],
        "canonical_mechanism": "office_decision_support", "authority_refs": [],
    }
    value.update(extra)
    return value


def run(**extra):
    value = dict(cycle_id="cycle-1", observed_at=NOW, inputs={"readiness": projection()}, candidates=[])
    value.update(extra)
    return run_momentum_cycle(**value)


def test_recommends_highest_priority_valid_action_deterministically():
    candidates = [candidate(priority=10), candidate(priority=20, action_id="urgent", idempotency_key="urgent")]
    first = run(candidates=candidates)
    second = run(candidates=reversed(candidates))
    assert first == second
    assert first["disposition"] == "recommend"
    assert first["selected_action"]["action_id"] == "urgent"
    assert [stage["stage"] for stage in first["stages"]] == ["observe", "reconcile", "classify", "propose", "authorize", "act", "verify", "record"]


def test_stale_conflicting_and_protected_inputs_hold_without_action():
    for inputs in (
        {"readiness": projection("stale")},
        {"authority": projection("indeterminate")},
        {"blocker": projection(protected_decision=True)},
    ):
        called = []
        result = run(inputs=inputs, candidates=[candidate("preauthorized", authority_refs=["authority/a.json"])], mode="live", action_adapter=lambda item: called.append(item) or {"evidence_reference": "outcome.json"})
        assert result["disposition"] == "escalate"
        assert result["action_executed"] is False
        assert called == []


def test_duplicate_and_cooldown_produce_safe_idle():
    duplicate = run(candidates=[candidate()], prior_action_keys=["key-recommendation"])
    cooling = run(candidates=[candidate()], last_action_at="2026-07-18T11:59:00Z")
    assert duplicate["safe_idle"] is True
    assert cooling["safe_idle"] is True


def test_dry_run_never_invokes_adapter_even_when_preauthorized():
    called = []
    action = candidate("preauthorized", authority_refs=["authority/delegation.json"])
    result = run(candidates=[action], mode="dry_run", action_adapter=lambda item: called.append(item) or {})
    assert result["disposition"] == "authorized_dry_run"
    assert result["action_executed"] is False
    assert called == []


def test_live_action_requires_explicit_authority_and_canonical_adapter_evidence():
    denied = run(candidates=[candidate("preauthorized")], mode="live", action_adapter=lambda item: {"evidence_reference": "outcome.json"})
    assert denied["action_executed"] is False
    allowed_action = candidate("delegated", authority_refs=["dispatch/delegation.json"], canonical_mechanism="execution_dispatch")
    before = deepcopy(allowed_action)
    allowed = run(candidates=[allowed_action], mode="live", action_adapter=lambda item: {"evidence_reference": "dispatch/result.json", "status": "completed"})
    assert allowed["disposition"] == "attempted"
    assert allowed["action_executed"] is True
    assert "dispatch/result.json" in allowed["evidence_references"]
    assert allowed_action == before


def test_prohibited_and_protected_candidates_never_execute():
    called = []
    result = run(candidates=[candidate("prohibited", priority=100), candidate("protected", priority=90)], mode="live", action_adapter=lambda item: called.append(item) or {})
    assert result["disposition"] == "escalate"
    assert called == []


def test_missing_projection_authority_boundary_fails_closed():
    result = run(inputs={"bad": {"state": "ready", "authorizes_action": True}}, candidates=[candidate()])
    assert result["safe_idle"] is True
    assert "does not explicitly deny authority" in " ".join(result["holds"])


def test_adapter_without_outcome_evidence_is_visible_failure():
    action = candidate("preauthorized", authority_refs=["authority/a.json"])
    result = run(candidates=[action], mode="live", action_adapter=lambda item: {"status": "completed"})
    assert result["disposition"] == "verification_failed"
    assert result["action_executed"] is True
