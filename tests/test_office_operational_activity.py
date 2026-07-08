import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from estate.core.office_operational_activity import load_office_operational_activity
from estate.core.steward_command_center import generate_command_center, render_command_center_html

NOW = datetime(2026, 7, 8, 12, 0, tzinfo=timezone.utc)


def write_json(root, rel, payload):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def status(**overrides):
    data = {
        "activity_id": "act-1",
        "current_state": "Running",
        "last_event_type": "Execution Started",
        "last_message": "Worker is running",
        "started_at": "2026-07-08T11:55:00Z",
        "updated_at": "2026-07-08T11:59:00Z",
        "elapsed_seconds": 240,
        "worker_id": "worker.codex.1",
        "provider_id": "codex-cli",
        "provider_type": "Codex CLI",
        "assignment_id": "ASSIGN-1",
        "work_package_id": "WP-0602",
        "classification": "Estate Internal",
        "budget_source": "steward-approved",
        "validation_status": "not_validated",
        "requires_attention": False,
        "artifact_paths": ["runtime/example.json"],
        "metadata": {},
    }
    data.update(overrides)
    return data


def test_loader_handles_missing_files(tmp_path):
    panel = load_office_operational_activity(tmp_path, now=NOW)
    assert panel["available"] is False
    assert panel["runtime_directory_accessible"] is False
    assert "runtime/operations/status/latest.json" in panel["expected_status_artifact_paths"]


def test_loader_handles_valid_latest_status(tmp_path):
    write_json(tmp_path, "runtime/operations/status/latest.json", {"status": status()})
    panel = load_office_operational_activity(tmp_path, now=NOW)
    assert panel["latest_status"]["activity_id"] == "act-1"
    assert panel["summary"]["latest_status_available"] is True


def test_loader_handles_valid_active_status(tmp_path):
    write_json(tmp_path, "runtime/operations/status/active.json", [status()])
    panel = load_office_operational_activity(tmp_path, now=NOW)
    assert panel["groups"]["active"][0]["worker_id"] == "worker.codex.1"


def test_loader_handles_valid_recent_status(tmp_path):
    write_json(tmp_path, "runtime/operations/status/recent.json", [status(current_state="Completed", updated_at="2026-07-08T10:00:00Z")])
    panel = load_office_operational_activity(tmp_path, now=NOW)
    assert panel["groups"]["recently_completed"][0]["current_state"] == "Completed"


def test_loader_handles_malformed_json_without_crashing(tmp_path):
    path = tmp_path / "runtime/operations/status/active.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{not-json", encoding="utf-8")
    panel = load_office_operational_activity(tmp_path, now=NOW)
    assert panel["summary"]["error_count"] == 1
    assert "Malformed JSON" in panel["errors"][0]["message"]


def test_active_activity_renders(tmp_path):
    write_json(tmp_path, "runtime/operations/status/active.json", [status()])
    html = render_command_center_html(generate_command_center(tmp_path, write=False))
    assert "Operational Activity" in html
    assert "worker.codex.1" in html
    assert "ASSIGN-1" in html


def test_blocked_or_attention_required_activity_renders_prominently(tmp_path):
    write_json(tmp_path, "runtime/operations/status/active.json", [status(activity_id="blocked", current_state="Blocked", requires_attention=True, last_message="Need Steward decision")])
    html = render_command_center_html(generate_command_center(tmp_path, write=False))
    assert "Blocked / Attention Required (1)" in html
    assert "attention=True" in html
    assert "Need Steward decision" in html


def test_completed_activity_renders_in_recent_group(tmp_path):
    write_json(tmp_path, "runtime/operations/status/recent.json", [status(activity_id="done", current_state="Completed", updated_at="2026-07-08T10:00:00Z", last_message="Done")])
    html = render_command_center_html(generate_command_center(tmp_path, write=False))
    assert "Recently Completed (1)" in html
    assert "Done" in html


def test_sensitive_messages_redacted_unless_summary_safe(tmp_path):
    write_json(tmp_path, "runtime/operations/status/active.json", [
        status(activity_id="secret", classification="Steward Only", last_message="secret details"),
        status(activity_id="safe", classification="Local Only", last_message="safe summary", metadata={"summary_safe": True}),
    ])
    html = render_command_center_html(generate_command_center(tmp_path, write=False))
    assert "secret details" not in html
    assert "Sensitive operational message redacted" in html
    assert "safe summary" in html


def test_stale_data_is_marked_stale(tmp_path):
    write_json(tmp_path, "runtime/operations/status/active.json", [status(updated_at="2026-07-08T11:00:00Z")])
    panel = load_office_operational_activity(tmp_path, now=NOW)
    assert panel["groups"]["active"][0]["freshness"]["state"] == "stale"


def test_empty_state_renders_honestly(tmp_path):
    html = render_command_center_html(generate_command_center(tmp_path, write=False))
    assert "No active operational status found" in html
    assert "No fake green status is shown" in html
