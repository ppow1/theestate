from __future__ import annotations

import hashlib
import json
from pathlib import Path

REVIEW_STATES = {
    "draft", "pending_steward_review", "revision_requested", "provisionally_approved", "canonical", "rejected", "superseded"
}
REQUIRED_LAYERS = ("public", "internal", "restricted", "private")
REQUIRED_ASSET_BUCKETS = ("canonical", "candidates", "rejected", "superseded", "comparisons", "turnarounds", "thumbnails", "group_images")
REQUIRED_VIEWS = {"front", "front_three_quarter", "side", "rear_three_quarter", "rear"}
FIXED_COMPARISON_VARIABLES = {"identity", "facial_fingerprint", "pose", "expression", "camera_position", "focal_length", "lighting", "background", "wardrobe"}

class ValidationError(Exception):
    """Raised when a Visual Bible manifest violates campaign governance."""

def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)

def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()

def validate_manifest(manifest: dict, *, root: Path | None = None) -> None:
    _require(manifest.get("schema_version") == "visual_bible_foundation_v1", "unsupported schema_version")
    resident = manifest.get("resident", {})
    _require(resident.get("adult_status") == "adult", "resident must carry explicit adult status")
    _require(resident.get("resident_id"), "resident_id is required")
    _require("public" in set(manifest.get("visibility_layers", [])), "public visibility layer is required")

    physical = manifest.get("physical_specification", {})
    approval = physical.get("steward_approval", {})
    if physical.get("status") == "canonical":
        _require(approval.get("approved") is True, "canonical physical specification requires Steward approval")
    provenance = physical.get("provenance", {})
    _require(str(provenance.get("hash", "")).startswith("sha256:"), "physical provenance hash is required")

    cues = manifest.get("visual_fingerprint", {}).get("primary_cues", [])
    _require(3 <= len(cues) <= 7, "visual fingerprint requires three to seven primary cues")

    comparisons = manifest.get("review_workflow", {}).get("measurement_variant_comparisons", [])
    for comparison in comparisons:
        _require(len(comparison.get("variants", [])) == 3, "measurement comparisons require exactly three variants")
        _require(set(comparison.get("views", [])) >= REQUIRED_VIEWS, "measurement comparisons require all five turnaround views")
        _require(comparison.get("vertical_alignment") is True, "measurement comparisons must be vertically aligned")
        _require(set(comparison.get("fixed_variables", [])) >= FIXED_COMPARISON_VARIABLES, "comparison fixed variables are incomplete")
        heel = comparison.get("heel_set", {})
        _require(heel.get("included") is True and float(heel.get("heel_height_inches", 0)) >= 3, "at least one 3-inch-or-higher heel comparison is required")
        _require(comparison.get("regenerate_if_not_distinguishable") is True, "comparison must require regeneration when differences are indistinguishable")
        _require(comparison.get("steward_selection_notes") is not None, "Steward selection notes are required")

    assets = manifest.get("asset_library", {})
    canonical_ids = {asset.get("asset_id") for asset in assets.get("canonical", [])}
    candidate_ids = {asset.get("asset_id") for asset in assets.get("candidates", [])}
    rejected_ids = {asset.get("asset_id") for asset in assets.get("rejected", [])}
    _require(not (canonical_ids & candidate_ids), "candidate assets cannot also be canonical")
    _require(not (canonical_ids & rejected_ids), "rejected assets cannot also be canonical")
    for bucket_name in ("canonical", "candidates", "rejected", "superseded"):
        for asset in assets.get(bucket_name, []):
            _require(asset.get("review_state") in REVIEW_STATES, f"{bucket_name} asset has invalid review_state")
            if bucket_name != "canonical":
                _require(asset.get("review_state") != "canonical", f"{bucket_name} asset may not use canonical state")
            if root and asset.get("path") and Path(root, asset["path"]).exists():
                _require(asset.get("hash") == _hash_file(Path(root, asset["path"])), f"hash mismatch for {asset['path']}")

    lock = manifest.get("canonical_lock", {})
    _require(lock.get("explicit_steward_approval_required") is True, "canonical lock requires explicit Steward approval flag")
    if lock.get("status") == "canonically_locked":
        record = lock.get("lock_record", {})
        _require(record.get("approving_authority") == "Steward", "canonical lock requires Steward approving authority")
        _require(record.get("accepted_physical_specification_hash"), "canonical lock requires accepted physical hash")

def validate_repository(root: Path) -> None:
    residents_root = root / "data" / "visual_bibles" / "residents"
    _require(residents_root.exists(), "resident Visual Bible root missing")
    for resident_dir in [p for p in residents_root.iterdir() if p.is_dir()]:
        for layer in REQUIRED_LAYERS:
            layer_dir = resident_dir / layer
            _require(layer_dir.exists(), f"missing visibility layer {resident_dir.name}/{layer}")
            for bucket in REQUIRED_ASSET_BUCKETS:
                _require((layer_dir / "assets" / bucket).exists(), f"missing asset bucket {resident_dir.name}/{layer}/assets/{bucket}")
        manifest_path = resident_dir / "visual_bible_manifest.json"
        if manifest_path.exists():
            validate_manifest(json.loads(manifest_path.read_text(encoding="utf-8")), root=root)
