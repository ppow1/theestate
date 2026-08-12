import json

from estate.core.autonomous_chatgpt_mailbox_worker import (
    AutonomousChatGPTMailboxWorker,
    generic_worker_prompt,
    reserved_worker_prompt,
)
from estate.core.consultation_store import ConsultationStore


def _store_with_consultation(tmp_path, *, root_id="1.00", ec8="ec8-worker-1"):
    store = ConsultationStore(tmp_path / "consultations.db")
    record = store.allocate_root(status="awaiting_reasoning", objective="Return three recommendations")
    assert record.logical_consultation_id == root_id
    return store.attach_ec8(record.logical_consultation_id, ec8)


def test_generic_prompt_contains_no_request_id_and_requires_one_claim_next():
    prompt = generic_worker_prompt()
    assert "claim the next eligible reasoning request" in prompt.lower()
    assert "EMPTY_QUEUE" in prompt
    assert "WORKER_COMPLETE" in prompt
    assert "worker_id=chatgpt" in prompt
    assert "ec8-" not in prompt
    assert "INFORMATION_ONLY" in prompt
    assert "EXECUTION_RECOMMENDED" in prompt
    for field in ("objective", "required_capability", "allowed_scope", "prohibited_scope", "evidence_requirements", "validation_criteria", "consultation_correlation"):
        assert field in prompt
    assert "write_scope" in prompt
    assert "software_engineering_test" in prompt


def test_reserved_prompt_binds_exact_internal_lane_without_claim_next():
    prompt = reserved_worker_prompt("52.00", "ec8-reserved-52")
    assert "request_id=ec8-reserved-52" in prompt
    assert "worker_id=chatgpt" in prompt
    assert "lease_seconds=900" in prompt
    assert "do not call claim_next" in prompt.lower()


def test_worker_can_read_bounded_local_context_without_github(tmp_path):
    store = ConsultationStore(tmp_path / "consultations.db")
    consultation = store.allocate_root(status="resolved", objective="durable context")
    store.append_response(consultation.logical_consultation_id, {"content": "recommendation"})
    worker = AutonomousChatGPTMailboxWorker(store, state_path=tmp_path / "state.json")

    context = worker.bounded_local_context(consultation.consultation_root_id, latest=1)

    assert context["root_consultation_id"] == consultation.logical_consultation_id
    assert context["turns"][0]["logical_consultation_id"] == consultation.logical_consultation_id
    assert context["turns"][0]["response"] == {"content": "recommendation"}


def test_structured_information_only_is_persisted_without_execution_handoff(tmp_path):
    _store_with_consultation(tmp_path, ec8="ec8-info")
    store = ConsultationStore(tmp_path / "consultations.db")
    response = {
        "response_id": "resp-info",
        "content": '{"reasoning":"Three risks.","decision":{"classification":"INFORMATION_ONLY","rationale":"No bounded execution is needed."}}',
    }
    worker = AutonomousChatGPTMailboxWorker(
        store,
        state_path=tmp_path / "state.json",
        browser_runner=lambda *_: {"marker": "WORKER_COMPLETE"},
        read_request=lambda rid: {"request_id": rid, "state": "resolved", "response": response},
    )
    result = worker.run_once()
    assert result.status == "WORKER_COMPLETE"
    assert store.execution_requests(store.get("1.00").logical_consultation_id) == []
    assert store.get("1.00").response["structured_decision"]["classification"] == "INFORMATION_ONLY"


def test_structured_execution_decision_hands_off_without_duplicate_request(tmp_path):
    _store_with_consultation(tmp_path, ec8="ec8-execution")
    store = ConsultationStore(tmp_path / "consultations.db")
    response = {
        "response_id": "resp-execution",
        "content": '{"reasoning":"Inspect a bounded fixture.","decision":{"classification":"EXECUTION_RECOMMENDED","rationale":"The assumption needs verification.","execution":{"objective":"fixture diagnostic","required_capability":"software_engineering_test","allowed_scope":["src"],"prohibited_scope":["archive","runtime"],"evidence_requirements":["observed result"],"validation_criteria":"confirm the assumption","consultation_correlation":"1.00"}}}',
    }
    handoffs = []
    worker = AutonomousChatGPTMailboxWorker(
        store,
        state_path=tmp_path / "state.json",
        browser_runner=lambda *_: {"marker": "WORKER_COMPLETE"},
        read_request=lambda rid: {"request_id": rid, "state": "resolved", "response": response},
        decision_handler=lambda logical_id, normalized: handoffs.append((logical_id, normalized)) or {"status": "execution_requested", "execution_request_id": "exec-test"},
    )
    result = worker.run_once()
    assert result.status == "EXECUTION_REQUESTED"
    assert result.reason == "exec-test"
    assert handoffs and handoffs[0][0] == "1.00"


