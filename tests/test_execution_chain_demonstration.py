from pathlib import Path
import json

from estate.core.execution_chain_demonstration import run_execution_chain_demonstration


def test_successful_deterministic_end_to_end_demonstration(tmp_path):
    result = run_execution_chain_demonstration(root=tmp_path)
    assert result["failures"] == []
    assert result["preview_status"] == "previewed"
    assert result["provider_call_count"] == 1
    assert result["lease_released"] is True
    assert result["provider_result_status"] == "completed"
    assert result["reconciliation_status"] == "reconciled"
    assert result["final_dispatch_state"] == "Validation"
    assert result["activity_evidence_count"] >= 1
    assert result["institutional_acceptance_state"] == "not_granted"
    assert result["live_provider_called"] is False
    assert result["fake_provider_runner_used"] is True
    assert (tmp_path / result["artifacts"]["demonstration_result"]).is_file()
    assert (tmp_path / result["artifacts"]["demonstration_report"]).is_file()


def test_preview_and_inspection_do_not_duplicate_provider_call(tmp_path):
    result = run_execution_chain_demonstration(root=tmp_path)
    assert result["preview_status"] == "previewed"
    assert result["provider_call_count"] == 1
    sessions = list((tmp_path / "runtime/execution_adapters/sessions").glob("*.json"))
    assert len(sessions) >= 2  # fixture preview + demonstration preview/start evidence


def test_invalid_authorization_blocks_without_provider_call(tmp_path):
    result = run_execution_chain_demonstration(root=tmp_path, invalid_authorization=True)
    assert result["provider_call_count"] == 0
    assert result["final_dispatch_state"] == "Ready"
    assert result["start_status"] in {"blocked", "failed"}


def test_failed_fake_provider_result_is_preserved(tmp_path):
    result = run_execution_chain_demonstration(root=tmp_path, fake_provider_status="failed")
    assert result["provider_call_count"] == 1
    assert result["final_dispatch_state"] == "Failed"
    result_paths = list((tmp_path / "runtime/execution_adapters/results").glob("*.json"))
    assert result_paths
    payload = json.loads(result_paths[0].read_text(encoding="utf-8"))
    assert payload["status"] == "failed"
    assert payload["metadata"]["live_provider_called"] is True


def test_active_repository_runtime_untouched(tmp_path):
    before = set(Path("runtime/execution_adapters/demonstrations").glob("*.json")) if Path("runtime/execution_adapters/demonstrations").exists() else set()
    run_execution_chain_demonstration(root=tmp_path)
    after = set(Path("runtime/execution_adapters/demonstrations").glob("*.json")) if Path("runtime/execution_adapters/demonstrations").exists() else set()
    assert after == before
