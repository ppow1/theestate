import json

from estate.core.continuous_momentum_engine import ChatGPTReasoningCMEOwner
from estate.core.consultation_store import ConsultationStore


class FakeProcess:
    pid = 0


def test_cme_owns_one_bounded_activation_and_reconciles_authority(tmp_path):
    store = ConsultationStore(tmp_path / "consultations.db")
    record = store.allocate_root(status="awaiting_reasoning", objective="safe reasoning")
    record = store.attach_ec8(record.logical_consultation_id, "ec8-cme")
    launches = []
    authoritative = {"state": "queued", "claim": {}}

    def launch(command, **kwargs):
        launches.append(command)
        return FakeProcess()

    owner = ChatGPTReasoningCMEOwner(
        store,
        state_path=tmp_path / "state.json",
        lock_path=tmp_path / "owner.lock",
        launcher=launch,
        read_request=lambda _rid: authoritative,
    )
    started = owner.tick()
    duplicate = owner.tick()
    assert started["status"] == "STARTED"
    assert duplicate["status"] == "ALREADY_RUNNING"
    assert len(launches) == 1
    assert "start_chatgpt_mailbox_worker_canonical.ps1" in launches[0][-2]

    authoritative.update({"state": "resolved", "response": {"content": "done"}})
    completed = owner.reconcile()
    assert completed["status"] == "COMPLETE"
    assert json.loads((tmp_path / "state.json").read_text()) ["state"] == "STOPPED"


def test_cme_suppresses_active_lease_and_escalation(tmp_path):
    store = ConsultationStore(tmp_path / "consultations.db")
    leased = store.allocate_root(status="awaiting_reasoning", objective="leased")
    leased = store.attach_ec8(leased.logical_consultation_id, "ec8-leased")
    owner = ChatGPTReasoningCMEOwner(
        store, state_path=tmp_path / "state.json", lock_path=tmp_path / "owner.lock",
        launcher=lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("must not launch")),
        read_request=lambda _rid: {"state": "acknowledged", "claim": {"worker_id": "chatgpt", "lease_expires_at": "2999-01-01T00:00:00Z"}},
    )
    assert owner.tick()["state"] == "WAITING_FOR_AUTHORITATIVE_COMPLETION"

    quiet_store = ConsultationStore(tmp_path / "quiet.db")
    quiet_store.allocate_root(status="steward_decision_required", objective="paused")
    owner2 = ChatGPTReasoningCMEOwner(quiet_store, state_path=tmp_path / "state-2.json", lock_path=tmp_path / "owner-2.lock", launcher=lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("must not launch")), read_request=lambda _rid: {})
    assert owner2.tick()["result"] == "EMPTY_QUEUE"


def test_cme_restart_reconstructs_eligible_work(tmp_path):
    store = ConsultationStore(tmp_path / "consultations.db")
    record = store.allocate_root(status="awaiting_reasoning", objective="restart recovery")
    store.attach_ec8(record.logical_consultation_id, "ec8-restart")
    state = tmp_path / "state.json"
    lock = tmp_path / "owner.lock"
    first = ChatGPTReasoningCMEOwner(store, state_path=state, lock_path=lock, launcher=lambda *_args, **_kwargs: FakeProcess(), read_request=lambda _rid: {"state": "queued"})
    assert first.tick()["status"] == "STARTED"
    # A fresh owner sees the persisted activation/lock and does not launch a second worker.
    second = ChatGPTReasoningCMEOwner(store, state_path=state, lock_path=lock, launcher=lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("duplicate launch")), read_request=lambda _rid: {"state": "queued"})
    assert second.tick()["status"] == "ALREADY_RUNNING"


def test_cme_recovers_dead_owner_and_preserves_activation_history(tmp_path):
    store = ConsultationStore(tmp_path / "consultations.db")
    record = store.allocate_root(status="awaiting_reasoning", objective="stale recovery")
    store.attach_ec8(record.logical_consultation_id, "ec8-stale")
    state = tmp_path / "state.json"
    lock = tmp_path / "owner.lock"
    state.write_text(json.dumps({
        "owner": "CME", "state": "PROCESSING", "activation_id": "old-activation",
        "logical_consultation_id": record.logical_consultation_id, "pid": 999991,
    }))
    lock.write_text(json.dumps({"activation_id": "old-activation", "pid": 999992}))
    launches = []
    owner = ChatGPTReasoningCMEOwner(
        store, state_path=state, lock_path=lock,
        launcher=lambda command, **kwargs: launches.append(command) or FakeProcess(),
        read_request=lambda _rid: {"state": "queued", "claim": {}},
    )
    started = owner.tick()
    assert started["status"] == "STARTED"
    recovered = json.loads(state.read_text())
    assert recovered["activation_history"][0]["activation_id"] == "old-activation"
    # Stale ownership is recorded and the newly started fake activation owns
    # the replacement lock; the lock must not disappear while STARTED.
    replacement_lock = json.loads(lock.read_text())
    assert replacement_lock["activation_id"] == started["activation_id"]
    assert replacement_lock["pid"] == __import__("os").getpid()
    assert store.get(record.logical_consultation_id).ec8_request_id == "ec8-stale"
    assert len(launches) == 1
    assert owner.reconcile_stale_owner()["status"] == "LIVE_OWNER"


def test_cme_does_not_clear_live_owner_or_active_lease(tmp_path):
    store = ConsultationStore(tmp_path / "consultations.db")
    record = store.allocate_root(status="awaiting_reasoning", objective="live guard")
    store.attach_ec8(record.logical_consultation_id, "ec8-live")
    state = tmp_path / "state.json"
    lock = tmp_path / "owner.lock"
    state.write_text(json.dumps({"owner": "CME", "state": "PROCESSING", "pid": __import__("os").getpid(), "logical_consultation_id": record.logical_consultation_id}))
    lock.write_text(json.dumps({"pid": __import__("os").getpid()}))
    owner = ChatGPTReasoningCMEOwner(store, state_path=state, lock_path=lock, read_request=lambda _rid: {"state": "acknowledged", "claim": {"lease_expires_at": "2999-01-01T00:00:00Z"}})
    assert owner.reconcile_stale_owner()["status"] == "LIVE_OWNER"
    assert lock.exists()
