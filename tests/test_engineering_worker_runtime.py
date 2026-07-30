import importlib.util
import json
from pathlib import Path


RUNTIME_PATH = Path("external/engineering_worker_runtime/engineering_worker_runtime.py")
SPEC = importlib.util.spec_from_file_location("engineering_worker_runtime", RUNTIME_PATH)
runtime = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(runtime)


def provider(provider_id="fixture-provider", capabilities=None, adapter_kind="deterministic_local_artifact"):
    return {
        "provider_id": provider_id,
        "provider_type": "fixture",
        "implementation_kind": adapter_kind,
        "adapter_kind": adapter_kind,
        "capabilities": capabilities or ["documentation_draft"],
        "status": "implemented",
    }


def package(tmp_path, *, outcome="Produce a structured work product.", artifact_type="structured_work_product", capabilities=None, criteria=None, providers=None, retries=0):
    return {
        "commission": {
            "commission_id": "commission-test",
            "grace_objective_id": "objective-test",
            "requested_outcome": outcome,
            "artifact_type": artifact_type,
            "required_capabilities": capabilities or ["documentation_draft"],
            "acceptance_criteria": criteria or [{"kind": "artifact_exists"}, {"kind": "provider_receipt"}],
            "constraints": [],
            "allowed_providers": [],
        },
        "provider_catalog": providers or [provider()],
        "retry_policy": {"max_retries": retries},
    }


def run(tmp_path, payload):
    evidence = tmp_path / "evidence"
    result = runtime.run_worker(payload, tmp_path / "worktree", evidence)
    return result, evidence


def test_generic_commissions_interpret_select_execute_and_validate(tmp_path):
    image, _ = run(tmp_path / "image", package(tmp_path, outcome="Produce a visual artifact.", artifact_type="visual_artifact"))
    text, _ = run(tmp_path / "text", package(tmp_path, outcome="Produce a structured specification.", artifact_type="text_artifact"))
    assert image["status"] == text["status"] == "completed"
    assert image["provider_selection"]["provider_id"] == "fixture-provider"
    assert image["validation"]["passed"] is True
    assert image["authority"]["institutional_acceptance_granted"] is False
    assert "bicycle" not in json.dumps(image).lower()


def test_provider_is_selected_from_declared_capabilities(tmp_path):
    payload = package(tmp_path, capabilities=["specialized_capability"], providers=[provider("wrong", ["documentation_draft"]), provider("right", ["specialized_capability"])])
    result, _ = run(tmp_path, payload)
    assert result["status"] == "completed"
    assert result["provider_selection"]["provider_id"] == "right"


def test_bicycle_is_ordinary_image_commission_data_not_worker_logic(tmp_path):
    result, _ = run(tmp_path, package(
        tmp_path,
        outcome="Produce an image of an adult three-wheeled bicycle on a white studio background.",
        artifact_type="image_artifact",
        capabilities=["image_generation"],
        providers=[provider("image-fixture", ["image_generation"])],
    ))
    assert result["status"] == "completed"
    assert result["commission"]["artifact_type"] == "image_artifact"
    assert result["provider_selection"]["provider_id"] == "image-fixture"


def test_successful_process_without_artifact_or_receipt_cannot_complete(tmp_path):
    result, _ = run(tmp_path, package(tmp_path, providers=[provider("unimplemented", adapter_kind="unregistered")]))
    assert result["status"] == "blocked"
    assert result["final_disposition"] == "blocked"


def test_validation_failure_is_failed_and_retry_history_is_preserved(tmp_path):
    result, _ = run(tmp_path, package(tmp_path, criteria=[{"kind": "artifact_contains", "value": "not-present"}], retries=1))
    assert result["status"] == "failed"
    assert len(result["retry_history"]) == 2
    assert result["validation"]["passed"] is False


def test_missing_commission_is_rejected_before_false_completion(tmp_path):
    try:
        runtime.run_worker({"provider_catalog": [provider()]}, tmp_path / "worktree", tmp_path / "evidence")
    except ValueError as exc:
        assert "commission" in str(exc)
    else:
        raise AssertionError("missing commission must not complete")
