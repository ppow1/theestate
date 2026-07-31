from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker

from estate.core.execution_provider_adapter import ExecutionProviderAdapterResult, utc_now
from estate.core.execution_dispatch import load_dispatch_queue
from estate.core.grace_helen_engineering_composition import GraceHelenEngineeringComposition
from estate.core.grace_operations_runtime import GraceObjective, GraceOperationsRuntime
from estate.core.ptm_production_readiness import append_ptm_event
from estate.core.ptm_readiness_integration import PtmReadinessGateError, PtmCapabilityDependencyResolver, revalidate_readiness
from estate.core.engineering_capability_enablement import CapabilityEnablementLifecycle


ROOT = Path(__file__).parents[1]


def _copy_ptm_authority(root: Path) -> None:
    for name in ("readiness_freshness_policy.json", "waiver_authorities.json"):
        target = root / "config/ptm" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / "config/ptm" / name, target)
    for name in ("readiness_freshness_policy_v1.schema.json", "waiver_authorities_v1.schema.json", "readiness_resolution_v1.schema.json", "event_v1.schema.json"):
        target = root / "schemas/ptm" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / "schemas/ptm" / name, target)


def _ptm_ready(root: Path, objective_id: str, *, task_id: str | None = None, marker: str = "accepted", dependency_state: str = "satisfied", gate_state: str = "pass") -> dict:
    _copy_ptm_authority(root)
    task_id = task_id or f"task-{objective_id}"
    source = root / "ptm-evidence.json"
    source.write_text(json.dumps({"accepted": True, "marker": marker}) + "\n", encoding="utf-8")
    source_ref = {"source_path": source.name, "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(), "adapter_name": "fixture", "adapter_version": "1"}
    observed = utc_now()
    return append_ptm_event(root, event_type="task.readiness_inputs", aggregate_type="task", aggregate_id=task_id, stream_id=f"task:{task_id}", actor_ref="fixture-ptm", authority_refs=["PTM"], source_refs=[source_ref], payload_schema="estate.ptm.readiness-input.v1", payload={"objective_id": objective_id, "task_id": task_id, "enabling_project_id": "project-test", "dependencies": [{"dependency_id": "dep-test", "state": dependency_state, "observed_at": observed}], "gate_checks": [{"name": "dependency_gate", "state": gate_state, "observed_at": observed}], "source_references": [source_ref]}, idempotency_key=f"fixture:{objective_id}:{task_id}:{marker}", occurred_at=observed)


def _context(root: Path):
    objective = GraceObjective.create(requested_by="Steward", title="Bounded integration", summary="Create one bounded integration artifact.")
    GraceOperationsRuntime(root).conduct_objective(objective)
    comp = GraceHelenEngineeringComposition(root)
    inquiry = comp.request_capability(objective.objective_id, "fixture_capability")
    determination = comp.determine_capability(inquiry["capability_request_id"], disposition="qualified_and_available", worker_profile_id="fixture-worker", qualification_evidence=["qualification/fixture.json"], availability_evidence=["availability/fixture.json"])
    return objective, comp, determination


def _commission(root: Path):
    objective, comp, determination = _context(root)
    event = _ptm_ready(root, objective.objective_id)
    commission = comp.commission_engineering(objective.objective_id, determination["determination_id"], grace_action_id="grace-action", operations_decision_id="operations-decision", bounded_objective=objective.summary, acceptance_criteria=["bounded artifact validated"], ptm_source_high_watermark=event["event_id"], ptm_task_or_package_id=f"task-{objective.objective_id}", enabling_project_id="project-test")
    return objective, comp, commission, event


def test_ready_ptm_gates_commission_and_dispatch_and_completion(tmp_path):
    objective, comp, commission, event = _commission(tmp_path)
    assert commission["readiness_state"] == "ready"
    assert commission["source_high_watermark"] == event["event_id"]
    accepted = comp.accept_commission(commission["commission_id"])
    auth, dispatch = comp.authorize_dispatch(accepted["commission_id"], provider_id="fixture-provider", provider_type="fixture", adapter_reference="fixture.adapter@1")
    assert dispatch["provider_metadata"]["ptm_revalidation_result"] == "passed"
    assert dispatch["provider_metadata"]["ptm_readiness"]["readiness_resolution_id"] == commission["readiness_resolution_id"]
    result = ExecutionProviderAdapterResult(adapter_request_id="fixture-request", dispatch_id=auth["dispatch_id"], provider_id="fixture-provider", status="completed", started_at=utc_now(), finished_at=utc_now(), artifacts=["artifacts/bounded.txt"], validation_status="passed", metadata={"provider_receipt": "runtime/fixture-receipt.json", "live_provider_called": False})
    completion = comp.reconcile_validate_complete(auth["authorization_id"], result, validation_passed=True)
    assert completion["ptm_readiness_resolution_id"] == commission["readiness_resolution_id"]
    completion_schema = json.loads((ROOT / "schemas/engineering/completion_evidence_chain_v1.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator(completion_schema, format_checker=FormatChecker()).validate({"commission_id": completion["engineering_commission_id"], "dispatch_id": completion["dispatch_id"], "ptm_readiness_resolution_id": completion["ptm_readiness_resolution_id"], "ptm_readiness_projection_digest": completion["ptm_readiness_projection_digest"], "provider_execution_receipt": completion["provider_execution_receipt"], "artifact_references": completion["artifact_references"], "validation_evidence": completion["validation_evidence"], "reconciliation_outcome": completion["reconciliation_outcome"]})
    receipt = comp.receive_completion(completion["completion_id"], objective.objective_id)
    assert receipt["institutional_acceptance_state"] == "not_granted"
    assert comp.objective_state(objective.objective_id)["state"] == "completed"
    assert len(load_dispatch_queue(tmp_path)) == 1


def test_missing_or_non_ready_ptm_never_creates_commission(tmp_path):
    objective, comp, determination = _context(tmp_path)
    with pytest.raises(PermissionError, match="PTM readiness"):
        comp.commission_engineering(objective.objective_id, determination["determination_id"], grace_action_id="grace-action", operations_decision_id="operations-decision", bounded_objective=objective.summary, acceptance_criteria=["bounded artifact"], ptm_source_high_watermark="missing", ptm_task_or_package_id=f"task-{objective.objective_id}", enabling_project_id="project-test")
    assert not list((tmp_path / "runtime/grace_helen_engineering/engineering_commissions").glob("*.json"))


@pytest.mark.parametrize(("dependency_state", "gate_state"), [("unknown", "pass"), ("unsatisfied", "pass"), ("satisfied", "fail")])
def test_unknown_not_ready_and_blocked_ptm_states_never_create_commission(tmp_path, dependency_state, gate_state):
    objective, comp, determination = _context(tmp_path)
    event = _ptm_ready(tmp_path, objective.objective_id, dependency_state=dependency_state, gate_state=gate_state, marker=dependency_state + gate_state)
    with pytest.raises(PermissionError, match="PTM readiness"):
        comp.commission_engineering(objective.objective_id, determination["determination_id"], grace_action_id="grace-action", operations_decision_id="operations-decision", bounded_objective=objective.summary, acceptance_criteria=["bounded artifact"], ptm_source_high_watermark=event["event_id"], ptm_task_or_package_id=f"task-{objective.objective_id}", enabling_project_id="project-test")
    assert not list((tmp_path / "runtime/grace_helen_engineering/engineering_commissions").glob("*.json"))


def test_dispatch_revalidates_changed_high_watermark_before_queue_insertion(tmp_path):
    objective, comp, commission, _ = _commission(tmp_path)
    accepted = comp.accept_commission(commission["commission_id"])
    _ptm_ready(tmp_path, objective.objective_id, task_id=f"task-{objective.objective_id}", marker="changed")
    with pytest.raises(PermissionError, match="high-watermark"):
        comp.authorize_dispatch(accepted["commission_id"], provider_id="fixture-provider", provider_type="fixture", adapter_reference="fixture.adapter@1")
    assert not (tmp_path / "runtime/execution_dispatch/queue.json").exists()
    rejections = list((tmp_path / "runtime/grace_helen_engineering/dispatch_rejections").glob("*.json"))
    assert len(rejections) == 1
    rejection = json.loads(rejections[0].read_text(encoding="utf-8"))
    assert rejection["institutional_acceptance_state"] == "not_granted"
    rejection_schema = json.loads((ROOT / "schemas/dispatch/rejection_v1.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator(rejection_schema, format_checker=FormatChecker()).validate(rejection)


def test_policy_drift_rejects_dispatch_without_provider_invocation(tmp_path):
    objective, comp, commission, _ = _commission(tmp_path)
    accepted = comp.accept_commission(commission["commission_id"])
    policy_path = tmp_path / "config/ptm/readiness_freshness_policy.json"
    policy = json.loads(policy_path.read_text(encoding="utf-8")); policy["policy_version"] = "2.0.0"; policy_path.write_text(json.dumps(policy), encoding="utf-8")
    with pytest.raises(PermissionError, match="policy"):
        comp.authorize_dispatch(accepted["commission_id"], provider_id="fixture-provider", provider_type="fixture", adapter_reference="fixture.adapter@1")
    assert not (tmp_path / "runtime/execution_dispatch/queue.json").exists()


def test_repeated_equivalent_commission_is_idempotent(tmp_path):
    objective, comp, determination = _context(tmp_path)
    event = _ptm_ready(tmp_path, objective.objective_id)
    kwargs = {"grace_action_id": "grace-action", "operations_decision_id": "operations-decision", "bounded_objective": objective.summary, "acceptance_criteria": ["bounded artifact"], "ptm_source_high_watermark": event["event_id"], "ptm_task_or_package_id": f"task-{objective.objective_id}", "enabling_project_id": "project-test", "idempotency_key": "commission-replay-1"}
    first = comp.commission_engineering(objective.objective_id, determination["determination_id"], **kwargs)
    second = comp.commission_engineering(objective.objective_id, determination["determination_id"], **kwargs)
    assert first == second
    assert len(list((tmp_path / "runtime/grace_helen_engineering/engineering_commissions").glob("*.json"))) == 1


def test_new_authority_schemas_are_closed_and_validate_binding(tmp_path):
    _, comp, commission, _ = _commission(tmp_path)
    binding = commission["ptm_readiness"]
    for relative in ("schemas/engineering/commission_ptm_evidence_v1.schema.json", "schemas/dispatch/readiness_evidence_v1.schema.json"):
        schema = json.loads((ROOT / relative).read_text(encoding="utf-8")); Draft202012Validator.check_schema(schema)
        candidate = binding | {"engineering_commission_id": commission["commission_id"], "revalidated_at": utc_now(), "revalidation_result": "passed"}
        candidate = {key: value for key, value in candidate.items() if key in schema["properties"]}
        Draft202012Validator(schema, format_checker=FormatChecker()).validate(candidate)
    assert "provider" not in binding


def test_production_capability_enablement_uses_ptm_adapter_and_fails_closed_without_resolution(tmp_path):
    lifecycle = CapabilityEnablementLifecycle(tmp_path)
    assert isinstance(lifecycle.canonical_dependency_resolver, PtmCapabilityDependencyResolver)
    assert lifecycle.canonical_dependency_resolver("missing-dependency") is None
