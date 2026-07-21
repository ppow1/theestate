"""Governed WP-4112 measurement-variant review validation.

This module validates records; it never generates imagery or mutates canonical data.
"""
from __future__ import annotations

from copy import deepcopy
from decimal import Decimal
from typing import Any

from .validator import ValidationError

VARIANTS = ("A", "B", "C")
REQUIRED_ANGLES = ("front", "front_three_quarter", "side", "rear_three_quarter", "rear")
APPROVED_DIMENSIONS = {
    "bust", "chest", "waist", "hips", "shoulder_width", "torso_length",
    "leg_length", "inseam", "waist_placement", "overall_build", "silhouette_balance",
}
LOCKED_CONDITIONS = (
    "resident_identity", "facial_fingerprint", "age_presentation", "hairstyle",
    "expression", "pose", "camera_profile_id", "lighting_profile_id", "background_id",
    "wardrobe_specification_id", "footwear_id", "heel_height", "image_dimensions",
    "generation_model", "model_version", "seed", "prompt", "negative_prompt",
    "generation_settings",
)
DIAGNOSTIC_CODES = {
    "SPREAD_TOO_NARROW", "CONCEALING_WARDROBE", "POSE_MISMATCH", "CROP_MISMATCH",
    "CAMERA_MISMATCH", "SCALE_MISMATCH", "INSUFFICIENT_RESOLUTION", "BAD_ALIGNMENT",
    "LIGHTING_INTERFERENCE", "FOOTWEAR_POSTURE_CONFUSION", "IDENTITY_DRIFT",
    "WRONG_VARIABLE_CHANGED",
}
CORRECTION_CODES = {
    "ADJUST_SPREAD", "IMPROVE_FITTED_WARDROBE", "CORRECT_ALIGNMENT", "CORRECT_CAMERA",
    "CORRECT_FOOTWEAR", "IMPROVE_ANNOTATION", "INCREASE_RESOLUTION", "CORRECT_PROMPTS",
    "RESTORE_IDENTITY_LOCKS", "STEWARD_ESCALATION",
}


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def _exact(value: Any) -> Decimal:
    """Parse a JSON number/string without binary floating-point normalization."""
    _require(not isinstance(value, bool), "measurement value must be numeric")
    try:
        return Decimal(str(value))
    except Exception as exc:  # Decimal raises several input-specific exceptions
        raise ValidationError("measurement value must be an exact decimal") from exc


def _measurement_map(variant: dict) -> dict[str, tuple[Decimal, str]]:
    result = {}
    for name, measurement in variant.get("measurements", {}).items():
        _require(isinstance(measurement, dict), f"measurement {name} must be an object")
        unit = measurement.get("unit")
        _require(unit in {"in", "cm", "ratio", "descriptor"}, f"unsupported unit for {name}")
        result[name] = (_exact(measurement.get("value")), unit)
    return result


