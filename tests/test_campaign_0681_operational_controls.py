from estate.core.runtime_recovery import evaluate_operational_control

NOW = "2026-07-18T12:00:00Z"


def request(action, state, roles, **extra):
    value = dict(
        work_id="WP-X", current_state=state, action=action, actor_id="employee-1",
        actor_roles=roles, reason_code="operator_requested",
        evidence_reference="collaboration/evidence/control.json", requested_at=NOW,
    )
    value.update(extra)
    return evaluate_operational_control(**value)


def checkpoint(at="2026-07-18T11:55:00Z", **extra):
    value = {"reference": "runtime/checkpoints/WP-X.json", "checkpointed_at": at, "freshness_seconds": 3600, "checksum_valid": True}
    value.update(extra)
    return value


def test_pause_is_attributable_and_does_not_dispatch_or_mutate():
    result = request("pause", "active", ["Operations Manager"])
    assert result["allowed"] is True
    assert result["planned_state"] == "paused"
    assert result["creates_dispatch"] is False
    assert result["mutates_state"] is False
    assert result["audit_event"]["actor_id"] == "employee-1"


def test_resume_requires_authority_and_current_checkpoint():
    allowed = request("resume", "paused", ["Work Owner"], checkpoint=checkpoint())
    refused = request("resume", "paused", ["Observer"], checkpoint=checkpoint("2026-07-16T00:00:00Z"))
    assert allowed["allowed"] is True
    assert allowed["planned_state"] == "queued"
    assert refused["allowed"] is False
    assert {"resume requires one of: Operations Manager, Work Owner", "recovery checkpoint is stale"} <= set(refused["refusal_reasons"])


def test_retry_budget_cooldown_and_duplicate_prevent_unbounded_work():
    exhausted = request("retry", "failed", ["Traffic Controller"], reason_code="validation_failure", failure_count=2, retry_budget=2, idempotency_key="retry-3")
    cooling = request("retry", "failed", ["Traffic Controller"], reason_code="validation_failure", failure_count=1, retry_budget=2, idempotency_key="retry-2", last_attempt_at="2026-07-18T11:59:00Z")
    duplicate = request("retry", "failed", ["Traffic Controller"], reason_code="validation_failure", idempotency_key="retry-1", prior_idempotency_keys=["retry-1"])
    assert "bounded retry budget exhausted" in exhausted["refusal_reasons"]
    assert "retry cooldown has not elapsed" in cooling["refusal_reasons"]
    assert "duplicate retry idempotency key" in duplicate["refusal_reasons"]


def test_recovery_preserves_checkpoint_and_returns_to_paused_review():
    result = request("recover", "interrupted", ["Recovery Operator"], reason_code="interrupted_execution", checkpoint=checkpoint())
    assert result["allowed"] is True
    assert result["planned_state"] == "paused"
    assert result["checkpoint_reference"] == "runtime/checkpoints/WP-X.json"
    assert "Preserve prior evidence" in result["rollback_contract"]


def test_protected_blocker_and_abandonment_authority_fail_closed():
    blocked = request("resume", "paused", ["Operations Manager"], checkpoint=checkpoint(), blocker_type="acceptance")
    refused = request("abandon", "failed", ["Operations Manager"], reason_code="protected_abandonment")
    allowed = request("abandon", "failed", ["Chief Architect"], reason_code="protected_abandonment")
    assert blocked["allowed"] is False
    assert refused["allowed"] is False
    assert allowed["allowed"] is True
    assert allowed["authorizes_acceptance"] is False


def test_invalid_transition_and_missing_provenance_are_refused():
    result = request("resume", "active", ["Work Owner"], checkpoint=checkpoint(), actor_id="", evidence_reference="", reason_code="made_up")
    assert result["allowed"] is False
    assert result["planned_state"] == "active"
    assert len(result["refusal_reasons"]) >= 3
