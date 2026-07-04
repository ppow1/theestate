import json
from datetime import datetime, timezone
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from estate.core.autonomous_operations_audit import append_autonomous_operations_audit, build_autonomous_operations_audit_record, read_audit_records


def write_json(root, rel, payload):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def baseline(root, decision="continue", presence="present", ready=1):
    write_json(root, "runtime/autonomy/autonomous_operations_state.json", {"generated_at": "2026-07-03T00:00:00Z", "decision": decision, "reason": f"{decision} reason", "recommended_next_action": "Review next advisory step.", "blocked_conditions": []})
    write_json(root, "runtime/work_packages/autonomous_work_queue_scheduler.json", {"summary": {"ready_count": ready}})
    write_json(root, "runtime/workers/worker_runtime_monitor.json", {"summary": {"active_worker_count": 0, "blocked_worker_count": 0}})
    write_json(root, "runtime/steward/steward_presence_state.json", {"current_state": presence})
    write_json(root, "runtime/notifications/notification_router_report.json", {})
    write_json(root, "runtime/audit/recall_audit_log.json", {"records": []})
    write_json(root, "runtime/validation/local_operational_validation_run.json", {"steps": [{"status": "ok"}]})
    write_json(root, "runtime/validation/operational_validation_report.json", {"status": "ok"})
    write_json(root, "runtime/briefings/morning_briefing.json", {"sections": {}})
    write_json(root, "runtime/operations/morning_briefing.json", {"sections": {}})


def test_append_behavior_and_parseable_jsonl(tmp_path):
    baseline(tmp_path)
    append_autonomous_operations_audit(root=tmp_path, now=datetime(2026, 7, 3, 1, tzinfo=timezone.utc))
    append_autonomous_operations_audit(root=tmp_path, now=datetime(2026, 7, 3, 2, tzinfo=timezone.utc))
    records = read_audit_records(tmp_path)
    assert len(records) == 2
    assert records[0]["timestamp"] == "2026-07-03T01:00:00Z"
    assert records[1]["timestamp"] == "2026-07-03T02:00:00Z"
    assert (tmp_path / "operations/autonomy/autonomous_operations_audit.md").exists()


def test_missing_evidence_is_visible_and_unknown_if_continue(tmp_path):
    baseline(tmp_path, decision="continue")
    (tmp_path / "runtime/workers/worker_runtime_monitor.json").unlink()
    record = build_autonomous_operations_audit_record(root=tmp_path)
    assert record["decision"] == "unknown"
    assert any(item["type"] == "missing_evidence" for item in record["blocked_conditions"])


def test_conflicting_evidence_recording(tmp_path):
    baseline(tmp_path, decision="continue", presence="recall_sent", ready=1)
    record = build_autonomous_operations_audit_record(root=tmp_path)
    assert any(item["type"] == "continue_vs_recall_state" for item in record["blocked_conditions"])
    assert any(item["type"] == "recall_vs_ready_work" for item in record["blocked_conditions"])


def test_continue_pause_recall_unknown_decisions(tmp_path):
    for decision in ["continue", "pause", "recall_recommended", "unknown"]:
        root = tmp_path / decision
        baseline(root, decision=decision)
        record = build_autonomous_operations_audit_record(root=root)
        assert record["decision"] == decision


def test_failed_validation_records_blocked_condition(tmp_path):
    baseline(tmp_path, decision="pause")
    write_json(tmp_path, "runtime/validation/local_operational_validation_run.json", {"steps": [{"status": "failed"}]})
    record = build_autonomous_operations_audit_record(root=tmp_path)
    assert any(item["type"] == "failed_validation" for item in record["blocked_conditions"])
