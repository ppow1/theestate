import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from estate.core.execution_dispatch import EVENTS_OUTPUT, enqueue_dispatch_request, inspect_dispatch_item
from estate.core.execution_provider_adapter_runtime import RESULTS_DIR, write_adapter_result
from estate.core.execution_provider_adapter import ExecutionProviderAdapterResult
from estate.core.execution_result_reconciliation_runtime import reconcile_result, inspect_reconciliation
from estate.core.execution_activity import EVENTS_OUTPUT as ACTIVITY_EVENTS_OUTPUT


def dispatch_payload(**overrides):
    payload = {
        "dispatch_id": "dispatch-result-001",
        "work_package_id": "WP-0505",
        "title": "Result reconciliation",
        "assigned_worker": "Codex Worker",
        "provider": "codex_cloud_web",
        "profile_label": "cloud",
        "classification": "Estate Internal",
        "state": "Ready",
        "prompt_source": "collaboration/work_packages/pending/WP-0505.md",
        "allowed_read_paths": ["src", "tests"],
        "allowed_write_paths": ["src/estate/core", "tests"],
        "provider_metadata": {"adapter_request_id": "adapter-result-001", "validation_required": True},
    }
    payload.update(overrides)
    return payload


def result(**overrides):
    payload = {
        "adapter_request_id": "adapter-result-001",
        "dispatch_id": "dispatch-result-001",
        "provider_id": "codex_cloud_web",
        "status": "completed",
        "started_at": "2026-07-10T00:00:00Z",
        "finished_at": "2026-07-10T00:01:00Z",
        "summary": "Provider completed implementation.",
        "artifacts": ["runtime/provider/result.json"],
        "events": [],
        "validation_status": "not_run",
        "errors": [],
        "warnings": [],
        "metadata": {"live_provider_called": False},
    }
    payload.update(overrides)
    return ExecutionProviderAdapterResult(**payload)


def write_result(root, r):
    return write_adapter_result(r, root=root)


def activity_types(root):
    return [json.loads(l)["event_type"] for l in (root / ACTIVITY_EVENTS_OUTPUT).read_text().splitlines() if l.strip()]


def test_successful_completed_result_reconciles_to_validation(tmp_path):
    enqueue_dispatch_request(dispatch_payload(), tmp_path)
    path = write_result(tmp_path, result())
    payload = reconcile_result("dispatch-result-001", path, tmp_path)
    item = inspect_dispatch_item("dispatch-result-001", tmp_path)
    assert payload["dispatch_state"] == "Validation"
    assert item.state == "Validation"
    assert item.provider_metadata["validation_state"] == "prepared"
    assert item.provider_metadata["institutional_acceptance_state"] == "not_granted"
    assert "provider_result_ready_for_validation" in activity_types(tmp_path)


def test_completed_result_with_validation_not_required_completes_but_not_accepts(tmp_path):
    enqueue_dispatch_request(dispatch_payload(provider_metadata={"adapter_request_id": "adapter-result-001", "validation_required": False}), tmp_path)
    payload = reconcile_result("dispatch-result-001", write_result(tmp_path, result()), tmp_path)
    assert payload["dispatch_state"] == "Completed"
    assert payload["institutional_acceptance_state"] == "not_granted"


@pytest.mark.parametrize("status,state,event", [("failed", "Failed", "provider_execution_failed"), ("blocked", "Blocked", "provider_result_blocked")])
def test_failed_and_blocked_results_require_attention(tmp_path, status, state, event):
    enqueue_dispatch_request(dispatch_payload(), tmp_path)
    payload = reconcile_result("dispatch-result-001", write_result(tmp_path, result(status=status, summary=f"Provider {status}.")), tmp_path)
    assert payload["dispatch_state"] == state
    assert payload["attention_required"] is True
    assert event in activity_types(tmp_path)
    assert "provider_result_requires_attention" in activity_types(tmp_path)


