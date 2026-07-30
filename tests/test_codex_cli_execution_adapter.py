from __future__ import annotations

from pathlib import Path
import shutil

from estate.core.codex_bridge import run_codex_bridge_request
from estate.core.codex_bridge_execution_provider_adapter import CodexCliExecutionProviderAdapter
from estate.core.execution_provider_adapter import ExecutionProviderAdapterRequest
from estate.core.execution_provider_adapter_runtime import load_registered_adapter


def make_request(root: Path, **overrides):
    catalog = Path(__file__).resolve().parents[1] / "config" / "providers" / "catalog.json"
    target_catalog = root / "config" / "providers" / "catalog.json"
    target_catalog.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(catalog, target_catalog)
    prompt = root / "commission.md"
    prompt.write_text("Create the declared artifact.\n", encoding="utf-8")
    data = {
        "adapter_request_id": "adapter-codex-001",
        "dispatch_id": "dispatch-codex-001",
        "provider_id": "codex.execution.cli",
        "provider_type": "execution",
        "work_package_id": "WP-codex-test",
        "work_package_path": "commission.md",
        "prompt_source": "commission.md",
        "classification": "Estate Internal",
        "read_scope_paths": ["."],
        "write_scope_paths": ["output"],
        "blocked_scope_paths": ["runtime", ".git"],
        "expected_outputs": ["output/result.md"],
        "decision_reference": "decision/codex-test",
        "boundary_review_reference": "boundary/codex-test",
        "metadata": {"sandbox": "workspace-write", "codex_home_profile": "default", "approval_policy": "never"},
    }
    data.update(overrides)
    return ExecutionProviderAdapterRequest.from_dict(data)


def fake_runner(bridge_request, *, root, dry_run):
    result = run_codex_bridge_request(bridge_request, root=root, dry_run=True)
    output = Path(root) / "output" / "result.md"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("bounded work product\n", encoding="utf-8")
    result.status = "succeeded"
    result.exit_code = 0
    result.final_message = "Created declared artifact."
    return result


def test_canonical_adapter_is_registered_from_provider_catalog(tmp_path):
    adapter = load_registered_adapter(make_request(tmp_path), root=tmp_path)
    assert isinstance(adapter, CodexCliExecutionProviderAdapter)
    assert adapter.adapter_id == "codex-cli-execution-adapter"


def test_canonical_adapter_requires_declared_artifact_and_receipt(tmp_path):
    request = make_request(tmp_path)
    result = CodexCliExecutionProviderAdapter(root=tmp_path, bridge_runner=fake_runner).submit(request)
    assert result.status == "completed"
    assert result.validation_status == "passed"
    assert result.metadata["provider_receipt"] in result.artifacts
    assert (tmp_path / result.metadata["provider_receipt"]).is_file()


def test_canonical_adapter_fails_closed_without_artifact(tmp_path):
    request = make_request(tmp_path, expected_outputs=["output/missing.md"])
    result = CodexCliExecutionProviderAdapter(root=tmp_path, bridge_runner=fake_runner).submit(request)
    assert result.status == "blocked"
    assert result.validation_status == "failed"
    assert any("missing declared artifact" in error for error in result.errors)


def test_canonical_adapter_does_not_claim_completion_without_explicit_outputs(tmp_path):
    request = make_request(tmp_path, expected_outputs=[])
    result = CodexCliExecutionProviderAdapter(root=tmp_path, bridge_runner=fake_runner).submit(request)
    assert result.status == "blocked"
    assert "explicit expected_outputs" in result.errors[0]
