"""Governed, deterministic measurement-variant matrices (WP-4130)."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "measurement_variant_matrix_v1"
VARIANT_ROLES = ("baseline", "lower", "target", "higher")
LIFECYCLE_STATES = {"candidate", "selected", "rejected", "superseded", "unresolved"}
CATEGORIES = {"top", "middle", "bottom"}
UNITS = {"cm", "mm", "ratio"}
FIXED_VARIABLES = ("resident_height", "frame", "proportions", "posture", "face", "hair",
                   "expression", "wardrobe", "footwear", "camera", "lighting", "crop", "background")
ANGLES = ("front", "front_left_45", "left_profile", "rear_left_45", "rear")


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def sha256(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def manifest_hash(manifest: dict[str, Any]) -> str:
    return sha256(canonical_json({k: v for k, v in manifest.items() if k != "integrity"}))


def _error(out: list[dict[str, str]], code: str, message: str, location: str = "$") -> None:
    out.append({"code": code, "severity": "error", "location": location, "message": message})


def validate_matrix(m: dict[str, Any]) -> dict[str, Any]:
    """Fail closed on drift, invalid lifecycle claims, provenance, and cross-resident reuse."""
    errors: list[dict[str, str]] = []
    if m.get("schema_version") != SCHEMA_VERSION:
        _error(errors, "MVM-SCHEMA-001", "Unsupported schema version.")
    resident = m.get("resident_id")
    authority = m.get("authority") or {}
    if not resident or authority.get("resident_id") != resident:
        _error(errors, "MVM-RESIDENT-001", "Authority must be bound to this resident.", "$.authority")
    provenance = m.get("provenance") or {}
    for key in ("physical_specification_ref", "scale_profile_ref", "created_by", "created_at"):
        if not provenance.get(key):
            _error(errors, "MVM-PROVENANCE-001", f"Missing provenance {key}.", "$.provenance")
    intended = m.get("intended_variable") or {}
    name, category = intended.get("name"), intended.get("category")
    if not name or category not in CATEGORIES or not intended.get("reason"):
        _error(errors, "MVM-INTENDED-001", "One categorized intended variable and narrative reason are required.")
    fixed = m.get("fixed_variables") or {}
    for key in FIXED_VARIABLES:
        if key not in fixed or fixed[key] in (None, "", {}):
            _error(errors, "MVM-FIXED-001", f"Missing fixed variable {key}.", f"$.fixed_variables.{key}")
    fingerprint = sha256(canonical_json(fixed))
    constraints = m.get("resident_constraints") or {}
    if constraints.get("resident_id") != resident or constraints.get("source_resident_id") not in (None, resident):
        _error(errors, "MVM-CONSTRAINT-001", "Constraints cannot propagate across residents.")
    ranges = constraints.get("ranges") or {}
    variants = m.get("variants") if isinstance(m.get("variants"), list) else []
    roles = [v.get("role") for v in variants]
    if len(set(v.get("variant_id") for v in variants)) != len(variants) or set(roles) != set(VARIANT_ROLES):
        _error(errors, "MVM-VARIANT-001", "Exactly one uniquely identified baseline/lower/target/higher variant is required.")
    baseline = next((v for v in variants if v.get("role") == "baseline"), None)
    for i, variant in enumerate(variants):
        loc = f"$.variants[{i}]"
        if variant.get("state") not in LIFECYCLE_STATES or not variant.get("label"):
            _error(errors, "MVM-LIFECYCLE-001", "Variant needs a label and valid lifecycle state.", loc)
        values = variant.get("measurements") or {}
        for dimension, measurement in values.items():
            value, unit = measurement.get("value"), measurement.get("unit")
            if unit not in UNITS or not isinstance(value, (int, float)) or value <= 0:
                _error(errors, "MVM-UNIT-001", "Measurements must be positive numbers in cm, mm, or ratio.", loc)
            allowed = ranges.get(dimension)
            if allowed and (unit != allowed.get("unit") or not allowed["min"] <= value <= allowed["max"]):
                _error(errors, "MVM-RANGE-001", f"{dimension} is outside the resident-authorized range.", loc)
        if variant.get("fixed_fingerprint") != fingerprint:
            _error(errors, "MVM-DRIFT-001", "Fixed-variable fingerprint differs from matrix lock.", loc)
        if baseline and variant is not baseline:
            changed = {k for k in set(values) | set(baseline.get("measurements", {}))
                       if values.get(k) != baseline.get("measurements", {}).get(k)}
            # Target may intentionally restate the authoritative baseline; lower and
            # higher must bracket it. No record may change a second dimension.
            if not changed.issubset({name}) or (variant.get("role") in {"lower", "higher"} and not changed):
                _error(errors, "MVM-OVAT-001", "A comparison must change only the declared variable.", loc)
    selected = [v for v in variants if v.get("state") == "selected"]
    review = m.get("steward_review") or {}
    if selected and not (len(selected) == 1 and review.get("status") == "decided" and
                         review.get("selected_variant_id") == selected[0].get("variant_id") and
                         review.get("steward_id") and review.get("rationale") and review.get("decided_at")):
        _error(errors, "MVM-SELECTION-001", "Selection requires one matching, evidenced Steward decision.")
    if review.get("status") == "pending" and selected:
        _error(errors, "MVM-PENDING-001", "Pending review cannot select a variant.")
    captures = m.get("capture_relationship") or {}
    if tuple(captures.get("angles", [])) != ANGLES or not captures.get("capture_set_refs") or not captures.get("vertical_sheet_ref"):
        _error(errors, "MVM-INTEGRATION-001", "Five ordered angles, capture-set refs, and vertical-sheet ref are required.")
    for variant in variants:
        if variant.get("role") != "baseline" and variant.get("state") in {"rejected", "superseded"} and not variant.get("disposition_reason"):
            _error(errors, "MVM-DISPOSITION-001", "Rejected/superseded variants require a reason.")
    integrity = m.get("integrity") or {}
    if integrity.get("manifest_sha256") not in (None, manifest_hash(m)):
        _error(errors, "MVM-HASH-001", "Manifest integrity hash is stale.")
    errors.sort(key=lambda d: (d["code"], d["location"], d["message"]))
    return {"schema_version": "measurement_variant_matrix_validation_v1",
            "status": "fail" if errors else "pass", "manifest_sha256": manifest_hash(m),
            "review_ready": not errors and review.get("status") == "pending",
            "diagnostics": errors}


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a WP-4130 measurement matrix")
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = validate_matrix(json.loads(args.manifest.read_text()))
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"status": result["status"], "review_ready": result["review_ready"]}))
    return 0 if result["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
