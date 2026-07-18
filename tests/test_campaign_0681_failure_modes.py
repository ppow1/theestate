import json

from estate.core.alfred_runtime import evaluate_operational_route
from estate.core.continuous_momentum_engine import run_momentum_cycle
from estate.core.operational_guardrails import evaluate_guardrails
from estate.core.readiness_evidence_projection import project_readiness_evidence
from estate.core.runtime_recovery import RuntimePersistenceStore, evaluate_operational_control
from estate.core.runtime_replay import RuntimeReplayEngine
from estate.core.steward_dashboard import build_operational_visibility

NOW = "2026-07-18T12:00:00Z"


def candidate():
    return {"action_id": "advance", "permission": "preauthorized", "priority": 10, "idempotency_key": "advance-1", "source_refs": ["evidence/action.json"], "canonical_mechanism": "execution_dispatch", "authority_refs": ["authority/delegation.json"]}


def projection(state):
    return {"state": state, "authorizes_action": False, "evidence_references": [f"evidence/{state}.json"], "warnings": []}


def test_degraded_failed_blocked_and_stale_dependencies_safe_idle_without_adapter_call():
    for state in ("degraded", "failed", "blocked", "stale"):
        called = []
        result = run_momentum_cycle(cycle_id=f"cycle-{state}", observed_at=NOW, inputs={"service": projection(state)}, candidates=[candidate()], mode="live", action_adapter=lambda item: called.append(item) or {"evidence_reference": "result.json"})
        assert result["action_executed"] is False
        assert result["disposition"] in {"safe_idle", "escalate"}
        assert called == []
        assert result["holds"]


def test_missing_and_conflicting_validation_cannot_produce_readiness_or_acceptance():
    evidence = [
        {"subject_id": "WP-X", "evidence_id": "pass", "state": "ready", "source_kind": "validation_result", "reference": "validation/pass.json", "issued_at": NOW},
        {"subject_id": "WP-X", "evidence_id": "fail", "state": "rejected", "source_kind": "validation_result", "reference": "validation/fail.json", "issued_at": NOW},
    ]
    result = project_readiness_evidence(evidence, subjects=["WP-MISSING"], observed_at=NOW)
    states = {item["subject_id"]: item["readiness_state"] for item in result["subjects"]}
    assert states == {"WP-MISSING": "unverified", "WP-X": "indeterminate"}
    assert result["aggregate_readiness"] == "indeterminate"


def test_conflicting_authority_and_unauthorized_policy_request_escalate():
    proposal = {"action_id": "deploy", "action_class": "mechanical_action", "authority_scope": "deployment", "target_mechanism": "deployment", "source_refs": ["request.json"], "permission": "protected", "protected_surfaces": ["deployment"]}
    rules = [
        {"rule_id": "allow", "disposition": "allow", "policy_kind": "office", "authority_source": "office/a.md", "decision_owner": "Office", "effective_from": "2026-07-18T00:00:00Z", "scope": {"action_class": "mechanical_action"}},
        {"rule_id": "deny", "disposition": "deny", "policy_kind": "office", "authority_source": "office/b.md", "decision_owner": "Steward", "effective_from": "2026-07-18T00:00:00Z", "scope": {"action_class": "mechanical_action"}},
    ]
    result = evaluate_guardrails(proposal, rules, evaluated_at=NOW)
    assert result["disposition"] == "escalate"
    assert result["action_may_proceed_to_existing_authorization_lane"] is False


def test_retry_exhaustion_and_protected_blocker_create_bounded_hold():
    result = evaluate_operational_control(work_id="WP-X", current_state="failed", action="retry", actor_id="tc", actor_roles=["Traffic Controller"], reason_code="retry_exhausted", evidence_reference="failure.json", requested_at=NOW, failure_count=2, retry_budget=2, cooldown_seconds=0, idempotency_key="retry-3", blocker_type="acceptance")
    assert result["allowed"] is False
    assert "bounded retry budget exhausted" in result["refusal_reasons"]
    assert any("acceptance blocker" in reason for reason in result["refusal_reasons"])
    assert result["creates_dispatch"] is False


def test_interrupted_checkpoint_replay_skips_completed_side_effect(tmp_path):
    store = RuntimePersistenceStore(tmp_path)
    store.persist_checkpoint(cycle_id="pilot", cycle_state="running", completed_side_effects=["message-1"], last_durable_event_position=0, campaign_state={"phase": "interrupted"})
    store.append_event("campaign_state_updated", {"campaign_state": {"phase": "recovered"}, "side_effect_id": "message-1"})
    store.append_event("campaign_state_updated", {"campaign_state": {"phase": "resume_review"}, "side_effect_id": "state-2"})
    result = RuntimeReplayEngine(tmp_path).replay_from_checkpoint("pilot")
    assert result["skipped_completed_side_effects"] == ["message-1"]
    assert result["reconstructed_state"]["campaign_state"] == {"phase": "resume_review"}


def test_stale_mailbox_route_is_refused_without_write(tmp_path):
    message = {"schema_version": "estate.repository-message.v1", "id": "msg-stale", "message_type": "notification", "source": "grace", "destination": "alfred", "created_at": "2026-07-16T00:00:00Z", "classification": "Estate Internal", "payload": {"title": "Stale message", "summary": "stale"}, "operational_context": {"authorizes_action": False}}
    result = evaluate_operational_route(message, root=tmp_path, now=NOW)
    assert result["routable"] is False
    assert not (tmp_path / "collaboration/messages/msg-stale.json").exists()


def test_dashboard_exposes_degradation_and_redacts_restricted_details():
    signals = [{"signal_id": "svc", "domain": "service", "title": "Restricted service", "summary": "failure details", "state": "degraded", "freshness": "current", "confidence": "high", "observed_at": NOW, "owner": "Service Owner", "classification": "Restricted", "evidence_references": ["health/service.json"], "warnings": ["dependency unavailable"]}]
    result = build_operational_visibility(signals, viewer={"role": "steward", "identity_evidence": ["personnel.json"], "allowed_classifications": ["Estate Internal"]}, generated_at=NOW)
    item = result["highest_priority_constraints"][0]
    assert item["state"] == "degraded"
    assert item["redacted"] is True
    assert item["evidence_references"] == ["health/service.json"]
