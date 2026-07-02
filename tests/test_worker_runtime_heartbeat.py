import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from estate.core.worker_runtime_heartbeat import (
    create_worker_heartbeat,
    format_worker_runtime_summary,
    generate_worker_runtime_summary,
)


def test_heartbeat_creation_writes_runtime_record(tmp_path):
    heartbeat = create_worker_heartbeat(
        "worker.implementation",
        activity="Implementing WP-0039",
        status="active",
        last_completed_work_package="WP-0038",
        root=tmp_path,
        observed_at="2026-07-02T12:00:00Z",
    )

    path = tmp_path / "runtime/workers/heartbeats/worker.implementation.json"
    assert path.exists()
    saved = json.loads(path.read_text(encoding="utf-8"))
    assert saved == heartbeat
    assert saved["status"] == "active"
    assert saved["last_completed_work_package"] == "WP-0038"


def test_stale_worker_detection_preserves_reported_status(tmp_path):
    create_worker_heartbeat(
        "worker.old",
        activity="Awaiting assignment",
        status="idle",
        root=tmp_path,
        observed_at="2026-07-02T10:00:00Z",
    )

    summary = generate_worker_runtime_summary(
        root=tmp_path,
        stale_after_minutes=30,
        write=False,
        now=datetime(2026, 7, 2, 11, 0, tzinfo=timezone.utc),
    )

    worker = summary["workers"][0]
    assert worker["stale"] is True
    assert worker["status"] == "idle"
    assert summary["summary"]["stale_worker_count"] == 1


def test_blocked_state_requires_and_reports_reason(tmp_path):
    with pytest.raises(ValueError):
        create_worker_heartbeat("worker.blocked", activity="Waiting", status="blocked", root=tmp_path)

    create_worker_heartbeat(
        "worker.blocked",
        activity="Waiting for CA review",
        status="blocked",
        blocking_reason="Dependency WP-0001 not approved.",
        root=tmp_path,
        observed_at="2026-07-02T12:00:00Z",
    )
    summary = generate_worker_runtime_summary(root=tmp_path, write=False, now=datetime(2026, 7, 2, 12, 5, tzinfo=timezone.utc))
    assert summary["workers"][0]["blocking_reason"] == "Dependency WP-0001 not approved."
    assert summary["summary"]["status_counts"]["blocked"] == 1


def test_summary_generation_writes_runtime_and_operations_outputs(tmp_path):
    create_worker_heartbeat("worker.idle", activity="Ready", status="idle", root=tmp_path, observed_at="2026-07-02T12:00:00Z")

    summary = generate_worker_runtime_summary(root=tmp_path, now=datetime(2026, 7, 2, 12, 1, tzinfo=timezone.utc))
    markdown = format_worker_runtime_summary(summary)

    assert (tmp_path / "runtime/workers/worker_runtime_heartbeat.json").exists()
    assert (tmp_path / "operations/workers/runtime_heartbeat.md").read_text(encoding="utf-8") == markdown
    assert "Worker Runtime Heartbeat" in markdown
