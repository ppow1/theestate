import hashlib
import json
from dataclasses import replace

import pytest

from estate.core.governed_local_provider import (
    ProviderAdmissionError,
    SHA256_DESCRIPTOR,
    execute_sha256,
    normalize_task_input,
    validate_admission,
)
from estate.core.grace_momentum_service import GraceMomentumService
from estate.core.wp4232_u1_acceptance import TEST_INPUT, TEST_SHA256, WP4232U1Acceptance


def test_deterministic_adapter_is_local_and_schema_bound():
    assert SHA256_DESCRIPTOR.locality == "in_process"
    assert SHA256_DESCRIPTOR.egress is False
    assert SHA256_DESCRIPTOR.spend is False
    assert SHA256_DESCRIPTOR.mutates_machine_state is False
    assert SHA256_DESCRIPTOR.deterministic is True
    assert execute_sha256(TEST_INPUT)["sha256"] == hashlib.sha256(TEST_INPUT.encode("utf-8")).hexdigest()
    with pytest.raises(ProviderAdmissionError):
        normalize_task_input("x" * 4097)
    with pytest.raises(ProviderAdmissionError):
        normalize_task_input(None)


def test_adapter_admission_rejects_egress_spend_and_unknown_identity():
    admission = {"adapter_id": SHA256_DESCRIPTOR.adapter_id, "adapter_version": SHA256_DESCRIPTOR.version,
                 "capability": SHA256_DESCRIPTOR.capability, "admitting_authority": "Engineering",
                 "authority_source": "test", "locality_assertion": "in_process", "no_egress_assertion": True,
                 "no_spend_assertion": True, "deterministic_effect_assertion": True,
                 "input_schema": SHA256_DESCRIPTOR.input_schema, "output_schema": SHA256_DESCRIPTOR.output_schema,
                 "effect_identity_policy": "test", "stop_capable": True, "rollback_capable": True}
    validate_admission(SHA256_DESCRIPTOR, admission)
    for field in ("no_egress_assertion", "no_spend_assertion", "deterministic_effect_assertion"):
        invalid = {**admission, field: False}
        with pytest.raises(ProviderAdmissionError):
            validate_admission(SHA256_DESCRIPTOR, invalid)
    with pytest.raises(ProviderAdmissionError):
        validate_admission(replace(SHA256_DESCRIPTOR, version="attacker"), admission)


def test_governed_readiness_fails_closed_before_admission(tmp_path):
    readiness = GraceMomentumService(tmp_path, mode="governed_local_test").readiness()
    assert readiness["ready"] is False
    assert readiness["provider_effects_enabled"] is False


def test_u1_real_runtime_lifecycle_and_recovery_evidence(tmp_path):
    report = WP4232U1Acceptance(tmp_path / "evidence").run()
    assert report["final_wp4232_bounded_live_executed"] is False
    assert report["missing_required_events"] == []
    assert report["readiness"]["ready"] is True
    assert report["exactly_once"]["duplicate_same_response"] is True
    assert report["exactly_once"]["event_count_unchanged"] is True
    assert report["exactly_once"]["duplicate_after_restart"] is True
    assert report["stop"]["blocked"] is True
    assert report["rollback"]["completed_effect_identity_preserved"] is True
    assert report["dual_surface"]["openwebui_kind"] == "refresh"
    assert report["dual_surface"]["estate_available"] is True
    assert (tmp_path / "evidence" / "acceptance_evidence.json").exists()


def test_u1_evidence_contains_contract_lifecycle(tmp_path):
    root = tmp_path / "evidence"
    WP4232U1Acceptance(root).run()
    data = json.loads((root / "acceptance_evidence.json").read_text(encoding="utf-8"))
    assert data["event_evidence"]["event_types"][-1] == "objective.completed"
    assert data["lifecycle"]["executed"]["record"]["output"]["sha256"] == TEST_SHA256
