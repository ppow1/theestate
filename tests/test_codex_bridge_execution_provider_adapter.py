import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from estate.core.codex_bridge import CodexBridgeResult, run_codex_bridge_request
from estate.core.codex_bridge_execution_provider_adapter import (
    CodexBridgeExecutionProviderAdapter,
    adapter_result_from_bridge_result,
    bridge_request_from_adapter_request,
    run_codex_bridge_adapter_dry_run,
)
from estate.core.execution_provider_adapter import ExecutionProviderAdapterRequest
from estate.core.execution_provider_adapter_runtime import RESULTS_DIR


def write_prompt(root: Path) -> None:
    path = root / "collaboration/work_packages/pending/WP-0504.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("Do the package.\n", encoding="utf-8")


def request(root: Path, **overrides) -> ExecutionProviderAdapterRequest:
    write_prompt(root)
    data = {
        "adapter_request_id": "adapter-wp-0504",
        "dispatch_id": "dispatch-wp-0504",
        "provider_id": "codex-cli-openai",
        "provider_type": "codex-cli",
        "profile_label": "default",
        "work_package_id": "WP-0504",
        "work_package_path": "collaboration/work_packages/pending/WP-0504.md",
        "prompt_source": "collaboration/work_packages/pending/WP-0504.md",
        "classification": "Estate Internal",
        "read_scope_paths": ["collaboration/work_packages/pending"],
        "write_scope_paths": ["src/estate/core", "tests", "docs/integration"],
        "blocked_scope_paths": ["archive", "runtime"],
        "expected_outputs": ["src/estate/core/codex_bridge_execution_provider_adapter.py"],
        "validation_required": True,
        "boundary_review_reference": "Ingrid/WP-0504",
        "decision_reference": "traffic-controller/WP-0504/authorized",
        "created_at": "2026-07-10T00:00:00Z",
        "metadata": {"sandbox": "workspace-write", "codex_home_profile": "default", "approval_policy": "never"},
    }
    data.update(overrides)
    return ExecutionProviderAdapterRequest.from_dict(data)


def test_supported_provider_detection(tmp_path):
    adapter = CodexBridgeExecutionProviderAdapter(root=tmp_path)
    assert adapter.supports(request(tmp_path))


def test_unsupported_provider_blocked(tmp_path):
    adapter = CodexBridgeExecutionProviderAdapter(root=tmp_path)
    validation = adapter.validate_request(request(tmp_path, provider_id="chatgpt-cli"))
    assert not validation.ok
    assert any("unsupported" in error for error in validation.errors)


def test_request_to_codex_bridge_translation_preserves_fields(tmp_path):
    adapter_request = request(tmp_path)
    bridge = bridge_request_from_adapter_request(adapter_request)
    assert bridge.request_id == "cbr-adapter-wp-0504"
    assert bridge.provider == "codex-cli-openai"
    assert bridge.work_package_id == "WP-0504"
    assert bridge.allowed_read_paths == ["collaboration/work_packages/pending"]
    assert bridge.allowed_write_paths == ["src/estate/core", "tests", "docs/integration"]
    assert bridge.expected_outputs == ["src/estate/core/codex_bridge_execution_provider_adapter.py"]
    assert bridge.approval_policy == "never"


def test_generated_prompt_is_governed_and_readable(tmp_path):
    adapter_request = request(tmp_path, prompt_source="A bounded fixture repair.", read_scope_paths=["Temp/fixture"])
    bridge = bridge_request_from_adapter_request(adapter_request, root=tmp_path)
    assert bridge.prompt_source.startswith("docs/prompts/generated-")
    assert not bridge.prompt_source.startswith("runtime/")
    assert "docs/prompts" in bridge.allowed_read_paths
    assert "Temp/fixture" in bridge.allowed_read_paths


def test_authorization_decision_reference_required(tmp_path):
    adapter = CodexBridgeExecutionProviderAdapter(root=tmp_path)
    validation = adapter.validate_request(request(tmp_path, decision_reference=None))
    assert not validation.ok
    assert any("decision_reference" in error for error in validation.errors)


