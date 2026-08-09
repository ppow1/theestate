import json
import subprocess
import sys
from pathlib import Path

import pytest

from estate.core.operational_events import OperationalEvent, append_event_artifact


def event_payload(**overrides):
    data = {
        "event_id": "evt-1", "event_type": "Execution Started", "state": "Running",
        "created_at": "2026-07-08T00:00:00Z", "classification": "Estate Internal",
        "message": "Worker started", "request_id": "req-1",
    }
    data.update(overrides)
    return data


def test_valid_event_accepted():
    event = OperationalEvent.from_dict(event_payload())
    assert event.validation_status == "not_validated"
    assert event.requires_attention is False


def test_invalid_classification_rejected():
    with pytest.raises(ValueError):
        OperationalEvent.from_dict(event_payload(classification="Secret"))


def test_invalid_state_rejected():
    with pytest.raises(ValueError):
        OperationalEvent.from_dict(event_payload(state="Mystery"))


def test_operator_attention_event_types_are_canonical():
    required = OperationalEvent.from_dict(event_payload(event_type="Operator Attention Required", state="Waiting", requires_attention=True))
    resolved = OperationalEvent.from_dict(event_payload(event_type="Operator Attention Resolved", state="Completed"))
    assert required.requires_attention is True
    assert resolved.state == "Completed"


def test_event_artifact_written(tmp_path):
    event = OperationalEvent.from_dict(event_payload())
    path = append_event_artifact(event, root=tmp_path)
    assert path.exists()
    assert json.loads(path.read_text().splitlines()[0])["event_id"] == "evt-1"


def test_cli_record_command_succeeds_for_valid_event(tmp_path):
    event_file = tmp_path / "event.json"
    event_file.write_text(json.dumps(event_payload(event_id="evt-cli", request_id="req-cli")), encoding="utf-8")
    result = subprocess.run([sys.executable, "-m", "estate.cli.main", "operations-event-record", "--event", str(event_file)], cwd=Path.cwd(), text=True, capture_output=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "Operational event recorded" in result.stdout


def test_cli_record_command_fails_for_invalid_event(tmp_path):
    event_file = tmp_path / "event.json"
    event_file.write_text(json.dumps(event_payload(classification="Secret")), encoding="utf-8")
    result = subprocess.run([sys.executable, "-m", "estate.cli.main", "operations-event-record", "--event", str(event_file)], cwd=Path.cwd(), text=True, capture_output=True)
    assert result.returncode == 1
