import pytest

from estate.core.consultation_store import ConsultationStore
from estate.core.grace_consultation_loop import (
    GraceConsultationLoop,
    external_reasoning_claim_present,
    external_reasoning_provenance,
    is_continuation_request,
    is_explicit_delegation_request,
)


def test_resident_gateway_routes_only_explicit_delegation(monkeypatch):
    from estate.core.resident_gateway import chat_completion

    class FakeLoop:
        def __init__(self, *args, **kwargs):
            pass

        def delegate(self, text, *, session_id=None, **kwargs):
            return {
                "logical_consultation_id": "7.00",
                "root_logical_id": "7.00",
                "ec8_request_id": "ec8-fake",
                "response_id": "resp-fake",
                    "worker": "chatgpt",
                    "status": "validating",
                    "response": "authoritative advice",
                    "authoritative": True,
                }

    monkeypatch.setattr("estate.core.grace_consultation_loop.GraceConsultationLoop", FakeLoop)
    code, body = chat_completion({"model": "estate/grace", "messages": [{"role": "user", "content": "Ask ChatGPT for a second opinion."}], "stream": False})
    assert code == 200
    assert body["choices"][0]["message"]["content"] == "authoritative advice"
    assert body["estate"]["consultation"]["ec8_request_id"] == "ec8-fake"



def test_explicit_delegation_boundary_is_narrow():
    assert is_explicit_delegation_request("Grace, ask ChatGPT for a second opinion.")
    assert is_explicit_delegation_request("Please consult ChatGPT.")
    assert not is_explicit_delegation_request("Grace, summarize the current state.")


def test_ordinary_second_opinion_language_routes_to_existing_workflow():
    assert is_explicit_delegation_request("I want a second opinion on this, not from you.")
    assert is_explicit_delegation_request("Give me another perspective on the recommendation.")
    assert is_explicit_delegation_request("Please obtain an independent reasoning review.")


def test_second_opinion_on_this_resolves_immediately_prior_grace_recommendation():
    from estate.core.resident_gateway import _second_opinion_context

    context = _second_opinion_context({"messages": [
        {"role": "user", "content": "Should Grace remain central as parallelism grows?"},
        {"role": "assistant", "content": "My recommendation is to remain central with bounded delegation."},
        {"role": "user", "content": "I want a second opinion on this, not from you."},
    ]}, latest_user="I want a second opinion on this, not from you.", session_id="chat-1")
    assert context["purpose"] == "independent_second_opinion"
    assert context["proposition"].startswith("Should Grace remain")
    assert context["current_recommendation"].startswith("My recommendation")


def test_unrelated_or_missing_prior_referent_does_not_create_context():
    from estate.core.resident_gateway import _second_opinion_context

    assert _second_opinion_context({"messages": [
        {"role": "user", "content": "I want a second opinion on this, not from you."},
    ]}, latest_user="I want a second opinion on this, not from you.", session_id="chat-1") is None


def test_external_claim_requires_authoritative_correlated_result():
    assert external_reasoning_claim_present("I obtained a second opinion from Engineering.")
    evidence = external_reasoning_provenance(
        {
            "authoritative": True,
            "root_logical_id": "12.00",
            "logical_consultation_id": "12.01",
            "ec8_request_id": "ec8-real",
            "response_id": "resp-real",
            "worker": "chatgpt",
            "status": "validating",
            "response": "bounded contribution",
        },
        "I want a second opinion on this, not from you.",
    )
    assert evidence["external_reasoning_performed"] is True
    assert evidence["consultation_root"] == "12.00"
    assert evidence["consultation_turn"] == "12.01"
    assert evidence["comms8_request_id"] == "ec8-real"
    assert evidence["request_fingerprint"]


def test_missing_authoritative_response_cannot_support_external_claim():
    evidence = external_reasoning_provenance(
        {
            "authoritative": False,
            "root_logical_id": "12.00",
            "logical_consultation_id": "12.01",
            "ec8_request_id": "ec8-real",
            "response_id": None,
            "worker": "chatgpt",
            "status": "awaiting_reasoning",
        },
        "I want a second opinion on this, not from you.",
    )
    assert evidence["external_reasoning_performed"] is False
    assert evidence["consultation_root"] is None
    assert evidence["response_id"] is None


