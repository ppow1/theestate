import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from estate.core.decision_queue import generate_decision_queue, format_decision_queue_markdown
from estate.core.steward_command_center import generate_command_center, render_command_center_html


def write_json(root, rel, payload):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_decision_queue_renders_empty_state(tmp_path):
    queue = generate_decision_queue(tmp_path, write=False)

    assert queue["summary"]["decision_count"] == 0
    assert queue["empty_state"] == "No pending Steward decisions were found in available local artifacts."
    assert queue["constraints"]["does_not_approve_decisions"] is True
    assert queue["notifies_steward"] is False
    assert "No pending Steward decisions" in format_decision_queue_markdown(queue)


def test_decision_queue_renders_representative_decisions(tmp_path):
    write_json(tmp_path, "runtime/audit/recall_audit_log.json", {
        "records": [{"record_id": "recall-1", "recall_reason": "operational", "acknowledgement_state": "pending"}]
    })
    write_json(tmp_path, "runtime/notifications/notification_router_report.json", {
        "notifications": [{"id": "notification-1", "class": "recall", "summary": "Steward-only decision", "reason": "security", "requested_by": "alfred", "priority": "urgent", "action": "prepare_recall_delivery", "eligible_for_immediate_delivery": True}]
    })
    write_json(tmp_path, "runtime/alfred/operational_briefing.json", {
        "messages_requiring_acknowledgement": [{"id": "msg-1", "title": "Acknowledge review", "created_by": "Chief Architect", "ack_status": "pending"}]
    })
    write_json(tmp_path, "runtime/briefings/morning_briefing.json", {
        "sections": {"pending_approvals": [{"id": "WP-X", "title": "Review work package", "path": "collaboration/work_packages/pending/WP-X.md"}]}
    })
    (tmp_path / "collaboration/work_packages/open").mkdir(parents=True)
    (tmp_path / "collaboration/work_packages/open/WP-BLOCK.md").write_text("# Blocked Work\n\n## Blockers\n- Needs Steward decision\n", encoding="utf-8")
    write_json(tmp_path, "collaboration/messages/msg_ack.json", {"id": "msg_ack", "created_by": "Helen", "requires_ack": True, "ack_status": "pending", "payload": {"title": "Ack required"}})

    queue = generate_decision_queue(tmp_path, write=True)

    assert queue["summary"]["decision_count"] >= 6
    titles = [item["title"] for item in queue["decisions"]]
    assert "Steward-only decision" in titles
    assert "Blocked Work" in titles
    assert (tmp_path / "runtime/steward/decision_queue.json").exists()
    assert (tmp_path / "operations/steward/decision_queue.md").exists()


def test_decision_queue_handles_missing_source_artifacts(tmp_path):
    queue = generate_decision_queue(tmp_path, write=False)

    assert any(w["type"] == "missing_source_artifact" for w in queue["source_warnings"])
    assert queue["summary"]["empty"] is True


def test_command_center_includes_generated_decision_queue_panel(tmp_path):
    write_json(tmp_path, "collaboration/messages/msg_ack.json", {"id": "msg_ack", "created_by": "Helen", "requires_ack": True, "ack_status": "pending", "payload": {"title": "Ack required"}})

    payload = generate_command_center(tmp_path, write=False)
    html = render_command_center_html(payload)

    assert payload["panels"]["steward_decision_queue"]["available"] is True
    assert "Ack required" in html


def test_decision_queue_cli_registration(tmp_path):
    result = subprocess.run(
        [sys.executable, "-m", "estate.cli.main", "decision-queue", "--json"],
        cwd=tmp_path,
        env={"PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src")},
        capture_output=True,
        text=True,
        check=True,
    )

    payload = json.loads(result.stdout)
    assert payload["summary"]["decision_count"] == 0
    assert (tmp_path / "runtime/steward/decision_queue.json").exists()
