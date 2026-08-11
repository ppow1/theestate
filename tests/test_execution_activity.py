import json
import subprocess
import sys
from pathlib import Path

from estate.core.execution_activity import (
    CURRENT_OUTPUT,
    EVENTS_OUTPUT,
    REPORT_OUTPUT,
    generate_execution_activity_surface,
    parse_activity_jsonl,
)


def write_json(root: Path, rel: str, payload):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return path


def write_jsonl(root: Path, rel: str, rows):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")
    return path


def test_parses_jsonl_activity_events_and_preserves_unknown_event_types(tmp_path):
    path = write_jsonl(tmp_path, "runtime/execution_activity/events.jsonl", [
        {
            "event_id": "evt-known",
            "request_id": "req-known",
            "event_type": "execution_started",
            "state": "Running",
            "timestamp": "2026-07-08T00:00:01Z",
            "summary": "Started.",
        },
        {
            "event_id": "evt-future",
            "request_id": "req-future",
            "event_type": "future_provider_signal",
            "state": "Running",
            "timestamp": "2026-07-08T00:00:02Z",
            "summary": "Future event type.",
        },
    ])

    events, warnings = parse_activity_jsonl(path)

    assert warnings == []
    assert [event.event_type for event in events] == ["execution_started", "future_provider_signal"]


def test_missing_runtime_files_do_not_fail_and_generate_empty_artifacts(tmp_path):
    snapshot = generate_execution_activity_surface(tmp_path, generated_at="2026-07-08T00:00:00Z")

    assert snapshot["summary"]["event_count"] == 0
    assert snapshot["active"] == []
    assert snapshot["warnings"]
    assert (tmp_path / CURRENT_OUTPUT).is_file()
    assert (tmp_path / REPORT_OUTPUT).is_file()
    assert (tmp_path / EVENTS_OUTPUT).is_file()


def test_aggregates_activity_categories_and_preserves_profile_labels(tmp_path):
    write_jsonl(tmp_path, "runtime/execution_activity/events.jsonl", [
        {
            "event_id": "evt-active",
            "request_id": "req-active",
            "work_package_id": "WP-ACTIVE",
            "source": "execution_activity",
            "worker_label": "Codex Seat 3",
            "provider": "codex-cli-openai",
            "profile_label": "A2C3",
            "state": "Running",
            "event_type": "execution_started",
            "timestamp": "2026-07-08T00:00:01Z",
            "classification": "Estate Internal",
            "validation_status": "not_started",
            "summary": "Execution started.",
        },
        {
            "event_id": "evt-blocked",
            "request_id": "req-blocked",
            "work_package_id": "WP-BLOCKED",
            "worker_label": "Codex Seat 2",
            "provider": "codex-cli-openai",
            "profile_label": "A2C2",
            "state": "Awaiting Approval",
            "event_type": "waiting_for_approval",
            "timestamp": "2026-07-08T00:00:02Z",
            "attention_required": True,
            "summary": "Approval needed.",
        },
        {
            "event_id": "evt-failed",
            "request_id": "req-failed",
            "work_package_id": "WP-FAILED",
            "worker_label": "Validation Worker",
            "provider": "pytest",
            "state": "Failed",
            "event_type": "validation_failed",
            "timestamp": "2026-07-08T00:00:03Z",
            "summary": "Validation failed.",
        },
        {
            "event_id": "evt-complete",
            "request_id": "req-complete",
            "work_package_id": "WP-COMPLETE",
            "worker_label": "Codex Seat 1",
            "provider": "codex-cli-openai",
            "profile_label": "A2C1",
            "state": "Completed",
            "event_type": "execution_complete",
            "timestamp": "2026-07-08T00:00:04Z",
            "summary": "Execution complete.",
        },
    ])

    snapshot = generate_execution_activity_surface(tmp_path, generated_at="2026-07-08T00:00:05Z")

    assert [item["request_id"] for item in snapshot["active"]] == ["req-active"]
    assert [item["request_id"] for item in snapshot["blocked"]] == ["req-blocked"]
    assert [item["request_id"] for item in snapshot["attention_required"]] == ["req-failed", "req-blocked"]
    assert [item["request_id"] for item in snapshot["failed"]] == ["req-failed"]
    assert [item["request_id"] for item in snapshot["recently_completed"]] == ["req-complete"]
    assert snapshot["active"][0]["profile_label"] == "A2C3"
    codex_provider = next(provider for provider in snapshot["providers"] if provider["provider"] == "codex-cli-openai")
    assert codex_provider["profile_labels"] == ["A2C1", "A2C2", "A2C3"]
    assert codex_provider["saturation_status"] == "unknown"


