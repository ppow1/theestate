import json

import pytest

from estate.core.governed_execution_runtime_state import ensure_governed_execution_runtime_state
from estate.core.gpu_runtime_lifecycle import inspect_gpu_runtime_lanes


def test_fresh_state_initializes_idempotently(tmp_path):
    first = ensure_governed_execution_runtime_state(tmp_path)
    second = ensure_governed_execution_runtime_state(tmp_path)
    assert first["status"] == second["status"] == "READY"
    assert second["created"] == []
    assert json.loads((tmp_path / "runtime/engineering_scheduler/compute_reservations.json").read_text()) == []
    assert json.loads((tmp_path / "runtime/execution_dispatch/queue.json").read_text())["items"] == []
    assert json.loads((tmp_path / "runtime/execution_activity/current.json").read_text())["active"] == []
    assert (tmp_path / "runtime/execution_adapters/reconciliation").is_dir()


def test_valid_existing_state_is_preserved(tmp_path):
    ensure_governed_execution_runtime_state(tmp_path)
    reservation = [{"reservation_id": "r1", "state": "released"}]
    path = tmp_path / "runtime/engineering_scheduler/compute_reservations.json"
    path.write_text(json.dumps(reservation), encoding="utf-8")
    before = path.read_bytes()
    result = ensure_governed_execution_runtime_state(tmp_path)
    assert path.read_bytes() == before
    assert result["created"] == []


@pytest.mark.parametrize("relative", [
    "runtime/engineering_scheduler/compute_reservations.json",
    "runtime/execution_dispatch/queue.json",
    "runtime/execution_activity/current.json",
])
def test_malformed_existing_state_fails_closed(tmp_path, relative):
    path = tmp_path / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{not-json", encoding="utf-8")
    with pytest.raises(RuntimeError):
        ensure_governed_execution_runtime_state(tmp_path)


def test_cleanup_gate_can_evaluate_initialized_idle_runtime(tmp_path):
    ensure_governed_execution_runtime_state(tmp_path)
    lane_path = tmp_path / "config/runtime/gpu_runtime_lanes.json"
    lane_path.parent.mkdir(parents=True, exist_ok=True)
    lane_path.write_text(json.dumps({"lanes": []}), encoding="utf-8")
    assert inspect_gpu_runtime_lanes(tmp_path)["lanes"] == []
