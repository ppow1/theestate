from copy import deepcopy
from datetime import datetime, timezone

import pytest

from estate.core.health_signal_integration import (
    adapt_resident_health,
    adapt_service_health,
    adapt_validation_health,
    adapt_worker_heartbeat,
    aggregate_health,
    normalize_health_evidence,
    reconcile_health_signals,
    unknown_signal,
)

NOW = "2026-07-17T12:00:00Z"


def evidence(state="healthy", **overrides):
    item = {
        "subject_type": "service", "subject_id": "svc-a", "health_domain": "service",
        "state": state, "source_timestamp": "2026-07-17T11:55:00Z", "ttl_seconds": 600,
        "source_kind": "canonical_registry", "evidence_references": ["runtime/services/registry.json"],
    }
    item.update(overrides)
    return item


def test_contract_is_deterministic_complete_and_observation_only():
    source = evidence(campaign_impact={"campaign_id": "CAMPAIGN-0681"})
    before = deepcopy(source)
    first = normalize_health_evidence(source, observed_at=NOW)
    second = normalize_health_evidence(source, observed_at=NOW)
    assert first == second
    assert source == before
    assert first["normalized_state"] == "healthy"
    assert first["freshness"] == "current"
    assert first["canonical_evidence_references"]
    assert first["responsible_lane"] and first["reevaluation_trigger"]
    assert first["progression_effect"] == "observation_only"
    assert first["authorizes_action"] is False


@pytest.mark.parametrize("state,expected", [
    ("degraded", "degraded"), ("offline", "unavailable"), ("failed", "failed"),
    ("nonsense", "unknown"), ("paused", "unavailable"),
])
def test_explicit_states_are_normalized(state, expected):
    assert normalize_health_evidence(evidence(state), observed_at=NOW)["normalized_state"] == expected


def test_missing_evidence_is_unknown_not_healthy():
    signal = unknown_signal("resident", "grace", "resident", observed_at=NOW, required_dependency=True)
    assert signal["normalized_state"] == "unknown"
    assert signal["progression_effect"] == "blocks_progression"
    assert "missing" in " ".join(signal["uncertainty_or_contradiction_warnings"])


def test_stale_evidence_cannot_be_current_health():
    signal = normalize_health_evidence(evidence(source_timestamp="2026-07-17T10:00:00Z"), observed_at=NOW)
    assert signal["normalized_state"] == "stale"
    assert signal["freshness"] == "stale"
    assert signal["reported_state"] == "healthy"


def test_equal_authority_contradiction_fails_closed():
    result = reconcile_health_signals([evidence("healthy"), evidence("failed", evidence_references=["operations/services/failure.md"])], observed_at=NOW)
    assert result["normalized_state"] == "contradictory"
    assert result["progression_effect"] == "blocks_progression"
    assert result["derivation_rule"] == "equal-precedence-opposing-current-evidence-fail-closed"
    assert len(result["canonical_evidence_references"]) == 2


def test_repository_evidence_outranks_runtime_claim():
    durable = evidence("failed", source_kind="repository_authoritative")
    runtime = evidence("healthy", source_kind="runtime_heartbeat", evidence_references=["runtime/heartbeat.json"])
    result = reconcile_health_signals([runtime, durable], observed_at=NOW)
    assert result["normalized_state"] == "failed"
    assert result["source_kind"] == "repository_authoritative"


def test_recovery_requires_explicit_clearance():
    failure = evidence("failed", source_timestamp="2026-07-17T11:40:00Z", evidence_references=["failure-1"])
    optimistic = evidence("healthy", source_timestamp="2026-07-17T11:59:00Z", evidence_references=["recovery-1"])
    uncleared = reconcile_health_signals([failure, optimistic], observed_at=NOW)
    assert uncleared["normalized_state"] == "degraded"
    optimistic["recovery_clears"] = ["failure-1"]
    recovered = reconcile_health_signals([failure, optimistic], observed_at=NOW)
    assert recovered["normalized_state"] == "healthy"


def test_resident_adapter_uses_lifecycle_not_conversation_and_preserves_input():
    record = {"resident_id": "grace", "status": "stand_down", "updated_at": "2026-07-17T11:59:00Z"}
    before = deepcopy(record)
    signal = adapt_resident_health(record, source_path="runtime/residents/lifecycle/grace.json", observed_at=NOW, interaction={"responsive": True})
    assert signal["normalized_state"] == "unavailable"
    assert "does not prove readiness" in " ".join(signal["uncertainty_or_contradiction_warnings"])
    assert signal["progression_effect"] == "requires_protected_review"
    assert record == before


def test_service_dependency_degradation_is_not_hidden():
    entry = {"service_id": "api", "health_status": "healthy", "last_known_update": "2026-07-17T11:59:00Z", "owner": "Engineering", "dependency_health": {"summary": "failed"}}
    signal = adapt_service_health(entry, source_path="runtime/services/service_health_registry.json", observed_at=NOW, required_dependency=True)
    assert signal["normalized_state"] == "failed"
    aggregate = aggregate_health([normalize_health_evidence(evidence(), observed_at=NOW), signal], campaign_id="CAMPAIGN-0681", work_package_id="WP-0692")
    assert aggregate["overall_state"] == "failed"
    assert aggregate["progression_effect"] == "blocks_progression"
    assert aggregate["blocker_facts"][0]["authorizes_action"] is False


def test_partial_domains_remain_separate_and_machine_readable():
    heartbeat = adapt_worker_heartbeat({"worker_id": "codex-1", "status": "active", "last_heartbeat": "2026-07-17T11:59:00Z"}, source_path="runtime/workers/heartbeats/codex-1.json", observed_at=NOW)
    validation = adapt_validation_health({"work_package_id": "WP-0691", "status": "failed", "completed_at": "2026-07-17T11:59:30Z"}, source_path="runtime/validation/work_packages/WP-0691.json", observed_at=NOW)
    result = aggregate_health([heartbeat, validation])
    assert {s["health_domain"] for s in result["signals"]} == {"runtime", "validation"}
    assert result["overall_state"] == "failed"
    assert result["observation_only"] is True


def test_invalid_domain_or_mixed_subject_reconciliation_is_rejected():
    with pytest.raises(ValueError):
        normalize_health_evidence({"subject_id": "x", "health_domain": "invented"}, observed_at=NOW)
    a = normalize_health_evidence(evidence(), observed_at=NOW)
    b = normalize_health_evidence(evidence(subject_id="svc-b"), observed_at=NOW)
    with pytest.raises(ValueError):
        reconcile_health_signals([a, b], observed_at=NOW)


def test_observation_does_not_mutate_canonical_records():
    records = [
        normalize_health_evidence(evidence(), observed_at=NOW),
        adapt_worker_heartbeat({"worker_id": "worker", "status": "blocked", "last_heartbeat": "2026-07-17T11:59:00Z"}, source_path="runtime/workers/heartbeats/worker.json", observed_at=NOW),
    ]
    before = deepcopy(records)
    aggregate_health(records, campaign_id="CAMPAIGN-0681")
    assert records == before