def test_codex_bridge_events_and_current_status_feed_the_surface(tmp_path):
    write_jsonl(tmp_path, "runtime/codex_bridge/cbr-001/events.jsonl", [
        {
            "event_id": "cbr-001-0002-execution_started",
            "event_type": "execution_started",
            "request_id": "cbr-001",
            "work_package_id": "WP-CODEX-BRIDGE-IMPLEMENTATION",
            "worker_label": "codex-bridge",
            "provider": "codex-cli-openai",
            "profile_label": "A2C3",
            "current_state": "Running",
            "timestamp": "2026-07-08T00:01:00Z",
            "security_classification": "Estate Internal",
            "summary": "Codex CLI child process started.",
        },
    ])
    write_json(tmp_path, "runtime/codex_bridge/current_status.json", {
        "request_id": "cbr-002",
        "worker": "codex-bridge",
        "current_assignment": "WP-CODEX-BRIDGE-IMPLEMENTATION",
        "current_state": "Completed",
        "elapsed_seconds": 1,
        "provider": "codex-cli-openai",
        "profile_label": "A2C2",
        "security_classification": "Estate Internal",
        "validation_status": "passed",
        "last_event": {"event_id": "cbr-002-0005-execution_complete", "event_type": "execution_complete", "summary": "Dry-run completed."},
        "attention_required": False,
        "updated_at": "2026-07-08T00:02:00Z",
    })

    snapshot = generate_execution_activity_surface(tmp_path, generated_at="2026-07-08T00:03:00Z")

    assert any(item["request_id"] == "cbr-001" for item in snapshot["active"])
    assert any(item["request_id"] == "cbr-002" for item in snapshot["recently_completed"])
    assert any("runtime/codex_bridge/cbr-001/events.jsonl" in source for source in snapshot["sources"])


def test_generated_artifacts_redact_secrets_auth_paths_and_raw_output_fields(tmp_path):
    write_jsonl(tmp_path, "runtime/execution_activity/events.jsonl", [
        {
            "event_id": "evt-secret",
            "request_id": "req-secret",
            "event_type": "execution_started",
            "state": "Running",
            "timestamp": "2026-07-08T00:00:01Z",
            "summary": "token=sk-testsecret1234567890 auth at C:\\Users\\Pat\\.codex\\auth.json",
            "stdout": "secret stdout should be excluded",
            "stderr": "secret stderr should be excluded",
        }
    ])

    generate_execution_activity_surface(tmp_path, generated_at="2026-07-08T00:00:02Z")
    combined = (
        (tmp_path / EVENTS_OUTPUT).read_text(encoding="utf-8")
        + (tmp_path / CURRENT_OUTPUT).read_text(encoding="utf-8")
        + (tmp_path / REPORT_OUTPUT).read_text(encoding="utf-8")
    )

    assert "sk-testsecret1234567890" not in combined
    assert ".codex" not in combined
    assert "auth.json" not in combined
    assert "secret stdout" not in combined
    assert "secret stderr" not in combined
    assert "[REDACTED_SECRET]" in combined
    assert "[REDACTED_AUTH_PATH]" in combined


