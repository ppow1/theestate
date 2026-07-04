import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from estate.core.operations_notification_center import (
    acknowledge_operations_notification,
    generate_operations_notification_center,
)
from estate.core.steward_command_center import generate_command_center


def write_json(root, rel, payload):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def seed(root):
    write_json(root, "runtime/services/service_status_board.json", {"generated_at": "2026-07-04T10:00:00+00:00", "summary": {"warning_count": 1}, "warnings": [{"message": "Service degraded."}]})
    write_json(root, "runtime/validation/local_operational_validation_run.json", {"generated_at": "2026-07-04T10:01:00+00:00", "summary": {"failed_steps": 1, "warning_count": 0}})
    write_json(root, "runtime/workers/worker_runtime_monitor.json", {"generated_at": "2026-07-04T10:02:00+00:00", "summary": {"warning_count": 1}, "warnings": [{"message": "Worker stale."}]})
    write_json(root, "runtime/collaboration/mailbox_index.json", {"generated_at": "2026-07-04T10:03:00+00:00", "messages": [{"message_id": "m1", "title": "Review needed", "requires_ack": True, "created_at": "2026-07-04T10:03:00+00:00", "path": "collaboration/messages/m1.json"}]})
    msg = root / "collaboration/messages/m1.json"
    msg.parent.mkdir(parents=True, exist_ok=True)
    msg.write_text("{}", encoding="utf-8")
    write_json(root, "collaboration/work_packages/completions/WP-9999_codex_done.json", {"work_package_id": "WP-9999", "completed_at": "2026-07-04T10:04:00+00:00", "summary": "Ready for review.", "ready_for_ca_review": True})


def test_notification_center_aggregates_filters_links_and_missing_sources(tmp_path):
    seed(tmp_path)
    payload = generate_operations_notification_center(tmp_path, write=True, severities=["warning"])

    assert payload["authority"] == "aggregator_only_not_source_of_truth"
    assert payload["summary"]["filtered_notification_count"] >= 3
    assert payload["summary"]["unavailable_source_count"] > 0
    assert all(note["severity"] == "warning" for note in payload["notifications"])
    assert any(note["source_link"]["available"] for note in payload["notifications"])
    assert payload["operations_center_integration"]["acknowledgement_mutates_authoritative_sources"] is False
    assert (tmp_path / "runtime/notifications/operations_notification_center.json").exists()
    assert (tmp_path / "operations/notifications/operations_notification_center.md").exists()


def test_notification_center_local_acknowledgement_does_not_change_source(tmp_path):
    seed(tmp_path)
    first = generate_operations_notification_center(tmp_path, write=False, sources=["mailboxes"])
    note_id = first["notifications"][0]["id"]
    acknowledge_operations_notification(note_id, tmp_path)
    second = generate_operations_notification_center(tmp_path, write=False, sources=["mailboxes"], acknowledged=True)

    assert second["notifications"][0]["id"] == note_id
    assert second["notifications"][0]["locally_acknowledged"] is True
    source = json.loads((tmp_path / "runtime/collaboration/mailbox_index.json").read_text(encoding="utf-8"))
    assert "ack_status" not in source["messages"][0]


def test_notification_center_cli_and_command_center_integration(tmp_path):
    seed(tmp_path)
    result = subprocess.run(
        [sys.executable, "-m", "estate.cli.main", "operations-notification-center", "--json", "--source", "validation"],
        cwd=tmp_path,
        env={"PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src")},
        capture_output=True,
        text=True,
        check=True,
    )
    payload = json.loads(result.stdout)
    center = generate_command_center(tmp_path, write=True)

    assert payload["filters"]["sources"] == ["validation"]
    assert center["status_bar"]["notification_count"] >= 1
    assert "operations_notification_center" in center["panels"]
    assert "Operations Center Notification Center" in (tmp_path / "runtime/steward/command_center.html").read_text(encoding="utf-8")
