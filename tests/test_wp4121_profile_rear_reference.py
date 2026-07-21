import hashlib
import json
from copy import deepcopy
from pathlib import Path
import pytest
from estate.portraits import (
    PortraitValidationError,
    validate_catalog,
    validate_profile_rear_manifest,
    validate_profile_rear_sidecar,
)

ROOT = Path(__file__).resolve().parents[1]
REG = {
    r["id"]: r
    for r in json.loads((ROOT / "data/registry/residents.json").read_text())
    if r["status"] == "Active"
}
MAN = json.loads(
    (ROOT / "data/portraits/residents/evelyn/profile_rear/manifest.json").read_text()
)
GEOM = {
    x: "documented"
    for x in [
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
    ]
}


def asset(tmp_path):
    p = tmp_path / "a.png"
    p.write_bytes(b"wp4121-image")
    h = hashlib.sha256(p.read_bytes()).hexdigest()
    return {
        "schema_version": "profile_rear_asset_metadata_v1",
        "asset_id": "a",
        "resident_id": "evelyn",
        "category": "left_face_profile",
        "lifecycle_state": "candidate",
        "access_tier": "Estate Restricted",
        "asset_path": "a.png",
        "sha256": h,
        "source_references": [
            "hero",
            "office",
            "face",
            "height",
            "wardrobe",
            "full_body",
        ],
        "prompts": {
            "resident_binding": "evelyn",
            "positive_template_revision": 1,
            "negative_template_revision": 1,
        },
        "generation": {"model": "test", "version": "1", "seed": 1, "settings": {}},
        "camera": {
            "focal_length_equivalent_mm": 85,
            "distance_m": 2.5,
            "eye_level": "crop_center",
            "floor_plane": "level",
            "yaw_degrees": -90,
            "pitch_degrees": 0,
            "roll_degrees": 0,
        },
        "crop": {
            "type": "portrait",
            "required_regions_complete": True,
            "crown_hair_complete": True,
            "both_feet_footwear_complete": False,
        },
        "pose": {"classification": "true_profile", "neutral": True},
        "identity_fidelity": {
            "hero_match": "pass",
            "office_match": "pass",
            "left_right_consistency": "pass",
        },
        "geometry": dict(GEOM),
        "physical_fidelity": {
            "height": "not_applicable",
            "proportion": "pass",
            "posture": "pass",
            "silhouette": "pass",
        },
        "wardrobe_grooming": {
            "wardrobe_reference": "wardrobe",
            "footwear_reference": "not_visible",
            "grooming_reference": "identity",
            "accessory_reference": "none",
            "continuity_checks": {
                "wardrobe": "pass",
                "footwear": "not_applicable",
                "grooming": "pass",
                "accessories": "not_applicable",
            },
        },
        "provenance": {
            "created_at": "2026-07-21T00:00:00Z",
            "operator": "test",
            "reference_images": [],
        },
        "validation": {"state": "pass", "diagnostics": []},
        "hidden_caption_test": {"state": "pending"},
        "steward_review": {"state": "pending"},
        "canonical": {"declared": False, "steward_approval": None},
        "lineage": {"predecessor": None, "successor": None},
    }


def test_catalog_and_all_active_residents_have_honest_coverage():
    validate_catalog(ROOT)
    for resident in REG:
        key = resident.lower().replace("-", "_")
        m = json.loads(
            (
                ROOT / f"data/portraits/residents/{key}/profile_rear/manifest.json"
            ).read_text()
        )
        assert len(m["categories"]) == 10 and all(
            x["state"] == "pending_generation" and x["evidence"] is None
            for x in m["categories"]
        )
        assert not m["candidates"] and not any(m["canonical"].values())


def test_manifest_rejects_cross_resident_and_missing_category():
    m = deepcopy(MAN)
    m["resident_template_binding"] = "grace"
    with pytest.raises(PortraitValidationError, match="cross-resident"):
        validate_profile_rear_manifest(m, root=ROOT, registry_record=REG["evelyn"])
    m = deepcopy(MAN)
    m["categories"].pop()
    with pytest.raises(PortraitValidationError, match="missing required"):
        validate_profile_rear_manifest(m, root=ROOT, registry_record=REG["evelyn"])


@pytest.mark.parametrize(
    ("change", "message"),
    [
        (
            lambda a: a["camera"].__setitem__("focal_length_equivalent_mm", 24),
            "camera normalization",
        ),
        (lambda a: a["camera"].pop("yaw_degrees"), "camera angle"),
        (
            lambda a: a["crop"].__setitem__("required_regions_complete", False),
            "incomplete crop",
        ),
        (lambda a: a["geometry"].pop("ear"), "missing geometry"),
        (lambda a: a["provenance"].pop("operator"), "missing provenance"),
        (
            lambda a: a["prompts"].__setitem__("resident_binding", "grace"),
            "cross-resident",
        ),
    ],
)
def test_sidecar_rejects_invalid_evidence(tmp_path, change, message):
    a = asset(tmp_path)
    change(a)
    with pytest.raises(PortraitValidationError, match=message):
        validate_profile_rear_sidecar(a, root=tmp_path, resident_id="evelyn")


def test_full_body_crop_requires_feet(tmp_path):
    a = asset(tmp_path)
    a["category"] = "left_full_body_profile"
    a["crop"]["type"] = "whole_body"
    with pytest.raises(PortraitValidationError, match="whole-body"):
        validate_profile_rear_sidecar(a, root=tmp_path, resident_id="evelyn")


def test_flagged_candidate_cannot_be_canonical(tmp_path):
    a = asset(tmp_path)
    a["lifecycle_state"] = "canonical"
    a["canonical"] = {"declared": True, "steward_approval": "approval.json"}
    a["identity_fidelity"]["hero_match"] = "flag"
    (tmp_path / "approval.json").write_text(
        json.dumps(
            {
                "authority": "steward",
                "decision": "approve",
                "asset_id": "a",
                "category": "left_face_profile",
                "sha256": a["sha256"],
            }
        )
    )
    with pytest.raises(PortraitValidationError, match="flagged"):
        validate_profile_rear_sidecar(a, root=tmp_path, resident_id="evelyn")


def test_valid_category_bound_steward_promotion(tmp_path):
    a = asset(tmp_path)
    a["lifecycle_state"] = "canonical"
    a["canonical"] = {"declared": True, "steward_approval": "approval.json"}
    (tmp_path / "approval.json").write_text(
        json.dumps(
            {
                "authority": "steward",
                "decision": "approve",
                "asset_id": "a",
                "category": "left_face_profile",
                "sha256": a["sha256"],
            }
        )
    )
    validate_profile_rear_sidecar(a, root=tmp_path, resident_id="evelyn")
