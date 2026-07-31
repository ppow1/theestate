from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

from estate.core.execution_adapter_handoff_runtime import run_handoff_adapter, validate_handoff
from estate.core.execution_adapter_handoff_runtime import run_registered_handoff_adapter
from estate.core.execution_provider_adapter import ExecutionProviderAdapterRequest
import estate.core.execution_provider_adapter_runtime as adapter_runtime
from estate.core.execution_provider_adapter import ExecutionProviderAdapterResult, utc_now
from estate.core.grace_helen_engineering_composition import GraceHelenEngineeringComposition
from estate.core.grace_operations_runtime import GraceObjective, GraceOperationsRuntime
from estate.core.ptm_production_readiness import append_ptm_event


def _governed(tmp_path: Path, *, metadata: dict | None = None):
    authority = {"allowed_read_paths": ["docs/operations/Governed_Qwen_Local_Text_Provider.md", "config/providers/qwen_local_text.json"], "allowed_write_paths": ["docs/operations/examples/fixture-qwen.md", "runtime/engineering_adapter_receipts/fixture.json"]}
    objective = GraceObjective.create(requested_by="Steward", title="Qwen bounded validation", summary="Produce one bounded document.", metadata={"execution_authority": authority})
    GraceOperationsRuntime(tmp_path).conduct_objective(objective)
    action = next((tmp_path / "runtime/operations/grace/actions").glob("*.json"))
    prompt = tmp_path / "docs/operations/Governed_Qwen_Local_Text_Provider.md"
    prompt.parent.mkdir(parents=True, exist_ok=True); prompt.write_text("bounded prompt source\n", encoding="utf-8")
    (tmp_path / "config/providers/qwen_local_text.json").parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / "config/providers/qwen_local_text.json").write_text("{}\n", encoding="utf-8")
    comp = GraceHelenEngineeringComposition(tmp_path)
    inquiry = comp.request_capability(objective.objective_id, "documentation_draft")
    assessment = comp.determine_capability(inquiry["capability_request_id"], disposition="qualified_and_available", worker_profile_id="qwen-local-text", qualification_evidence=["qualification"], availability_evidence=["available"])
    for name in ("readiness_freshness_policy.json", "waiver_authorities.json"):
        target = tmp_path / "config/ptm" / name; target.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(Path("config/ptm") / name, target)
    for name in ("readiness_freshness_policy_v1.schema.json", "waiver_authorities_v1.schema.json", "readiness_resolution_v1.schema.json", "event_v1.schema.json"):
        target = tmp_path / "schemas/ptm" / name; target.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(Path("schemas/ptm") / name, target)
    source = tmp_path / "ptm-source.json"; source.write_text("{}\n", encoding="utf-8")
    event = append_ptm_event(tmp_path, event_type="task.readiness_inputs", aggregate_type="task", aggregate_id="task-1", stream_id="task:task-1", actor_ref="fixture", authority_refs=["PTM"], source_refs=[{"source_path": source.name, "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(), "adapter_name": "fixture", "adapter_version": "1"}], payload_schema="estate.ptm.readiness-input.v1", payload={"objective_id": objective.objective_id, "task_id": "task-1", "enabling_project_id": "project-1", "dependencies": [{"dependency_id": "d", "state": "satisfied", "observed_at": utc_now()}], "gate_checks": [{"name": "gate", "state": "pass", "observed_at": utc_now()}], "source_references": []}, idempotency_key="fixture-ptm", occurred_at=utc_now())
    action_record = json.loads(action.read_text(encoding="utf-8"))
    result = comp.governed_commission_and_dispatch(objective.objective_id, assessment["determination_id"], grace_action_id=action.stem.split("_", 1)[1], operations_decision_id=action_record["metadata"]["operations_decision_id"], bounded_objective=objective.summary, acceptance_criteria=["artifact"], ptm_source_high_watermark=event["event_id"], ptm_task_or_package_id="task-1", enabling_project_id="project-1", provider_id="qwen.local.text", provider_type="execution", adapter_reference="qwen-local-ollama-text-adapter@1.0.0", execution_metadata=metadata or authority, idempotency_key="fixture-qwen")
    return result


def test_governed_authority_reaches_fake_adapter_once(tmp_path):
    result = _governed(tmp_path)
    dispatch = result["dispatch"]; calls = []

    class FakeAdapter:
        def submit(self, request):
            calls.append(request)
            return ExecutionProviderAdapterResult(adapter_request_id=request.adapter_request_id, dispatch_id=request.dispatch_id, provider_id=request.provider_id, status="accepted", started_at=utc_now(), finished_at=utc_now(), validation_status="passed", metadata={"live_provider_called": False})

    checked = validate_handoff(dispatch["dispatch_id"], tmp_path)
    assert checked["status"] == "handoff_validated"
    request = checked["adapter_request"]
    assert request["prompt_source"].startswith("runtime/operations/grace/actions/")
    assert request["read_scope_paths"] == ["docs/operations/Governed_Qwen_Local_Text_Provider.md", "config/providers/qwen_local_text.json"]
    assert request["write_scope_paths"] == request["expected_outputs"]
    run = run_handoff_adapter(dispatch["dispatch_id"], tmp_path, adapter=FakeAdapter(), test_only=True)
    assert run["status"] == "accepted" and run["live_provider_called"] is False
    assert len(calls) == 1


def test_qwen_provider_extension_is_canonical_and_reaches_adapter_request(tmp_path):
    result = _governed(tmp_path)
    extension = result["commission"]["execution_authority"]["provider_extension"]
    assert extension["requested_capability"] == "documentation_draft"
    assert extension["authorized_model_identity"] == "qwen3:8b"
    assert extension["provider_receipt_path"] in result["dispatch"]["expected_outputs"]
    assert extension == result["authorization"]["provider_extension"]
    checked = validate_handoff(result["dispatch"]["dispatch_id"], tmp_path)
    assert checked["status"] == "handoff_validated"
    assert checked["adapter_request"]["provider_extension"] == extension


def test_qwen_provider_extension_tampering_blocks_before_request_publication(tmp_path):
    result = _governed(tmp_path)
    queue_path = tmp_path / "runtime/execution_dispatch/queue.json"
    payload = json.loads(queue_path.read_text(encoding="utf-8"))
    payload["items"][0]["provider_metadata"]["provider_extension"]["provider_receipt_path"] = "runtime/engineering_adapter_receipts/other.json"
    queue_path.write_text(json.dumps(payload), encoding="utf-8")
    checked = validate_handoff(result["dispatch"]["dispatch_id"], tmp_path)
    assert checked["status"] == "blocked"
    assert any("provider" in error.lower() or "extension" in error.lower() for error in checked["errors"])
    assert not (tmp_path / "runtime/execution_adapters/requests").exists()


def test_qwen_provider_extension_stale_helen_evidence_blocks_final_handoff(tmp_path):
    result = _governed(tmp_path)
    determination_id = result["dispatch"]["provider_metadata"]["helen_determination_id"]
    path = tmp_path / "runtime/grace_helen_engineering/helen_determinations" / f"{determination_id}.json"
    record = json.loads(path.read_text(encoding="utf-8")); record["evidence_expires_at"] = "2000-01-01T00:00:00Z"; path.write_text(json.dumps(record), encoding="utf-8")
    checked = validate_handoff(result["dispatch"]["dispatch_id"], tmp_path)
    assert checked["status"] == "blocked"
    assert any("Helen" in error or "stale" in error for error in checked["errors"])


def test_technical_handoff_fails_closed_for_missing_or_broad_scope(tmp_path):
    result = _governed(tmp_path)
    dispatch_id = result["dispatch"]["dispatch_id"]
    queue_path = tmp_path / "runtime/execution_dispatch/queue.json"
    payload = json.loads(queue_path.read_text(encoding="utf-8")); item = payload["items"][0]
    item["allowed_read_paths"] = ["."]; queue_path.write_text(json.dumps(payload), encoding="utf-8")
    checked = validate_handoff(dispatch_id, tmp_path)
    assert checked["status"] == "blocked"
    assert any("unsafe" in error or "broaden" in error for error in checked["errors"])


def test_caller_metadata_cannot_override_canonical_grace_authority(tmp_path):
    authority = {"allowed_read_paths": ["other.md"], "allowed_write_paths": ["other.out"]}
    try:
        _governed(tmp_path, metadata=authority)
    except ValueError as exc:
        assert "canonical Grace authority" in str(exc)
    else:
        raise AssertionError("caller metadata unexpectedly became execution authority")


def test_prompt_source_digest_is_rechecked_at_final_handoff(tmp_path):
    result = _governed(tmp_path)
    action_path = next((tmp_path / "runtime/operations/grace/actions").glob("*.json"))
    action_path.write_text(action_path.read_text(encoding="utf-8") + "tampered\n", encoding="utf-8")
    checked = validate_handoff(result["dispatch"]["dispatch_id"], tmp_path)
    assert checked["status"] == "blocked"
    assert any("digest" in error for error in checked["errors"])


def test_arbitrary_authorization_string_cannot_authorize_technical_dispatch(tmp_path):
    result = _governed(tmp_path)
    queue_path = tmp_path / "runtime/execution_dispatch/queue.json"
    payload = json.loads(queue_path.read_text(encoding="utf-8")); item = payload["items"][0]
    item["provider_metadata"]["authorization_reference"] = "authorized=true"
    item["provider_metadata"]["decision_reference"] = "authorized=true"
    queue_path.write_text(json.dumps(payload), encoding="utf-8")
    checked = validate_handoff(result["dispatch"]["dispatch_id"], tmp_path)
    assert checked["status"] == "blocked"
    assert any("canonical" in error or "recognized" in error for error in checked["errors"])


def test_ptm_is_revalidated_at_final_handoff(tmp_path):
    result = _governed(tmp_path)
    queue_path = tmp_path / "runtime/execution_dispatch/queue.json"
    payload = json.loads(queue_path.read_text(encoding="utf-8")); item = payload["items"][0]
    resolution_id = item["provider_metadata"]["ptm_readiness"]["readiness_resolution_id"]
    readiness_path = tmp_path / "runtime/ptm/readiness" / f"{resolution_id}.json"
    readiness = json.loads(readiness_path.read_text(encoding="utf-8")); readiness["expires_at"] = "2000-01-01T00:00:00Z"; readiness_path.write_text(json.dumps(readiness), encoding="utf-8")
    queue_path.write_text(json.dumps(payload), encoding="utf-8")
    checked = validate_handoff(result["dispatch"]["dispatch_id"], tmp_path)
    assert checked["status"] == "blocked"
    assert any("PTM" in error for error in checked["errors"])


def test_expected_outputs_may_be_bounded_files_inside_write_scope():
    request = ExecutionProviderAdapterRequest.create(adapter_request_id="adapter-subset", dispatch_id="dispatch-subset", provider_id="fixture", provider_type="fixture", adapter_reference="fixture@1", prompt_source="runtime/operations/grace/actions/action.json", prompt_source_type="estate.grace.action.v1", prompt_source_digest="a" * 64, read_scope_paths=["docs"], write_scope_paths=["docs/output"], expected_outputs=["docs/output/result.md"], decision_reference="operations-control/decision", authorization_reference="runtime/grace_helen_engineering/engineering_authorizations/auth.json", grace_objective_id="grace-obj-1", grace_action_id="grace-act-1", helen_determination_id="heldet-1", engineering_commission_id="engcom-1", engineering_authorization_id="engauth-1", ptm_readiness={"readiness_resolution_id": "res-1"}, metadata={"technical_execution": True, "provider_id": "fixture", "adapter_reference": "fixture@1"})
    assert request.validate().ok


def test_fake_adapter_seam_requires_explicit_test_only_flag(tmp_path):
    result = _governed(tmp_path)
    class FakeAdapter:
        def submit(self, request):
            raise AssertionError("should not execute")
    try:
        run_handoff_adapter(result["dispatch"]["dispatch_id"], tmp_path, adapter=FakeAdapter())
    except PermissionError as exc:
        assert "test injection" in str(exc)
    else:
        raise AssertionError("arbitrary adapter seam was callable without test guard")


def test_registered_runner_uses_validated_catalog_adapter_without_bypass(tmp_path, monkeypatch):
    result = _governed(tmp_path)
    calls = []
    class FakeAdapter:
        def validate_request(self, request):
            return request.validate()
        def submit(self, request):
            calls.append(request)
            return ExecutionProviderAdapterResult(adapter_request_id=request.adapter_request_id, dispatch_id=request.dispatch_id, provider_id=request.provider_id, status="accepted", started_at=utc_now(), finished_at=utc_now(), metadata={"live_provider_called": False})
    monkeypatch.setattr(adapter_runtime, "load_registered_adapter", lambda request, root=None, bridge_runner=None: FakeAdapter())
    run = run_registered_handoff_adapter(result["dispatch"]["dispatch_id"], tmp_path)
    assert run["status"] == "accepted" and run["live_provider_called"] is False and len(calls) == 1
    assert calls[0].metadata["prompt_text"] == (tmp_path / calls[0].prompt_source).read_bytes().decode("utf-8")
