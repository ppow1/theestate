from __future__ import annotations

import json

import pytest

from estate.core.compute_resources import ComputeResourceRequirements
from estate.core.compute_resources import ComputeResourceObservation
from estate.core.compute_office_panel import build_compute_panel
from estate.core.gpu_runtime_lanes import RuntimeLane, load_registered_lanes, require_allocation_matches_lane, select_runtime_lane


def lane(name: str, uuid: str, port: int) -> RuntimeLane:
    return RuntimeLane(
        runtime_lane_id=name,
        provider_id="qwen.local.text",
        endpoint_type="ollama-http",
        endpoint_address=f"http://127.0.0.1:{port}",
        host_id="host-a",
        compute_resource_id=f"host-a:nvidia:{uuid}",
        gpu_uuid=uuid,
        model_identity="qwen3:8b",
        environment_binding={"CUDA_VISIBLE_DEVICES": uuid, "OLLAMA_HOST": f"http://127.0.0.1:{port}"},
    )


def test_lanes_are_uuid_bound_and_support_arbitrary_n():
    lanes = [lane(f"qwen-{n}", f"GPU-{n:04d}", 12000 + n) for n in range(5)]
    selected = select_runtime_lane(lanes, provider_id="qwen.local.text", model_identity="qwen3:8b", required_gpu_uuid="GPU-0003", required_resource_id="host-a:nvidia:GPU-0003")
    assert selected["selected"] == "qwen-3"
    assert selected["eligible"] is True


def test_allocation_mismatch_fails_closed():
    selected = lane("qwen-4090", "GPU-4090", 12409)
    with pytest.raises(PermissionError, match="UUID"):
        require_allocation_matches_lane(allocated_gpu_uuid="GPU-other", allocated_resource_id=selected.compute_resource_id, lane=selected)
    with pytest.raises(PermissionError, match="resource"):
        require_allocation_matches_lane(allocated_gpu_uuid=selected.gpu_uuid, allocated_resource_id="wrong", lane=selected)


def test_required_lane_does_not_fallback_to_shared_or_other_gpu():
    lanes = [lane("qwen-a", "GPU-A", 12401)]
    result = select_runtime_lane(lanes, provider_id="qwen.local.text", model_identity="qwen3:8b", required_gpu_uuid="GPU-B", required_resource_id="host-a:nvidia:GPU-B")
    assert result["eligible"] is False
    assert result["selected"] is None


def test_registered_lane_loader_rejects_ordinal_only_binding(tmp_path):
    path = tmp_path / "config/runtime/gpu_runtime_lanes.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({"lanes": [{"runtime_lane_id": "bad", "provider_id": "qwen.local.text", "endpoint_type": "ollama-http", "endpoint_address": "http://127.0.0.1:12400", "host_id": "host", "compute_resource_id": "host:nvidia:GPU-1", "gpu_uuid": "GPU-1", "model_identity": "qwen3:8b", "environment_binding": {"CUDA_VISIBLE_DEVICES": "0"}}]}), encoding="utf-8")
    assert load_registered_lanes(tmp_path) == []


def test_compute_requirement_serializes_physical_identity():
    req = ComputeResourceRequirements(requires_gpu=True, minimum_vram_mib=1024, required_resource_id="host:nvidia:GPU-A", required_gpu_uuid="GPU-A", freshness_seconds=120)
    payload = req.to_dict()
    assert payload["required_gpu_uuid"] == "GPU-A"
    assert "cuda:0" not in json.dumps(payload)


def test_office_projection_is_n_device_and_correlates_lanes(tmp_path):
    configured = lane("qwen-4090", "GPU-A", 12409)
    path = tmp_path / "config/runtime/gpu_runtime_lanes.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({"lanes": [configured.to_dict()]}), encoding="utf-8")
    observations = [
        ComputeResourceObservation(resource_id="host-a:nvidia:GPU-A", host_id="host-a", nvidia_uuid="GPU-A", name="RTX", memory_total_mib=24000, memory_used_mib=100, memory_free_mib=23900, utilization_percent=31, health_state="healthy", capacity_state="available"),
        ComputeResourceObservation(resource_id="host-a:nvidia:GPU-B", host_id="host-a", nvidia_uuid="GPU-B", name="P100", memory_total_mib=16000, memory_used_mib=200, memory_free_mib=15800, utilization_percent=0, health_state="healthy", capacity_state="available"),
        ComputeResourceObservation(resource_id="host-a:nvidia:GPU-C", host_id="host-a", nvidia_uuid="GPU-C", name="Future", memory_total_mib=12000, memory_used_mib=0, memory_free_mib=12000, utilization_percent=0, health_state="healthy", capacity_state="available"),
    ]
    payload = build_compute_panel(tmp_path, observations=observations)
    assert payload["resource_count"] == 3
    assert payload["resources"][0]["runtime_lanes"][0]["runtime_lane_id"] == "qwen-4090"
    assert payload["resources"][1]["runtime_lanes"] == []
