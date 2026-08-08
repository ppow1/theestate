from concurrent.futures import ThreadPoolExecutor

from estate.core.consultation_store import ConsultationStore
from estate.core.grace_parallel_portfolio import (
    build_portfolio,
    claim_activation,
    mark_activation_active,
    reconcile_ready,
    release_activation,
)


def _root(store, objective):
    return store.allocate_root(status="awaiting_reasoning", objective=objective)


def test_reconciliation_reserves_independent_roots_and_is_idempotent(tmp_path):
    store = ConsultationStore(tmp_path / "consultations.db")
    first = _root(store, "A")
    second = _root(store, "B")
    result = reconcile_ready(store, reasoning_capacity=2, provider_key="reasoning")
    assert result["newly_reserved_count"] == 2
    assert result["active_activation_count"] == 2
    repeated = reconcile_ready(store, reasoning_capacity=2, provider_key="reasoning")
    assert repeated["newly_reserved_count"] == 0
    assert repeated["active_activation_count"] == 2
    assert {item["root_id"] for item in repeated["items"]} == {first.root_logical_id, second.root_logical_id}


def test_capacity_is_held_and_release_does_not_fail_root(tmp_path):
    store = ConsultationStore(tmp_path / "consultations.db")
    _root(store, "A")
    _root(store, "B")
    result = reconcile_ready(store, reasoning_capacity=1, provider_key="codex")
    assert result["active_activation_count"] == 1
    assert result["held_capacity_count"] == 1
    held = next(item for item in result["items"] if item["classification"] == "HELD_CAPACITY")
    active = next(item for item in result["items"] if item["classification"] == "ACTIVE")
    release_activation(store, active["activation_id"], reason="worker_complete")
    resumed = reconcile_ready(store, reasoning_capacity=1, provider_key="codex")
    assert resumed["newly_reserved_count"] == 1
    assert resumed["active_activation_count"] == 1
    assert any(item["continuation_id"] == held["continuation_id"] and item["classification"] == "ACTIVE" for item in resumed["items"])


def test_two_selectors_get_one_durable_reservation(tmp_path):
    store = ConsultationStore(tmp_path / "consultations.db")
    record = _root(store, "same root")
    kwargs = dict(root_logical_id=record.root_logical_id, continuation_logical_id=record.logical_consultation_id,
                  worker_class="reasoning", provider_key="provider", idempotency_key="root:continuation:reasoning", capacity=1)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: claim_activation(store, **kwargs), range(2)))
    assert sorted(item["status"] for item in results) == ["ALREADY_RESERVED", "RESERVED"]


def test_controller_pid_is_not_worker_pid_and_active_count_is_durable(tmp_path):
    store = ConsultationStore(tmp_path / "consultations.db")
    record = _root(store, "worker identity")
    claimed = claim_activation(store, root_logical_id=record.root_logical_id, continuation_logical_id=record.logical_consultation_id,
                               worker_class="reasoning", provider_key="provider", idempotency_key="id", capacity=1, owner_pid=101)
    assert claimed["controller_pid"] == 101
    assert claimed["worker_pid"] is None
    assert mark_activation_active(store, claimed["activation_id"], worker_pid=202)["status"] == "ACTIVE"
    assert build_portfolio(store)["active_activation_count"] == 1


def test_synthetic_portfolio_explains_ready_blocked_and_steward_lanes(tmp_path):
    store = ConsultationStore(tmp_path / "consultations.db")
    ready_a = _root(store, "A reasoning")
    ready_b = _root(store, "B reasoning")
    execution = _root(store, "C execution")
    blocked = _root(store, "D dependency")
    steward = _root(store, "E decision")
    store.add_tags(blocked.logical_consultation_id, ["blocked_dependency"])
    store.set_status(steward.logical_consultation_id, "steward_decision_required")
    result = reconcile_ready(store, reasoning_capacity=2, provider_key="reasoning")
    by_id = {item["continuation_id"]: item["classification"] for item in result["items"]}
    assert by_id[ready_a.logical_consultation_id] == "ACTIVE"
    assert by_id[ready_b.logical_consultation_id] == "ACTIVE"
    assert by_id[execution.logical_consultation_id] == "HELD_CAPACITY"
    assert by_id[blocked.logical_consultation_id] == "BLOCKED_DEPENDENCY"
    assert by_id[steward.logical_consultation_id] == "WAITING_STEWARD"