def test_sandbox_and_profile_validation(tmp_path):
    adapter = CodexBridgeExecutionProviderAdapter(root=tmp_path)
    bad_sandbox = adapter.validate_request(request(tmp_path, metadata={"sandbox": "danger-full-access", "codex_home_profile": "default"}))
    bad_profile = adapter.validate_request(request(tmp_path, metadata={"sandbox": "read-only", "codex_home_profile": "missing"}))
    assert any("danger-full-access" in error for error in bad_sandbox.errors)
    assert any("provider profile" in error for error in bad_profile.errors)


def test_path_scope_preservation_and_blocked_conflict(tmp_path):
    bridge = bridge_request_from_adapter_request(request(tmp_path))
    assert bridge.allowed_read_paths == ["collaboration/work_packages/pending"]
    conflict = request(tmp_path, write_scope_paths=["archive/institutional_memory"])
    validation = CodexBridgeExecutionProviderAdapter(root=tmp_path).validate_request(conflict)
    assert any("conflicts" in error for error in validation.errors)


def test_dry_run_writes_artifacts_without_live_provider_call(tmp_path):
    payload = run_codex_bridge_adapter_dry_run(request(tmp_path), root=tmp_path)
    assert payload["status"] == "dry_run_completed"
    assert payload["metadata"]["live_provider_called"] is False
    assert Path(payload["result_path"]).is_file()
    assert Path(payload["report_path"]).is_file()
    assert (tmp_path / RESULTS_DIR / "adapter-wp-0504.json").is_file()


def test_fake_runner_submit_success_maps_bridge_result(tmp_path):
    calls = []

    def fake_runner(bridge_request, **kwargs):
        calls.append((bridge_request, kwargs))
        result = run_codex_bridge_request(bridge_request, root=tmp_path, dry_run=True)
        result.status = "succeeded"
        result.final_message = "Fake runner completed."
        result.changed_files = ["src/estate/core/example.py"]
        result.tests_run = ["pytest -q"]
        return result

    result = CodexBridgeExecutionProviderAdapter(root=tmp_path, bridge_runner=fake_runner).submit(request(tmp_path))
    assert result.status == "completed"
    assert result.metadata["live_provider_called"] is True
    assert result.metadata["changed_files"] == ["src/estate/core/example.py"]
    assert result.metadata["tests_run"] == ["pytest -q"]
    assert calls and calls[0][0].request_id == "cbr-adapter-wp-0504"


def test_fake_runner_submit_failure_maps_errors(tmp_path):
    def fake_runner(bridge_request, **kwargs):
        result = run_codex_bridge_request(bridge_request, root=tmp_path, dry_run=True)
        result.status = "failed"
        result.stderr = "simulated failure"
        return result

    result = CodexBridgeExecutionProviderAdapter(root=tmp_path, bridge_runner=fake_runner).submit(request(tmp_path))
    assert result.status == "failed"
    assert "simulated failure" in result.errors
    assert result.metadata["live_provider_called"] is True


def test_submit_without_runner_blocked_before_live_provider(tmp_path):
    result = CodexBridgeExecutionProviderAdapter(root=tmp_path).submit(request(tmp_path))
    assert result.status == "blocked"
    assert result.metadata["live_provider_called"] is False
    assert any("bridge_runner" in error for error in result.errors)


def test_bridge_result_to_adapter_result_preserves_lifecycle_and_artifacts(tmp_path):
    adapter_request = request(tmp_path)
    bridge_request = bridge_request_from_adapter_request(adapter_request)
    bridge_result = run_codex_bridge_request(bridge_request, root=tmp_path, dry_run=True)
    result = adapter_result_from_bridge_result(adapter_request, bridge_request, bridge_result, live_provider_called=False)
    assert result.dispatch_id == "dispatch-wp-0504"
    assert result.metadata["codex_bridge_request_id"] == bridge_request.request_id
    assert result.events == bridge_result.lifecycle_events
    assert bridge_result.audit_path in result.artifacts


def test_no_automatic_dispatch_completion(tmp_path):
    result = CodexBridgeExecutionProviderAdapter(root=tmp_path).dry_run(request(tmp_path))
    serialized = json.dumps(result.to_dict()).lower()
    assert "dispatch_completed" not in serialized
    assert "institutional_acceptance" not in serialized
