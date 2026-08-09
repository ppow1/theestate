from datetime import datetime, timedelta, timezone

import pytest

from estate.core.compute_resources import (
    ComputeResourceObservation,
    ComputeResourceRequirements,
    ComputeReservationLedger,
    canonical_resource_id,
    classify_observation,
    reconcile_runtime_ordinals,
    select_resource,
)
from estate.core.execution_dispatch import DispatchRequest, dispatch_request_from_dict
from estate.core.compute_office_panel import build_compute_panel


def _device(uuid, name, *, free=10000, ordinal=None):
    d = ComputeResourceObservation(
        resource_id=canonical_resource_id("host-a", uuid), host_id="host-a", nvidia_uuid=uuid,
        name=name, memory_total_mib=16000, memory_free_mib=free, compute_capability="8.9",
        runtime_ordinals=[] if ordinal is None else [ordinal], observed_at="2026-08-09T12:00:00Z",
    )
    return classify_observation(d, now="2026-08-09T12:00:10Z")


def test_n_devices_and_uuid_identity_survive_ordinal_reordering():
    devices = [_device(f"GPU-{i}", f"GPU {i}", ordinal=i) for i in range(4)]
    reconcile_runtime_ordinals(devices, [{"uuid": "GPU-3", "ordinal": 0}, {"uuid": "GPU-0", "ordinal": 3}])
    assert len(devices) == 4
    assert devices[0].resource_id.endswith("GPU-0")
    assert devices[0].runtime_ordinals == [0, 3]
    assert devices[3].resource_id.endswith("GPU-3")


def test_missing_identity_and_disappearance_fail_closed():
    device = _device("GPU-x", "P100")
    device.visible_in_nvml = False
    classify_observation(device, now="2026-08-09T12:00:10Z")
    req = ComputeResourceRequirements(requires_gpu=True, required_resource_id=device.resource_id)
    result = select_resource([device], req)
    assert device.health_state == "unavailable"
    assert result["eligible"] is False
    assert "no fallback" in result["reason"]


def test_stale_and_vram_capacity_are_distinct_from_health():
    device = _device("GPU-low", "P100", free=100)
    classify_observation(device, now="2026-08-09T12:04:00Z", freshness_seconds=30, required_vram_mib=1000)
    assert device.health_state == "stale"
    assert device.capacity_state == "insufficient"


def test_required_and_preferred_selection_is_explainable_without_fallback():
    a, b = _device("GPU-a", "4090", free=20000), _device("GPU-b", "P100", free=4000)
    req = ComputeResourceRequirements(requires_gpu=True, minimum_vram_mib=12000, preferred_resource_id=b.resource_id)
    result = select_resource([a, b], req)
    assert result["selected"] == a.resource_id
    assert result["reason"] == "alternate eligible resource selected"
    required = ComputeResourceRequirements(requires_gpu=True, required_resource_id=b.resource_id, minimum_vram_mib=12000)
    assert select_resource([a, b], required)["eligible"] is False


def test_reservation_ledger_does_not_overbook_constrained_resource(tmp_path):
    ledger = ComputeReservationLedger(tmp_path)
    ledger.reserve(reservation_id="r1", resource_id="host:nvidia:GPU-a", workload_id="w1")
    with pytest.raises(ValueError, match="already reserved"):
        ledger.reserve(reservation_id="r2", resource_id="host:nvidia:GPU-a", workload_id="w2")
    assert ledger.release("r1")
    ledger.reserve(reservation_id="r2", resource_id="host:nvidia:GPU-a", workload_id="w2")


def test_dispatch_resource_requirements_round_trip_and_malformed_payload_safe():
    request = dispatch_request_from_dict({"dispatch_id": "d1", "classification": "Estate Internal", "compute_resource_requirements": {"requires_gpu": True, "required_resource_id": "host:nvidia:GPU-a"}})
    assert request.compute_resource_requirements["required_resource_id"].endswith("GPU-a")
    malformed = dispatch_request_from_dict({"dispatch_id": "d2", "classification": "Estate Internal", "compute_resource_requirements": "bad"})
    assert malformed.compute_resource_requirements == {}


def test_office_projection_is_dynamic_for_n_devices():
    devices = [_device("GPU-1", "RTX 4090"), _device("GPU-2", "Tesla P100"), _device("GPU-3", "future")]
    panel = build_compute_panel(observations=devices)
    assert panel["resource_count"] == 3
    assert {row["nvidia_uuid"] for row in panel["resources"]} == {"GPU-1", "GPU-2", "GPU-3"}
    assert panel["read_only"] is True
