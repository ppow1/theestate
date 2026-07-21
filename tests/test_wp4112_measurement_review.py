import copy
import json
from pathlib import Path

import pytest

from estate.visual_bible import (
    ValidationError, create_regeneration_request, validate_comparison_set,
    validate_decision, validate_promotion,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/visual_bible/wp4112_valid_comparison.json"


def comparison():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def decision():
    return {
        "decision_id": "decision-test-1", "comparison_set_id": "mcs-test-001",
        "chosen_candidate": "B", "rejected_candidates": ["A", "C"],
        "steward_notes": "synthetic test record", "selection_rationale": "synthetic gate exercise",
        "confidence_level": "moderate", "unresolved_concerns": [],
        "approval_timestamp": "2026-07-21T00:00:00Z", "reviewer_identity": "steward-test-actor",
        "reviewer_authority": "Steward", "superseded_decision_ids": [],
        "retained_rejected_evidence": ["A", "C"], "approval_state": "explicitly_approved",
    }


def test_valid_abc_exact_units_wp4111_controls_layout_and_heel_cycle():
    record = comparison()
    validate_comparison_set(record)
    assert record["variants"]["B"]["measurements"]["waist"]["value"] == "28.00"
    assert record["artifacts"]["primary_vertical_sheet"]["variant_order"][1] == "B"
    assert record["camera_profile_id"].startswith("wp4111-")


@pytest.mark.parametrize("dimension", ["bust", "chest", "waist", "hips", "shoulder_width", "torso_length", "leg_length", "inseam", "waist_placement", "overall_build", "silhouette_balance"])
def test_every_approved_dimension_can_be_tested(dimension):
    record = comparison()
    for label, value in zip("ABC", ("1.0", "2.0", "3.0")):
        record["variants"][label]["measurements"] = {dimension: {"value": value, "unit": "in"}}
    record["tested_dimensions"] = [dimension]
    record["resident_range_policy"]["approved_bounds"] = {dimension: {"minimum": "0", "maximum": "4", "unit": "in"}}
    validate_comparison_set(record)


def test_custom_dimension_requires_explicit_authorization():
    record = comparison()
    record["tested_dimensions"] = ["neck_length"]
    for label in "ABC":
        record["variants"][label]["measurements"]["neck_length"] = record["variants"][label]["measurements"].pop("waist")
    record["resident_range_policy"]["approved_bounds"]["neck_length"] = record["resident_range_policy"]["approved_bounds"].pop("waist")
    with pytest.raises(ValidationError, match="unauthorized"):
        validate_comparison_set(record)
    record["authorized_custom_dimensions"] = ["neck_length"]
    validate_comparison_set(record)


@pytest.mark.parametrize("control", ["resident_identity", "facial_fingerprint", "age_presentation", "pose", "camera_profile_id", "wardrobe_specification_id", "footwear_id", "heel_height", "generation_model", "prompt", "negative_prompt"])
def test_locked_identity_generation_camera_wardrobe_and_footwear_mismatch_fails(control):
    record = comparison()
    record["controls"][control]["C"] = "drift"
    with pytest.raises(ValidationError, match="control mismatch"):
        validate_comparison_set(record)


def test_unauthorized_measurement_change_and_metric_unit_mismatch_fail():
    record = comparison()
    record["variants"]["C"]["measurements"]["hips"]["value"] = "38.5"
    with pytest.raises(ValidationError, match="only declared"):
        validate_comparison_set(record)
    record = comparison()
    record["variants"]["C"]["measurements"]["waist"]["unit"] = "cm"
    with pytest.raises(ValidationError, match="unit mismatch"):
        validate_comparison_set(record)


def test_metric_values_preserve_exact_decimal_strings():
    record = comparison()
    for label, value in zip("ABC", ("69.85", "71.12", "72.39")):
        record["variants"][label]["measurements"]["waist"] = {"value": value, "unit": "cm"}
    record["resident_range_policy"]["approved_bounds"]["waist"] = {"minimum": "69.00", "maximum": "73.00", "unit": "cm"}
    validate_comparison_set(record)
    assert record["variants"]["B"]["measurements"]["waist"]["value"] == "71.12"


def test_angle_alignment_primary_vertical_and_supplemental_matrix_are_required():
    record = comparison(); record["variants"]["A"]["angles"].pop()
    with pytest.raises(ValidationError, match="five-angle"):
        validate_comparison_set(record)
    record = comparison(); record["artifacts"]["primary_vertical_sheet"]["variant_order"] = ["B", "A", "C"]
    with pytest.raises(ValidationError, match="B centered"):
        validate_comparison_set(record)
    record = comparison(); record["artifacts"]["same_angle_matrix"]["independent_scaling_prohibited"] = False
    with pytest.raises(ValidationError, match="independent variant scaling"):
        validate_comparison_set(record)


def test_heel_minimum_posture_separation_and_exemption():
    record = comparison(); record["footwear_protocol"]["heel_height"]["value"] = "2.99"
    with pytest.raises(ValidationError, match="at least three"):
        validate_comparison_set(record)
    record = comparison(); record["footwear_protocol"]["posture_separate_from_measurements"] = False
    with pytest.raises(ValidationError, match="posture"):
        validate_comparison_set(record)
    record = comparison(); record["footwear_protocol"] = {"heels_applicable": False, "exemption_rationale": "synthetic mobility profile exemption", "canonical_standing_height_unchanged": True, "posture_separate_from_measurements": True}
    validate_comparison_set(record)


def test_incomplete_provenance_blocks_review():
    record = comparison(); del record["provenance"]["negative_prompt"]
    with pytest.raises(ValidationError, match="incomplete provenance"):
        validate_comparison_set(record)


def test_legibility_failure_requires_diagnostics_and_deterministic_regeneration():
    record = comparison()
    request = create_regeneration_request(record, ["SPREAD_TOO_NARROW"], ["ADJUST_SPREAD", "IMPROVE_ANNOTATION"])
    assert request == create_regeneration_request(record, ["SPREAD_TOO_NARROW"], ["IMPROVE_ANNOTATION", "ADJUST_SPREAD"])
    assert request["source_range_policy"] == record["resident_range_policy"]
    record["legibility_assessment"] = {"status": "fail", "diagnostic_codes": ["SPREAD_TOO_NARROW"]}
    record["regeneration_request"] = request
    record["review_status"] = "failed"
    validate_comparison_set(record)
    record["review_status"] = "review_pending"
    with pytest.raises(ValidationError, match="must fail"):
        validate_comparison_set(record)


def test_resident_ranges_are_independent_and_automatic_widening_fails():
    first = comparison(); second = comparison()
    second["resident_id"] = "resident-other-adult"; second["resident_range_policy"]["resident_id"] = "resident-other-adult"
    second["resident_range_policy"]["approved_bounds"]["waist"] = {"minimum": "10", "maximum": "20", "unit": "in"}
    validate_comparison_set(first)
    with pytest.raises(ValidationError, match="bounds"):
        validate_comparison_set(second)


def test_evelyn_calibration_is_isolated_and_never_silently_promoted():
    record = comparison(); record["resident_id"] = "resident-evelyn"; record["resident_range_policy"]["resident_id"] = "resident-evelyn"
    with pytest.raises(ValidationError, match="isolated and provisional"):
        validate_comparison_set(record)
    record["resident_range_policy"]["scope"] = "evelyn_provisional_calibration_only"
    validate_comparison_set(record)
    record["canonical_promotion_status"] = "pending_explicit_steward_approval"
    with pytest.raises(ValidationError, match="cannot request promotion"):
        validate_comparison_set(record)


def test_decision_retains_rejected_and_superseded_evidence():
    record = comparison(); validate_decision(decision(), record)
    bad = decision(); bad["retained_rejected_evidence"] = ["A"]
    with pytest.raises(ValidationError, match="may not be deleted"):
        validate_decision(bad, record)
    historical = decision(); historical["superseded_decision_ids"] = ["decision-old"]
    validate_decision(historical, record)


def test_non_steward_or_unapproved_decision_cannot_promote():
    record = comparison(); dec = decision()
    promotion = {"decision_id": dec["decision_id"], "selected_variant": "B", "approved_by": dec["reviewer_identity"], "approval_authority": "Steward", "new_physical_specification_version": "2", "supersedes_physical_specification_version": "1", "preserve_rejected_evidence": True}
    validate_promotion(promotion, dec, record)
    dec["approval_state"] = "unapproved"
    with pytest.raises(ValidationError, match="explicit Steward approval"):
        validate_promotion(promotion, dec, record)
    dec = decision(); dec["reviewer_authority"] = "operator"
    with pytest.raises(ValidationError, match="only the Steward"):
        validate_promotion(promotion, dec, record)


def test_validation_does_not_mutate_machine_readable_output():
    record = comparison(); before = copy.deepcopy(record)
    validate_comparison_set(record)
    assert record == before


def test_json_schemas_accept_fixture_and_each_record_kind():
    jsonschema = pytest.importorskip("jsonschema")
    comparison_schema = json.loads((ROOT / "data/schemas/visual_bible/measurement_review/measurement_comparison_set_v1.schema.json").read_text())
    jsonschema.Draft202012Validator.check_schema(comparison_schema)
    jsonschema.validate(comparison(), comparison_schema)
    records_schema = json.loads((ROOT / "data/schemas/visual_bible/measurement_review/measurement_review_records_v1.schema.json").read_text())
    jsonschema.Draft202012Validator.check_schema(records_schema)
    record = {**decision(), "record_type": "steward_decision"}
    jsonschema.validate(record, records_schema)
