import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pytest

from estate.core.execution_provider_adapter import (
    DeterministicDryRunExecutionProviderAdapter,
    ExecutionProviderAdapter,
    ExecutionProviderAdapterRequest,
)


def valid_request(**overrides):
    data = {
        "adapter_request_id": "adapter-001",
        "dispatch_id": "dispatch-001",
        "provider_id": "dry-run-provider",
        "provider_type": "dry-run",
        "profile_label": "A2C3",
        "work_package_id": "WP-0613",
        "work_package_path": "collaboration/work_packages/pending/WP-0613_Execution_Provider_Adapter_Contract.md",
        "prompt_source": "collaboration/work_packages/pending/WP-0613_Execution_Provider_Adapter_Contract.md",
        "classification": "Estate Internal",
        "read_scope_paths": ["docs", "src"],
        "write_scope_paths": ["src/estate/core"],
        "blocked_scope_paths": ["archive"],
        "expected_outputs": ["docs/integration/execution_provider_adapter_contract.md"],
        "validation_required": True,
        "boundary_review_reference": "Ingrid/WP-0613",
        "decision_reference": "operations/decision/WP-0613",
        "created_at": "2026-07-09T00:00:00Z",
        "metadata": {"codex_home_profile": "default"},
    }
    data.update(overrides)
    return ExecutionProviderAdapterRequest.from_dict(data)


def test_valid_adapter_request_accepted():
    request = valid_request()
    validation = request.validate()
    assert validation.ok
    assert validation.status == "accepted"


def test_invalid_classification_rejected():
    validation = valid_request(classification="Public Secret").validate()
    assert not validation.ok
    assert any("classification" in error for error in validation.errors)


def test_missing_dispatch_id_rejected():
    validation = valid_request(dispatch_id="").validate()
    assert not validation.ok
    assert any("dispatch_id is required" in error for error in validation.errors)


def test_missing_provider_id_rejected():
    validation = valid_request(provider_id="").validate()
    assert not validation.ok
    assert any("provider_id is required" in error for error in validation.errors)


def test_path_scope_conflict_blocked():
    validation = valid_request(write_scope_paths=["archive/institutional_memory"], blocked_scope_paths=["archive"]).validate()
    assert not validation.ok
    assert any("conflicts" in error for error in validation.errors)


def test_dry_run_adapter_validates_request_without_provider_work():
    request = valid_request()
    adapter = DeterministicDryRunExecutionProviderAdapter()
    result = adapter.dry_run(request)
    assert result.status == "dry_run_completed"
    assert result.validation_status == "passed"
    assert result.metadata["live_provider_called"] is False


def test_adapter_interface_does_not_require_codex_specific_fields():
    request = valid_request(profile_label=None, metadata={})
    assert isinstance(DeterministicDryRunExecutionProviderAdapter(), ExecutionProviderAdapter)
    assert request.metadata == {}
    assert request.validate().ok


def test_codex_bridge_compatibility_fields_can_be_represented_without_coupling():
    request = valid_request(provider_id="codex-cli-openai", provider_type="codex_bridge", profile_label="A2C1", metadata={"codex_home_profile": "business-seat-1", "sandbox": "read-only"})
    assert request.provider_type == "codex_bridge"
    assert request.profile_label == "A2C1"
    assert request.metadata["codex_home_profile"] == "business-seat-1"
    assert request.validate().ok
