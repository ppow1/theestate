import json
from pathlib import Path

import pytest
import yaml
from PIL import Image

from estate.visual_bible.evelyn_turnaround import (
    build_sdxl_openpose_workflow,
    create_front_tpose_pose_asset,
    load_profile_registry,
    normalize_source_set,
    validate_profiles,
    verify_source_set,
)

ROOT = Path(__file__).resolve().parents[1]


def test_registry_loads_and_declares_disabled_non_sdxl_profiles():
    registry = load_profile_registry(ROOT)
    assert registry["schema_version"] == "evelyn_generation_profiles.v1"
    enabled = [p for p in registry["profiles"] if p["enabled"]]
    disabled = [p for p in registry["profiles"] if not p["enabled"]]
    assert {p["model_family"] for p in enabled} == {"sdxl"}
    assert any(p["model_family"] == "flux" for p in disabled)
    assert any("IPAdapter" in p["label"] and p["disabled_reason"] for p in disabled)


def test_source_manifest_hashes_match_supplied_evelyn_sources():
    registry = load_profile_registry(ROOT)
    result = verify_source_set(ROOT, registry)
    assert result["status"] == "pass"
    assert sorted(result["sources"]) == ["front", "left", "rear"]
    assert all(record["sha256"] for record in result["sources"].values())


def _make_fixture_source_set(tmp_path):
    root = tmp_path
    source_root = root / "sources"
    source_root.mkdir()
    images = {}
    for name, color in {
        "front": (190, 160, 140),
        "left": (180, 150, 130),
        "rear": (170, 140, 125),
    }.items():
        image = Image.new("RGB", (120, 180), (92, 92, 92))
        for x in range(42, 78):
            for y in range(18, 165):
                image.putpixel((x, y), color)
        path = source_root / f"Evelyn_{name.title() if name != 'rear' else 'Rear'}_V1_Candidate.png"
        if name == "left":
            path = source_root / "Evelyn_Left_V1_Candidate.png"
        image.save(path)
        images[name] = {"file": path.name, "sha256": path.read_bytes().hex()}
    for name, record in images.items():
        import hashlib

        record["sha256"] = hashlib.sha256((source_root / record["file"]).read_bytes()).hexdigest().upper()
    manifest = {
        "resident": "evelyn",
        "source_policy": {"immutable_originals": True, "modify_in_place": False, "normalized_derivatives_required": True},
        "images": images,
    }
    (source_root / "Evelyn_V1_Source_Manifest.yaml").write_text(yaml.safe_dump(manifest), encoding="utf-8")
    registry = {
        "source_set": {"root": "sources", "manifest": "Evelyn_V1_Source_Manifest.yaml"},
        "normalized_output_root": "derived/normalized",
        "pose_asset_root": "derived/pose",
        "common_generation": {"width": 128, "height": 192},
    }
    return root, registry


def test_normalization_writes_gray_derived_manifest_without_source_mutation(tmp_path):
    root, registry = _make_fixture_source_set(tmp_path)
    before = {path.name: path.read_bytes() for path in (root / "sources").glob("*.png")}
    manifest = normalize_source_set(root, registry)
    assert sorted(manifest["outputs"]) == ["front", "left", "rear"]
    for record in manifest["outputs"].values():
        out = root / record["path"]
        assert out.is_file()
        assert Image.open(out).getpixel((0, 0)) == (128, 128, 128)
    after = {path.name: path.read_bytes() for path in (root / "sources").glob("*.png")}
    assert before == after


def test_pose_asset_and_workflow_are_deterministic_candidate_controls(tmp_path):
    registry = {"pose_asset_root": "derived/pose", "common_generation": {"width": 128, "height": 192}}
    pose = create_front_tpose_pose_asset(tmp_path, registry)
    assert (tmp_path / pose["image"]).is_file()
    assert pose["canonical"] is False
    profile = {
        "checkpoint": "RealVisXL_V5.0_fp16.safetensors",
        "required_models": {"controlnet": ["diffusion_pytorch_model_promax.safetensors"]},
    }
    full_registry = {
        "common_generation": {
            "width": 768,
            "height": 1152,
            "steps": 30,
            "cfg": 5.5,
            "sampler_name": "dpmpp_2m_sde",
            "scheduler": "karras",
            "denoise": 1.0,
            "controlnet_strength": 0.82,
            "controlnet_start_percent": 0.0,
            "controlnet_end_percent": 0.92,
        }
    }
    workflow = build_sdxl_openpose_workflow(profile, full_registry, angle="front", seed=1, filename_prefix="x/y", pose_image_name="pose.png")
    classes = {node["class_type"] for node in workflow.values()}
    assert {"ControlNetLoader", "ControlNetApplyAdvanced", "LoadImage", "KSampler"} <= classes
    assert "true T-pose" in workflow["6"]["inputs"]["text"]


def test_profile_validation_skips_disabled_and_reports_missing_enabled_requirements():
    registry = {
        "profiles": [
            {"id": "ok", "label": "OK", "enabled": True, "checkpoint": "a.safetensors", "workflow": "w", "required_nodes": ["CheckpointLoaderSimple"], "required_models": {"checkpoint": ["a.safetensors"]}},
            {"id": "bad", "label": "Bad", "enabled": True, "checkpoint": "b.safetensors", "workflow": "w", "required_nodes": ["MissingNode"], "required_models": {"checkpoint": ["b.safetensors"]}},
            {"id": "off", "label": "Off", "enabled": False, "disabled_reason": "not used", "required_nodes": ["MissingNode"]},
        ]
    }
    inventory = {"nodes": ["CheckpointLoaderSimple"], "checkpoints": ["a.safetensors"], "controlnets": [], "ipadapter_files": [], "clip_vision": []}
    result = validate_profiles(registry, inventory)
    by_id = {item["id"]: item for item in result["profiles"]}
    assert by_id["ok"]["compatible"] is True
    assert by_id["bad"]["compatible"] is False
    assert by_id["off"]["enabled"] is False and by_id["off"]["disabled_reason"] == "not used"
    assert result["status"] == "fail"
