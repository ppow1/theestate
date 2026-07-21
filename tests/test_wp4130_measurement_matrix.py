import json
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

from estate.portraits.measurement_matrix import (FIXED_VARIABLES, canonical_json,
    manifest_hash, sha256, validate_matrix)

ROOT = Path(__file__).resolve().parents[1]

def fixture():
    return json.loads((ROOT / "tests/fixtures/measurement_matrix/evelyn_pending.json").read_text())

def codes(result):
    return {d["code"] for d in result["diagnostics"]}

def test_pending_evelyn_matrix_is_valid_and_honest():
    result = validate_matrix(fixture())
    assert result["status"] == "pass" and result["review_ready"] is True
    assert len(FIXED_VARIABLES) == 13

def test_manifest_hash_is_deterministic_and_ignores_integrity():
    m = fixture(); first = manifest_hash(m)
    m["integrity"]["manifest_sha256"] = first
    assert manifest_hash(m) == first

def test_one_variable_and_fixed_lock_drift_are_detected():
    m = fixture()
    m["variants"][1]["measurements"]["hip_circumference"]["value"] = 76.2
    m["variants"][2]["fixed_fingerprint"] = "sha256:" + "0" * 64
    assert {"MVM-OVAT-001", "MVM-DRIFT-001"} <= codes(validate_matrix(m))

def test_wardrobe_and_pose_cannot_become_measurement_effects():
    m = fixture(); m["fixed_variables"]["wardrobe"]["fit"] = "loose"
    assert "MVM-DRIFT-001" in codes(validate_matrix(m))
    m = fixture(); m["intended_variable"].update(name="pose", category="middle")
    assert "MVM-OVAT-001" in codes(validate_matrix(m))

def test_units_ranges_and_resident_boundary_fail_closed():
    m = fixture(); m["variants"][3]["measurements"]["waist_circumference"] = {"value":99,"unit":"in"}
    m["resident_constraints"]["source_resident_id"] = "another-resident"
    assert {"MVM-UNIT-001", "MVM-RANGE-001", "MVM-CONSTRAINT-001"} <= codes(validate_matrix(m))

def test_selection_requires_steward_evidence():
    m = fixture(); m["variants"][2]["state"] = "selected"
    assert "MVM-SELECTION-001" in codes(validate_matrix(m))
    m["steward_review"] = {"status":"decided","selected_variant_id":m["variants"][2]["variant_id"],"steward_id":"steward","rationale":"Approved after genuine review.","decided_at":"2026-07-22T00:00:00Z"}
    assert validate_matrix(m)["status"] == "pass"

def test_rejection_and_supersession_retain_reason():
    for state in ("rejected", "superseded"):
        m=fixture(); m["variants"][1]["state"] = state
        assert "MVM-DISPOSITION-001" in codes(validate_matrix(m))
        m["variants"][1]["disposition_reason"] = "Outside resident-specific calibration preference."
        assert validate_matrix(m)["status"] == "pass"

def test_capture_sheet_integration_and_cli(tmp_path):
    m=fixture(); m["capture_relationship"]["angles"].reverse()
    assert "MVM-INTEGRATION-001" in codes(validate_matrix(m))
    output=tmp_path/"result.json"
    run=subprocess.run([sys.executable,"-m","estate.portraits.measurement_matrix",str(ROOT/"tests/fixtures/measurement_matrix/evelyn_pending.json"),"--output",str(output)],cwd=ROOT,env={"PYTHONPATH":str(ROOT/"src")},capture_output=True,text=True)
    assert run.returncode == 0 and json.loads(output.read_text())["status"] == "pass"

def test_schema_and_generation_queue_are_honest():
    json.loads((ROOT/"data/schemas/visual_bible/measurement_matrix/measurement_variant_matrix_v1.schema.json").read_text())
    q=json.loads((ROOT/"data/visual_bibles/measurement_matrices/generation_queue.json").read_text())
    assert q["state"] == "blocked_inputs" and q["fabricated_outputs"] is False
