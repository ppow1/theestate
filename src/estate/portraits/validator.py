from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

REQUIRED_SLOTS = {"hero", "professional_office", "full_body", "profile_rear", "three_quarter", "expression_sheet", "headshot", "thumbnail"}
MANIFEST_STATES = {"not_started", "candidate_generation", "steward_review", "canonical_locked"}
TERMINAL_NONCANON = {"rejected", "superseded"}
OFFICE_STATES = {"candidate", "canonical", "anchor", "rejected", "superseded", "pending"}
OFFICE_SCENES = {"seated_desk", "standing_environmental", "conversational", "candid_work"}
FULL_BODY_CATEGORIES = {"neutral_front", "relaxed_front", "three_quarter", "side", "rear", "walking", "seated", "signature_pose", "scale_reference", "footwear_variant"}
FULL_BODY_STATES = {"pending_generation", "candidate", "pending_review", "approved", "canonical", "rejected", "superseded"}
PROFILE_REAR_CATEGORIES = {
    "left_face_profile",
    "right_face_profile",
    "left_full_body_profile",
    "right_full_body_profile",
    "rear_head_shoulders",
    "rear_full_body",
    "rear_three_quarter_left",
    "rear_three_quarter_right",
    "rear_hair_silhouette",
    "rear_posture_shoulders",
}
PROFILE_REAR_STATES = {
    "pending_generation",
    "candidate",
    "pending_review",
    "approved",
    "canonical",
    "rejected",
    "superseded",
}
MAJOR_BODY_REGIONS = {"crown_hair", "head", "neck", "torso", "pelvis", "left_arm_hand", "right_arm_hand", "left_leg", "right_leg", "left_foot_shoe", "right_foot_shoe"}
REQUIRED_DIRS = {"candidates", "canonical", "derivatives", "metadata", "reviews", "comparison_boards", "rejected", "superseded", "locks", "generation_queue"}


