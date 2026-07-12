import pytest

from estate.core.resident_runtime_operations import (
    ChatRunner, TurnCoordinator, diagnostic_snapshot, generate_continuity_package,
    monitoring_summary, reflection_recommendation, rehydrate_resident, validate_renewal,
)


def test_multi_resident_turns_are_deterministic_and_private():
    c = TurnCoordinator("room-a", ["alfred", "helen", "alfred", "ingrid"], max_fanout=2)
    turns = c.coordinate("status?", addressees=["helen"], open_floor=False)
    assert [t.speaker for t in turns] == ["helen"]
    assert turns[0].sequence == 1
    assert turns[0].disclosure["hidden_cognition_shared"] is False
    open_turns = c.coordinate("open", open_floor=True, abstain=["alfred"], failures={"helen": "timeout"})
    assert [t.speaker for t in open_turns] == ["alfred", "helen"]
    assert open_turns[0].status == "abstained"
    assert open_turns[1].status == "failed"


def test_reflection_recommendation_distinguishes_vessel_and_identity(tmp_path):
    rec = reflection_recommendation("alfred", {"context_congestion": True, "repeated_failure": True, "implementation": "degraded", "evidence": [{"secret": "x"}]}, root=tmp_path)
    assert rec["severity"] == "review"
    assert rec["implementation_vessel_health"] == "degraded"
    assert rec["may_initiate_renewal"] is False
    assert rec["evidence"][0]["secret"] == "[REDACTED]"


def test_continuity_package_blocks_missing_and_is_deterministic(tmp_path):
    root = tmp_path
    p = root / "docs/residents/alfred/Alfred_Resident_Profile_v0_1.md"
    p.parent.mkdir(parents=True)
    p.write_text("Alfred profile canonical source. " * 10)
    a = generate_continuity_package("alfred", root=root)
    b = generate_continuity_package("alfred", root=root)
    assert a["ready"] is True
    assert a["manifest"] == b["manifest"]
    bad = generate_continuity_package("helen", root=root)
    assert bad["ready"] is False
    assert bad["structural_warnings"][0]["type"] == "missing_mandatory_file"


def test_renewal_validation_and_rehydration_require_assignment_and_validation(tmp_path):
    p = tmp_path / "docs/residents/alfred/Alfred_Resident_Profile_v0_1.md"
    p.parent.mkdir(parents=True)
    p.write_text("Alfred profile canonical source. " * 10)
    pkg = generate_continuity_package("alfred", root=tmp_path)
    failed = validate_renewal(pkg, subject_id="alfred", old_impl="old", new_impl="new", root=tmp_path)
    assert failed["acceptance_recommendation"] == "fail"
    val = validate_renewal(pkg, subject_id="alfred", old_impl="old", new_impl="new", completed_assignment=True, root=tmp_path)
    receipt = rehydrate_resident({"subject_id":"alfred", "target_implementation":"new", "continuity_package":pkg, "validation":val, "authority_scope":"resident", "expected_assignment":"bounded task"}, root=tmp_path)
    assert receipt["loaded_sources"] == pkg["reading_order"]
    assert receipt["prior_implementation_fallback"] == "read_only"
    assert receipt["self_approved"] is False


def test_diagnostics_and_monitoring_are_privacy_safe(tmp_path):
    snap = diagnostic_snapshot("evelyn", root=tmp_path, evidence={"identity":{"state":"healthy"}, "provider":{"state":"degraded"}, "message_body":"private", "conversation_boundary_violation": True})
    assert snap["overall_state"] == "blocked"
    assert snap["redacted"] is True
    summary = monitoring_summary([snap], root=tmp_path)
    assert summary["alerts"][0]["severity"] == "blocked"
    assert summary["stores_private_transcripts"] is False
    assert summary["can_activate_validate_accept_or_retire"] is False


def test_chat_runner_requires_completion_signal_and_redacts(tmp_path):
    runner = ChatRunner({"job_id":"wp-4062", "worker":"chatgpt", "prompts":["one"], "credential":"secret"}, root=tmp_path)
    state = runner.save()
    assert state["state"] == "queued"
    assert state["manifest"]["credential"] == "[REDACTED]"
    runner.transition("submitted", {"turn_id":"t1"})
    with pytest.raises(ValueError):
        runner.transition("completed", {})
    done = runner.transition("completed", {"completion_signal": "artifact present"})
    assert done["prompt_index"] == 1
