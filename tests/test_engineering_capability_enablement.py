from __future__ import annotations

import pytest
import shutil
from pathlib import Path

from estate.core.engineering_capability_enablement import CapabilityEnablementLifecycle, CapabilityEvidence
from estate.core.grace_operations_runtime import GraceObjective, GraceOperationsRuntime


def objective(root):
    catalog = Path(__file__).resolve().parents[1] / "config" / "providers" / "catalog.json"
    target = root / "config" / "providers" / "catalog.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(catalog, target)
    item = GraceObjective.create(requested_by="Steward", title="Bounded work", summary="Create a bounded work product.")
    GraceOperationsRuntime(root).conduct_objective(item)
    return item


def available(capability="repository_implementation"):
    return CapabilityEvidence(
        capability_id=capability, worker_id="worker-codex", provider_id="codex.execution.cli",
        adapter_id="codex-cli-execution-adapter", declaration="declared", qualification="qualified",
        health="healthy", availability="available", authorization="authorized",
        evidence_references=["qualification/codex.json", "health/codex.json", "authorization/codex.json"],
    )


def test_available_capability_can_be_registered_and_resumed(tmp_path):
    obj = objective(tmp_path)
    lifecycle = CapabilityEnablementLifecycle(tmp_path)
    inquiry = lifecycle.create_inquiry(objective_id=obj.objective_id, campaign_id="CAMPAIGN-X", package_id="WP-X", requested_outcome="bounded repository artifact", required_capabilities=["repository_implementation"])
    assessment = lifecycle.assess(inquiry["record_id"], [available()])
    assert assessment["overall_disposition"] == "available"
    selection = lifecycle.select_provider(assessment["record_id"], "repository_implementation")
    assert selection["provider_id"] == "codex.execution.cli"
    assert selection["authorization_required"] is True
    proposal = lifecycle._record("creation_proposals", "capprop", {"objective_id": obj.objective_id, "worker_specification_id": "workerspec-existing", "gap_id": "gap-existing", "proposed_by": "Helen", "status": "proposed"})
    dependency = lifecycle.link_enabling_project(proposal_id=proposal["record_id"], enabling_project_id="project-enable-codex", original_objective_id=obj.objective_id, canonical_ptm_dependency_id="ptm-dep-codex")
    registration = lifecycle.record_registration(dependency_id=dependency["record_id"], provider_id="codex.execution.cli", adapter_id="codex-cli-execution-adapter", adapter_version="1.0.0", capability_claims=["repository_implementation"], qualification_evidence=["qualification/codex.json"], health_evidence=["health/codex.json"], authorization_evidence=["authorization/codex.json"], receipt_contract={"schema": "provider_receipt.v1"}, artifact_contract={"schema": "artifact_manifest.v1"})
    result = lifecycle.reevaluate(dependency_id=dependency["record_id"], registration_id=registration["record_id"], evidence=[available()], canonical_dependency_evidence=["ptm/dep-codex/confirmed"])
    assert result["status"] == "passed"
    assert (tmp_path / "runtime/grace_helen_engineering/capability_enablement/resumptions").exists()
    assert GraceOperationsRuntime(tmp_path).status()["available"] is True


@pytest.mark.parametrize("field,expected", [("qualification", "declared_but_unqualified"), ("health", "qualified_but_unhealthy"), ("availability", "healthy_but_unavailable"), ("authorization", "available_but_unauthorized")])
def test_helen_assessment_reports_distinct_non_available_states(tmp_path, field, expected):
    obj = objective(tmp_path)
    lifecycle = CapabilityEnablementLifecycle(tmp_path)
    inquiry = lifecycle.create_inquiry(objective_id=obj.objective_id, campaign_id="CAMPAIGN-X", package_id="WP-X", requested_outcome="bounded artifact", required_capabilities=["repository_implementation"])
    fact = available()
    values = fact.to_dict(); values[field] = {"qualification": "unqualified", "health": "unhealthy", "availability": "unavailable", "authorization": "unauthorized"}[field]
    assessment = lifecycle.assess(inquiry["record_id"], [values])
    assert assessment["capability_dispositions"]["repository_implementation"] == expected


