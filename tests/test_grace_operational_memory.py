import json

from estate.core.consultation_store import ConsultationStore
from estate.core.grace_operational_memory import (
    classify_operational_request,
    derive_terminal_provenance_status,
    enforce_terminal_provenance_status,
    is_operational_state_query,
    read_operational_snapshot,
    render_operational_snapshot,
)


def _fixture_store(tmp_path):
    db = tmp_path / "consultations.db"
    store = ConsultationStore(db)
    root = store.allocate_root(objective="controlled fixture", status="continuation_required")
    turn = store.allocate_continuation(root.logical_consultation_id, status="response_received")
    store.append_response(turn.logical_consultation_id, {
        "content": "validated",
        "structured_decision": {"classification": "INFORMATION_ONLY"},
    }, response_id="resp-real")
    store.attach_execution_request(turn.logical_consultation_id, "exec-real", dispatch_id="dispatch-real", status="completed")
    store.record_execution_attempt("exec-real", "attempt-real", provider_id="provider-real", status="completed")
    return db, root.logical_consultation_id, turn.logical_consultation_id


def test_latest_completed_root_normalizes_continuation_and_counts_execution(tmp_path):
    db, root_id, turn_id = _fixture_store(tmp_path)
    cme = tmp_path / "cme.json"
    cme.write_text(json.dumps({"state": "IDLE", "result": "EMPTY_QUEUE"}), encoding="utf-8")
    snapshot = read_operational_snapshot(database_path=db, cme_state_path=cme)
    assert snapshot["authoritative"] is True
    assert snapshot["latest_completed_consultation"]["root_logical_id"] == root_id
    assert snapshot["latest_completed_consultation"]["latest_turn_logical_id"] == turn_id
    assert snapshot["latest_completed_consultation"]["execution_occurred"] is True
    assert snapshot["latest_completed_consultation"]["logical_execution_request_count"] == 1
    assert snapshot["latest_completed_consultation"]["physical_execution_attempt_count"] == 1
    assert snapshot["provenance"]["latest_completed_consultation"]["authority"] == "authoritative"


def test_unavailable_store_fails_closed(tmp_path):
    cme = tmp_path / "cme.json"
    cme.write_text(json.dumps({"state": "IDLE"}), encoding="utf-8")
    snapshot = read_operational_snapshot(database_path=tmp_path / "missing.db", cme_state_path=cme)
    assert snapshot["authoritative"] is False
    assert "STATE_UNAVAILABLE" in render_operational_snapshot(snapshot)
    assert snapshot["operational_memory_available"] is False


def test_operational_read_is_read_only_and_does_not_surface_plausible_fake_ids(tmp_path, monkeypatch):
    db, _, _ = _fixture_store(tmp_path)
    cme = tmp_path / "cme.json"
    cme.write_text(json.dumps({"state": "IDLE"}), encoding="utf-8")
    before = db.read_bytes()
    snapshot = read_operational_snapshot(database_path=db, cme_state_path=cme)
    after = db.read_bytes()
    rendered = render_operational_snapshot(snapshot)
    assert before == after
    assert snapshot["mutation_performed"] is False
    assert "consultation-root-78942" not in rendered
    assert "9.07" not in rendered
    assert "ec8-fake" not in rendered
    assert "exec-fake" not in rendered


def test_boundary_is_narrow_for_conceptual_conversation():
    assert is_operational_state_query("What makes Grace a good operations resident?") is False
    assert is_operational_state_query("Tell me the current operational status and latest consultation.") is True


def test_grace_gateway_operational_query_bypasses_model_and_session_mutation(monkeypatch, tmp_path):
    import estate.core.grace_operational_memory as memory
    from estate.core import resident_gateway

    snapshot = {
        "schema_version": "estate.grace.operational_memory.v1",
        "operation": "read_operational_snapshot",
        "authoritative": True,
        "operational_state": "IDLE",
        "latest_completed_consultation": {
            "root_logical_id": "9.00", "latest_turn_logical_id": "9.04",
            "final_state": "response_received", "execution_occurred": True,
            "logical_execution_request_count": 1, "physical_execution_attempt_count": 1,
        },
        "operational_memory_available": True, "provenance": {},
        "unavailable": [], "mutation_performed": False,
    }
    monkeypatch.setattr(memory, "read_operational_snapshot", lambda: snapshot)
    monkeypatch.setattr(resident_gateway, "process_chat", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("model path used")))
    code, body = resident_gateway.chat_completion({
        "model": "estate/grace",
        "messages": [{"role": "user", "content": "What is the current operational status and most recent completed consultation?"}],
        "stream": False,
    }, root=tmp_path)
    assert code == 200
    assert body["estate"]["operational_memory"]["runtime_bridge_invoked"] is True
    assert body["estate"]["operational_memory"]["native_tool_call"] is False
    assert not list(tmp_path.rglob("*"))


def test_action_claim_requires_authoritative_action_provenance():
    from estate.core.resident_interaction import guard_action_completion_claim

    guarded, metadata = guard_action_completion_claim("I recorded the smoke results and documented recovery.")
    assert "have not performed" in guarded
    assert metadata["claim_provenance"] == "unavailable/unverified"
    assert metadata["action_claim_blocked"] is True


