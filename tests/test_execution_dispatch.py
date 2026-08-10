import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from estate.core.execution_dispatch import (
    CURRENT_OUTPUT,
    EVENTS_OUTPUT,
    HANDOFF_DIR,
    QUEUE_OUTPUT,
    REPORT_OUTPUT,
    block_dispatch_item,
    cancel_dispatch_item,
    complete_dispatch_item,
    enqueue_dispatch_request,
    format_execution_dispatch_report,
    generate_current_dispatch_snapshot,
    inspect_dispatch_item,
    list_dispatch_items,
    mark_dispatch_attention,
    prepare_codex_bridge_handoff,
    update_dispatch_state,
)


def write_json(root: Path, rel: str, payload):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return path


def write_text(root: Path, rel: str, text: str = "Prompt\n"):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def request_payload(**overrides):
    payload = {
        "dispatch_id": "dispatch-001",
        "work_package_id": "WP-EXAMPLE",
        "title": "Example dispatch",
        "requested_by": "Steward",
        "assigned_worker": "Codex Worker",
        "provider": "codex-cli-openai",
        "profile_label": "A2C3",
        "classification": "Estate Internal",
        "priority": "High",
        "state": "Queued",
        "prompt_source": "docs/governance/workers/WP-EXAMPLE.md",
        "sandbox": "read-only",
        "allowed_read_paths": ["docs/governance/workers"],
        "allowed_write_paths": [],
        "allowed_providers": ["codex-cli-openai", "codex-cli-ollama"],
        "forbidden_providers": [],
        "dependencies": [],
        "validation_commands": ["pytest -q tests/test_example.py"],
        "attention_required": False,
        "created_at": "2026-07-08T00:00:00Z",
        "updated_at": "2026-07-08T00:00:00Z",
    }
    payload.update(overrides)
    return payload


def read_json(root: Path, rel: Path):
    return json.loads((root / rel).read_text(encoding="utf-8"))


def read_events(root: Path):
    return [json.loads(line) for line in (root / EVENTS_OUTPUT).read_text(encoding="utf-8").splitlines() if line.strip()]


def test_enqueue_persists_dispatch_request_and_lists_queued_items(tmp_path):
    write_text(tmp_path, "docs/governance/workers/WP-EXAMPLE.md")

    item = enqueue_dispatch_request(request_payload(), tmp_path)
    listed = list_dispatch_items(tmp_path, state="Queued")

    assert item.dispatch_id == "dispatch-001"
    assert listed[0].dispatch_id == "dispatch-001"
    assert (tmp_path / QUEUE_OUTPUT).is_file()
    assert read_json(tmp_path, QUEUE_OUTPUT)["items"][0]["classification"] == "Estate Internal"


def test_inspect_and_update_state_emit_deterministic_item_state(tmp_path):
    enqueue_dispatch_request(request_payload(), tmp_path)

    updated = update_dispatch_state("dispatch-001", "Running", tmp_path, summary="Started locally.")
    inspected = inspect_dispatch_item("dispatch-001", tmp_path)

    assert updated.state == "Running"
    assert inspected.state == "Running"
    assert read_events(tmp_path)[-1]["event_type"] == "dispatch_started"


def test_cancel_block_complete_and_attention_operations(tmp_path):
    enqueue_dispatch_request(request_payload(), tmp_path)

    blocked = block_dispatch_item("dispatch-001", "Waiting for Ingrid boundary review.", tmp_path)
    attention = mark_dispatch_attention("dispatch-001", tmp_path, reason="Steward review requested.")
    completed = complete_dispatch_item("dispatch-001", tmp_path, result_reference="runtime/codex_bridge/dispatch-001/audit.json")

    assert blocked.state == "Blocked"
    assert attention.attention_required is True
    assert completed.state == "Completed"
    assert completed.result_reference == "runtime/codex_bridge/dispatch-001/audit.json"

    enqueue_dispatch_request(request_payload(dispatch_id="dispatch-002", created_at="2026-07-08T00:01:00Z"), tmp_path)
    cancelled = cancel_dispatch_item("dispatch-002", tmp_path, reason="Superseded.")

    event_types = [event["event_type"] for event in read_events(tmp_path)]
    assert "dispatch_blocked" in event_types
    assert "dispatch_awaiting_approval" in event_types
    assert "dispatch_completed" in event_types
    assert event_types[-1] == "dispatch_cancelled"
    assert cancelled.state == "Cancelled"


