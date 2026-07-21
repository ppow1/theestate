import json
from copy import deepcopy
from pathlib import Path

from estate.portraits import run_consistency_validation, validate_consistency_manifest, validate_estate_separation

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests/fixtures/portrait_consistency"


def load(name):
    return json.loads((FIXTURES / name).read_text())


def test_complete_structural_and_steward_evidence_passes():
    result = validate_consistency_manifest(load("valid_manifest.json"), root=ROOT)
    assert result["status"] == "pass"
    assert result["canonical_promotion_eligible"] is True
    assert result["visual_validation"] == "steward_records_only_no_computer_vision"
    assert result["diagnostics"] == []


def test_invalid_fixture_reports_hash_binding_coverage_score_and_visual_failure():
    result = validate_consistency_manifest(load("invalid_manifest.json"), root=ROOT)
    codes = {d["code"] for d in result["diagnostics"]}
    assert result["status"] == "fail" and not result["canonical_promotion_eligible"]
    assert {"PCV-COVERAGE-001", "PCV-HASH-001", "PCV-BINDING-001", "PCV-SCORE-BORDERLINE-001", "PCV-VISUAL-FAIL-001"} <= codes
    assert result["remediation_packet"]


def test_missing_review_is_review_required_not_false_failure():
    manifest = load("valid_manifest.json")
    del manifest["steward_reviews"]["hair"]
    result = validate_consistency_manifest(manifest, root=ROOT)
    assert result["status"] == "review_required"
    assert any(d["code"] == "PCV-REVIEW-MISSING-001" for d in result["diagnostics"])


def test_declared_fingerprint_and_byte_convergence_detected():
    first = load("valid_manifest.json")
    second = deepcopy(first)
    second["resident_id"] = "grace"
    second["assets"] = [dict(a, identity_binding="grace") for a in second["assets"]]
    diagnostics = validate_estate_separation([first, second])
    codes = {d["code"] for d in diagnostics}
    assert {"PCV-CONVERGENCE-001", "PCV-CROSS-RESIDENT-HASH-001"} <= codes


def test_runner_writes_integration_report(tmp_path):
    output = tmp_path / "report.json"
    report = run_consistency_validation(FIXTURES / "valid_manifest.json", output, root=ROOT)
    assert report["status"] == "pass"
    assert json.loads(output.read_text())["implementation_claim"].endswith("no computer vision")


def test_schemas_and_canon_are_present():
    for path in [
        "data/schemas/visual_bible/consistency/portrait_consistency_manifest_v1.schema.json",
        "data/schemas/visual_bible/consistency/portrait_consistency_result_v1.schema.json",
    ]:
        json.loads((ROOT / path).read_text())
    canon = (ROOT / "docs/visual_bible/wp4125_portrait_consistency_validation_runtime_canon.md").read_text()
    assert "false positive" in canon and "Steward" in canon and "no computer vision" in canon