def test_missing_capability_creates_gap_and_blocks(tmp_path):
    obj = objective(tmp_path)
    lifecycle = CapabilityEnablementLifecycle(tmp_path)
    inquiry = lifecycle.create_inquiry(objective_id=obj.objective_id, campaign_id="CAMPAIGN-X", package_id="WP-X", requested_outcome="visual artifact", required_capabilities=["vision_measurement"])
    assessment = lifecycle.assess(inquiry["record_id"], [])
    assert assessment["capability_dispositions"]["vision_measurement"] == "uncertain"
    assert list((tmp_path / "runtime/grace_helen_engineering/capability_enablement/gaps").glob("*.json"))


def test_recursive_bootstrap_is_not_implied_by_registration(tmp_path):
    obj = objective(tmp_path)
    lifecycle = CapabilityEnablementLifecycle(tmp_path)
    inquiry = lifecycle.create_inquiry(objective_id=obj.objective_id, campaign_id="CAMPAIGN-X", package_id="WP-X", requested_outcome="physical measurement", required_capabilities=["vision_measurement"])
    assessment = lifecycle.assess(inquiry["record_id"], [])
    gap = next((tmp_path / "runtime/grace_helen_engineering/capability_enablement/gaps").glob("*.json"))
    spec = lifecycle.create_worker_specification(gap_id=gap.stem, role="vision worker", required_capabilities=["vision_measurement"], qualifications=["calibrated_measurement_test"], technical_expectations=["must preserve uncertainty"], authorization_scope=["local test artifacts"], health_requirements=["fresh local health"], input_contract={"type": "image"}, output_contract={"type": "measurement"}, artifact_contract={"type": "json"}, receipt_contract={"type": "receipt"}, timeout_seconds=60, cancellation="operator_cancel", retry_semantics="bounded", validation_requirements=["known-scale test"], sandbox_boundaries=["authorized worktree"])
    assert spec["implementation_authorized"] is False


def test_declared_capability_without_provider_and_adapter_evidence_is_not_available(tmp_path):
    obj = objective(tmp_path)
    lifecycle = CapabilityEnablementLifecycle(tmp_path)
    inquiry = lifecycle.create_inquiry(objective_id=obj.objective_id, campaign_id="CAMPAIGN-X", package_id="WP-X", requested_outcome="bounded artifact", required_capabilities=["repository_implementation"])
    fact = available().to_dict(); fact["provider_id"] = None; fact["adapter_id"] = None
    assessment = lifecycle.assess(inquiry["record_id"], [fact])
    assert assessment["capability_dispositions"]["repository_implementation"] == "conflicting_evidence"
    with pytest.raises(PermissionError):
        lifecycle.select_provider(assessment["record_id"], "repository_implementation")


def test_local_enablement_record_cannot_resume_without_canonical_ptm_dependency(tmp_path):
    obj = objective(tmp_path)
    lifecycle = CapabilityEnablementLifecycle(tmp_path)
    proposal = lifecycle._record("creation_proposals", "capprop", {"objective_id": obj.objective_id, "worker_specification_id": "workerspec-existing", "gap_id": "gap-existing", "proposed_by": "Helen", "status": "proposed"})
    dependency = lifecycle.link_enabling_project(proposal_id=proposal["record_id"], enabling_project_id="project-enable-codex", original_objective_id=obj.objective_id)
    registration = lifecycle.record_registration(dependency_id=dependency["record_id"], provider_id="codex.execution.cli", adapter_id="codex-cli-execution-adapter", adapter_version="1.0.0", capability_claims=["repository_implementation"], qualification_evidence=["qualification/codex.json"], health_evidence=["health/codex.json"], authorization_evidence=["authorization/codex.json"], receipt_contract={"schema": "provider_receipt.v1"}, artifact_contract={"schema": "artifact_manifest.v1"})
    result = lifecycle.reevaluate(dependency_id=dependency["record_id"], registration_id=registration["record_id"], evidence=[available()])
    assert result["disposition"] == "dependency_not_confirmed"
    assert not list((tmp_path / "runtime/grace_helen_engineering/capability_enablement/resumptions").glob("*.json"))