def test_preserves_profile_labels_and_provider_metadata(tmp_path):
    enqueue_dispatch_request(request_payload(profile_label="A2C3", provider_metadata={"seat_label": "A2C3"}), tmp_path)
    enqueue_dispatch_request(
        request_payload(
            dispatch_id="dispatch-ollama",
            provider="codex-cli-ollama",
            profile_label="local-ollama",
            created_at="2026-07-08T00:01:00Z",
        ),
        tmp_path,
    )

    snapshot = generate_current_dispatch_snapshot(tmp_path)
    labels = {(item["provider"], item["profile_label"]) for item in snapshot["provider_assignments"]}

    assert ("codex-cli-openai", "A2C3") in labels
    assert ("codex-cli-ollama", "local-ollama") in labels
    assert inspect_dispatch_item("dispatch-001", tmp_path).provider_metadata["seat_label"] == "A2C3"


def test_rejects_missing_classification(tmp_path):
    with pytest.raises(ValueError, match="classification is required"):
        enqueue_dispatch_request(request_payload(classification=""), tmp_path)


def test_current_snapshot_and_report_answer_queue_questions(tmp_path):
    enqueue_dispatch_request(request_payload(dependencies=["WP-DEPENDENCY"]), tmp_path)
    enqueue_dispatch_request(
        request_payload(
            dispatch_id="dispatch-ready",
            state="Ready",
            priority="Normal",
            created_at="2026-07-08T00:01:00Z",
        ),
        tmp_path,
    )
    block_dispatch_item("dispatch-001", "Dependency not complete.", tmp_path)

    snapshot = generate_current_dispatch_snapshot(tmp_path, generated_at="2026-07-08T00:02:00Z")
    report = format_execution_dispatch_report(snapshot)

    assert snapshot["summary"]["ready_count"] == 1
    assert snapshot["summary"]["blocked_count"] == 1
    assert snapshot["summary"]["attention_required_count"] == 1
    assert snapshot["waiting_on_dependencies"][0]["dispatch_id"] == "dispatch-001"
    assert "Provider/Profile Assignments" in report
    assert "dispatch-ready" in report
    assert (tmp_path / CURRENT_OUTPUT).is_file()
    assert (tmp_path / REPORT_OUTPUT).is_file()


def test_dispatch_events_include_required_fields(tmp_path):
    enqueue_dispatch_request(request_payload(), tmp_path)
    update_dispatch_state("dispatch-001", "Ready", tmp_path)
    prepare_codex_bridge_handoff("dispatch-001", tmp_path)

    events = read_events(tmp_path)
    assert [event["event_type"] for event in events] == [
        "dispatch_enqueued",
        "dispatch_ready",
        "dispatch_handoff_prepared",
    ]
    for event in events:
        assert event["event_id"]
        assert event["dispatch_id"] == "dispatch-001"
        assert event["work_package_id"] == "WP-EXAMPLE"
        assert event["provider"] == "codex-cli-openai"
        assert event["profile_label"] == "A2C3"
        assert event["timestamp"]
        assert "summary" in event


