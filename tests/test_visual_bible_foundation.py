import json
from pathlib import Path

import pytest

from estate.visual_bible import ValidationError, validate_manifest, validate_repository

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "visual_bibles" / "residents" / "evelyn" / "visual_bible_manifest.json"


def load_manifest():
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def test_visual_bible_repository_structure_and_manifest_are_valid():
    validate_repository(ROOT)
    validate_manifest(load_manifest(), root=ROOT)


def test_candidate_rejected_and_canonical_states_are_separated():
    manifest = load_manifest()
    manifest["asset_library"]["canonical"].append({"asset_id": "A1", "review_state": "canonical"})
    manifest["asset_library"]["candidates"].append({"asset_id": "A1", "review_state": "pending_steward_review"})
    with pytest.raises(ValidationError, match="candidate assets cannot also be canonical"):
        validate_manifest(manifest)


def test_measurement_comparison_requires_alignment_views_and_heels():
    manifest = load_manifest()
    comparison = manifest["review_workflow"]["measurement_variant_comparisons"][0]
    comparison["vertical_alignment"] = False
    with pytest.raises(ValidationError, match="vertically aligned"):
        validate_manifest(manifest)
    comparison["vertical_alignment"] = True
    comparison["heel_set"]["heel_height_inches"] = 2
    with pytest.raises(ValidationError, match="3-inch-or-higher"):
        validate_manifest(manifest)


def test_canonical_lock_requires_explicit_steward_approval():
    manifest = load_manifest()
    manifest["canonical_lock"]["status"] = "canonically_locked"
    manifest["canonical_lock"]["lock_record"] = {"approving_authority": "Office"}
    with pytest.raises(ValidationError, match="Steward"):
        validate_manifest(manifest)


def test_cross_resident_identity_requires_own_fingerprint():
    manifest = load_manifest()
    manifest["visual_fingerprint"]["primary_cues"] = ["only one cue"]
    with pytest.raises(ValidationError, match="three to seven"):
        validate_manifest(manifest)
