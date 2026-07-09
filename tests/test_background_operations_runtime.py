import json
import os
from pathlib import Path
from datetime import datetime, timezone, timedelta

from estate.core.background_operations_runtime import BackgroundOperationsRuntime
from estate.core.steward_command_center import generate_command_center


def write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")


def request_types(root: Path):
    return {json.loads(p.read_text())["request_type"] for p in (root / "runtime/background_operations/requests").glob("*.json")}


def test_cycle_produces_no_requests_when_no_watch_triggered(tmp_path):
    rt = BackgroundOperationsRuntime(tmp_path)
    status = rt.run_cycle()
    assert status["summary"]["generated_requests_count"] == 0
    assert (tmp_path / "runtime/background_operations/status/summary.json").exists()
    assert status["live_provider_called"] is False
    assert status["provider_execution_performed"] is False
    assert status["dispatch_execution_performed"] is False


def test_pending_routing_recommendation_creates_review_request(tmp_path):
    write_json(tmp_path / "runtime/provider_routing/status/summary.json", {"latest_recommendation_id": "prr-1", "recommendation_only": True})
    status = BackgroundOperationsRuntime(tmp_path).run_cycle()
    assert "routing_review_request" in request_types(tmp_path)
    assert status["summary"]["generated_requests_count"] >= 1


def test_pending_movement_decision_creates_traffic_controller_request(tmp_path):
    write_json(tmp_path / "runtime/provider_routing/status/summary.json", {"latest_recommendation_id": "prr-2", "recommendation_only": True})
    status = BackgroundOperationsRuntime(tmp_path).run_cycle()
    assert "traffic_controller_review_request" in request_types(tmp_path)
    assert status["summary"]["pending_movement_decision_count"] == 1


def test_missing_ring2_review_creates_validation_request(tmp_path):
    write_json(tmp_path / "runtime/validation/work_packages/WP-0617_validation.json", {"validation_status": "passed"})
    BackgroundOperationsRuntime(tmp_path).run_cycle()
    assert "validation_review_request" in request_types(tmp_path)


def test_stale_validation_artifact_creates_review_request(tmp_path):
    p = tmp_path / "runtime/validation/work_packages/WP-0618_validation.json"
    write_json(p, {"validation_status": "passed"})
    old = (datetime.now(timezone.utc) - timedelta(days=3)).timestamp()
    os.utime(p, (old, old))
    status = BackgroundOperationsRuntime(tmp_path).run_cycle()
    assert status["summary"]["stale_validation_count"] == 1
    assert "validation_review_request" in request_types(tmp_path)


def test_provider_capacity_warning_creates_capacity_request(tmp_path):
    write_json(tmp_path / "runtime/providers/health/status/summary.json", {"providers": [{"provider_id": "codex", "capacity_state": "saturated"}]})
    BackgroundOperationsRuntime(tmp_path).run_cycle()
    assert "provider_capacity_review_request" in request_types(tmp_path)


def test_worker_assignment_gap_creates_assignment_request(tmp_path):
    (tmp_path / "collaboration/work_packages/pending").mkdir(parents=True)
    (tmp_path / "collaboration/work_packages/pending/WP-9999_Test.md").write_text("# test", encoding="utf-8")
    write_json(tmp_path / "runtime/workers/assignments/status/board.json", {"assignments": []})
    BackgroundOperationsRuntime(tmp_path).run_cycle()
    assert "worker_assignment_review_request" in request_types(tmp_path)


def test_cooldown_prevents_repeated_duplicate_requests(tmp_path):
    write_json(tmp_path / "runtime/provider_routing/status/summary.json", {"latest_recommendation_id": "prr-3", "recommendation_only": True})
    rt = BackgroundOperationsRuntime(tmp_path)
    first = rt.run_cycle()
    second = rt.run_cycle()
    assert first["summary"]["generated_requests_count"] >= 1
    assert second["summary"]["generated_requests_count"] == 0


def test_office_payload_reflects_background_operations_status(tmp_path):
    write_json(tmp_path / "runtime/provider_routing/status/summary.json", {"latest_recommendation_id": "prr-office", "recommendation_only": True})
    BackgroundOperationsRuntime(tmp_path).run_cycle()
    payload = generate_command_center(root=tmp_path, write=False)
    assert payload["status_bar"]["background_operations_available"] is True
    assert payload["status_bar"]["active_watches_count"] >= 1


def test_no_duplicate_core_systems_introduced():
    assert not Path("src/estate/core/background_event_feed.py").exists()
    assert not Path("src/estate/core/background_provider_registry.py").exists()
    assert not Path("src/estate/core/background_dispatch_queue.py").exists()
