import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from estate.core.operator_activity_stream import generate_operator_activity_stream, format_operator_activity_stream


def write_json(root, rel, payload):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def seed(root):
    write_json(root, "runtime/validation/local_operational_validation_run.json", {"generated_at": "2026-07-04T10:00:00+00:00", "summary": {"failed_steps": 1, "warning_count": 0}})
    write_json(root, "runtime/workers/worker_runtime_monitor.json", {"generated_at": "2026-07-04T10:01:00+00:00", "summary": {"stale_worker_count": 1, "warning_count": 1}, "warnings": [{"message": "Worker heartbeat is stale."}]})
    write_json(root, "runtime/collaboration/mailbox_index.json", {"generated_at": "2026-07-04T10:02:00+00:00", "summary": {"message_count": 2, "warning_count": 0}})
    write_json(root, "runtime/services/service_status_board.json", {"generated_at": "2026-07-04T10:03:00+00:00", "summary": {"warning_count": 0}})
    write_json(root, "collaboration/work_packages/completions/WP-9999_codex_done.json", {"work_package_id": "WP-9999", "completed_at": "2026-07-04T10:04:00Z", "summary": "Completed test package."})


def test_activity_stream_filters_verbosity_and_links(tmp_path):
    seed(tmp_path)
    payload = generate_operator_activity_stream(tmp_path, write=True, sources=["validation"], severities=["error"], verbosity="normal")

    assert payload["summary"]["filtered_event_count"] == 1
    assert payload["events"][0]["source"] == "validation"
    assert payload["events"][0]["severity"] == "error"
    assert payload["events"][0]["link"]["available"] is True
    assert payload["operations_center_integration"]["dockable_bottom_status_panel_ready"] is True
    assert (tmp_path / "runtime/steward/operator_activity_stream.json").exists()
    assert (tmp_path / "operations/steward/operator_activity_stream.md").exists()


def test_activity_stream_warning_only_and_detailed_verbosity(tmp_path):
    seed(tmp_path)
    normal = generate_operator_activity_stream(tmp_path, write=False, severities=["warning"], verbosity="normal")
    detailed = generate_operator_activity_stream(tmp_path, write=False, severities=["warning"], verbosity="detailed")

    assert normal["summary"]["filtered_event_count"] <= detailed["summary"]["filtered_event_count"]
    assert any("Worker heartbeat is stale" in event["message"] for event in detailed["events"])


def test_activity_stream_empty_state_for_no_matches(tmp_path):
    seed(tmp_path)
    payload = generate_operator_activity_stream(tmp_path, write=False, sources=["notifications"], severities=["error"], verbosity="quiet")
    markdown = format_operator_activity_stream(payload)

    assert payload["events"] == []
    assert payload["empty_state"] == "No activity matches the selected filters."
    assert "No activity matches" in markdown


def test_activity_stream_quiet_live_updates_include_new_completion(tmp_path):
    seed(tmp_path)
    first = generate_operator_activity_stream(tmp_path, write=False, sources=["completions"], verbosity="quiet")
    write_json(tmp_path, "collaboration/work_packages/completions/WP-1000_codex_done.json", {"work_package_id": "WP-1000", "completed_at": "2026-07-04T10:05:00Z", "summary": "New live completion."})
    second = generate_operator_activity_stream(tmp_path, write=False, sources=["completions"], verbosity="quiet")

    assert second["summary"]["filtered_event_count"] == first["summary"]["filtered_event_count"] + 1
    assert second["events"][0]["topic"] == "WP-1000"


def test_operator_activity_stream_cli(tmp_path):
    seed(tmp_path)
    result = subprocess.run(
        [sys.executable, "-m", "estate.cli.main", "operator-activity-stream", "--json", "--source", "validation", "--severity", "error"],
        cwd=tmp_path,
        env={"PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src")},
        capture_output=True,
        text=True,
        check=True,
    )

    payload = json.loads(result.stdout)
    assert payload["events"][0]["source"] == "validation"
    assert (tmp_path / "runtime/steward/operator_activity_stream.json").exists()