def test_dry_run_result_does_not_advance_execution_state(tmp_path):
    enqueue_dispatch_request(dispatch_payload(), tmp_path)
    payload = reconcile_result("dispatch-result-001", write_result(tmp_path, result(status="dry_run_completed")), tmp_path)
    assert payload["dispatch_state"] == "Ready"
    assert inspect_dispatch_item("dispatch-result-001", tmp_path).state == "Ready"


def test_mismatched_dispatch_id_rejected(tmp_path):
    enqueue_dispatch_request(dispatch_payload(), tmp_path)
    with pytest.raises(ValueError, match="dispatch ID"):
        reconcile_result("dispatch-result-001", write_result(tmp_path, result(dispatch_id="other")), tmp_path)


def test_mismatched_provider_id_rejected(tmp_path):
    enqueue_dispatch_request(dispatch_payload(), tmp_path)
    with pytest.raises(ValueError, match="provider ID"):
        reconcile_result("dispatch-result-001", write_result(tmp_path, result(provider_id="other")), tmp_path)


def test_malformed_result_rejected(tmp_path):
    enqueue_dispatch_request(dispatch_payload(), tmp_path)
    with pytest.raises(ValueError, match="artifact"):
        reconcile_result("dispatch-result-001", write_result(tmp_path, result(artifacts=[])), tmp_path)


def test_impossible_lifecycle_transition_rejected(tmp_path):
    enqueue_dispatch_request(dispatch_payload(state="Blocked"), tmp_path)
    with pytest.raises(ValueError, match="impossible lifecycle transition"):
        reconcile_result("dispatch-result-001", write_result(tmp_path, result(status="dry_run_completed")), tmp_path)


def test_terminal_state_regression_protection(tmp_path):
    enqueue_dispatch_request(dispatch_payload(state="Cancelled"), tmp_path)
    with pytest.raises(ValueError, match="terminal state"):
        reconcile_result("dispatch-result-001", write_result(tmp_path, result(status="completed")), tmp_path)


def test_result_and_artifact_reference_persistence_and_inspect(tmp_path):
    enqueue_dispatch_request(dispatch_payload(), tmp_path)
    payload = reconcile_result("dispatch-result-001", write_result(tmp_path, result()), tmp_path)
    item = inspect_dispatch_item("dispatch-result-001", tmp_path)
    assert item.result_reference == str(RESULTS_DIR / "adapter-result-001.json")
    assert item.provider_metadata["result_artifacts"] == ["runtime/provider/result.json"]
    assert inspect_reconciliation("dispatch-result-001", tmp_path)["status"] == "available"
    assert Path(tmp_path / payload["reconciliation_path"]).is_file()


def test_idempotent_replay_does_not_duplicate_activity_or_dispatch_events(tmp_path):
    enqueue_dispatch_request(dispatch_payload(), tmp_path)
    path = write_result(tmp_path, result())
    first = reconcile_result("dispatch-result-001", path, tmp_path)
    dispatch_events_before = (tmp_path / EVENTS_OUTPUT).read_text()
    activity_before = (tmp_path / ACTIVITY_EVENTS_OUTPUT).read_text()
    second = reconcile_result("dispatch-result-001", path, tmp_path)
    assert second["status"] == "replayed"
    assert first["result_content_hash"] == second["result_content_hash"]
    assert (tmp_path / EVENTS_OUTPUT).read_text() == dispatch_events_before
    assert (tmp_path / ACTIVITY_EVENTS_OUTPUT).read_text() == activity_before


def test_no_live_provider_or_acceptance_mutation(tmp_path, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("subprocess/provider should not be called")
    monkeypatch.setattr("subprocess.run", forbidden)
    enqueue_dispatch_request(dispatch_payload(), tmp_path)
    payload = reconcile_result("dispatch-result-001", write_result(tmp_path, result()), tmp_path)
    assert payload["live_provider_called"] is False
    assert payload["institutional_acceptance_state"] == "not_granted"
