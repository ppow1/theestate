import json

import estate.core.grace_momentum_service as control
from estate.core.grace_momentum_service import GraceMomentumService, TEST_IDENTITIES, reference_command


def _assignment_command():
    command = reference_command("assignment.execute_local", objective_id="objective-image-test", idempotency_key="assignment-image-test")
    return {
        **command,
        "assignment_id": "assignment-image-test",
        "directive_id": "directive-image-test",
        "title": "Generate Evelyn headshot",
        "summary": "Approved local image generation",
        "adapter_id": "comfyui.local.image",
        "task_input": {"workflow": {"4": {"class_type": "CheckpointLoaderSimple"}}},
    }


def test_approved_local_assignment_persists_complete_lifecycle(tmp_path, monkeypatch):
    artifact = tmp_path / "evelyn.png"
    artifact.write_bytes(b"PNG")

    def fake_execute(task, *, root, endpoint, timeout_seconds):
        return {
            "artifact_id": "artifact-evelyn",
            "artifact_path": str(artifact),
            "prompt_id": "prompt-evelyn",
            "image_generated": True,
            "provider_endpoint": endpoint,
            "workflow_submitted": True,
            "live_provider_called": True,
        }

    monkeypatch.setattr(control, "execute_comfyui_image", fake_execute)
    service = GraceMomentumService(tmp_path, mode="governed_local_test")
    result = service.command(_assignment_command(), TEST_IDENTITIES["grace"])

    assert result["disposition"] == "completed"
    assert result["assignment_id"] == "assignment-image-test"
    assert result["dispatch_id"]
    assert result["artifact"]["artifact_id"] == "artifact-evelyn"
    assert json.loads((tmp_path / "runtime/production/grace_momentum/assignments.json").read_text())["assignment-image-test"]["state"] == "completed"
    assert service.query("assignment.record", TEST_IDENTITIES["observer"], assignment_id="assignment-image-test")["result"]["state"] == "completed"
    assert service.query("execution.progress", TEST_IDENTITIES["observer"], assignment_id="assignment-image-test")["result"]
    assert service.query("execution.completion", TEST_IDENTITIES["observer"], objective_id="objective-image-test")["result"]["dispatch_id"] == result["dispatch_id"]
    assert service.query("execution.artifact", TEST_IDENTITIES["observer"], dispatch_id=result["dispatch_id"])["result"]["artifact_id"] == "artifact-evelyn"


def test_local_assignment_records_deterministic_failure(tmp_path, monkeypatch):
    def fail_execute(*args, **kwargs):
        raise RuntimeError("approved image provider rejected workflow: checkpoint unavailable")

    monkeypatch.setattr(control, "execute_comfyui_image", fail_execute)
    service = GraceMomentumService(tmp_path, mode="governed_local_test")
    result = service.command(_assignment_command(), TEST_IDENTITIES["grace"])

    assert result["disposition"] == "failed"
    assert result["execution_state"] == "failed"
    assert "checkpoint unavailable" in result["failure"]["reason"]
    assignment = service.query("assignment.record", TEST_IDENTITIES["observer"], assignment_id="assignment-image-test")["result"]
    assert assignment["state"] == "failed"
    assert service.query("execution.failure", TEST_IDENTITIES["observer"], assignment_id="assignment-image-test")["result"]["reason"].endswith("checkpoint unavailable")