def test_unproven_external_provider_claim_is_detected_for_gateway_guard():
    from estate.core.resident_gateway import _guard_unproven_external_claim

    result = _guard_unproven_external_claim(
        "I obtained a second opinion and Engineering concluded the timing was safe."
    )
    assert "Performed: No" in result
    assert "no external conclusion is asserted" in result


def test_root_persists_before_create_and_returns_authoritative_result(tmp_path):
    store = ConsultationStore(tmp_path / "consultations.db")
    observed = {}

    def create(arguments):
        records = store.search(status="awaiting_reasoning")
        observed["persisted_before_create"] = len(records) == 1
        observed["arguments"] = arguments
        return {"request_id": "ec8-live-root", "state": "queued"}

    def wake():
        observed["prompt_has_id"] = False
        return {"status": "WORKER_COMPLETE"}

    def read(request_id):
        assert request_id == "ec8-live-root"
        return {"state": "resolved", "response": {"response_id": "resp-1", "content": "three recommendations"}}

    loop = GraceConsultationLoop(store, create_request=create, read_request=read, wake_worker=wake, sleep=lambda _: None)
    result = loop.delegate("Grace, ask ChatGPT for a second opinion on restart risks.", session_id="chat-1", tags=("comms8",))
    record = store.get(result["logical_consultation_id"])
    assert observed["persisted_before_create"] is True
    assert observed["arguments"]["workflow_id"] == "estate-grace-consultation-1-00"
    assert observed["arguments"]["input_data"]["consultation_id"] == "1.00"
    assert result["ec8_request_id"] == "ec8-live-root"
    assert result["authoritative"] is True
    assert record.status == "validating"
    assert record.response["content"] == "three recommendations"


def test_second_opinion_persists_bounded_proposition_before_transport(tmp_path):
    store = ConsultationStore(tmp_path / "consultations.db")
    observed = {}

    def create(arguments):
        record = store.get("1.00")
        observed["record"] = record
        observed["package"] = arguments["input_data"]["durable_context"]
        return {"request_id": "ec8-proposition", "state": "queued"}

    loop = GraceConsultationLoop(
        store,
        create_request=create,
        read_request=lambda _: {"state": "resolved", "response": {"response_id": "resp-proposition", "content": "independent analysis"}},
        wake_worker=lambda: {"status": "WORKER_COMPLETE"},
        sleep=lambda _: None,
    )
    result = loop.delegate(
        "I want a second opinion on this, not from you.",
        session_id="chat-1",
        second_opinion_context={
            "purpose": "independent_second_opinion",
            "proposition": "Should Grace remain the central operational orchestrator as parallelism grows?",
            "current_recommendation": "Grace should remain central, with bounded resident delegation.",
            "constraints": ["No execution is requested."],
            "requested_analysis": ["evaluate independently"],
            "bounded_context": "user: orchestration question\nassistant: Grace recommendation",
            "source_interaction": {"session_id": "chat-1"},
        },
    )
    assert observed["record"].objective.startswith("Should Grace remain")
    assert observed["record"].current_evidence["second_opinion"]["current_recommendation"].startswith("Grace should")
    assert observed["package"]["second_opinion"]["proposition"].startswith("Should Grace remain")
    assert result["logical_consultation_id"] == "1.00"


def test_proposition_context_repair_is_root_continuation_and_idempotent(tmp_path):
    store = ConsultationStore(tmp_path / "consultations.db")
    root = store.allocate_root(status="response_received", objective="I want a second opinion on this, not from you.", question="I want a second opinion on this, not from you.")
    store.append_response(root.logical_consultation_id, {"content": "CONTEXT_REQUIRED", "response_id": "resp-old"}, response_id="resp-old")
    calls = []
    loop = GraceConsultationLoop(
        store,
        create_request=lambda args: calls.append(args) or {"request_id": "ec8-repair", "state": "queued"},
    )
    first = loop.create_proposition_context_continuation(
        "1.00",
        proposition="Should Grace remain the central operational orchestrator as parallelism grows?",
        current_recommendation="Remain central with bounded delegation.",
        bounded_context="bounded prior exchange",
    )
    second = loop.create_proposition_context_continuation(
        "1.00",
        proposition="Should Grace remain the central operational orchestrator as parallelism grows?",
    )
    child = store.get(first["logical_consultation_id"])
    assert child.logical_consultation_id == "1.01"
    assert child.root_logical_id == "1.00"
    assert child.parent_logical_id == "1.00"
    assert child.continuation_reason == "missing_persisted_proposition"
    assert child.current_evidence["second_opinion"]["proposition"].startswith("Should Grace remain")
    assert second["idempotent"] is True
    assert len(calls) == 1