def test_cli_generates_current_snapshot_json(tmp_path):
    write_jsonl(tmp_path, "runtime/execution_activity/events.jsonl", [
        {
            "event_id": "evt-cli",
            "request_id": "req-cli",
            "event_type": "execution_started",
            "state": "Running",
            "timestamp": "2026-07-08T00:00:01Z",
            "summary": "CLI visible.",
        }
    ])

    result = subprocess.run(
        [sys.executable, "-m", "estate.cli.main", "execution-activity", "--json"],
        cwd=tmp_path,
        env={"PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src"), "ESTATE_ROOT": str(tmp_path)},
        capture_output=True,
        text=True,
        check=True,
    )
    payload = json.loads(result.stdout)

    assert payload["summary"]["active_count"] == 1
    assert (tmp_path / CURRENT_OUTPUT).is_file()
    assert (tmp_path / REPORT_OUTPUT).is_file()


def test_office_command_center_reads_generated_execution_activity_artifact(tmp_path):
    write_json(tmp_path, "runtime/execution_activity/current.json", {
        "version": 1,
        "generated_at": "2026-07-08T00:00:00Z",
        "source": "runtime/execution_activity/events.jsonl",
        "active": [],
        "blocked": [],
        "attention_required": [],
        "recently_completed": [],
        "failed": [],
        "providers": [],
        "warnings": [],
        "summary": {"active_count": 2, "blocked_count": 1, "attention_required_count": 1, "failed_count": 0},
    })

    from estate.core.steward_command_center import generate_command_center

    payload = generate_command_center(tmp_path, write=False)

    assert payload["panels"]["execution_activity"]["available"] is True
    assert payload["status_bar"]["execution_active_count"] == 2
    assert payload["status_bar"]["execution_blocked_count"] == 1
    assert any(event["source"] == "execution_activity" for event in payload["activity_console"]["events"])


def test_multiple_physical_resources_remain_distinct_in_office_activity(tmp_path):
    write_jsonl(tmp_path, "runtime/execution_activity/events.jsonl", [
        {
            "event_id": "evt-gpu-a",
            "request_id": "dispatch-a",
            "event_type": "execution_started",
            "state": "Running",
            "timestamp": "2026-08-11T18:10:13Z",
            "provider": "qwen.local.text",
            "compute_resource_id": "host:nvidia:GPU-A",
            "gpu_uuid": "GPU-A",
            "actual_runtime_resource_id": "host:nvidia:GPU-B",
            "actual_runtime_gpu_uuid": "GPU-B",
            "placement_match": False,
            "runtime_lane_id": "lane-a",
            "model_identity": "model-a",
            "reservation_reference": "reservation-a",
        },
        {
            "event_id": "evt-gpu-b",
            "request_id": "dispatch-b",
            "event_type": "execution_started",
            "state": "Running",
            "timestamp": "2026-08-11T18:10:13Z",
            "provider": "qwen.local.text",
            "compute_resource_id": "host:nvidia:GPU-B",
            "gpu_uuid": "GPU-B",
            "runtime_lane_id": "lane-b",
            "model_identity": "model-b",
            "reservation_reference": "reservation-b",
        },
    ])

    snapshot = generate_execution_activity_surface(tmp_path)

    assert snapshot["summary"]["active_count"] == 2
    assert {item["compute_resource_id"] for item in snapshot["active"]} == {
        "host:nvidia:GPU-A",
        "host:nvidia:GPU-B",
    }
    assert {item["runtime_lane_id"] for item in snapshot["active"]} == {"lane-a", "lane-b"}
    assert {item["reservation_reference"] for item in snapshot["active"]} == {"reservation-a", "reservation-b"}
    mismatch = next(item for item in snapshot["active"] if item["request_id"] == "dispatch-a")
    assert mismatch["gpu_uuid"] == "GPU-A"
    assert mismatch["actual_runtime_gpu_uuid"] == "GPU-B"
    assert mismatch["placement_match"] is False
