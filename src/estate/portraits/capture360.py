"""Governed, fail-closed 360 capture-set runtime for WP-4128."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "resident_360_capture_manifest_v1"
ANGLES = (
    "front", "front_left_45", "left_profile", "rear_left_45", "rear",
    "rear_right_45", "right_profile", "front_right_45",
)
ANGLE_DEGREES = dict(zip(ANGLES, (0, 45, 90, 135, 180, 225, 270, 315)))
STATES = {"candidate", "review", "accepted", "rejected", "superseded", "pending"}
SET_STATES = STATES | {"incomplete"}
FOOTWEAR_VARIANTS = {"flat_foot", "heel"}
ID = re.compile(r"^[a-z0-9]+(?:_[a-z0-9]+)*$")


def deterministic_filename(resident_id: str, variant_id: str, angle_id: str,
                           footwear_id: str, wardrobe_id: str, state: str,
                           revision: int, extension: str = "png") -> str:
    """Return the only governed filename form; all tokens are metadata IDs."""
    values = (resident_id, variant_id, angle_id, footwear_id, wardrobe_id, state)
    if not all(ID.fullmatch(value or "") for value in values):
        raise ValueError("filename identifiers must be lowercase snake_case")
    if angle_id not in ANGLES or state not in STATES or revision < 1:
        raise ValueError("invalid angle, state, or revision")
    if extension.lower() not in {"png", "webp", "tif", "tiff"}:
        raise ValueError("unsupported capture extension")
    return f"{resident_id}__{variant_id}__{angle_id}__{footwear_id}__{wardrobe_id}__{state}__r{revision:03d}.{extension.lower()}"


def deterministic_directory(resident_id: str, variant_id: str, state: str) -> Path:
    if not all(ID.fullmatch(value or "") for value in (resident_id, variant_id, state)) or state not in SET_STATES:
        raise ValueError("invalid directory identifier")
    tier = "canonical" if state == "accepted" else "review"
    return Path("data/visual_bibles/residents") / resident_id / "internal" / "capture_360" / tier / variant_id


def _add(items: list[dict[str, Any]], code: str, message: str, *, angle: str | None = None) -> None:
    item: dict[str, Any] = {"code": code, "severity": "error", "message": message}
    if angle:
        item["angle"] = angle
    items.append(item)


def _fingerprint(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def validate_capture_set(manifest: dict[str, Any], *, root: Path | None = None) -> dict[str, Any]:
    """Validate completeness, fixed controls, honest files, provenance and approval."""
    diagnostics: list[dict[str, Any]] = []
    if manifest.get("schema_version") != SCHEMA_VERSION:
        _add(diagnostics, "C360-SCHEMA-001", "Unsupported schema version.")
    state = manifest.get("state")
    if state not in SET_STATES:
        _add(diagnostics, "C360-STATE-001", "Invalid capture-set state.")
    required = ("resident_id", "capture_set_id", "variant_id", "measurement_record",
                "canonical_height_cm", "controls", "prompt", "negative_prompt",
                "provenance", "angles", "review")
    for name in required:
        if name not in manifest:
            _add(diagnostics, "C360-REQUIRED-001", f"Missing {name}.")
    if not isinstance(manifest.get("canonical_height_cm"), (int, float)) or manifest.get("canonical_height_cm", 0) <= 0:
        _add(diagnostics, "C360-HEIGHT-001", "Positive canonical height is required.")
    controls = manifest.get("controls") or {}
    control_names = ("identity_ref", "expression", "grooming", "wardrobe", "pose_family",
                     "camera", "focal_length_mm", "distance_m", "lighting", "background",
                     "floor_plane", "scale", "footwear")
    for name in control_names:
        if controls.get(name) in (None, "", {}):
            _add(diagnostics, "C360-CONTROL-001", f"Missing fixed control: {name}.")
    footwear = controls.get("footwear") or {}
    if footwear.get("variant") not in FOOTWEAR_VARIANTS:
        _add(diagnostics, "C360-FOOTWEAR-001", "Footwear variant must be flat_foot or heel.")
    if footwear.get("variant") == "heel" and not isinstance(footwear.get("heel_height_cm"), (int, float)):
        _add(diagnostics, "C360-FOOTWEAR-002", "Heel sets require heel_height_cm.")
    provenance = manifest.get("provenance") or {}
    for name in ("source_refs", "workflow", "seed", "settings", "adapter", "record_sha256"):
        if provenance.get(name) in (None, "", [], {}):
            _add(diagnostics, "C360-PROVENANCE-001", f"Missing provenance: {name}.")
    for key in ("prompt", "negative_prompt"):
        value = manifest.get(key) or {}
        if not value.get("template_ref") or not str(value.get("sha256", "")).startswith("sha256:"):
            _add(diagnostics, "C360-PROMPT-001", f"{key} requires template_ref and SHA-256.")

    angles = manifest.get("angles") if isinstance(manifest.get("angles"), list) else []
    by_id: dict[str, dict[str, Any]] = {}
    fixed = _fingerprint(controls)
    for angle in angles:
        aid = angle.get("angle_id")
        if aid not in ANGLES or aid in by_id:
            _add(diagnostics, "C360-ANGLE-001", "Unknown or duplicate required angle.", angle=str(aid))
            continue
        by_id[aid] = angle
        if angle.get("nominal_degrees") != ANGLE_DEGREES[aid]:
            _add(diagnostics, "C360-ORIENTATION-001", "Nominal orientation does not match angle ID.", angle=aid)
        tolerance = angle.get("tolerance_degrees")
        observed = angle.get("observed_degrees")
        if not isinstance(tolerance, (int, float)) or tolerance < 0 or tolerance > 5:
            _add(diagnostics, "C360-TOLERANCE-001", "Angle tolerance must be between 0 and 5 degrees.", angle=aid)
        elif observed is not None and abs(((observed - ANGLE_DEGREES[aid] + 180) % 360) - 180) > tolerance:
            _add(diagnostics, "C360-TOLERANCE-002", "Observed orientation exceeds tolerance.", angle=aid)
        if angle.get("controls_fingerprint") != fixed:
            _add(diagnostics, "C360-CONSISTENCY-001", "Angle does not bind the set controls.", angle=aid)
        slot_state = angle.get("state")
        asset = angle.get("asset") or {}
        if slot_state == "pending":
            if asset:
                _add(diagnostics, "C360-PENDING-ASSET-001", "Pending angle cannot claim asset bytes.", angle=aid)
        elif slot_state not in STATES - {"pending"}:
            _add(diagnostics, "C360-ANGLE-STATE-001", "Invalid angle state.", angle=aid)
        else:
            for name in ("path", "sha256", "generation_receipt_ref"):
                if not asset.get(name):
                    _add(diagnostics, "C360-ASSET-001", f"Materialized angle missing {name}.", angle=aid)
            if root and asset.get("path"):
                path = root / asset["path"]
                if not path.is_file():
                    _add(diagnostics, "C360-FILE-001", "Declared capture file is missing.", angle=aid)
                elif "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest() != asset.get("sha256"):
                    _add(diagnostics, "C360-HASH-001", "Capture hash does not match bytes.", angle=aid)
    missing = [angle for angle in ANGLES if angle not in by_id]
    if missing:
        _add(diagnostics, "C360-COVERAGE-001", "Missing angle records: " + ", ".join(missing) + ".")
    materialized = sum((by_id.get(a) or {}).get("state") != "pending" for a in ANGLES)
    complete = not missing and materialized == len(ANGLES)
    if state == "accepted":
        decision = (manifest.get("review") or {}).get("steward_decision") or {}
        if not complete:
            _add(diagnostics, "C360-ACCEPT-INCOMPLETE-001", "An incomplete set cannot be accepted.")
        if not (decision.get("explicit_approval") is True and decision.get("authority_role") == "Steward"
                and all(decision.get(k) for k in ("decision_id", "steward_id", "decided_at", "evidence_ref"))):
            _add(diagnostics, "C360-APPROVAL-001", "Accepted set requires explicit Steward evidence.")
    diagnostics.sort(key=lambda x: (x["code"], x.get("angle", ""), x["message"]))
    return {"schema_version": "capture_360_validation_v1",
            "status": "fail" if diagnostics else "pass", "complete": complete,
            "coverage": {"required": 8, "represented": 8 - len(missing), "materialized": materialized},
            "comparison_compatible": complete and not diagnostics, "diagnostics": diagnostics}


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a governed WP-4128 360 capture manifest")
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = validate_capture_set(json.loads(args.manifest.read_text()), root=args.root)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"status": result["status"], "complete": result["complete"], "diagnostics": len(result["diagnostics"])}))
    return 0 if result["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
