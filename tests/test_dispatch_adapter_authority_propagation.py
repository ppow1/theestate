from __future__ import annotations

import hashlib
import shutil
from pathlib import Path

from estate.core.execution_adapter_handoff_runtime import run_handoff_adapter, validate_handoff
from estate.core.execution_provider_adapter import ExecutionProviderAdapterResult, utc_now
from estate.core.grace_helen_engineering_composition import GraceHelenEngineeringComposition
from estate.core.grace_operations_runtime import GraceObjective, GraceOperationsRuntime
from estate.core.ptm_production_readiness import append_ptm_event


def _governed(tmp_path: Path, *, metadata: dict | None = None):
    objective = GraceObjective.create(requested_by="Steward", title="Qwen bounded validation", summary="Produce one bounded document.")
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
    authority = {"prompt_source": "docs/operations/Governed_Qwen_Local_Text_Provider.md", "prompt_source_type": "estate.grace.action.v1", "allowed_read_paths": ["docs/operations/Governed_Qwen_Local_Text_Provider.md", "config/providers/qwen_local_text.json"], "allowed_write_paths": ["docs/operations/examples/fixture-qwen.md", "runtime/engineering_adapter_receipts/fixture.json"]}
    result = comp.governed_commission_and_dispatch(objective.objective_id, assessment["determination_id"], grace_action_id=action.stem.split("_", 1)[1], operations_decision_id="opact-fixture", bounded_objective=objective.summary, acceptance_criteria=["artifact"], ptm_source_high_watermark=event["event_id"], ptm_task_or_package_id="task-1", enabling_project_id="project-1", provider_id="qwen.local.text", provider_type="execution", adapter_reference="qwen-local-ollama-text-adapter@1.0.0", execution_metadata=metadata or authority, idempotency_key="fixture-qwen")
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
    assert request["prompt_source"] == "docs/operations/Governed_Qwen_Local_Text_Provider.md"
    assert request["read_scope_paths"] == ["docs/operations/Governed_Qwen_Local_Text_Provider.md", "config/providers/qwen_local_text.json"]
    assert request["write_scope_paths"] == request["expected_outputs"]
    run = run_handoff_adapter(dispatch["dispatch_id"], tmp_path, adapter=FakeAdapter())
    assert run["status"] == "accepted" and run["live_provider_called"] is False
    assert len(calls) == 1


def test_technical_handoff_fails_closed_for_missing_or_broad_scope(tmp_path):
    result = _governed(tmp_path)
    dispatch_id = result["dispatch"]["dispatch_id"]
    import json
    queue_path = tmp_path / "runtime/execution_dispatch/queue.json"
    payload = json.loads(queue_path.read_text(encoding="utf-8")); item = payload["items"][0]
    item["allowed_read_paths"] = ["."]; queue_path.write_text(json.dumps(payload), encoding="utf-8")
    checked = validate_handoff(dispatch_id, tmp_path)
    assert checked["status"] == "blocked"
    assert any("unsafe" in error or "broaden" in error for error in checked["errors"])
