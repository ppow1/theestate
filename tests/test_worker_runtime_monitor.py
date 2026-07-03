import json
from datetime import datetime, timezone

from estate.core.worker_runtime_heartbeat import create_worker_heartbeat, generate_worker_runtime_summary
from estate.core.worker_runtime_monitor import generate_worker_runtime_monitor, format_worker_runtime_monitor


def write_json(root, rel, payload):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_monitor_reports_active_idle_blocked_stale_and_offline_workers(tmp_path):
    for worker_id, status, observed, kwargs in [
        ("worker.active", "active", "2026-07-03T12:00:00Z", {"activity": "Implementing WP-1"}),
        ("worker.idle", "idle", "2026-07-03T12:00:00Z", {"activity": "Ready"}),
        ("worker.blocked", "blocked", "2026-07-03T12:00:00Z", {"activity": "Waiting", "blocking_reason": "Needs CA review"}),
        ("worker.stale", "active", "2026-07-03T10:00:00Z", {"activity": "Old work"}),
        ("worker.offline", "offline", "2026-07-03T12:00:00Z", {"activity": "Signed out"}),
    ]:
        create_worker_heartbeat(worker_id, status=status, root=tmp_path, observed_at=observed, **kwargs)
    generate_worker_runtime_summary(root=tmp_path, stale_after_minutes=30, now=datetime(2026, 7, 3, 12, 10, tzinfo=timezone.utc))

    payload = generate_worker_runtime_monitor(root=tmp_path, stale_after_minutes=30, write=False, now=datetime(2026, 7, 3, 12, 10, tzinfo=timezone.utc))

    assert payload["summary"]["active_worker_count"] == 1
    assert payload["summary"]["idle_worker_count"] == 1
    assert payload["summary"]["blocked_worker_count"] == 1
    assert payload["summary"]["stale_worker_count"] == 1
    assert payload["summary"]["offline_worker_count"] == 1
    assert payload["blocked_workers"][0]["blocking_reason"] == "Needs CA review"


def test_monitor_attaches_assignment_mailbox_and_writes_json_and_markdown(tmp_path):
    create_worker_heartbeat("worker.impl", activity="Coding", status="active", root=tmp_path, observed_at="2026-07-03T12:00:00Z")
    generate_worker_runtime_summary(root=tmp_path, now=datetime(2026, 7, 3, 12, 1, tzinfo=timezone.utc))
    write_json(tmp_path, "runtime/work_packages/assignment_queue.json", {"work_packages": [{"work_package_id": "WP-0064", "owner": "worker.impl", "state": "claimed", "next_action": "Implement monitor", "blockers": []}]})
    write_json(tmp_path, "collaboration/status/worker_inbox_summary.json", {"workers": [{"worker": "worker.impl", "message_count": 2}]})
    write_json(tmp_path, "runtime/mailboxes/synchronization_duty_latest.json", {"summary": {}})
    write_json(tmp_path, "runtime/validation/local_operational_validation_run.json", {"summary": {}})

    payload = generate_worker_runtime_monitor(root=tmp_path, now=datetime(2026, 7, 3, 12, 1, tzinfo=timezone.utc))
    markdown = format_worker_runtime_monitor(payload)

    worker = payload["workers"][0]
    assert worker["current_assignment"]["work_package_id"] == "WP-0064"
    assert worker["mailbox"]["message_count"] == 2
    assert (tmp_path / "runtime/workers/worker_runtime_monitor.json").exists()
    assert (tmp_path / "operations/workers/worker_runtime_monitor.md").read_text(encoding="utf-8") == markdown


def test_monitor_missing_artifacts_warn_and_empty_workers_do_not_fail(tmp_path):
    payload = generate_worker_runtime_monitor(root=tmp_path, write=False, now=datetime(2026, 7, 3, 12, 0, tzinfo=timezone.utc))

    assert payload["summary"]["worker_count"] == 0
    assert payload["workers"] == []
    assert payload["warnings"]
    assert all(w["type"] == "missing_optional_artifact" for w in payload["warnings"])