def test_invalid_structured_execution_decision_fails_closed(tmp_path):
    _store_with_consultation(tmp_path, ec8="ec8-invalid")
    store = ConsultationStore(tmp_path / "consultations.db")
    response = {
        "response_id": "resp-invalid",
        "content": '{"reasoning":"run it","decision":{"classification":"EXECUTION_RECOMMENDED","execution":{"objective":"x","required_capability":"software_engineering_test","allowed_scope":["."],"prohibited_scope":["archive"],"evidence_requirements":["result"],"validation_criteria":"check","consultation_correlation":"1.00"}}}',
    }
    worker = AutonomousChatGPTMailboxWorker(
        store,
        state_path=tmp_path / "state.json",
        browser_runner=lambda *_: {"marker": "WORKER_COMPLETE"},
        read_request=lambda rid: {"request_id": rid, "state": "resolved", "response": response},
    )
    result = worker.run_once()
    assert result.status == "EXECUTION_DECISION_INVALID"
    assert store.execution_requests("1.00") == []


def test_incomplete_execution_recommendation_can_queue_format_repair_without_execution(tmp_path):
    _store_with_consultation(tmp_path, ec8="ec8-format-repair")
    store = ConsultationStore(tmp_path / "consultations.db")
    response = {
        "response_id": "resp-format-repair",
        "content": '{"reasoning":"repair is warranted","decision":{"classification":"EXECUTION_RECOMMENDED","execution":{"objective":"fixture repair","allowed_scope":["Temp/fixture"],"prohibited_scope":["production","runtime"]}}}',
    }
    repairs = []
    worker = AutonomousChatGPTMailboxWorker(
        store,
        state_path=tmp_path / "state.json",
        browser_runner=lambda *_: {"marker": "WORKER_COMPLETE"},
        read_request=lambda rid: {"request_id": rid, "state": "resolved", "response": response},
        format_repair_handler=lambda logical_id, reason: repairs.append((logical_id, reason)) or {"logical_consultation_id": "1.01"},
    )
    result = worker.run_once()
    assert result.status == "FORMAT_REPAIR_REQUESTED"
    assert repairs and repairs[0][0] == "1.00"
    assert store.execution_requests("1.00") == []


def test_empty_queue_does_not_wake_browser(tmp_path):
    store = ConsultationStore(tmp_path / "consultations.db")
    calls = []
    worker = AutonomousChatGPTMailboxWorker(store, state_path=tmp_path / "state.json", browser_runner=lambda *_: calls.append(True))
    result = worker.run_once()
    assert result.status == "EMPTY_QUEUE"
    assert calls == []
    assert json.loads((tmp_path / "state.json").read_text())["state"] == "IDLE"


def test_single_consultation_processes_exactly_one_and_updates_store(tmp_path):
    store = ConsultationStore(tmp_path / "consultations.db")
    consultation = _store_with_consultation(tmp_path)
    browser_calls = []

    def browser(script, prompt):
        browser_calls.append((script, prompt))
        return {"marker": "WORKER_COMPLETE"}

    reads = []
    def read(request_id):
        assert request_id == "ec8-worker-1"
        reads.append(True)
        if len(reads) == 1:
            return {"request_id": request_id, "state": "queued"}
        return {"request_id": request_id, "state": "resolved", "response": {"content": "three recommendations"}}

    worker = AutonomousChatGPTMailboxWorker(store, state_path=tmp_path / "state.json", browser_runner=browser, read_request=read)
    result = worker.run_once()
    stored = store.get(consultation.logical_consultation_id)
    assert result.status == "WORKER_COMPLETE"
    assert len(browser_calls) == 1
    assert stored.status == "resolved"
    assert stored.response == {"content": "three recommendations"}


def test_multiple_consultations_process_only_oldest_one_per_activation(tmp_path):
    store = ConsultationStore(tmp_path / "consultations.db")
    first = _store_with_consultation(tmp_path, ec8="ec8-first")
    second = store.allocate_root(status="awaiting_reasoning", objective="second")
    second = store.attach_ec8(second.logical_consultation_id, "ec8-second")
    processed = []
    worker = AutonomousChatGPTMailboxWorker(
        store,
        state_path=tmp_path / "state.json",
        browser_runner=lambda *_: {"marker": "WORKER_COMPLETE"},
        read_request=lambda rid: processed.append(rid) or {"state": "resolved", "response": {"content": rid}},
    )
    assert worker.run_once().ec8_request_id == "ec8-first"
    assert processed == ["ec8-first"]
    assert store.get(second.logical_consultation_id).status == "awaiting_reasoning"


