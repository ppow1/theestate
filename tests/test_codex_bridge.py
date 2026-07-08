import json
import subprocess
import uuid
from pathlib import Path

from estate.core.codex_bridge import (
    CodexBridgeRequest,
    build_codex_command,
    normalize_text,
    parse_jsonl_output,
    parse_text_output,
    run_codex_bridge_request,
    validate_bridge_request,
)


def make_root(name: str) -> Path:
    root = Path("Temp") / "test_codex_bridge" / f"{name}_{uuid.uuid4().hex}"
    root.mkdir(parents=True, exist_ok=True)
    return root.resolve()


def write(root: Path, rel: str, text: str = "Prompt\n") -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def request(root: Path, **overrides) -> CodexBridgeRequest:
    prompt = write(root, "docs/prompts/request.md")
    values = {
        "request_id": "cbr-test-001",
        "prompt_source": "docs/prompts/request.md",
        "classification": "Estate Internal",
        "work_package_id": "WP-CODEX-BRIDGE-IMPLEMENTATION",
        "cwd": ".",
        "allowed_read_paths": ["docs/prompts"],
    }
    values.update(overrides)
    return CodexBridgeRequest(**values)


def test_request_validation_accepts_read_only_allowed_request():
    root = make_root("valid_read_only")
    req = request(root)

    result = validate_bridge_request(req, root)

    assert result.accepted is True
    assert result.errors == []


def test_request_validation_rejects_missing_classification():
    root = make_root("missing_classification")
    req = request(root, classification="")

    result = validate_bridge_request(req, root)

    assert result.accepted is False
    assert "classification is required" in result.errors


def test_request_validation_rejects_danger_full_access():
    root = make_root("danger_full_access")
    req = request(root, sandbox="danger-full-access")

    result = validate_bridge_request(req, root)

    assert result.accepted is False
    assert "danger-full-access is prohibited" in result.errors


def test_request_validation_rejects_cloud_apply():
    root = make_root("cloud_apply")
    req = request(root, cloud_apply_requested=True)

    result = validate_bridge_request(req, root)

    assert result.accepted is False
    assert "cloud apply is prohibited" in result.errors


def test_request_validation_rejects_bypass_flags():
    root = make_root("bypass_flags")
    req = request(root, bypass_flags=["--dangerously-bypass-approvals-and-sandbox"])

    result = validate_bridge_request(req, root)

    assert result.accepted is False
    assert "bypass flags are prohibited" in result.errors


def test_request_validation_rejects_unknown_provider_profile():
    root = make_root("unknown_profile")
    req = request(root, codex_home_profile="unknown-seat")

    result = validate_bridge_request(req, root)

    assert result.accepted is False
    assert "provider profile is unknown" in result.errors


def test_request_validation_rejects_prompt_outside_allowed_read_paths():
    root = make_root("outside_read")
    write(root, "outside/request.md")
    req = request(root, prompt_source="outside/request.md", allowed_read_paths=["docs/prompts"])

    result = validate_bridge_request(req, root)

    assert result.accepted is False
    assert "prompt source is outside allowed read paths" in result.errors


def test_request_validation_rejects_workspace_write_without_write_paths():
    root = make_root("write_without_paths")
    req = request(root, sandbox="workspace-write")

    result = validate_bridge_request(req, root)

    assert result.accepted is False
    assert "workspace-write requires explicit allowed write paths" in result.errors


def test_request_validation_rejects_too_broad_write_paths():
    root = make_root("broad_write")
    req = request(root, sandbox="workspace-write", allowed_write_paths=["."])

    result = validate_bridge_request(req, root)

    assert result.accepted is False
    assert any("allowed write path is too broad" in error for error in result.errors)


def test_default_command_shape_places_top_level_options_before_exec():
    root = make_root("command_shape")
    req = request(root)

    command = build_codex_command(req)

    assert command == [
        "codex",
        "--ask-for-approval",
        "never",
        "exec",
        "--sandbox",
        "read-only",
        "--color",
        "never",
        "--ephemeral",
        "--json",
        "-",
    ]