def test_action_claim_accepts_successful_authoritative_action_and_inference_remains_allowed():
    from estate.core.resident_interaction import guard_action_completion_claim

    completed, metadata = guard_action_completion_claim(
        "I recorded the smoke results.",
        action_result={"status": "completed", "provenance": "authoritative_action", "action_id": "act-1"},
    )
    assert completed == "I recorded the smoke results."
    assert metadata["claim_provenance"] == "authoritative_action"
    inference, metadata = guard_action_completion_claim("The next sensible step is a read-only owner check.")
    assert inference.startswith("The next sensible")
    assert metadata["claim_provenance"] == "model_inference"


def test_read_provenance_can_support_verification_but_not_write_claims():
    from estate.core.resident_interaction import guard_action_completion_claim

    verified, metadata = guard_action_completion_claim(
        "I verified the live state.",
        action_result={"status": "verified", "provenance": "authoritative_read"},
    )
    assert verified == "I verified the live state."
    assert metadata["claim_provenance"] == "authoritative_read"
    blocked, metadata = guard_action_completion_claim(
        "I recorded the live state.",
        action_result={"status": "verified", "provenance": "authoritative_read"},
    )
    assert "have not performed" in blocked
    assert metadata["action_claim_blocked"] is True


def test_process_chat_does_not_false_closeout_without_action_result(monkeypatch, tmp_path):
    from estate.core import resident_interaction as interaction

    monkeypatch.setattr(
        interaction,
        "_fallback_response",
        lambda *args, **kwargs: "I recorded the smoke results and documented the recovery observations.",
    )
    monkeypatch.setattr(
        interaction.LocalOllamaAdapter,
        "generate",
        lambda *args, **kwargs: {"ok": True, "text": "I recorded the smoke results and documented the recovery observations.", "metadata": {"provider": "test", "fallback_used": False}},
    )
    result = interaction.process_chat("grace", "Record the smoke results and document recovery.", root=tmp_path)
    assert "have not performed" in result["turn"]["resident_response"]
    assert result["turn"]["claim_provenance"]["claim_provenance"] == "unavailable/unverified"


def test_composite_provenance_prompt_is_not_classified_as_direct_read():
    prompt = """Grace, this is a read-only provenance test. Do not create or modify consultations.

1. Did you actually record the grounding acceptance anywhere during this conversation?
2. Identify authoritative evidence.
3. Distinguish executed, recommended, requested, and pending.
End with PENDING_EXECUTION or INSUFFICIENT_EVIDENCE."""
    result = classify_operational_request(prompt)
    assert result["mode"] == "grounded_composite_reasoning"


def test_composite_gateway_preserves_request_and_composes_after_read(monkeypatch, tmp_path):
    from estate.core import resident_interaction
    from estate.core.resident_gateway import chat_completion

    monkeypatch.setattr(resident_interaction, "process_chat", lambda *args, **kwargs: {
        "turn": {"resident_response": "Partial operational snapshot only."}
    })
    prompt = """Grace, this is a read-only provenance test. Do not create or modify consultations, execution requests, Comms8 messages, files, or operational state.

1. Did you actually record the grounding acceptance anywhere during this conversation?
2. For each claimed action, identify authoritative evidence that proves it occurred.
3. If unavailable, say it was not performed.
4. Distinguish executed, recommended, requested, and pending actions.
5. End with AUTHORITATIVELY_COMPLETED, PENDING_EXECUTION, or INSUFFICIENT_EVIDENCE."""
    code, body = chat_completion({"model": "estate/grace", "messages": [{"role": "user", "content": prompt}], "stream": False}, root=tmp_path)
    content = body["choices"][0]["message"]["content"]
    assert code == 200
    assert "I did not actually record" in content
    assert "INSUFFICIENT_EVIDENCE" in content
    assert body["estate"]["composite_reasoning"]["original_request_preserved"] is True
    assert body["estate"]["composite_reasoning"]["model_reasoning_attempted"] is True
    assert not list(tmp_path.rglob("*"))


def test_response_modes_cover_direct_composite_and_conceptual_requests():
    assert classify_operational_request("What is the latest completed consultation?")["mode"] == "direct_authoritative_read"
    assert classify_operational_request("What is the latest root and why does its state matter?")["mode"] == "grounded_composite_reasoning"
    assert classify_operational_request("What is currently blocked and what should we recommend next?")["mode"] == "grounded_composite_reasoning"
    assert classify_operational_request("Explain how Grace's CME role differs from Alfred's attention role.")["mode"] == "conceptual"


def test_terminal_status_is_about_underlying_action_not_completed_inquiry():
    from estate.core.grace_operational_memory import build_composite_operational_evidence

    evidence = build_composite_operational_evidence({"authoritative": True}, "provenance")
    assert derive_terminal_provenance_status(evidence) == "INSUFFICIENT_EVIDENCE"
    assert enforce_terminal_provenance_status("The inquiry is complete.\nAUTHORITATIVELY_COMPLETED", "End with AUTHORITATIVELY_COMPLETED", evidence).endswith("INSUFFICIENT_EVIDENCE")


def test_successful_authoritative_action_selects_completed():
    evidence = {"action_evidence": {"authoritative_action_result": {"status": "completed", "provenance": "authoritative_action"}}}
    assert derive_terminal_provenance_status(evidence) == "AUTHORITATIVELY_COMPLETED"


def test_requested_pending_action_selects_pending_execution():
    evidence = {"action_evidence": {"requested_action_pending": True}}
    assert derive_terminal_provenance_status(evidence) == "PENDING_EXECUTION"


def test_read_evidence_does_not_emit_action_completion():
    evidence = {"action_evidence": {"authoritative_read_available": True, "provenance": "authoritative_read"}}
    assert derive_terminal_provenance_status(evidence) == "INSUFFICIENT_EVIDENCE"