def test_create_failure_retains_identity_and_does_not_allocate_retry_turn(tmp_path):
    store = ConsultationStore(tmp_path / "consultations.db")
    loop = GraceConsultationLoop(
        store,
        create_request=lambda _args: (_ for _ in ()).throw(ConnectionError("live_down")),
        read_request=lambda _rid: {},
        wake_worker=lambda: {},
        sleep=lambda _: None,
    )
    with pytest.raises(RuntimeError, match="comms8_create_failed"):
        loop.delegate("Ask ChatGPT to review this failure.")
    records = store.search(status="open")
    assert len(records) == 1
    assert records[0].logical_consultation_id == "1.00"
    assert records[0].ec8_request_id is None


def test_continuation_preserves_lineage_and_bounded_context(tmp_path):
    store = ConsultationStore(tmp_path / "consultations.db")
    root = store.allocate_root(status="validating", objective="restart reliability")
    root = store.append_response(root.logical_consultation_id, {"content": "Use bounded recovery."})
    store.set_status(root.logical_consultation_id, "validating")
    observed = {}

    def create(arguments):
        observed["arguments"] = arguments
        return {"request_id": "ec8-live-continuation", "state": "queued"}

    loop = GraceConsultationLoop(
        store,
        create_request=create,
        read_request=lambda rid: {"state": "resolved", "response": {"response_id": "resp-2", "content": "Add session reattachment."}},
        wake_worker=lambda: {},
        sleep=lambda _: None,
    )
    result = loop.delegate("Assume we tried the first recommendation and discovered a browser session loss after restart. Ask ChatGPT what changes.")
    record = store.get(result["logical_consultation_id"])
    assert record.logical_consultation_id == "1.01"
    assert record.parent_logical_id == "1.00"
    assert record.root_logical_id == "1.00"
    assert "Use bounded recovery." in (observed["arguments"]["input_data"]["prior_context_summary"] or "")


def test_context_required_and_no_fabricated_completion(tmp_path):
    store = ConsultationStore(tmp_path / "consultations.db")
    loop = GraceConsultationLoop(
        store,
        create_request=lambda _args: {"request_id": "ec8-context", "state": "queued"},
        read_request=lambda _rid: {"state": "queued"},
        wake_worker=lambda: {"status": "CONTEXT_REQUIRED"},
        sleep=lambda _: None,
    )
    with pytest.raises(RuntimeError, match="context_required"):
        loop.delegate("Ask ChatGPT to review this missing context.")
    record = store.get("1.00")
    assert record.status == "continuation_required"
    assert record.response is None


def test_expired_transport_retries_same_logical_turn_and_preserves_attempt(tmp_path):
    store = ConsultationStore(tmp_path / "consultations.db")
    record = store.allocate_root(status="awaiting_reasoning", objective="retry this")
    store = ConsultationStore(tmp_path / "consultations.db")
    store.attach_ec8(record.logical_consultation_id, "ec8-expired", "estate-grace-consultation-1-00")
    created = []

    def create(arguments):
        created.append(arguments)
        return {"request_id": "ec8-replacement", "state": "queued"}

    reads = []
    def read(request_id):
        reads.append(request_id)
        if request_id == "ec8-expired":
            return {"request_id": request_id, "state": "expired", "claim": {"worker_id": "codex"}}
        return {"request_id": request_id, "state": "resolved", "response": {"response_id": "resp-3", "content": "recovered"}}

    loop = GraceConsultationLoop(store, create_request=create, read_request=read, wake_worker=lambda: {"status": "WORKER_COMPLETE"}, sleep=lambda _: None)
    result = loop.recover_transport(record.logical_consultation_id)
    stored = store.get(record.logical_consultation_id)
    attempts = store.transport_attempts(record.logical_consultation_id)
    assert result["logical_consultation_id"] == "1.00"
    assert stored.ec8_request_id == "ec8-replacement"
    assert stored.status == "validating"
    assert [item.request_id for item in attempts] == ["ec8-expired", "ec8-replacement"]
    assert attempts[0].status == "expired"
    assert attempts[1].status == "resolved"
    assert created[0]["input_data"]["consultation_id"] == "1.00"
