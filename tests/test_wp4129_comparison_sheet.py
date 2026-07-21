import hashlib
import json
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

import pytest

from estate.portraits.comparison_sheet import (ANGLE_SETS, FIXED_CONTROLS, canonical_json,
    manifest_hash, render_html, sha256, validate_manifest)

ROOT = Path(__file__).resolve().parents[1]


def fixture():
    return json.loads((ROOT / "tests/fixtures/comparison_sheet/valid_pending_manifest.json").read_text())


def codes(result):
    return {item["code"] for item in result["diagnostics"]}


def materialize(manifest, root):
    fixed_hash = sha256(canonical_json(manifest["variables"]["fixed"]))
    for variant in manifest["variants"]:
        for cell in variant["cells"]:
            path = Path("sources") / f'{variant["variant_id"]}_{cell["angle_id"]}.png'
            data = f'test-only:{variant["variant_id"]}:{cell["angle_id"]}'.encode()
            (root / path).parent.mkdir(parents=True, exist_ok=True)
            (root / path).write_bytes(data)
            cell.update(state="ready", fixed_fingerprint=fixed_hash,
                        source={"path": str(path), "sha256": sha256(data),
                                "capture_manifest_ref": "test-only-capture.json",
                                "capture_set_id": f'test_{variant["variant_id"]}'})
    return manifest


def test_angle_order_and_fixed_controls_are_canonical():
    assert ANGLE_SETS["five"] == ("front", "front_left_45", "left_profile", "rear_left_45", "rear")
    assert len(ANGLE_SETS["eight"]) == 8
    assert {"camera", "crop", "scale", "footwear"} < set(FIXED_CONTROLS)


def test_pending_manifest_is_valid_but_not_generation_ready():
    result = validate_manifest(fixture())
    assert result["status"] == "pass"
    assert result["generation_ready"] is False
    assert result["coverage"] == {"required": 15, "materialized": 0}


def test_order_angle_and_fixed_control_drift_fail_closed():
    manifest = fixture()
    manifest["variants"][0]["order"] = 2
    manifest["variants"][1]["cells"].reverse()
    manifest["variants"][2]["cells"][0].update(state="ready", source={"path": "none"}, fixed_fingerprint="sha256:bad")
    assert {"VCS-ORDER-001", "VCS-ANGLE-001", "VCS-SOURCE-001", "VCS-CONSISTENCY-001"} <= codes(validate_manifest(manifest))


def test_footwear_is_exclusive_when_intended_variable():
    manifest = fixture()
    manifest["variables"]["intended"] = ["footwear", "height_cm"]
    assert "VCS-FOOTWEAR-001" in codes(validate_manifest(manifest))


def test_missing_and_hash_mismatched_sources_are_diagnosed(tmp_path):
    manifest = materialize(fixture(), tmp_path)
    (tmp_path / manifest["variants"][0]["cells"][0]["source"]["path"]).unlink()
    (tmp_path / manifest["variants"][0]["cells"][1]["source"]["path"]).write_bytes(b"changed")
    found = codes(validate_manifest(manifest, root=tmp_path))
    assert {"VCS-SOURCE-MISSING-001", "VCS-SOURCE-HASH-001"} <= found


def test_incomplete_sheet_cannot_claim_acceptance_or_output():
    manifest = fixture()
    manifest["review"].update(status="accepted", steward_id=None, difference_visible=False)
    manifest["output"]["state"] = "generated"
    assert {"VCS-ACCEPT-001", "VCS-REVIEW-001", "VCS-OUTPUT-001", "VCS-OUTPUT-HASH-001"} <= codes(validate_manifest(manifest))


def test_deterministic_html_render_and_source_links(tmp_path):
    manifest = materialize(fixture(), tmp_path)
    first_path, first_hash = render_html(manifest, tmp_path)
    first = first_path.read_bytes()
    first_path.unlink()
    second_path, second_hash = render_html(manifest, tmp_path)
    assert first == second_path.read_bytes() and first_hash == second_hash
    text = first.decode()
    assert "sources/lower_front.png" in text and text.index("1. Lower") < text.index("2. Candidate")


def test_stale_generated_metadata_is_rejected(tmp_path):
    manifest = materialize(fixture(), tmp_path)
    path, digest = render_html(manifest, tmp_path)
    manifest["output"].update(state="generated", sha256=digest, input_manifest_sha256="sha256:" + "0" * 64)
    assert "VCS-OUTPUT-HASH-001" in codes(validate_manifest(manifest, root=tmp_path))
    manifest["output"]["input_manifest_sha256"] = manifest_hash(manifest)
    assert validate_manifest(manifest, root=tmp_path)["status"] == "pass"


def test_schema_queue_and_cli_are_honest(tmp_path):
    json.loads((ROOT / "data/schemas/visual_bible/comparison_sheet/vertical_comparison_sheet_manifest_v1.schema.json").read_text())
    queue = json.loads((ROOT / "data/visual_bibles/comparison_sheets/generation_queue.json").read_text())
    assert queue["state"] == "blocked_inputs" and queue["fabricated_outputs"] is False
    output = tmp_path / "validation.json"
    run = subprocess.run([sys.executable, "-m", "estate.portraits.comparison_sheet",
        str(ROOT / "tests/fixtures/comparison_sheet/valid_pending_manifest.json"),
        "--root", str(ROOT), "--validation-output", str(output)], cwd=ROOT,
        env={"PYTHONPATH": str(ROOT / "src")}, capture_output=True, text=True)
    assert run.returncode == 0
    assert json.loads(output.read_text())["generation_ready"] is False
