import json
import subprocess
import sys

from estate.core.operational_events import OperationalEvent
from estate.core.operational_status import generate_summary_markdown, record_operational_event


def make_event(**overrides):
    data = {
        "event_id": overrides.pop("event_id", "evt-1"), "event_type": "Execution Started", "state": "Running",
        "created_at": "2026-07-08T00:00:00Z", "classification": "Estate Internal",
        "message": "Worker running", "request_id": "req-1",
    }
    data.update(overrides)
    return OperationalEvent.from_dict(data)


def test_latest_status_updated(tmp_path):
    paths = record_operational_event(make_event(), root=tmp_path)
    latest = json.loads(paths["latest"].read_text())
    assert latest["status"]["activity_id"] == "req-1"


def test_active_status_includes_running_activity(tmp_path):
    paths = record_operational_event(make_event(), root=tmp_path)
    active = json.loads(paths["active"].read_text())
    assert active[0]["current_state"] == "Running"


def test_recent_status_includes_completed_activity(tmp_path):
    paths = record_operational_event(make_event(event_type="Execution Complete", state="Completed", message="Done"), root=tmp_path)
    recent = json.loads(paths["recent"].read_text())
    assert recent[0]["current_state"] == "Completed"


def test_blocked_and_awaiting_approval_requires_attention(tmp_path):
    record_operational_event(make_event(event_id="evt-b", state="Blocked", event_type="Worker Blocked"), root=tmp_path)
    paths = record_operational_event(make_event(event_id="evt-a", request_id="req-2", state="Awaiting Approval", event_type="Waiting for Approval"), root=tmp_path)
    active = json.loads(paths["active"].read_text())
    assert all(item["requires_attention"] for item in active)


def test_summary_generation_works_with_no_activity(tmp_path):
    assert "No operational activity recorded" in generate_summary_markdown(root=tmp_path)


def test_summary_generation_redacts_sensitive_messages_unless_safe(tmp_path):
    record_operational_event(make_event(classification="Restricted", message="secret"), root=tmp_path)
    unsafe = generate_summary_markdown(root=tmp_path)
    assert "secret" not in unsafe
    record_operational_event(make_event(event_id="evt-safe", request_id="req-safe", classification="Restricted", message="safe", metadata={"summary_safe": True}), root=tmp_path)
    safe = generate_summary_markdown(root=tmp_path)
    assert "safe" in safe


def test_cli_summary_command_succeeds_with_and_without_activity():
    result = subprocess.run([sys.executable, "-m", "estate.cli.main", "operations-status-summary"], text=True, capture_output=True)
    assert result.returncode == 0
    assert "Operational Activity Summary" in result.stdout