def test_browser_disconnect_fails_without_claiming_or_fabricating(tmp_path):
    store = ConsultationStore(tmp_path / "consultations.db")
    consultation = _store_with_consultation(tmp_path)
    worker = AutonomousChatGPTMailboxWorker(
        store,
        state_path=tmp_path / "state.json",
        browser_runner=lambda *_: (_ for _ in ()).throw(RuntimeError("chatgpt_disconnect")),
        read_request=lambda _rid: {"state": "queued"},
    )
    result = worker.run_once()
    assert result.status == "ERROR"
    assert store.get(consultation.logical_consultation_id).status == "awaiting_reasoning"
    assert "chatgpt_disconnect" in json.loads((tmp_path / "state.json").read_text())["reason"]


def test_context_required_preserves_truthful_continuation_state(tmp_path):
    store = ConsultationStore(tmp_path / "consultations.db")
    consultation = _store_with_consultation(tmp_path)
    worker = AutonomousChatGPTMailboxWorker(
        store,
        state_path=tmp_path / "state.json",
        browser_runner=lambda *_: {"marker": "CONTEXT_REQUIRED"},
        read_request=lambda _rid: {"state": "queued"},
    )
    assert worker.run_once().status == "CONTEXT_REQUIRED"
    assert store.get(consultation.logical_consultation_id).status == "continuation_required"


def test_comms8_reconnect_or_github_outage_does_not_change_browser_contract(tmp_path):
    store = ConsultationStore(tmp_path / "consultations.db")
    consultation = _store_with_consultation(tmp_path)
    worker = AutonomousChatGPTMailboxWorker(
        store,
        state_path=tmp_path / "state.json",
        browser_runner=lambda _script, prompt: {"marker": "WORKER_COMPLETE", "prompt_has_no_id": "ec8-worker-1" not in prompt},
        read_request=lambda _rid: (_ for _ in ()).throw(ConnectionError("comms8_unavailable")),
    )
    result = worker.run_once()
    assert result.status == "ERROR"
    assert store.get(consultation.logical_consultation_id).status == "awaiting_reasoning"
    assert json.loads((tmp_path / "state.json").read_text())["state"] == "ERROR"


def test_live_attachment_readiness_failure_does_not_submit_prompt(tmp_path):
    store = ConsultationStore(tmp_path / "consultations.db")
    consultation = _store_with_consultation(tmp_path)
    calls = []
    worker = AutonomousChatGPTMailboxWorker(
        store,
        state_path=tmp_path / "state.json",
        browser_runner=lambda *_: calls.append(True) or {"marker": "READINESS_FAILED", "reason": "LIVE_APP_NOT_FOUND"},
        read_request=lambda _rid: {"state": "queued"},
    )
    result = worker.run_once()
    assert result.status == "ERROR"
    assert result.reason == "LIVE_APP_NOT_FOUND"
    assert calls == [True]
    assert store.get(consultation.logical_consultation_id).status == "awaiting_reasoning"
    assert json.loads((tmp_path / "state.json").read_text())["reason"] == "LIVE_APP_NOT_FOUND"


def test_active_foreign_lease_is_not_stolen_or_submitted(tmp_path):
    store = ConsultationStore(tmp_path / "consultations.db")
    consultation = _store_with_consultation(tmp_path)
    calls = []
    worker = AutonomousChatGPTMailboxWorker(
        store,
        state_path=tmp_path / "state.json",
        browser_runner=lambda *_: calls.append(True) or {"marker": "WORKER_COMPLETE"},
        read_request=lambda _rid: {
            "state": "acknowledged",
            "claim": {"worker_id": "other-worker", "lease_expires_at": "2999-01-01T00:00:00Z"},
        },
    )
    result = worker.run_once()
    assert result.status == "ERROR"
    assert result.reason == "active_foreign_lease:other-worker"
    assert calls == []
    assert store.get(consultation.logical_consultation_id).status == "awaiting_reasoning"


def test_active_canonical_lease_is_not_duplicated_after_worker_timeout(tmp_path):
    store = ConsultationStore(tmp_path / "consultations.db")
    consultation = _store_with_consultation(tmp_path)
    calls = []
    worker = AutonomousChatGPTMailboxWorker(
        store,
        state_path=tmp_path / "state.json",
        browser_runner=lambda *_: calls.append(True) or {"marker": "WORKER_COMPLETE"},
        read_request=lambda _rid: {"state": "acknowledged", "claim": {"worker_id": "chatgpt", "lease_expires_at": "2999-01-01T00:00:00Z"}},
    )
    result = worker.run_once()
    assert result.reason == "active_lease_in_progress"
    assert calls == []


