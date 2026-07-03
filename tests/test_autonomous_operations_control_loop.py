import json
from datetime import datetime, timezone
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from estate.core.autonomous_operations_control_loop import generate_autonomous_operations_control_loop


def write_json(root, rel, payload):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def baseline(root, *, ready=1, presence="present", local_status="ok", worker=None):
    write_json(root, "runtime/work_packages/autonomous_work_queue_scheduler.json", {"summary": {"ready_count": ready, "recommended_next_work_package": "WP-0100"}})
    write_json(root, "runtime/workers/worker_runtime_monitor.json", {"summary": worker or {"active_worker_count": 0, "blocked_worker_count": 0}})
    write_json(root, "runtime/steward/steward_presence_state.json", {"current_state": presence})
    write_json(root, "runtime/operations/morning_briefing.json", {"summary": {}})
    write_json(root, "runtime/validation/local_operational_validation_run.json", {"steps": [{"status": local_status}]})
    write_json(root, "runtime/validation/operational_validation_report.json", {"status": "ok"})
    write_json(root, "runtime/notifications/notification_router_report.json", {"notifications": []})
    write_json(root, "runtime/audit/recall_audit_log.json", {"records": []})
    write_json(root, "runtime/operations/daily_board_integration.json", {"summary": {}})


def test_continue_when_evidence_clear_and_ready_work_exists(tmp_path):
    baseline(tmp_path)
    payload = generate_autonomous_operations_control_loop(root=tmp_path, write=False, now=datetime(2026, 7, 3, tzinfo=timezone.utc))
    assert payload["decision"] == "continue"
    assert payload["blocked_conditions"] == []


def test_pause_when_missing_evidence(tmp_path):
    baseline(tmp_path)
    (tmp_path / "runtime/workers/worker_runtime_monitor.json").unlink()
    payload = generate_autonomous_operations_control_loop(root=tmp_path, write=False)
    assert payload["decision"] == "pause"
    assert any(item["type"] == "missing_or_unreadable_evidence" for item in payload["blocked_conditions"])


def test_recall_recommended_when_recall_state_active(tmp_path):
    baseline(tmp_path, presence="recall_sent")
    payload = generate_autonomous_operations_control_loop(root=tmp_path, write=False)
    assert payload["decision"] == "recall-recommended"
    assert any(item["type"] == "active_recall_lifecycle" for item in payload["blocked_conditions"])


def test_conflicting_evidence_pauses_without_recall_if_unknown_conflict(tmp_path):
    baseline(tmp_path, presence="recall_requested")
    payload = generate_autonomous_operations_control_loop(root=tmp_path, write=False)
    assert payload["decision"] == "recall-recommended"
    assert any(item["type"] == "recall_vs_ready_work" for item in payload["blocked_conditions"])


def test_failed_validation_pauses(tmp_path):
    baseline(tmp_path, local_status="failed")
    payload = generate_autonomous_operations_control_loop(root=tmp_path, write=False)
    assert payload["decision"] == "pause"
    assert any(item["type"] == "failed_validation" for item in payload["blocked_conditions"])


def test_no_ready_work_pauses(tmp_path):
    baseline(tmp_path, ready=0)
    payload = generate_autonomous_operations_control_loop(root=tmp_path, write=False)
    assert payload["decision"] == "pause"
    assert any(item["type"] == "no_ready_work" for item in payload["blocked_conditions"])


def test_pause_when_worker_blocked_and_writes_outputs(tmp_path):
    baseline(tmp_path, worker={"active_worker_count": 0, "blocked_worker_count": 1})
    payload = generate_autonomous_operations_control_loop(root=tmp_path)
    assert payload["decision"] == "pause"
    assert (tmp_path / "runtime/autonomy/autonomous_operations_state.json").exists()
    assert (tmp_path / "operations/autonomy/autonomous_operations_control_loop.md").exists()
    assert (tmp_path / "runtime/mission_control/autonomous_operations_control_loop.json").exists()