def test_jsonl_parser_extracts_final_message_and_token_usage():
    jsonl = "\n".join(
        [
            json.dumps({"type": "thread.started", "thread_id": "thread-1"}),
            json.dumps({"type": "turn.started"}),
            json.dumps({"type": "item.completed", "item": {"type": "agent_message", "text": "final answer"}}),
            json.dumps(
                {
                    "type": "turn.completed",
                    "usage": {
                        "input_tokens": 10,
                        "cached_input_tokens": 2,
                        "output_tokens": 4,
                        "reasoning_output_tokens": 0,
                    },
                }
            ),
        ]
    )

    parsed = parse_jsonl_output(jsonl)

    assert parsed.final_message == "final answer"
    assert parsed.usage["input_tokens"] == 10
    assert parsed.event_counts["turn.completed"] == 1


def test_jsonl_parser_records_failed_turns():
    parsed = parse_jsonl_output(
        "\n".join(
            [
                json.dumps({"type": "error", "message": "Reconnecting..."}),
                json.dumps({"type": "turn.failed", "error": {"message": "stream disconnected"}}),
            ]
        )
    )

    assert parsed.errors[0]["message"] == "Reconnecting..."
    assert parsed.failed_turns[0]["message"] == "stream disconnected"


def test_text_parser_extracts_stdout_final_message_and_stderr_token_usage():
    parsed = parse_text_output("hello\n", "warning\n\ntokens used\n5,930\n")

    assert parsed.final_message == "hello"
    assert parsed.usage == {"tokens_used": 5930}
    assert "warning" in parsed.telemetry["stderr"]


def test_ansi_and_control_cleanup_preserves_line_breaks():
    cleaned = normalize_text("\x1b[31mFAIL\x1b[0m\r\nbad\x08PASS\x07\n")

    assert cleaned == "FAIL\nbadPASS\n"


def test_cp437_mojibake_recovery_for_im():
    assert normalize_text("IΓÇÖm Codex.") == "I’m Codex."


def test_lifecycle_event_generation_and_status_snapshot():
    root = make_root("status_snapshot")
    req = request(root)

    result = run_codex_bridge_request(req, root=root, dry_run=True)

    event_types = [event["event_type"] for event in result.lifecycle_events]
    assert "--ask-for-approval" in result.command
    assert event_types[:3] == ["validation_started", "validation_passed", "job_accepted"]
    assert "execution_complete" in event_types
    status_path = root / result.status_snapshot_path
    snapshot = json.loads(status_path.read_text(encoding="utf-8"))
    assert snapshot["current_state"] == "Completed"
    assert snapshot["last_event"]["event_type"] == "execution_complete"


def test_audit_record_includes_lifecycle_event_and_status_references():
    root = make_root("audit_references")
    req = request(root)

    result = run_codex_bridge_request(req, root=root, dry_run=True)

    audit = json.loads((root / result.audit_path).read_text(encoding="utf-8"))
    assert audit["lifecycle_events_emitted"]
    assert audit["lifecycle_events_path"].endswith("events.jsonl")
    assert audit["current_status_snapshot_path"] == result.status_snapshot_path
    assert audit["promotion_recommendation"] == "review_command_before_live_execution"


def test_audit_record_redacts_secrets_and_does_not_include_raw_credentials():
    root = make_root("audit_redaction")
    req = request(root, request_id="cbr-secret-test")

    completed = subprocess.CompletedProcess(
        args=[],
        returncode=0,
        stdout=json.dumps({"type": "item.completed", "item": {"type": "agent_message", "text": "token=sk-testsecret1234567890"}})
        + "\n"
        + json.dumps({"type": "turn.completed", "usage": {"input_tokens": 1, "output_tokens": 1}})
        + "\n",
        stderr="Bearer secretbearertoken123456\n",
    )

    result = run_codex_bridge_request(req, root=root, run_process=lambda *args, **kwargs: completed)
    audit_text = (root / result.audit_path).read_text(encoding="utf-8")

    assert "sk-testsecret1234567890" not in audit_text
    assert "secretbearertoken123456" not in audit_text
    assert "[REDACTED_SECRET]" in audit_text
