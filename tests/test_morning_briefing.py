import json
from pathlib import Path

from estate.core.morning_briefing import generate_morning_briefing, format_morning_briefing


def _write(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_json(path: Path, payload):
    _write(path, json.dumps(payload))


def _representative_root(tmp_path: Path) -> Path:
    _write(tmp_path / "operations/alfred/operational_briefing.md", "# Alfred\nAll systems concise.\n")
    _write_json(tmp_path / "runtime/mailboxes/synchronization_duty_latest.json", {"summary": {"open_message_count": 2, "ack_required_count": 1}})
    _write(tmp_path / "operations/mailboxes/synchronization_duty.md", "# Mailbox\n")
    _write_json(tmp_path / "runtime/updates/check_updates_latest.json", {"summary": {"items": 3}})
    _write(tmp_path / "operations/updates/check_updates_latest.md", "# Updates\n")
    _write_json(tmp_path / "runtime/validation/local_operational_validation_latest.json", {"summary": {"warning_count": 1}})
    _write(tmp_path / "operations/validation/local_operational_validation_run.md", "# Validation\n")
    _write(tmp_path / "operations/boards/daily_board.md", "# Daily Board\n")
    _write(tmp_path / "operations/boards/daily_board_integration.md", "# Integration\n")
    _write(tmp_path / "operations/boards/parking_lot.md", "# Parking\nDeferred roadmap item.\n")
    _write_json(tmp_path / "runtime/notifications/notification_router_report.json", {"summary": {"recall_count": 1, "informational_count": 2}})
    _write_json(tmp_path / "runtime/audit/recall_audit_log.json", {
        "summary": {"record_count": 1, "pending_acknowledgement_count": 1},
        "records": [{"record_id": "recall-1", "recall_reason": "operational", "acknowledgement_state": "pending"}],
    })
    _write_json(tmp_path / "collaboration/work_packages/completions/WP-0999_codex_done.json", {
        "work_package_id": "WP-0999", "codex_status": "done", "summary": "Implemented representative package."
    })
    _write(tmp_path / "collaboration/work_packages/pending/WP-1000_review.md", "# Pending\n")
    return tmp_path


def test_briefing_generation_with_representative_artifacts(tmp_path):
    root = _representative_root(tmp_path)

    briefing = generate_morning_briefing(root=root, write=False)

    assert briefing["version"] == 1
    assert briefing["constraints"]["notifies_steward"] is False
    assert briefing["sections"]["mailbox_summary"]["open_message_count"] == 2
    assert briefing["sections"]["board_changes"]["parking_lot_highlights"] == ["Deferred roadmap item."]


def test_missing_artifact_warnings(tmp_path):
    briefing = generate_morning_briefing(root=tmp_path, write=False)

    assert briefing["warnings"]
    assert any(w["type"] == "missing_optional_artifact" for w in briefing["warnings"])


def test_completed_work_summary(tmp_path):
    root = _representative_root(tmp_path)

    completed = generate_morning_briefing(root=root, write=False)["sections"]["completed_work"]

    assert completed[0]["id"] == "WP-0999"
    assert "representative" in completed[0]["summary"]


def test_recall_summary(tmp_path):
    root = _representative_root(tmp_path)

    recalls = generate_morning_briefing(root=root, write=False)["sections"]["outstanding_recalls"]

    assert recalls == [{"record_id": "recall-1", "recall_reason": "operational", "acknowledgement_state": "pending"}]


def test_pending_approval_summary(tmp_path):
    root = _representative_root(tmp_path)

    pending = generate_morning_briefing(root=root, write=False)["sections"]["pending_approvals"]

    assert pending[0]["id"] == "WP-1000"


def test_markdown_and_json_output_generation(tmp_path):
    root = _representative_root(tmp_path)

    briefing = generate_morning_briefing(root=root, write=True)
    markdown = format_morning_briefing(briefing)

    assert (root / "runtime/briefings/morning_briefing.json").exists()
    assert (root / "operations/briefings/morning_briefing.md").read_text(encoding="utf-8") == markdown
    assert "## Recommended next actions" in markdown


def test_empty_overnight_activity_reports_no_events(tmp_path):
    briefing = generate_morning_briefing(root=tmp_path, write=False)

    summary = briefing["sections"]["summary"]
    assert summary["completed_work_count"] == 0
    assert summary["failed_or_blocked_work_count"] == 0
    assert summary["pending_decision_count"] == 0
    assert summary["outstanding_recall_count"] == 0
    assert briefing["constraints"]["executes_work"] is False
    assert briefing["constraints"]["notifies_steward"] is False


def test_successful_overnight_run_includes_accomplishments_worker_runtime_and_missions(tmp_path):
    root = _representative_root(tmp_path)
    _write_json(root / "runtime/workers/worker_runtime_monitor.json", {"summary": {"worker_count": 2, "stale_worker_count": 0, "blocked_worker_count": 0}, "workers": []})
    _write_json(root / "runtime/workers/worker_runtime_heartbeat.json", {"summary": {"worker_count": 2}})
    _write_json(root / "data/registry/missions.json", {"missions": [{"mission_id": "MISSION-1", "mission_title": "Night Run", "status": "active", "related_work_packages": ["WP-0999"]}]})
    _write_json(root / "runtime/work_packages/assignment_queue.json", {"work_packages": []})
    _write(root / "operations/work_packages/autonomous_work_queue_scheduler.md", "# Scheduler\nNo automatic execution.\n")
    _write_json(root / "runtime/steward/mission_control_workspace.json", {"data": {"summary": {"state": "ready"}}})

    sections = generate_morning_briefing(root=root, write=False)["sections"]

    assert sections["accomplishments"][0]["path"] == "collaboration/work_packages/completions/WP-0999_codex_done.json"
    assert sections["worker_runtime"]["summary"]["worker_count"] == 2
    assert sections["mission_status"]["counts"] == {"active": 1}


def test_failures_validation_issues_and_recalls_are_recommended(tmp_path):
    root = _representative_root(tmp_path)
    _write(root / "collaboration/work_packages/open/WP-2000_blocked.md", "# Blocked\n")
    _write_json(root / "runtime/validation/local_operational_validation_latest.json", {"summary": {"failure_count": 1}})
    _write_json(root / "runtime/workers/worker_runtime_monitor.json", {"summary": {"worker_count": 1, "stale_worker_count": 1, "blocked_worker_count": 1}})

    sections = generate_morning_briefing(root=root, write=False)["sections"]

    assert sections["failures"][0]["id"] == "WP-2000"
    assert sections["outstanding_recalls"][0]["record_id"] == "recall-1"
    assert any("validation failures" in action for action in sections["recommended_next_actions"])
    assert any("worker runtime" in action for action in sections["recommended_next_actions"])


def test_missing_artifact_handling_lists_sources_and_warnings(tmp_path):
    briefing = generate_morning_briefing(root=tmp_path, write=False)

    assert briefing["source_artifacts"]["worker_runtime_monitor"]["present"] is False
    assert briefing["source_artifacts"]["mission_registry"]["present"] is False
    assert any(w["path"] == "runtime/workers/worker_runtime_monitor.json" for w in briefing["warnings"])
    assert any("missing optional operational artifacts" in action for action in briefing["sections"]["recommended_next_actions"])
