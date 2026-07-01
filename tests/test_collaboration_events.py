import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from estate.core.collaboration_events import append_event, generate_event_summary, read_events


def test_append_valid_event_writes_outputs(tmp_path):
    event = append_event(
        "work.claimed",
        "tests",
        {"worker": "worker.test"},
        subject_id="msg_test_001",
        root=tmp_path,
    )

    assert event["type"] == "work.claimed"
    assert (tmp_path / "runtime" / "collaboration" / "events" / "events.jsonl").exists()
    assert (tmp_path / "runtime" / "collaboration" / "events" / "latest.json").exists()
    assert (tmp_path / "collaboration" / "status" / "event_summary.json").exists()


def test_read_events_tolerates_missing_log(tmp_path):
    events, errors = read_events(root=tmp_path)

    assert events == []
    assert errors == []


def test_read_events_reports_malformed_records(tmp_path):
    log = tmp_path / "runtime" / "collaboration" / "events" / "events.jsonl"
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text(
        json.dumps(
            {
                "id": "evt_valid",
                "version": 1,
                "type": "message.routed",
                "created_at": "2026-07-01T00:00:00",
                "source": "tests",
                "subject_id": "msg_test",
                "classification": "Estate Internal",
                "payload": {},
            }
        )
        + "\n{not-json}\n"
        + json.dumps({"id": "evt_invalid", "type": "not.supported"})
        + "\n",
        encoding="utf-8",
    )

    events, errors = read_events(root=tmp_path)

    assert len(events) == 1
    assert len(errors) == 2


def test_event_summary_generation_counts_events_and_errors(tmp_path):
    append_event("work.completed", "tests", {"ok": True}, root=tmp_path)
    log = tmp_path / "runtime" / "collaboration" / "events" / "events.jsonl"
    with log.open("a", encoding="utf-8") as handle:
        handle.write("malformed\n")

    summary = generate_event_summary(root=tmp_path)

    assert summary["event_count"] == 1
    assert summary["counts_by_type"]["work.completed"] == 1
    assert summary["malformed_record_count"] == 1
    assert (tmp_path / "collaboration" / "status" / "event_summary.json").exists()


def test_collaboration_events_cli_registered():
    result = subprocess.run(
        [sys.executable, "-m", "estate.cli.main", "collaboration-events", "--json"],
        cwd=Path(__file__).resolve().parents[1],
        env={"PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src")},
        text=True,
        capture_output=True,
        check=True,
    )

    payload = json.loads(result.stdout)
    assert payload["version"] == 1
    assert "event_types" in payload
