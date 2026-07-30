from __future__ import annotations

import pytest

from estate.core.execution_dispatch import DispatchRequest, enqueue_dispatch_request, load_dispatch_queue
from estate.core.execution_provider_adapter import ExecutionProviderAdapterResult, utc_now
from estate.core.grace_helen_engineering_composition import GraceHelenEngineeringComposition
from estate.core.grace_operations_runtime import GraceObjective, GraceOperationsRuntime


def _objective(root):
    objective = GraceObjective.create(requested_by="Steward", title="CAD drawings", summary="Create CAD drawings for Project 7 Chicken.")
    GraceOperationsRuntime(root).conduct_objective(objective)
    return objective


def _available(comp, objective):
    req = comp.request_capability(objective.objective_id, "cad_worker")
    return comp.determine_capability(req["capability_request_id"], disposition="qualified_and_available", worker_profile_id="worker-profile-cad", qualification_evidence=["qualification/cad.json"], availability_evidence=["availability/cad.json"])


def _commission(comp, objective, determination):
    commission = comp.commission_engineering(objective.objective_id, determination["determination_id"], grace_action_id="grace-act-test", operations_decision_id="ops-dec-test", bounded_objective=objective.summary, acceptance_criteria=["one validated drawing"])
    return comp.accept_commission(commission["commission_id"])


def test_fixture_normal_flow_preserves_authority_and_returns_to_grace(tmp_path):
    objective = _objective(tmp_path); comp = GraceHelenEngineeringComposition(tmp_path)
    determination = _available(comp, objective); commission = _commission(comp, objective, determination)
    auth, dispatch = comp.authorize_dispatch(commission["commission_id"], provider_id="fixture-cad-provider", provider_type="fixture", adapter_reference="tests.fixture")
    assert dispatch["requested_by"] == "Engineering"
    assert dispatch["provider_metadata"]["technical_execution"] is True
    result = ExecutionProviderAdapterResult(adapter_request_id="adapter-fixture", dispatch_id=auth["dispatch_id"], provider_id="fixture-cad-provider", status="completed", started_at=utc_now(), finished_at=utc_now(), summary="fixture worker finished", artifacts=["artifacts/project7.dwg"], validation_status="passed", metadata={"live_provider_called": False, "provider_receipt": "receipt://fixture/project7"})
    completion = comp.reconcile_validate_complete(auth["authorization_id"], result, validation_passed=True)
    receipt = comp.receive_completion(completion["completion_id"], objective.objective_id)
    assert receipt["objective_transition_applied"] == "completed"
    assert comp.objective_state(objective.objective_id)["state"] == "completed"
    assert len(load_dispatch_queue(tmp_path)) == 1
    assert not list(tmp_path.glob("**/*alfred*"))
    assert not list(tmp_path.glob("**/*steward*"))


def test_absent_capability_blocks_objective_and_creates_one_prerequisite(tmp_path):
    objective = _objective(tmp_path); comp = GraceHelenEngineeringComposition(tmp_path)
    req = comp.request_capability(objective.objective_id, "cad_worker")
    comp.determine_capability(req["capability_request_id"], disposition="capability_absent", reason="No qualified worker profile.")
    assert comp.objective_state(objective.objective_id)["state"] == "blocked_pending_capability"
    assert len(list((tmp_path / "runtime/grace_helen_engineering/capability_development").glob("*.json"))) == 1
    assert not (tmp_path / "runtime/execution_dispatch/queue.json").exists()


def test_unavailable_is_not_absent_and_does_not_create_development(tmp_path):
    objective = _objective(tmp_path); comp = GraceHelenEngineeringComposition(tmp_path)
    req = comp.request_capability(objective.objective_id, "cad_worker")
    comp.determine_capability(req["capability_request_id"], disposition="qualified_but_unavailable", worker_profile_id="worker-profile-cad", reason="Worker reserved.")
    assert comp.objective_state(objective.objective_id)["state"] == "blocked_pending_capability"
    assert not (tmp_path / "runtime/grace_helen_engineering/capability_development").exists()


def test_grace_cannot_bypass_engineering_for_technical_dispatch(tmp_path):
    objective = GraceObjective.create(requested_by="Steward", title="Technical", summary="Technical work.", metadata={"requires_engineering": True})
    with pytest.raises(PermissionError, match="Engineering"):
        GraceOperationsRuntime(tmp_path).conduct_objective(objective, request_dispatch=True)


def test_dispatch_rejects_technical_request_without_engineering_authorization(tmp_path):
    request = DispatchRequest(title="bad", classification="Estate Internal", provider_metadata={"technical_execution": True})
    with pytest.raises(ValueError, match="engineering_commission_id"):
        enqueue_dispatch_request(request, tmp_path)


def test_mismatches_validation_failure_and_duplicate_receipt_fail_closed_or_idempotent(tmp_path):
    objective = _objective(tmp_path); comp = GraceHelenEngineeringComposition(tmp_path)
    determination = _available(comp, objective); commission = _commission(comp, objective, determination)
    auth, _ = comp.authorize_dispatch(commission["commission_id"], provider_id="fixture-cad-provider", provider_type="fixture", adapter_reference="tests.fixture")
    bad = ExecutionProviderAdapterResult(adapter_request_id="bad", dispatch_id="dispatch-other", provider_id="fixture-cad-provider", status="completed", started_at=utc_now(), artifacts=["bad.dwg"])
    with pytest.raises(ValueError, match="unrelated"):
        comp.reconcile_validate_complete(auth["authorization_id"], bad, validation_passed=True)
    good = ExecutionProviderAdapterResult(adapter_request_id="good", dispatch_id=auth["dispatch_id"], provider_id="fixture-cad-provider", status="completed", started_at=utc_now(), artifacts=["good.dwg"], validation_status="passed", metadata={"provider_receipt": "receipt://fixture/good"})
    with pytest.raises(ValueError, match="validation failed"):
        comp.reconcile_validate_complete(auth["authorization_id"], good, validation_passed=False)
    completion = comp.reconcile_validate_complete(auth["authorization_id"], good, validation_passed=True)
    first = comp.receive_completion(completion["completion_id"], objective.objective_id)
    assert comp.receive_completion(completion["completion_id"], objective.objective_id) == first
    with pytest.raises(ValueError, match="does not belong"):
        comp.receive_completion(completion["completion_id"], "grace-obj-unrelated")


def test_completion_requires_artifact_and_provider_receipt(tmp_path):
    objective = _objective(tmp_path); comp = GraceHelenEngineeringComposition(tmp_path)
    determination = _available(comp, objective); commission = _commission(comp, objective, determination)
    auth, _ = comp.authorize_dispatch(commission["commission_id"], provider_id="fixture-cad-provider", provider_type="fixture", adapter_reference="tests.fixture")
    no_artifact = ExecutionProviderAdapterResult(adapter_request_id="no-artifact", dispatch_id=auth["dispatch_id"], provider_id="fixture-cad-provider", status="completed", started_at=utc_now(), validation_status="passed", metadata={"provider_receipt": "receipt://fixture/no-artifact"})
    with pytest.raises(ValueError, match="artifact"):
        comp.reconcile_validate_complete(auth["authorization_id"], no_artifact, validation_passed=True)
    no_receipt = ExecutionProviderAdapterResult(adapter_request_id="no-receipt", dispatch_id=auth["dispatch_id"], provider_id="fixture-cad-provider", status="completed", started_at=utc_now(), artifacts=["artifact.dwg"], validation_status="passed")
    with pytest.raises(ValueError, match="receipt"):
        comp.reconcile_validate_complete(auth["authorization_id"], no_receipt, validation_passed=True)
