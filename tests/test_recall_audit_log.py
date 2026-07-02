import json
from pathlib import Path

from estate.core.notification_router import route_notification_events
from estate.core.recall_audit_log import AUDIT_LOG_PATH, append_recall_audit_record, generate_recall_audit_summary


def _notification():
    event = {
        "id": "evt-recall-1",
        "source": "worker-ca3",
        "event_type": "recall_candidate",
        "requested_by": "alfred",
        "alfred_validated": True,
        "recall_reason": "operational",
        "priority": "urgent",
        "triggering_artifact": "collaboration/work_packages/pending/WP-0037_SERIES_recall_audit_log_v1.md",
        "blocked_decision": "Steward-only decision required.",
        "steward_only_rationale": "Existing authority is insufficient.",
        "options_or_recommended_next_action": "Recall Steward for decision.",
        "consequence_of_waiting": "Affected decision path remains paused.",
        "continuity_assessment": "Unrelated work may continue.",
        "supporting_references": ["docs/operations/Steward_Recall_Decision_Model_v1.md"],
    }
    return route_notification_events([event], write=False)["notifications"][0]


def _delivery(**overrides):
    payload = {
        "ok": True,
        "dry_run": False,
        "transport": "gotify",
        "delivery_id": "delivery-1",
        "status": "delivered",
        "message": "Accepted by adapter.",
        "completed_at": "2026-07-02T23:00:00+00:00",
    }
    payload.update(overrides)
    return payload


def test_successful_recall_record_creation(tmp_path):
    result = append_recall_audit_record(_notification(), _delivery(), root=tmp_path)

    assert result["ok"] is True
    assert result["appended"] is True
    path = tmp_path / AUDIT_LOG_PATH
    log = json.loads(path.read_text(encoding="utf-8"))
    record = log["records"][0]
    assert log["summary"]["record_count"] == 1
    assert record["originating_worker"] == "worker-ca3"
    assert record["requested_by"] == "alfred"
    assert record["recall_reason"] == "operational"
    assert record["transport"] == "gotify"
    assert record["delivery_result"]["status"] == "delivered"
    assert record["acknowledgement_state"] == "pending"
    assert record["acknowledgement_timestamp"] is None


def test_duplicate_safe_append_does_not_add_second_record(tmp_path):
    notification = _notification()
    delivery = _delivery()

    first = append_recall_audit_record(notification, delivery, root=tmp_path)
    second = append_recall_audit_record(notification, delivery, root=tmp_path)

    assert first["appended"] is True
    assert second["appended"] is False
    log = json.loads((tmp_path / AUDIT_LOG_PATH).read_text(encoding="utf-8"))
    assert len(log["records"]) == 1


def test_dry_run_returns_record_without_writing_log(tmp_path):
    result = append_recall_audit_record(_notification(), _delivery(delivery_id="dry-run-1", dry_run=True), root=tmp_path, dry_run=True)

    assert result["ok"] is True
    assert result["dry_run"] is True
    assert result["record"]["delivery_result"]["dry_run"] is True
    assert not (tmp_path / AUDIT_LOG_PATH).exists()


def test_markdown_summary_is_generated_from_committed_log(tmp_path):
    append_recall_audit_record(_notification(), _delivery(), root=tmp_path)

    result = generate_recall_audit_summary(root=tmp_path)

    assert result["ok"] is True
    assert (tmp_path / result["path"]).exists()
    assert "Recall Audit Log Summary" in (tmp_path / result["path"]).read_text(encoding="utf-8")
