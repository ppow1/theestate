from estate.core.chatgpt_reasoning_resident import (
    ChatGPTReasoningResident,
    build_durable_context_package,
    reasoning_wakeup_candidate,
)
from estate.core.autonomous_chatgpt_mailbox_worker import WorkerResult
from estate.core.consultation_store import ConsultationStore


class FakeWorker:
    def __init__(self, result):
        self.result = result
        self.calls = 0

    def run_once(self):
        self.calls += 1
        return self.result


def test_awaiting_reasoning_wakes_once_with_bounded_context(tmp_path):
    store = ConsultationStore(tmp_path / "consultations.db")
    record = store.allocate_root(status="awaiting_reasoning", objective="bounded context", question="Inspect the fixture")
    record = store.attach_ec8(record.logical_consultation_id, "ec8-test")
    states = []
    worker = FakeWorker(WorkerResult("WORKER_COMPLETE", record.logical_consultation_id, "ec8-test"))
    resident = ChatGPTReasoningResident(store, worker=worker, state_writer=states.append)

    result = resident.wake_once()
    context = resident.context_for(record.logical_consultation_id)
    assert result.status == "WORKER_COMPLETE"
    assert worker.calls == 1
    assert states[0]["state"] == "CHATGPT_REASONER_WAKE_PENDING"
    assert context["logical_consultation_id"] == record.logical_consultation_id
    assert len(context["compact_summary"]) <= 4000


def test_empty_queue_and_escalation_are_quiet_or_escalated(tmp_path):
    store = ConsultationStore(tmp_path / "consultations.db")
    fake = FakeWorker(WorkerResult("WORKER_COMPLETE"))
    states = []
    resident = ChatGPTReasoningResident(store, worker=fake, state_writer=states.append)
    assert resident.wake_once().status == "EMPTY_QUEUE"
    assert fake.calls == 0

    record = store.allocate_root(status="steward_decision_required", objective="paused")
    assert reasoning_wakeup_candidate(store, record.logical_consultation_id)["eligible"] is False


def test_cme_candidate_is_projection_only_and_idempotent(tmp_path):
    store = ConsultationStore(tmp_path / "consultations.db")
    record = store.allocate_root(status="awaiting_reasoning", objective="wake")
    record = store.attach_ec8(record.logical_consultation_id, "ec8-wake")
    first = reasoning_wakeup_candidate(store, record.logical_consultation_id)
    second = reasoning_wakeup_candidate(store, record.logical_consultation_id)
    assert first == second
    assert first["canonical_mechanism"] == "ChatGPTReasoningResident.wake_once"
    assert first["permission"] == "delegated"
