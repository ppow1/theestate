from datetime import datetime, timedelta, timezone

from estate.core.operations_scheduler import OperationsScheduler


def test_event_trigger_debounces_and_persists_state(tmp_path):
    now = datetime(2026, 7, 10, 12, 0, tzinfo=timezone.utc)
    scheduler = OperationsScheduler(tmp_path, now=now)

    payload = scheduler.trigger("repo.changed")

    assert set(payload["matched_jobs"]) == {"merge_discovery", "repository_monitoring"}
    state = scheduler.load_state()
    assert state["jobs"]["merge_discovery"]["next_run_at"] == "2026-07-10T12:01:00Z"
    assert state["jobs"]["repository_monitoring"]["next_run_at"] == "2026-07-10T12:00:45Z"
    assert (tmp_path / "runtime/operations_scheduler/state.json").exists()
    assert (tmp_path / "operations/operations_scheduler/status.md").exists()


def test_lease_prevents_overlap_and_catchup_is_bounded(tmp_path):
    first = datetime(2026, 7, 10, 12, 0, tzinfo=timezone.utc)
    scheduler = OperationsScheduler(tmp_path, now=first)
    state = scheduler.load_state()
    state["jobs"]["health_refresh"]["next_run_at"] = "2026-07-10T10:00:00Z"
    scheduler.save_state(state)

    due = scheduler.acquire_due()
    health = [item for item in due if item["job"].job_id == "health_refresh"][0]
    assert health["catch_up_runs"] == 1
    assert not [item for item in scheduler.acquire_due() if item["job"].job_id == "health_refresh"]


def test_retry_and_next_run_state(tmp_path):
    now = datetime(2026, 7, 10, 12, 0, tzinfo=timezone.utc)
    scheduler = OperationsScheduler(tmp_path, now=now)
    state = scheduler.load_state()
    state["jobs"]["merge_discovery"]["next_run_at"] = "2026-07-10T12:00:00Z"
    scheduler.save_state(state)
    item = [item for item in scheduler.acquire_due() if item["job"].job_id == "merge_discovery"][0]

    later = OperationsScheduler(tmp_path, now=now + timedelta(minutes=1))
    later.complete("merge_discovery", item["lease_id"], "failed", {"errors": ["boom"]}, "boom")

    failed = later.load_state()["jobs"]["merge_discovery"]
    assert failed["retry_count"] == 1
    assert failed["failure_count"] == 1
    assert failed["next_run_at"] == "2026-07-10T12:06:00Z"