def validate_comparison_set(record: dict) -> None:
    """Validate completeness, controls, layout, legibility, and review eligibility."""
    for field in (
        "comparison_set_id", "comparison_cycle_id", "resident_id", "visual_bible_revision",
        "source_physical_specification_id", "scale_profile_id", "camera_profile_id",
        "tested_dimensions", "locked_variables", "variants", "controls", "artifacts",
        "provenance", "resident_range_policy", "review_status", "canonical_promotion_status",
    ):
        _require(field in record, f"missing required field: {field}")

    variants = record["variants"]
    _require(set(variants) == set(VARIANTS), "exactly variants A, B, and C are required")
    _require([variants[label].get("label") for label in VARIANTS] == list(VARIANTS), "variant labels must match A/B/C keys")

    tested = record["tested_dimensions"]
    _require(bool(tested) and len(tested) == len(set(tested)), "tested dimensions must be non-empty and unique")
    authorized = set(record.get("authorized_custom_dimensions", []))
    _require(set(tested) <= APPROVED_DIMENSIONS | authorized, "unauthorized tested dimension")
    _require(not (authorized & APPROVED_DIMENSIONS), "custom authorization must only name custom dimensions")

    maps = {label: _measurement_map(variants[label]) for label in VARIANTS}
    _require(set(maps["A"]) == set(maps["B"]) == set(maps["C"]), "variants must record the same measurement fields")
    changed = {name for name in maps["A"] if len({maps[label][name] for label in VARIANTS}) > 1}
    _require(changed == set(tested), "only declared tested dimensions may change")
    for name in tested:
        units = {maps[label][name][1] for label in VARIANTS}
        _require(len(units) == 1, f"unit mismatch for {name}")
        values = [maps[label][name][0] for label in VARIANTS]
        _require(values[0] <= values[1] <= values[2], f"{name} must be ordered A <= B <= C")

    locked = set(record["locked_variables"])
    _require(set(LOCKED_CONDITIONS) <= locked, "locked-variable declaration is incomplete")
    controls = record["controls"]
    for condition in LOCKED_CONDITIONS:
        _require(condition in controls, f"missing locked control: {condition}")
        values = controls[condition]
        _require(isinstance(values, dict) and set(values) == set(VARIANTS), f"control {condition} requires A/B/C values")
        _require(values["A"] == values["B"] == values["C"], f"control mismatch: {condition}")
    _require(record["camera_profile_id"] == controls["camera_profile_id"]["B"], "WP-4111 camera profile reference mismatch")
    _require(record["scale_profile_id"], "WP-4111 scale profile reference is required")

    policy = record["resident_range_policy"]
    _require(policy.get("resident_id") == record["resident_id"], "range policy must belong to this resident")
    _require(policy.get("approved_bounds"), "resident-specific approved bounds are required")
    for name in tested:
        bounds = policy["approved_bounds"].get(name)
        _require(bounds is not None, f"approved resident bounds missing for {name}")
        low, high = _exact(bounds["minimum"]), _exact(bounds["maximum"])
        for label in VARIANTS:
            _require(low <= maps[label][name][0] <= high, f"{label} {name} exceeds resident-specific bounds")
    if record["resident_id"] == "resident-evelyn":
        _require(policy.get("scope") == "evelyn_provisional_calibration_only", "Evelyn values must remain isolated and provisional")
        _require(record["canonical_promotion_status"] == "not_requested", "Evelyn calibration example cannot request promotion")

    artifacts = record["artifacts"]
    primary = artifacts.get("primary_vertical_sheet", {})
    _require(primary.get("layout") == "vertical_A_B_C", "primary sheet must stack A/B/C vertically")
    _require(primary.get("variant_order") == list(VARIANTS), "primary sheet must order A, B, C with B centered")
    _require(primary.get("normal_review_size"), "normal review size must be declared")
    _require(primary.get("direct_single_surface") is True, "primary sheet must support direct single-surface inspection")
    for label in VARIANTS:
        _require(variants[label].get("angles") == list(REQUIRED_ANGLES), f"variant {label} requires ordered five-angle turnaround")
    matrix = artifacts.get("same_angle_matrix", {})
    _require(matrix.get("supplemental_only") is True, "same-angle matrix cannot replace the primary artifact")
    _require(matrix.get("angles") == list(REQUIRED_ANGLES), "same-angle matrix requires all ordered angles")
    _require(set(matrix.get("anatomical_guides", [])) >= {"top_of_head", "shoulder_line", "natural_waist", "fullest_hip", "knee_center", "floor_line"}, "anatomical alignment guides are incomplete")
    _require(matrix.get("independent_scaling_prohibited") is True, "independent variant scaling must be prohibited")

    wardrobe = record.get("wardrobe_protocol", {})
    _require(wardrobe.get("category") in {"neutral", "fitted", "silhouette_revealing"}, "invalid review wardrobe category")
    _require(wardrobe.get("opaque") is True and wardrobe.get("non_explicit") is True, "review wardrobe must be opaque and non-explicit")
    _require(wardrobe.get("adult_appropriate") is True and wardrobe.get("identity_preserving") is True, "review wardrobe safety controls are required")

    footwear = record.get("footwear_protocol", {})
    _require(footwear.get("canonical_standing_height_unchanged") is True, "footwear cannot rewrite canonical standing height")
    _require(footwear.get("posture_separate_from_measurements") is True, "footwear posture must remain separate from measurements")
    if footwear.get("heels_applicable"):
        _require(_exact(footwear.get("heel_height", {}).get("value")) >= Decimal("3"), "applicable heel cycle requires at least three inches")
        _require(footwear.get("heel_height", {}).get("unit") == "in", "heel protocol uses exact inches")
    else:
        _require(bool(footwear.get("exemption_rationale")), "heel inapplicability requires a rationale")

    provenance = record["provenance"]
    for field in ("generation_model", "model_version", "seed", "prompt", "negative_prompt", "workflow_hash", "asset_references", "lineage", "revision_history"):
        _require(field in provenance and provenance[field] not in (None, "", []), f"incomplete provenance: {field}")

    legibility = record.get("legibility_assessment", {})
    _require(legibility.get("status") in {"pass", "fail", "ambiguous", "pending"}, "invalid legibility status")
    if legibility.get("status") in {"fail", "ambiguous"}:
        diagnostics = set(legibility.get("diagnostic_codes", []))
        _require(bool(diagnostics) and diagnostics <= DIAGNOSTIC_CODES, "failed/ambiguous legibility requires valid diagnostics")
        request = record.get("regeneration_request", {})
        _require(request.get("comparison_set_id") == record["comparison_set_id"], "legibility failure requires a linked regeneration request")
        corrections = set(request.get("correction_codes", []))
        _require(bool(corrections) and corrections <= CORRECTION_CODES, "bounded regeneration corrections are required")
        _require(request.get("approved_bounds_unchanged") is True, "regeneration may not automatically widen approved bounds")
        _require(record["review_status"] == "failed", "illegible comparison must fail before review")
    if record["review_status"] in {"review_pending", "selected_but_unapproved", "steward_approved"}:
        _require(legibility.get("status") == "pass", "Steward review requires passed legibility evidence")


