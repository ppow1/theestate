import json
from datetime import datetime, timezone

from estate.core.operational_readiness_dashboard import generate_operational_readiness_dashboard, format_operational_readiness_dashboard


def write_json(root, rel, payload):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def baseline(root, *, validation=None, workers=None, autonomy=None, presence="present"):
    write_json(root, "runtime/steward/mission_control_workspace.json", {"data": {"summary": {"state": "ready"}}})
    write_json(root, "runtime/validation/validation_metrics_dashboard.json", {"summary": validation or {"pass_count": 2, "conditional_pass_count": 0, "fail_count": 0, "open_observation_count": 0, "confirmed_defect_count": 0}})
    write_json(root, "runtime/workers/worker_runtime_monitor.json", {"summary": workers or {"active_worker_count": 0, "idle_worker_count": 1, "blocked_worker_count": 0, "stale_worker_count": 0, "offline_worker_count": 0, "unknown_worker_count": 0}})
    write_json(root, "runtime/autonomy/autonomous_operations_state.json", autonomy or {"decision": "continue", "status": "continuation_allowed_advisory"})
    write_json(root, "runtime/notifications/operations_notification_center.json", {"notifications": []})
    write_json(root, "runtime/steward/steward_presence_state.json", {"current_state": presence})
    write_json(root, "runtime/operations/operations_board.json", {"blocked_work": []})


def test_readiness_healthy_when_all_sources_clear(tmp_path):
    baseline(tmp_path)
    payload = generate_operational_readiness_dashboard(root=tmp_path, write=False, now=datetime(2026, 7, 4, tzinfo=timezone.utc))
    assert payload["overall_readiness_status"] == "healthy"
    assert payload["blocking_issues"] == []
    assert payload["degraded_subsystems"] == []
    assert all(source["drill_down"] for source in payload["sources"])


def test_readiness_degraded_for_observations_and_stale_workers(tmp_path):
    baseline(tmp_path, validation={"pass_count": 1, "conditional_pass_count": 1, "fail_count": 0, "open_observation_count": 1, "confirmed_defect_count": 0}, workers={"active_worker_count": 0, "idle_worker_count": 1, "blocked_worker_count": 0, "stale_worker_count": 1, "offline_worker_count": 0, "unknown_worker_count": 0})
    payload = generate_operational_readiness_dashboard(root=tmp_path, write=False)
    assert payload["overall_readiness_status"] == "degraded"
    assert {item["type"] for item in payload["degraded_subsystems"]} >= {"validation_observations", "worker_availability_degraded"}


def test_readiness_blocked_for_failed_validation_recall_and_blocked_worker(tmp_path):
    baseline(tmp_path, validation={"pass_count": 1, "conditional_pass_count": 0, "fail_count": 1, "open_observation_count": 0, "confirmed_defect_count": 1}, workers={"active_worker_count": 0, "idle_worker_count": 0, "blocked_worker_count": 1, "stale_worker_count": 0, "offline_worker_count": 0, "unknown_worker_count": 0}, autonomy={"decision": "pause"}, presence="recall_sent")
    payload = generate_operational_readiness_dashboard(root=tmp_path, write=False)
    assert payload["overall_readiness_status"] == "blocked"
    types = {item["type"] for item in payload["blocking_issues"]}
    assert {"validation_failure_or_defect", "blocked_workers", "autonomous_operations_not_clear", "active_recall"} <= types
    assert payload["active_recalls"]


def test_startup_missing_artifacts_are_unavailable_not_errors(tmp_path):
    payload = generate_operational_readiness_dashboard(root=tmp_path, write=True)
    markdown = format_operational_readiness_dashboard(payload)
    assert payload["overall_readiness_status"] == "startup"
    assert all(source["status"] == "unavailable" for source in payload["sources"])
    assert all(warning["type"] == "unavailable_artifact" for warning in payload["warnings"])
    assert "Unavailable Artifacts" in markdown
    assert (tmp_path / "runtime/operations/operational_readiness_dashboard.json").exists()
    assert (tmp_path / "operations/readiness/operational_readiness_dashboard.md").exists()
