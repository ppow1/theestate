from estate.core.compute_resources import ComputeResourceObservation, ExpectedGPU, build_gpu_inventory, canonical_resource_id, classify_observation
from estate.core.p100_inference_lane import P100LaneConfig, P100_NAME, P100_UUID, build_launch_plan, health_gate_for_new_work, preflight_lane


def _rows(*, p100_name=P100_NAME, p100_healthy=True):
    p100 = ComputeResourceObservation(
        resource_id=canonical_resource_id("host-a", P100_UUID), host_id="host-a", nvidia_uuid=P100_UUID,
        name=p100_name, pci_bus_id="04:00.0", memory_total_mib=16384, memory_free_mib=16000,
        cuda_present=True, runtime_ordinals=[1], nvidia_smi_index=0, observed_at="2026-08-11T12:00:00Z",
    )
    if not p100_healthy:
        p100.visible_in_nvml = False
    rtx = ComputeResourceObservation(
        resource_id=canonical_resource_id("host-a", "GPU-4090"), host_id="host-a", nvidia_uuid="GPU-4090",
        name="NVIDIA GeForce RTX 4090", pci_bus_id="07:00.0", memory_total_mib=24564, memory_free_mib=22000,
        cuda_present=True, runtime_ordinals=[0], nvidia_smi_index=1, observed_at="2026-08-11T12:00:00Z",
    )
    return [classify_observation(p100, now="2026-08-11T12:00:10Z"), classify_observation(rtx, now="2026-08-11T12:00:10Z")]


def _config(tmp_path):
    model = tmp_path / "model.gguf"; model.write_bytes(b"model")
    backend = tmp_path / "llama-server.exe"; backend.write_bytes(b"backend")
    return P100LaneConfig(model=model, backend=backend)


def _multimodal_config(tmp_path, **kwargs):
    model = tmp_path / "model.gguf"; model.write_bytes(b"model")
    backend = tmp_path / "llama-server.exe"; backend.write_bytes(b"backend")
    return P100LaneConfig(model=model, backend=backend, multimodal_enabled=True, mmproj=tmp_path / "mmproj.gguf", **kwargs)


def test_lane_resolves_p100_by_uuid_despite_reversed_ordinals(tmp_path):
    plan = build_launch_plan(_config(tmp_path), _rows())
    assert plan["resolved_target"]["physical_uuid"] == P100_UUID
    assert plan["resolved_target"]["runtime_ordinal"] == 1
    assert plan["environment"]["CUDA_VISIBLE_DEVICES"] == "1"
    assert plan["argv"][-2:] == ["--device", "CUDA0"]


def test_lane_refuses_unhealthy_p100_without_fallback(tmp_path):
    result = preflight_lane(_config(tmp_path), _rows(p100_healthy=False))
    assert not result["ready"]
    assert result["no_fallback"] is True
    assert any("not dispatch eligible" in error for error in result["errors"])


def test_lane_refuses_identity_mismatch_and_missing_dependencies(tmp_path):
    config = P100LaneConfig(model=tmp_path / "missing.gguf", backend=tmp_path / "missing.exe")
    result = preflight_lane(config, _rows(p100_name="NVIDIA GeForce RTX 4090"))
    assert not result["ready"]
    assert any("identity mismatch" in error for error in result["errors"])
    assert any("model file is missing" in error for error in result["errors"])
    assert any("executable is missing" in error for error in result["errors"])


def test_health_loss_disables_new_work():
    row = _rows()[0]
    assert health_gate_for_new_work(row)["accept_new_work"]
    row.visible_in_nvml = False
    classify_observation(row, now="2026-08-11T12:00:10Z")
    gate = health_gate_for_new_work(row)
    assert gate["accept_new_work"] is False
    assert gate["status"] == "DEGRADED/LOST"


def test_multimodal_disabled_preserves_old_launch(tmp_path):
    plan = build_launch_plan(_config(tmp_path), _rows())
    assert "--mmproj" not in plan["argv"]


def test_multimodal_missing_projector_fails_closed(tmp_path):
    result = preflight_lane(_multimodal_config(tmp_path), _rows())
    assert not result["ready"]
    assert any("projector file is missing" in error for error in result["errors"])


def test_multimodal_valid_projector_adds_expected_args(tmp_path, monkeypatch):
    config = _multimodal_config(tmp_path)
    config.mmproj.write_bytes(b"projector")
    model_metadata = {
        "general.architecture": "qwen3vl", "general.type": "model",
        "general.name": "Qwen3 32B VL", "general.base_model.0.name": "Qwen3 VL 32B Instruct",
        "qwen3vl.embedding_length": 5120,
    }
    projector_metadata = {
        "general.architecture": "clip", "general.type": "mmproj",
        "general.name": "Qwen3 VL 32B Projector", "general.base_model.0.name": "Qwen3 VL 32B Instruct",
        "clip.projector_type": "qwen3vl_merger", "clip.vision.projection_dim": 5120,
    }
    monkeypatch.setattr("estate.core.p100_inference_lane._gguf_metadata", lambda path: model_metadata if path == config.model else projector_metadata)
    plan = build_launch_plan(config, _rows())
    assert plan["argv"][-3:] == ["--mmproj", str(config.mmproj), "--no-mmproj-offload"]


def test_multimodal_incompatible_projector_fails_closed(tmp_path, monkeypatch):
    config = _multimodal_config(tmp_path)
    config.mmproj.write_bytes(b"projector")
    monkeypatch.setattr("estate.core.p100_inference_lane._gguf_metadata", lambda path: {
        "general.architecture": "qwen3vl", "general.type": "mmproj",
        "general.name": "Qwen3 VL 8B", "clip.projector_type": "qwen3vl_merger",
        "clip.vision.projection_dim": 4096, "qwen3vl.embedding_length": 5120,
    })
    result = preflight_lane(config, _rows())
    assert not result["ready"]
    assert any("projection dimension" in error for error in result["errors"])


def test_multimodal_invalid_config_fails_clearly(tmp_path):
    config = P100LaneConfig(model=tmp_path / "model.gguf", backend=tmp_path / "llama-server.exe", multimodal_enabled=True)
    config.model.write_bytes(b"model"); config.backend.write_bytes(b"backend")
    result = preflight_lane(config, _rows())
    assert not result["ready"]
    assert any("mmproj_path is missing" in error for error in result["errors"])