def validate_decision(decision: dict, comparison: dict) -> None:
    """Validate append-only Steward decision and retained evidence semantics."""
    validate_comparison_set(comparison)
    for field in ("decision_id", "comparison_set_id", "reviewer_identity", "reviewer_authority", "steward_notes", "selection_rationale", "confidence_level", "unresolved_concerns", "approval_state", "retained_rejected_evidence", "superseded_decision_ids"):
        _require(field in decision, f"decision missing field: {field}")
    _require(decision["comparison_set_id"] == comparison["comparison_set_id"], "decision comparison link mismatch")
    _require(decision["reviewer_authority"] == "Steward", "only the Steward may make the governed decision")
    chosen = decision.get("chosen_candidate")
    _require(chosen in {*VARIANTS, None}, "chosen candidate must be A, B, C, or null")
    rejected = decision.get("rejected_candidates", [])
    _require(set(rejected) <= set(VARIANTS) and chosen not in rejected, "invalid rejected-candidate record")
    if chosen:
        _require(set(rejected) == set(VARIANTS) - {chosen}, "all non-selected candidates must be retained as rejected")
    _require(set(decision["retained_rejected_evidence"]) >= set(rejected), "rejected evidence may not be deleted")
    _require(decision["confidence_level"] in {"low", "moderate", "high"}, "invalid confidence level")
    _require(decision["approval_state"] in {"unapproved", "explicitly_approved"}, "approval must be explicit")
    if decision["approval_state"] == "explicitly_approved":
        _require(chosen is not None, "approval requires a selected candidate")
        _require(bool(decision.get("approval_timestamp")), "approval timestamp is required")


def validate_promotion(promotion: dict, decision: dict, comparison: dict) -> None:
    """Enforce the separate, explicit and versioned canonical-promotion boundary."""
    validate_decision(decision, comparison)
    _require(decision["approval_state"] == "explicitly_approved", "canonical promotion requires explicit Steward approval")
    _require(promotion.get("decision_id") == decision["decision_id"], "promotion must link the approved decision")
    _require(promotion.get("selected_variant") == decision["chosen_candidate"], "promotion candidate must match the decision")
    _require(promotion.get("approved_by") == decision["reviewer_identity"], "promotion approval identity mismatch")
    _require(promotion.get("approval_authority") == "Steward", "non-Steward promotion is prohibited")
    _require(bool(promotion.get("new_physical_specification_version")), "promotion must create a new physical specification version")
    _require(bool(promotion.get("supersedes_physical_specification_version")), "promotion must preserve the superseded version")
    _require(promotion.get("preserve_rejected_evidence") is True, "promotion must preserve rejected evidence")


def create_regeneration_request(record: dict, diagnostics: list[str], corrections: list[str]) -> dict:
    """Return a deterministic bounded request; never mutate or widen the input record."""
    _require(set(diagnostics) <= DIAGNOSTIC_CODES and diagnostics, "invalid regeneration diagnostics")
    _require(set(corrections) <= CORRECTION_CODES and corrections, "invalid regeneration corrections")
    return {
        "comparison_set_id": record["comparison_set_id"],
        "comparison_cycle_id": record["comparison_cycle_id"],
        "diagnostic_codes": sorted(set(diagnostics)),
        "correction_codes": sorted(set(corrections)),
        "approved_bounds_unchanged": True,
        "supersedes_comparison_set_id": record.get("comparison_set_id"),
        "source_range_policy": deepcopy(record["resident_range_policy"]),
    }