def test_prepare_codex_bridge_handoff_writes_dry_run_shape_without_live_execution(tmp_path):
    write_text(tmp_path, "docs/governance/workers/WP-EXAMPLE.md")
    enqueue_dispatch_request(request_payload(), tmp_path)

    handoff = prepare_codex_bridge_handoff("dispatch-001", tmp_path)

    assert handoff["request_id"] == "dispatch-001"
    assert handoff["dispatch_id"] == "dispatch-001"
    assert handoff["provider"] == "codex-cli-openai"
    assert handoff["profile_label"] == "A2C3"
    assert handoff["codex_home_profile"] == "A2C3"
    assert handoff["sandbox"] == "read-only"
    assert handoff["classification"] == "Estate Internal"
    assert handoff["allowed_read_paths"] == ["docs/governance/workers"]
    assert handoff["validation_commands"] == ["pytest -q tests/test_example.py"]
    assert handoff["dry_run"] is True
    assert handoff["handoff_mode"] == "dry_run_only_no_live_provider_invocation"
    assert (tmp_path / HANDOFF_DIR / "dispatch-001_codex_bridge_request.json").is_file()
    assert not (tmp_path / "runtime/codex_bridge").exists()


@pytest.mark.parametrize("seat", ["C1", "C2", "C3"])
def test_codex_dispatch_seat_reaches_bridge_handoff(tmp_path, seat):
    write_text(tmp_path, "docs/governance/workers/WP-EXAMPLE.md")
    payload = request_payload()
    payload["seat_id"] = seat
    enqueue_dispatch_request(payload, tmp_path)
    handoff = prepare_codex_bridge_handoff("dispatch-001", tmp_path)
    assert handoff["seat_id"] == seat
    assert handoff["codex_home_profile"] == seat


def test_unknown_codex_dispatch_seat_is_rejected(tmp_path):
    write_text(tmp_path, "docs/governance/workers/WP-EXAMPLE.md")
    payload = request_payload()
    payload["seat_id"] = "C4"
    enqueue_dispatch_request(payload, tmp_path)
    with pytest.raises(ValueError, match="seat_id"):
        prepare_codex_bridge_handoff("dispatch-001", tmp_path)


def test_deterministic_output_ordering_by_priority_created_at_and_id(tmp_path):
    enqueue_dispatch_request(request_payload(dispatch_id="dispatch-low", priority="Low", created_at="2026-07-08T00:00:00Z"), tmp_path)
    enqueue_dispatch_request(request_payload(dispatch_id="dispatch-high-b", priority="High", created_at="2026-07-08T00:01:00Z"), tmp_path)
    enqueue_dispatch_request(request_payload(dispatch_id="dispatch-high-a", priority="High", created_at="2026-07-08T00:01:00Z"), tmp_path)

    assert [item.dispatch_id for item in list_dispatch_items(tmp_path)] == [
        "dispatch-high-a",
        "dispatch-high-b",
        "dispatch-low",
    ]


def test_cli_enqueue_list_inspect_and_report_do_not_require_providers(tmp_path):
    write_text(tmp_path, "docs/governance/workers/WP-EXAMPLE.md")
    request_path = write_json(tmp_path, "request.json", request_payload())
    env = {
        "PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src"),
        "ESTATE_ROOT": str(tmp_path),
    }

    subprocess.run(
        [sys.executable, "-m", "estate.cli.main", "execution-dispatch", "enqueue", "--file", str(request_path), "--json"],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    result = subprocess.run(
        [sys.executable, "-m", "estate.cli.main", "execution-dispatch", "list", "--json"],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    report = subprocess.run(
        [sys.executable, "-m", "estate.cli.main", "execution-dispatch-report"],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )

    payload = json.loads(result.stdout)
    assert payload["items"][0]["dispatch_id"] == "dispatch-001"
    assert "Execution Dispatch Queue" in report.stdout
    assert (tmp_path / CURRENT_OUTPUT).is_file()
    assert not (tmp_path / "runtime/codex_bridge").exists()


def test_office_command_center_reads_generated_dispatch_artifact(tmp_path):
    enqueue_dispatch_request(request_payload(), tmp_path)
    update_dispatch_state("dispatch-001", "Ready", tmp_path)

    from estate.core.steward_command_center import generate_command_center

    payload = generate_command_center(tmp_path, write=False)

    assert payload["panels"]["execution_dispatch"]["available"] is True
    assert payload["status_bar"]["dispatch_ready_count"] == 1
    assert any(event["source"] == "execution_dispatch" for event in payload["activity_console"]["events"])
