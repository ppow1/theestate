import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from estate.core.execution_dispatch import EVENTS_OUTPUT, QUEUE_OUTPUT, enqueue_dispatch_request, inspect_dispatch_item
from estate.core.execution_adapter_handoff_runtime import dry_run_handoff, prepare_handoff, validate_handoff
from estate.core.execution_provider_adapter_runtime import REQUESTS_DIR, RESULTS_DIR


def payload(**overrides):
    data = {
        "dispatch_id": "dispatch-handoff-001",
        "work_package_id": "WP-0503",
        "title": "Governed handoff",
        "provider": "codex_cloud_web",
        "profile_label": "cloud",
        "classification": "Estate Internal",
        "state": "Ready",
        "prompt_source": "collaboration/work_packages/pending/WP-0503_Governed_Dispatch_to_Adapter_Handoff_Runtime.md",
        "sandbox": "workspace-write",
        "allowed_read_paths": ["src", "tests", "docs"],
        "allowed_write_paths": ["src/estate/core", "tests"],
        "allowed_providers": ["codex_cloud_web"],
        "forbidden_providers": [],
        "provider_metadata": {"decision_reference": "traffic-controller/WP-0503/authorized", "provider_type": "codex_cloud_web"},
    }
    data.update(overrides)
    return data


def read_events(root):
    return [json.loads(line) for line in (root / EVENTS_OUTPUT).read_text().splitlines() if line.strip()]


def test_successful_translation_and_dispatch_handoff_reference_update(tmp_path):
    enqueue_dispatch_request(payload(), tmp_path)
    result = prepare_handoff("dispatch-handoff-001", tmp_path)
    item = inspect_dispatch_item("dispatch-handoff-001", tmp_path)
    assert result["status"] == "handoff_validated"
    assert result["adapter_request"]["provider_id"] == "codex_cloud_web"
    assert item.handoff_reference == result["artifacts"]["request_path"]
    assert item.state == "Ready"
    assert item.state not in {"Running", "Completed"}
    assert (tmp_path / REQUESTS_DIR / f'{result["adapter_request"]["adapter_request_id"]}.json').is_file()
    assert read_events(tmp_path)[-1]["event_type"] == "dispatch_handoff_validated"


def test_missing_dispatch_item_rejected(tmp_path):
    result = validate_handoff("missing", tmp_path)
    assert result["status"] == "not_ready"
    assert result["errors"]


def test_not_ready_state_rejected(tmp_path):
    enqueue_dispatch_request(payload(state="Queued"), tmp_path)
    result = prepare_handoff("dispatch-handoff-001", tmp_path)
    assert result["status"] == "blocked"
    assert any("state" in e for e in result["errors"])


def test_missing_authorization_rejected(tmp_path):
    enqueue_dispatch_request(payload(provider_metadata={}), tmp_path)
    result = prepare_handoff("dispatch-handoff-001", tmp_path)
    assert result["status"] == "blocked"
    assert any("authorization" in e for e in result["errors"])


def test_forbidden_or_outside_allowed_provider_rejected(tmp_path):
    enqueue_dispatch_request(payload(), tmp_path)
    queue_path = tmp_path / QUEUE_OUTPUT
    queue = json.loads(queue_path.read_text())
    queue["items"][0]["provider"] = "codex_cli"
    queue["items"][0]["forbidden_providers"] = ["codex_cli"]
    queue["items"][0]["allowed_providers"] = ["codex_cloud_web"]
    queue_path.write_text(json.dumps(queue, indent=2, sort_keys=True) + "\n")
    result = prepare_handoff("dispatch-handoff-001", tmp_path)
    assert result["status"] == "blocked"
    assert any("forbidden" in e or "allowed" in e for e in result["errors"])


def test_required_scope_data_missing_rejected(tmp_path):
    enqueue_dispatch_request(payload(allowed_read_paths=[], allowed_write_paths=[]), tmp_path)
    result = prepare_handoff("dispatch-handoff-001", tmp_path)
    assert result["status"] == "blocked"
    assert any("allowed_read_paths" in e for e in result["errors"])
    assert any("allowed_write_paths" in e for e in result["errors"])


def test_deterministic_dry_run_writes_result_without_live_provider(tmp_path):
    enqueue_dispatch_request(payload(), tmp_path)
    result = dry_run_handoff("dispatch-handoff-001", tmp_path)
    request_id = result["adapter_request"]["adapter_request_id"]
    assert result["status"] == "dry_run_completed"
    assert result["live_provider_called"] is False
    assert result["dry_run_result"]["metadata"]["live_provider_called"] is False
    assert (tmp_path / RESULTS_DIR / f"{request_id}.json").is_file()
    assert inspect_dispatch_item("dispatch-handoff-001", tmp_path).state == "Ready"


def test_no_duplicate_runtime_systems_created(tmp_path):
    enqueue_dispatch_request(payload(), tmp_path)
    dry_run_handoff("dispatch-handoff-001", tmp_path)
    assert (tmp_path / QUEUE_OUTPUT).is_file()
    assert not (tmp_path / "runtime" / "execution_adapter_handoffs").exists()
    assert not (tmp_path / "runtime" / "provider_registry").exists()
    assert not (tmp_path / "runtime" / "events").exists()