def test_stable_assistant_requires_authoritative_comms8_completion(tmp_path):
    consultation_store = ConsultationStore(tmp_path / "consultations.db")
    consultation = consultation_store.allocate_root(status="awaiting_reasoning", objective="stable response")
    consultation_store.attach_ec8(consultation.logical_consultation_id, "ec8-stable")
    worker = AutonomousChatGPTMailboxWorker(
        consultation_store,
        state_path=tmp_path / "state.json",
        browser_runner=lambda *_: {"marker": "ASSISTANT_RESPONSE_STABLE", "trace": [{"state": "FINAL_ASSISTANT_STABLE"}]},
        read_request=lambda _rid: {"state": "resolved", "response": {"content": "authoritative"}},
    )
    assert worker.run_once().status == "WORKER_COMPLETE"

    consultation_store = ConsultationStore(tmp_path / "not-authoritative.db")
    consultation = consultation_store.allocate_root(status="awaiting_reasoning", objective="stable response")
    consultation_store.attach_ec8(consultation.logical_consultation_id, "ec8-stable-2")
    worker = AutonomousChatGPTMailboxWorker(
        consultation_store,
        state_path=tmp_path / "state-2.json",
        browser_runner=lambda *_: {"marker": "ASSISTANT_RESPONSE_STABLE"},
        read_request=lambda _rid: {"state": "acknowledged"},
    )
    assert worker.run_once().reason == "authoritative_comms8_completion_not_proven"


def test_browser_completion_failure_preserves_precise_classification(tmp_path):
    consultation_store = ConsultationStore(tmp_path / "consultations.db")
    consultation = consultation_store.allocate_root(status="awaiting_reasoning", objective="timeout")
    consultation_store.attach_ec8(consultation.logical_consultation_id, "ec8-timeout")
    worker = AutonomousChatGPTMailboxWorker(
        consultation_store,
        state_path=tmp_path / "state.json",
        browser_runner=lambda *_: {"marker": "BROWSER_COMPLETION_FAILED", "reason": "CHATGPT_GENERATION_EXCEEDED_TIMEOUT", "trace": []},
        read_request=lambda _rid: {"state": "acknowledged"},
    )
    result = worker.run_once()
    assert result.reason == "CHATGPT_GENERATION_EXCEEDED_TIMEOUT"


def test_expired_foreign_lease_allows_canonical_worker_recovery(tmp_path):
    store = ConsultationStore(tmp_path / "consultations.db")
    consultation = _store_with_consultation(tmp_path)
    reads = []
    worker = AutonomousChatGPTMailboxWorker(
        store,
        state_path=tmp_path / "state.json",
        browser_runner=lambda _script, prompt: {"marker": "WORKER_COMPLETE", "worker_id_required": "worker_id=chatgpt" in prompt},
        read_request=lambda _rid: reads.append(True) or ({"state": "queued"} if len(reads) == 1 else {"state": "resolved", "response": {"content": "done"}}),
    )
    assert worker.run_once().status == "WORKER_COMPLETE"
    assert store.get(consultation.logical_consultation_id).status == "resolved"


def test_missing_proposition_does_not_enter_evidence_adapter(tmp_path):
    store = ConsultationStore(tmp_path / "consultations.db")
    consultation = store.allocate_root(
        status="awaiting_reasoning",
        objective="I want a second opinion on this, not from you.",
        question="I want a second opinion on this, not from you.",
    )
    store.attach_ec8(consultation.logical_consultation_id, "ec8-context-repair")
    calls = []
    response = json.dumps({
        "reasoning": "CONTEXT_REQUIRED",
        "decision": {"classification": "MORE_REASONING_REQUIRED", "evidence_request": {
            "objective": "Provide the missing consultation subject.",
            "evidence_type": "consultation_materials",
            "allowed_scope": [],
            "prohibited_scope": ["/"],
            "required_capability": "repository_read",
            "evidence_requirements": ["proposition"],
            "consultation_correlation": "1.00",
        }},
    })
    worker = AutonomousChatGPTMailboxWorker(
        store,
        state_path=tmp_path / "state.json",
        browser_runner=lambda *_: {"marker": "WORKER_COMPLETE"},
        read_request=lambda _rid: {"state": "resolved", "response": {"response_id": "resp-context", "content": response}},
        decision_handler=lambda *_: calls.append(True) or {"status": "execution_requested"},
    )
    result = worker.run_once()
    assert result.status == "CONTEXT_REQUIRED"
    assert result.reason == "missing_persisted_proposition"
    assert calls == []
    assert store.get("1.00").status == "continuation_required"
