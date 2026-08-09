import pytest

from estate.core.authority_schema_runtime import load_registry
from estate.core.compute_resources import (
    ComputeReservationLedger,
    ComputeResourceObservation,
    ComputeResourceRequirements,
    canonical_resource_id,
    classify_observation,
    reconcile_runtime_ordinals,
    select_resource,
)
from estate.core.execution_dispatch import DispatchRequest, dispatch_request_from_dict, enqueue_dispatch_request
from estate.core.execution_provider_adapter import ExecutionProviderAdapterRequest
from estate.core.compute_office_panel import build_compute_panel


def _device(uuid: str, name: str, *, free: float = 16000, ordinal: int | None = None) -> ComputeResourceObservation:
    return classify_observation(ComputeResourceObservation(
        resource_id=canonical_resource_id("host-a", uuid), host_id="host-a", nvidia_uuid=uuid,
        name=name, memory_total_mib=free, memory_free_mib=free, compute_capability="8.9",
        runtime_ordinals=[] if ordinal is None else [ordinal], observation_timestamp="2026-08-09T12:00:00Z",
    ), now="2026-08-09T12:00:10Z")


def test_arbitrary_n_devices_and_uuid_identity_survive_ordinal_reordering():
    devices = [_device(f"GPU-{i}", f"GPU {i}", ordinal=i) for i in range(8)]
    reconcile_runtime_ordinals(devices, [{"uuid": "GPU-7", "ordinal": 0}, {"uuid": "GPU-0", "ordinal": 7}])
    assert len(devices) == 8
    assert devices[0].resource_id.endswith("GPU-0")
    assert devices[0].runtime_ordinals == [0, 7]
    assert devices[7].resource_id.endswith("GPU-7")


def test_disappeared_identity_mismatch_and_stale_evidence_fail_closed():
    device = _device("GPU-x", "P100")
    device.visible_in_nvml = False
    classify_observation(device, now="2026-08-09T12:00:10Z")
    assert device.health_state == "unavailable"
    assert not select_resource([device], ComputeResourceRequirements(requires_gpu=True, required_resource_id=device.resource_id))["eligible"]
    stale = _device("GPU-stale", "GPU")
    classify_observation(stale, now="2026-08-09T12:04:00Z", freshness_seconds=30)
    assert stale.health_state == "stale"


def test_vram_health_capacity_and_required_preferred_placement_are_distinct():
    fast = _device("GPU-fast", "4090", free=20000)
    small = _device("GPU-small", "P100", free=4000)
    classify_observation(small, now="2026-08-09T12:00:10Z", required_vram_mib=12000)
    assert small.health_state == "healthy"
    assert small.capacity_state == "insufficient"
    result = select_resource([fast, small], ComputeResourceRequirements(requires_gpu=True, minimum_vram_mib=12000, preferred_resource_id=small.resource_id))
    assert result["selected"] == fast.resource_id
    assert result["reason"] == "alternate eligible resource selected"
    required = ComputeResourceRequirements(requires_gpu=True, required_gpu_uuid=small.nvidia_uuid, minimum_vram_mib=12000)
    assert select_resource([fast, small], required)["eligible"] is False
    missing = ComputeResourceRequirements(requires_gpu=True, required_gpu_uuid="GPU-missing")
    missing_result = select_resource([fast, small], missing)
    assert missing_result["eligible"] is False
    assert missing_result["selected"] is None


def test_reservation_ledger_prevents_overbooking(tmp_path):
    ledger = ComputeReservationLedger(tmp_path)
    ledger.reserve(reservation_id="r1", resource_id="host:nvidia:GPU-a", workload_id="w1")
    with pytest.raises(ValueError, match="already reserved"):
        ledger.reserve(reservation_id="r2", resource_id="host:nvidia:GPU-a", workload_id="w2")
    assert ledger.release("r1")
    ledger.reserve(reservation_id="r2", resource_id="host:nvidia:GPU-a", workload_id="w2")


def test_dispatch_and_adapter_requirements_round_trip_without_dropping_current_gates(tmp_path):
    raw = {"dispatch_id": "d1", "classification": "Estate Internal", "compute_resource_requirements": {"requires_gpu": True, "required_gpu_uuid": "GPU-a"}}
    request = dispatch_request_from_dict(raw)
    assert request.compute_resource_requirements["required_gpu_uuid"] == "GPU-a"
    adapter = ExecutionProviderAdapterRequest.create(adapter_request_id="a1", dispatch_id="d1", provider_id="dry-run-provider", provider_type="dry-run", compute_resource_requirements=raw["compute_resource_requirements"])
    assert adapter.compute_resource_requirements["requires_gpu"] is True
    with pytest.raises(ValueError, match="technical execution requires"):
        enqueue_dispatch_request(DispatchRequest(dispatch_id="technical", classification="Estate Internal", provider_metadata={"technical_execution": True}, compute_resource_requirements=raw["compute_resource_requirements"]), tmp_path)
    registry, schemas = load_registry(tmp_path)
    assert "estate.compute-resource-requirements.v1" in schemas


def test_office_projection_is_dynamic_and_read_only():
    panel = build_compute_panel(observations=[_device("GPU-1", "4090"), _device("GPU-2", "P100"), _device("GPU-3", "future")])
    assert panel["resource_count"] == 3
    assert panel["read_only"] is True
    assert {row["nvidia_uuid"] for row in panel["resources"]} == {"GPU-1", "GPU-2", "GPU-3"}
