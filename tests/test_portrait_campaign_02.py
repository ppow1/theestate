import json
from pathlib import Path

import pytest

from estate.portraits import PortraitValidationError, validate_catalog, validate_resident_manifest

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "portraits" / "residents" / "evelyn" / "metadata" / "portrait_manifest.json"


def load_manifest():
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def test_campaign_02_catalog_and_resident_manifests_are_valid():
    validate_catalog(ROOT)


def test_all_required_portrait_slots_exist_for_evelyn():
    manifest = load_manifest()
    assert set(manifest["portrait_slots"]) >= {"hero", "professional_office", "full_body", "profile_rear", "three_quarter", "expression_sheet", "headshot", "thumbnail"}


def test_rejected_or_superseded_asset_cannot_be_canonical():
    manifest = load_manifest()
    manifest["assets"].append({
        "asset_id": "bad-lock",
        "portrait_type": "hero",
        "metadata_path": "data/portraits/residents/evelyn/metadata/bad-lock.json",
        "review_status": "rejected",
        "canonical_status": "canonical_locked",
        "steward_approval": {"approved": True},
    })
    with pytest.raises(PortraitValidationError, match="rejected or superseded"):
        validate_resident_manifest(manifest, root=ROOT)


def test_canonical_asset_requires_steward_approval():
    manifest = load_manifest()
    manifest["assets"].append({
        "asset_id": "unapproved-lock",
        "portrait_type": "headshot",
        "metadata_path": "data/portraits/residents/evelyn/metadata/unapproved-lock.json",
        "review_status": "approved",
        "canonical_status": "canonical_locked",
        "steward_approval": {"approved": False},
    })
    with pytest.raises(PortraitValidationError, match="Steward"):
        validate_resident_manifest(manifest, root=ROOT)


def test_duplicate_canonical_assets_rejected_per_slot():
    manifest = load_manifest()
    for asset_id in ["hero-a", "hero-b"]:
        manifest["assets"].append({
            "asset_id": asset_id,
            "portrait_type": "hero",
            "metadata_path": f"data/portraits/residents/evelyn/metadata/{asset_id}.json",
            "review_status": "approved",
            "canonical_status": "canonical_locked",
            "steward_approval": {"approved": True},
        })
    with pytest.raises(PortraitValidationError, match="duplicate canonical"):
        validate_resident_manifest(manifest, root=ROOT)