class PortraitValidationError(Exception):
    """Raised when Campaign 02 portrait governance is violated."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise PortraitValidationError(message)


def _load(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PortraitValidationError(f"cannot read JSON {path}: {exc}") from exc


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_hero_sidecar(sidecar: dict, *, root: Path) -> None:
    asset_id = sidecar.get("asset_id", "<unknown>")
    _require(sidecar.get("schema_version") == "hero_portrait_metadata_v1", f"asset {asset_id} has unsupported hero metadata schema")
    required = {"resident_id", "portrait_type", "lifecycle_state", "asset_path", "sha256", "technical", "provenance", "composition", "safe_areas", "review", "canonical"}
    _require(not (required - sidecar.keys()), f"asset {asset_id} is missing metadata fields: {sorted(required - sidecar.keys())}")
    _require(sidecar["portrait_type"] == "hero", f"asset {asset_id} must be portrait_type hero")
    asset_path = root / sidecar["asset_path"]
    _require(asset_path.is_file(), f"asset path does not exist: {sidecar['asset_path']}")
    actual_hash = _sha256(asset_path)
    _require(sidecar["sha256"] == actual_hash, f"stale hash for asset {asset_id}")
    canonical = sidecar["canonical"]
    declared = canonical.get("declared") is True
    _require(not (sidecar["lifecycle_state"] in TERMINAL_NONCANON and declared), "rejected or superseded assets cannot be canonical")
    if declared:
        _require(sidecar["lifecycle_state"] == "canonical", f"canonical asset {asset_id} has inconsistent lifecycle state")
        _require(canonical.get("canonical_hash") == actual_hash, f"stale canonical hash for asset {asset_id}")
        approval_path = canonical.get("steward_approval")
        _require(approval_path, f"canonical asset {asset_id} requires explicit Steward approval")
        approval = _load(root / approval_path)
        _require(approval.get("decision") == "approved", f"canonical asset {asset_id} has unapproved promotion")
        _require(approval.get("authority") == "steward", f"canonical asset {asset_id} approval authority is not Steward")
        _require(approval.get("asset_id") == asset_id and approval.get("sha256") == actual_hash, f"canonical asset {asset_id} approval does not match asset/hash")


def validate_office_sidecar(sidecar: dict, *, root: Path, authority: dict) -> None:
    asset_id = sidecar.get("asset_id", "<unknown>")
    required = {"resident_id", "office", "role", "scene", "lifecycle_state", "asset_path", "sha256", "environment", "wardrobe_reference", "narrative_action", "physical_fidelity", "technical", "provenance", "review", "hidden_caption_test", "canonical", "emotional_anchor", "lineage"}
    _require(sidecar.get("schema_version") == "office_portrait_asset_metadata_v1", f"asset {asset_id} has unsupported office metadata schema")
    _require(not (required - sidecar.keys()), f"asset {asset_id} is missing office metadata fields: {sorted(required - sidecar.keys())}")
    _require(sidecar["office"] == authority["office"], f"asset {asset_id} has incorrect office authority")
    _require(sidecar["role"] == authority["role"], f"asset {asset_id} has incorrect role")
    _require(sidecar["lifecycle_state"] in OFFICE_STATES, f"asset {asset_id} has invalid lifecycle state")
    env = sidecar["environment"]
    _require(env.get("classification") in {"canonical_architecture", "approved_interpretation", "placeholder"}, f"asset {asset_id} has invalid environment classification")
    _require(env.get("source_references") and env.get("version") and env.get("provenance_status"), f"asset {asset_id} has absent environment provenance")
    asset_path = root / sidecar["asset_path"]
    _require(asset_path.is_file(), f"asset path does not exist: {sidecar['asset_path']}")
    actual_hash = _sha256(asset_path)
    _require(sidecar["sha256"] == actual_hash, f"stale hash for asset {asset_id}")
    canonical = sidecar["canonical"].get("declared") is True
    anchor = sidecar["emotional_anchor"].get("declared") is True
    _require(not (sidecar["lifecycle_state"] in TERMINAL_NONCANON and (canonical or anchor)), f"terminal office asset {asset_id} cannot be promoted")
    _require(not (env["classification"] == "placeholder" and (canonical or anchor)), f"placeholder office asset {asset_id} cannot be promoted")
    for designation, record in (("canonical", sidecar["canonical"]), ("anchor", sidecar["emotional_anchor"])):
        if record.get("declared") is not True:
            continue
        approval_path = record.get("steward_approval")
        _require(approval_path, f"unapproved {designation} promotion for asset {asset_id}")
        approval = _load(root / approval_path)
        _require(approval.get("authority") == "steward" and approval.get("decision") == "approved", f"unapproved {designation} promotion for asset {asset_id}")
        _require(approval.get("asset_id") == asset_id and approval.get("sha256") == actual_hash, f"{designation} approval does not match asset/hash")
        if designation == "anchor":
            _require(record.get("narrative_label") and record.get("truth_rationale"), f"anchor asset {asset_id} needs narrative truth rationale")


def validate_office_manifest(manifest: dict, *, root: Path, registry_record: dict) -> None:
    _require(manifest.get("schema_version") == "resident_office_portrait_manifest_v1", "unsupported office portrait manifest schema")
    resident = manifest.get("resident", {})
    _require(manifest.get("authority", {}).get("source"), f"missing office authority for {resident.get('resident_id', '<unknown>')}")
    _require(resident.get("resident_id") == registry_record["id"], "office manifest resident mismatch")
    _require(resident.get("office") == registry_record["office"], f"incorrect office authority for {registry_record['id']}")
    _require(resident.get("role") == registry_record["role"], f"incorrect role for {registry_record['id']}")
    environment = manifest.get("environment", {})
    _require(environment.get("source_references") and environment.get("version") and environment.get("provenance_status"), f"absent environment provenance for {registry_record['id']}")
    required = {s.get("scene_type") for s in manifest.get("required_scenes", []) if s.get("required")}
    _require(required >= OFFICE_SCENES, f"missing required office scenes for {registry_record['id']}")
    canonical_ids, anchor_ids = [], []
    for candidate in manifest.get("candidates", []):
        sidecar = _load(root / candidate["metadata_path"])
        validate_office_sidecar(sidecar, root=root, authority=registry_record)
        if sidecar["canonical"].get("declared"): canonical_ids.append(sidecar["asset_id"])
        if sidecar["emotional_anchor"].get("declared"): anchor_ids.append(sidecar["asset_id"])
    _require(len(canonical_ids) <= 1, f"duplicate canonical office portraits for {registry_record['id']}")
    declared = manifest.get("canonical_office_portrait")
    _require(declared is None or declared.get("asset_id") in canonical_ids, f"office canon declaration does not resolve for {registry_record['id']}")
    for anchor in manifest.get("emotional_anchors", []):
        _require(anchor.get("asset_id") in anchor_ids, f"unapproved anchor promotion for {registry_record['id']}")


def validate_full_body_sidecar(sidecar: dict, *, root: Path, resident_id: str) -> None:
    asset_id = sidecar.get("asset_id", "<unknown>")
    required = {"resident_id", "category", "lifecycle_state", "access_tier", "asset_path", "sha256", "source_references", "prompts", "generation", "camera", "crop", "pose", "physical_fidelity", "wardrobe", "footwear", "scale_reference", "provenance", "validation", "steward_review", "canonical", "lineage"}
    _require(sidecar.get("schema_version") == "full_body_asset_metadata_v1", f"asset {asset_id} has unsupported full-body schema")
    _require(not (required - sidecar.keys()), f"asset {asset_id} is missing full-body metadata: {sorted(required-sidecar.keys())}")
    _require(sidecar["resident_id"] == resident_id, f"cross-resident template inheritance for asset {asset_id}")
    _require(sidecar["category"] in FULL_BODY_CATEGORIES and sidecar["lifecycle_state"] in FULL_BODY_STATES-{"pending_generation"}, f"invalid full-body category/state for asset {asset_id}")
    _require(sidecar["source_references"] and sidecar["provenance"].get("created_at") and sidecar["provenance"].get("operator"), f"missing provenance for asset {asset_id}")
    _require(sidecar["prompts"].get("resident_binding") == resident_id, f"cross-resident template inheritance for asset {asset_id}")
    camera = sidecar["camera"]
    focal = camera.get("focal_length_equivalent_mm", 0)
    _require(70 <= focal <= 105 and camera.get("distance_m") and camera.get("height") and camera.get("floor_plane") == "level", f"perspective distortion or missing camera calibration for asset {asset_id}")
    crop = sidecar["crop"]
    visible = set(crop.get("visible_major_regions", []))
    _require(crop.get("crown_hair_complete") is True, f"cropped crown or hair for asset {asset_id}")
    _require(crop.get("both_feet_and_footwear_complete") is True, f"cropped feet for asset {asset_id}")
    _require(MAJOR_BODY_REGIONS <= visible, f"missing major body regions for asset {asset_id}")
    footwear = sidecar["footwear"]
    _require(footwear.get("type") and footwear.get("heel_height_in") is not None and footwear.get("source_reference"), f"incorrect or undocumented footwear for asset {asset_id}")
    _require(footwear.get("posture_effect_documented") is True, f"unexplained heel or posture changes for asset {asset_id}")
    physical = sidecar["physical_fidelity"]
    _require(physical.get("height_check") in {"pass", "flag", "fail"} and physical.get("proportion_check") in {"pass", "flag", "fail"} and physical.get("posture_check") in {"pass", "flag", "fail"}, f"missing physical validation for asset {asset_id}")
    scale = sidecar["scale_reference"]
    _require(scale.get("consistency_check") in {"pass", "flag", "fail"}, f"missing scale validation for asset {asset_id}")
    asset_path = root / sidecar["asset_path"]
    _require(asset_path.is_file(), f"asset path does not exist: {sidecar['asset_path']}")
    actual_hash = _sha256(asset_path)
    _require(sidecar["sha256"] == actual_hash, f"stale hash for asset {asset_id}")
    canonical = sidecar["canonical"].get("declared") is True
    _require(not (sidecar["lifecycle_state"] in TERMINAL_NONCANON and canonical), f"terminal full-body asset {asset_id} cannot be canonical")
    _require(sidecar["steward_review"].get("state"), f"missing Steward review state for asset {asset_id}")
    blocking = any(value in {"flag", "fail"} for value in (physical["height_check"], physical["proportion_check"], physical["posture_check"], scale["consistency_check"]))
    if canonical:
        _require(sidecar["lifecycle_state"] == "canonical", f"candidate asset {asset_id} presented as canon")
        _require(not blocking, f"flagged asset {asset_id} cannot be canonical")
        approval_path = sidecar["canonical"].get("steward_approval")
        _require(approval_path, f"candidate asset {asset_id} presented as canon without Steward approval")
        approval = _load(root / approval_path)
        _require(approval.get("authority") == "steward" and approval.get("decision") == "approve" and approval.get("asset_id") == asset_id and approval.get("sha256") == actual_hash, f"candidate asset {asset_id} presented as canon without matching approval")


def validate_full_body_manifest(manifest: dict, *, root: Path, registry_record: dict) -> None:
    _require(manifest.get("schema_version") == "resident_full_body_manifest_v1", "unsupported full-body manifest schema")
    resident_id = registry_record["id"]
    _require(manifest.get("resident", {}).get("resident_id") == resident_id, f"full-body resident mismatch for {resident_id}")
    _require(manifest.get("resident_template_binding") == resident_id and manifest.get("cross_resident_inheritance") is False, f"cross-resident template inheritance for {resident_id}")
    _require(manifest.get("source_references") and len(manifest["source_references"]) >= 4, f"missing provenance for {resident_id}")
    categories = manifest.get("categories", [])
    _require({c.get("category") for c in categories if c.get("required")} == FULL_BODY_CATEGORIES, f"missing required full-body categories for {resident_id}")
    _require(manifest.get("steward_review", {}).get("state"), f"missing Steward review state for {resident_id}")
    _require(manifest.get("campaign_03_boundary") == "No three-variant 360-degree measurement comparison is performed by WP-4120.", f"Campaign 03 boundary missing for {resident_id}")
    candidates = {}
    for record in manifest.get("candidates", []):
        sidecar = _load(root / record["metadata_path"])
        validate_full_body_sidecar(sidecar, root=root, resident_id=resident_id)
        candidates[sidecar["asset_id"]] = sidecar
    for category in categories:
        if category.get("state") == "pending_generation":
            _require(category.get("evidence") is None and not category.get("candidate_asset_ids") and category.get("canonical_asset_id") is None, f"pending category presented as evidence for {resident_id}")
        canonical_id = category.get("canonical_asset_id")
        if canonical_id:
            _require(canonical_id in candidates and candidates[canonical_id]["canonical"].get("declared") is True, f"candidate asset presented as canon for {resident_id}/{category['category']}")


def validate_profile_rear_sidecar(
    sidecar: dict, *, root: Path, resident_id: str
) -> None:
    asset_id = sidecar.get("asset_id", "<unknown>")
    required = {
        "resident_id",
        "category",
        "lifecycle_state",
        "access_tier",
        "asset_path",
        "sha256",
        "source_references",
        "prompts",
        "generation",
        "camera",
        "crop",
        "pose",
        "identity_fidelity",
        "geometry",
        "physical_fidelity",
        "wardrobe_grooming",
        "provenance",
        "validation",
        "hidden_caption_test",
        "steward_review",
        "canonical",
        "lineage",
    }
    _require(
        sidecar.get("schema_version") == "profile_rear_asset_metadata_v1",
        f"asset {asset_id} has unsupported profile/rear schema",
    )
    _require(
        not (required - sidecar.keys()),
        f"asset {asset_id} is missing profile/rear metadata: {sorted(required - sidecar.keys())}",
    )
    _require(
        sidecar["resident_id"] == resident_id
        and sidecar["prompts"].get("resident_binding") == resident_id,
        f"cross-resident identity binding for asset {asset_id}",
    )
    _require(
        sidecar["category"] in PROFILE_REAR_CATEGORIES
        and sidecar["lifecycle_state"] in PROFILE_REAR_STATES - {"pending_generation"},
        f"invalid profile/rear category/state for asset {asset_id}",
    )
    _require(
        sidecar["source_references"]
        and sidecar["provenance"].get("created_at")
        and sidecar["provenance"].get("operator"),
        f"missing provenance for asset {asset_id}",
    )
    camera = sidecar["camera"]
    _require(
        70 <= camera.get("focal_length_equivalent_mm", 0) <= 105
        and camera.get("distance_m")
        and camera.get("eye_level")
        and camera.get("floor_plane") == "level",
        f"camera normalization failure for asset {asset_id}",
    )
    _require(
        camera.get("yaw_degrees") is not None
        and camera.get("pitch_degrees") is not None
        and camera.get("roll_degrees") is not None,
        f"missing camera angle receipt for asset {asset_id}",
    )
    crop = sidecar["crop"]
    _require(
        crop.get("type") in {"portrait", "whole_body"}
        and crop.get("required_regions_complete") is True,
        f"invalid or incomplete crop for asset {asset_id}",
    )
    if "full_body" in sidecar["category"]:
        _require(
            crop.get("crown_hair_complete") is True
            and crop.get("both_feet_footwear_complete") is True,
            f"whole-body profile/rear crop is incomplete for asset {asset_id}",
        )
    geometry = sidecar["geometry"]
    needed = {
        "nose",
        "lips",
        "chin",
        "jaw",
        "brow",
        "ear",
        "hairline",
        "neck",
        "shoulders",
        "back",
        "posture",
        "silhouette",
        "distinguishing_features",
        "asymmetry",
    }
    _require(
        not (needed - set(geometry)),
        f"missing geometry observations for asset {asset_id}",
    )
    checks = (
        list(sidecar["identity_fidelity"].values())
        + list(sidecar["physical_fidelity"].values())
        + list(sidecar["wardrobe_grooming"].get("continuity_checks", {}).values())
    )
    _require(
        checks and all(v in {"pass", "flag", "fail", "not_applicable"} for v in checks),
        f"invalid fidelity diagnostics for asset {asset_id}",
    )
    asset_path = root / sidecar["asset_path"]
    _require(
        asset_path.is_file(), f"asset path does not exist: {sidecar['asset_path']}"
    )
    actual_hash = _sha256(asset_path)
    _require(sidecar["sha256"] == actual_hash, f"stale hash for asset {asset_id}")
    canonical = sidecar["canonical"].get("declared") is True
    _require(
        not (sidecar["lifecycle_state"] in TERMINAL_NONCANON and canonical),
        f"terminal profile/rear asset {asset_id} cannot be canonical",
    )
    _require(
        sidecar["steward_review"].get("state"),
        f"missing Steward review state for asset {asset_id}",
    )
    if canonical:
        _require(
            sidecar["lifecycle_state"] == "canonical"
            and not any(v in {"flag", "fail"} for v in checks),
            f"candidate or flagged asset {asset_id} presented as canon",
        )
        approval_path = sidecar["canonical"].get("steward_approval")
        _require(
            approval_path,
            f"profile/rear canon requires Steward approval for {asset_id}",
        )
        approval = _load(root / approval_path)
        _require(
            approval.get("authority") == "steward"
            and approval.get("decision") == "approve"
            and approval.get("asset_id") == asset_id
            and approval.get("sha256") == actual_hash
            and approval.get("category") == sidecar["category"],
            f"profile/rear approval does not match asset/hash/category for {asset_id}",
        )


def validate_profile_rear_manifest(
    manifest: dict, *, root: Path, registry_record: dict
) -> None:
    _require(
        manifest.get("schema_version") == "resident_profile_rear_manifest_v1",
        "unsupported profile/rear manifest schema",
    )
    resident_id = registry_record["id"]
    _require(
        manifest.get("resident", {}).get("resident_id") == resident_id,
        f"profile/rear resident mismatch for {resident_id}",
    )
    _require(
        manifest.get("resident_template_binding") == resident_id
        and manifest.get("cross_resident_inheritance") is False,
        f"cross-resident identity binding for {resident_id}",
    )
    _require(
        len(manifest.get("source_references", [])) >= 6,
        f"missing profile/rear source provenance for {resident_id}",
    )
    categories = manifest.get("categories", [])
    _require(
        {c.get("category") for c in categories if c.get("required")}
        == PROFILE_REAR_CATEGORIES,
        f"missing required profile/rear categories for {resident_id}",
    )
    _require(
        manifest.get("naming_convention")
        == "{resident_id}__profile-rear__{category}__{crop}__v{revision:03d}__{asset_id}.{ext}",
        f"non-deterministic profile/rear naming for {resident_id}",
    )
    _require(
        manifest.get("steward_review", {}).get("state"),
        f"missing Steward review state for {resident_id}",
    )
    candidates = {}
    for record in manifest.get("candidates", []):
        sidecar = _load(root / record["metadata_path"])
        validate_profile_rear_sidecar(sidecar, root=root, resident_id=resident_id)
        candidates[sidecar["asset_id"]] = sidecar
    for category in categories:
        if category.get("state") == "pending_generation":
            _require(
                category.get("evidence") is None
                and not category.get("candidate_asset_ids")
                and category.get("canonical_asset_id") is None,
                f"pending profile/rear category presented as evidence for {resident_id}",
            )
        canonical_id = category.get("canonical_asset_id")
        if canonical_id:
            _require(
                canonical_id in candidates
                and candidates[canonical_id]["canonical"].get("declared") is True,
                f"candidate profile/rear asset presented as canon for {resident_id}/{category['category']}",
            )


def validate_resident_manifest(manifest: dict, *, root: Path | None = None) -> None:
    _require(manifest.get("schema_version") == "resident_portrait_manifest_v1", "unsupported resident portrait schema")
    _require(manifest.get("resident_id"), "resident_id is required")
    _require(manifest.get("status") in MANIFEST_STATES, "invalid resident portrait manifest state")
    _require(manifest.get("adult_presentation_required") is True, "adult presentation guard is required")
    slots = manifest.get("portrait_slots", {})
    _require(set(slots) >= REQUIRED_SLOTS, "all Campaign 02 portrait slots are required")
    canonical_by_slot: dict[str, list[str]] = {slot: [] for slot in REQUIRED_SLOTS}
    hero_candidates = 0
    for asset in manifest.get("assets", []):
        asset_id = asset.get("asset_id")
        slot = asset.get("portrait_type")
        _require(slot in REQUIRED_SLOTS, f"asset {asset_id} has unsupported portrait_type")
        metadata_path = asset.get("metadata_path")
        _require(metadata_path, f"asset {asset_id} is missing metadata_path")
        state = asset.get("review_status")
        canonical = asset.get("canonical_status") == "canonical_locked"
        _require(not (state in TERMINAL_NONCANON and canonical), "rejected or superseded assets cannot be canonical")
        if root:
            sidecar_path = root / metadata_path
            _require(sidecar_path.is_file(), f"missing metadata sidecar: {metadata_path}")
            sidecar = _load(sidecar_path)
            _require(sidecar.get("asset_id") == asset_id, f"metadata sidecar asset mismatch for {asset_id}")
            if slot == "hero":
                validate_hero_sidecar(sidecar, root=root)
                if sidecar.get("lifecycle_state") == "candidate":
                    hero_candidates += 1
                _require(canonical == (sidecar.get("canonical", {}).get("declared") is True), f"manifest/sidecar canonical mismatch for {asset_id}")
        if canonical:
            _require(asset.get("steward_approval", {}).get("approved") is True, "canonical assets require explicit Steward approval")
            canonical_by_slot[slot].append(asset_id)
    for slot, ids in canonical_by_slot.items():
        _require(len(ids) <= 1, f"duplicate canonical assets for {slot}")
    for slot, record in slots.items():
        if record.get("canonical_status") == "canonical_locked":
            _require(record.get("canonical_asset_id"), f"locked slot {slot} must name canonical_asset_id")
            _require(record.get("canonical_asset_id") in canonical_by_slot[slot], f"locked slot {slot} does not resolve to validated canon")
            _require(record.get("steward_approval_required") is True, f"locked slot {slot} must preserve Steward approval requirement")
    if manifest.get("status") == "steward_review":
        _require(hero_candidates >= 3, "Steward review requires at least three valid hero candidates")
    if manifest.get("status") == "canonical_locked":
        _require(len(canonical_by_slot["hero"]) == 1, "canonical_locked resident requires exactly one canonical hero")


def validate_catalog(root: Path) -> None:
    catalog_path = root / "data" / "portraits" / "estate_portrait_catalog.json"
    _require(catalog_path.exists(), "estate portrait catalog is missing")
    catalog = _load(catalog_path)
    _require(catalog.get("schema_version") == "portrait_asset_catalog_v1", "unsupported catalog schema")
    _require(catalog.get("validation_rules", {}).get("steward_approval_required_for_canonical") is True, "Steward canonical rule is required")
    residents = catalog.get("residents", [])
    _require(residents, "catalog must include commissioned residents")
    registry = {item["id"]: item for item in _load(root / "data" / "registry" / "residents.json") if item.get("status") == "Active"}
    commissioned = set(registry)
    catalogued = {item["resident_id"] for item in residents}
    _require(catalogued == commissioned, f"catalog resident coverage differs: missing={sorted(commissioned-catalogued)}, extra={sorted(catalogued-commissioned)}")
    for resident in residents:
        path = root / resident["manifest_path"]
        _require(path.exists(), f"resident manifest missing: {resident['manifest_path']}")
        manifest = _load(path)
        _require(resident.get("status") == manifest.get("status"), f"catalog status mismatch for {resident['resident_id']}")
        validate_resident_manifest(manifest, root=root)
        base = path.parents[1]
        for directory in REQUIRED_DIRS:
            _require((base / directory).is_dir(), f"resident directory missing: {base / directory}")
        hero_manifest = _load(base / "metadata" / "hero_manifest.json")
        _require(hero_manifest.get("resident_id") == resident["resident_id"], f"hero manifest resident mismatch for {resident['resident_id']}")
        _require(hero_manifest.get("status") == manifest.get("portrait_slots", {}).get("hero", {}).get("status"), f"hero state mismatch for {resident['resident_id']}")
        office_path = resident.get("office_portrait_manifest_path")
        _require(office_path, f"office portrait manifest catalog link missing for {resident['resident_id']}")
        _require(manifest.get("portrait_slots", {}).get("professional_office", {}).get("office_manifest_path") == office_path, f"office manifest slot/catalog mismatch for {resident['resident_id']}")
        validate_office_manifest(_load(root / office_path), root=root, registry_record=registry[resident["resident_id"]])
        full_body_path = resident.get("full_body_manifest_path")
        _require(full_body_path and manifest.get("portrait_slots", {}).get("full_body", {}).get("full_body_manifest_path") == full_body_path, f"full-body manifest catalog/slot link missing for {resident['resident_id']}")
        validate_full_body_manifest(_load(root / full_body_path), root=root, registry_record=registry[resident["resident_id"]])
        profile_rear_path = resident.get("profile_rear_manifest_path")
        _require(profile_rear_path and manifest.get("portrait_slots", {}).get("profile_rear", {}).get("profile_rear_manifest_path") == profile_rear_path, f"profile/rear manifest catalog/slot link missing for {resident['resident_id']}")
        validate_profile_rear_manifest(_load(root / profile_rear_path), root=root, registry_record=registry[resident["resident_id"]])


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Estate portrait catalog and hero canon")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    validate_catalog(args.root.resolve())
    print("Portrait catalog and WP-4118 through WP-4121 runtime canon validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
