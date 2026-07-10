import json
from estate.core.operational_watch_runtime import OperationalWatchRuntime


def test_disable_prevents_dry_run_trigger(tmp_path):
    rt = OperationalWatchRuntime(tmp_path)
    rt.set_enabled("worker_assignment_gap_watch", False)
    result = rt.evaluate("worker_assignment_gap_watch")
    assert result["enabled"] is False
    assert result["would_trigger"] is False
    watches = json.loads((tmp_path / "runtime/background_operations/watches.json").read_text())["watches"]
    disabled = [w for w in watches if w["watch_id"] == "worker_assignment_gap_watch"][0]
    assert disabled["enabled"] is False


def test_pause_persists_runtime_state_outside_repository_defaults(tmp_path):
    rt = OperationalWatchRuntime(tmp_path)
    payload = rt.pause("pending_routing_recommendation_watch")
    assert payload["paused"] is True
    state_path = tmp_path / "runtime/background_operations/watch_state.json"
    assert state_path.exists()
    state = json.loads(state_path.read_text())
    assert state["watches"]["pending_routing_recommendation_watch"]["paused"] is True


def test_dry_run_evaluate_reports_trigger_without_writing_request(tmp_path):
    (tmp_path / "collaboration/work_packages/pending").mkdir(parents=True)
    (tmp_path / "collaboration/work_packages/pending/WP-9999_Test.md").write_text("# test", encoding="utf-8")
    rt = OperationalWatchRuntime(tmp_path)
    result = rt.evaluate("worker_assignment_gap_watch")
    assert result["dry_run"] is True
    assert result["would_trigger"] is True
    assert not (tmp_path / "runtime/background_operations/requests").exists()
