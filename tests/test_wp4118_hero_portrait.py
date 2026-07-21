import hashlib
import json
from copy import deepcopy
from pathlib import Path

import pytest

from estate.portraits import PortraitValidationError, validate_catalog, validate_resident_manifest

ROOT = Path(__file__).resolve().parents[1]
EVELYN = ROOT / "data/portraits/residents/evelyn/metadata/portrait_manifest.json"


def _manifest():
    return json.loads(EVELYN.read_text(encoding="utf-8"))


def _candidate(tmp_path: Path, asset_id="candidate-a", declared=False):
    asset = tmp_path / f"{asset_id}.png"
    asset.write_bytes(b"repository-test-image-bytes")
    digest = hashlib.sha256(asset.read_bytes()).hexdigest()
    sidecar = {
        "schema_version": "hero_portrait_metadata_v1",
        "asset_id": asset_id,
        "resident_id": "evelyn",
        "portrait_type": "hero",
        "lifecycle_state": "canonical" if declared else "candidate",
        "asset_path": asset.name,
        "sha256": digest,
        "technical": {"mime_type": "image/png", "width_px": 4096, "height_px": 4096, "color_profile": "sRGB"},
        "provenance": {"workflow": "test-fixture", "model": "test-fixture", "seed": 1, "settings": {}, "generation_date": "2026-07-21T00:00:00Z", "prompt_version": "test", "negative_prompt_version": "test", "source_references": ["test"]},
        "composition": {"crop": "head_shoulders", "expression_intent": "test", "role_intent": "test", "adult_presentation_verified": True},
        "safe_areas": {key: {"status": "pass", "rationale": "fixture"} for key in ("square", "four_by_five", "sixteen_by_nine")},
        "review": {"state": "approved" if declared else "candidate", "review_record": None},
        "canonical": {"declared": declared, "canonical_hash": digest if declared else None, "steward_approval": "approval.json" if declared else None},
    }
    sidecar_path = tmp_path / f"{asset_id}.json"
    sidecar_path.write_text(json.dumps(sidecar), encoding="utf-8")
    record = {"asset_id": asset_id, "portrait_type": "hero", "metadata_path": sidecar_path.name, "review_status": "approved" if declared else "candidate", "canonical_status": "canonical_locked" if declared else "not_canonical", "steward_approval": {"approved": declared}}
    return record, sidecar, sidecar_path, digest


def test_all_commissioned_residents_have_honest_hero_state():
    validate_catalog(ROOT)
    registry = json.loads((ROOT / "data/registry/residents.json").read_text(encoding="utf-8"))
    catalog = json.loads((ROOT / "data/portraits/estate_portrait_catalog.json").read_text(encoding="utf-8"))
    assert {r["id"] for r in registry if r["status"] == "Active"} == {r["resident_id"] for r in catalog["residents"]}
    assert {r["status"] for r in catalog["residents"]} == {"not_started"}


def test_missing_metadata_sidecar_is_rejected(tmp_path):
    manifest = _manifest()
    manifest["assets"] = [{"asset_id": "missing", "portrait_type": "hero", "metadata_path": "missing.json", "review_status": "candidate", "canonical_status": "not_canonical", "steward_approval": {"approved": False}}]
    with pytest.raises(PortraitValidationError, match="missing metadata sidecar"):
        validate_resident_manifest(manifest, root=tmp_path)


def test_stale_asset_hash_is_rejected(tmp_path):
    manifest = _manifest()
    record, sidecar, sidecar_path, _ = _candidate(tmp_path)
    sidecar["sha256"] = "0" * 64
    sidecar_path.write_text(json.dumps(sidecar), encoding="utf-8")
    manifest["assets"] = [record]
    with pytest.raises(PortraitValidationError, match="stale hash"):
        validate_resident_manifest(manifest, root=tmp_path)


def test_unapproved_canonical_promotion_is_rejected(tmp_path):
    manifest = _manifest()
    record, _, _, digest = _candidate(tmp_path, declared=True)
    (tmp_path / "approval.json").write_text(json.dumps({"decision": "pending", "authority": "steward", "asset_id": "candidate-a", "sha256": digest}), encoding="utf-8")
    manifest["assets"] = [record]
    with pytest.raises(PortraitValidationError, match="unapproved promotion"):
        validate_resident_manifest(manifest, root=tmp_path)


def test_duplicate_canonical_hero_declarations_are_rejected(tmp_path):
    manifest = _manifest()
    records = []
    for asset_id in ("canon-a", "canon-b"):
        record, _, _, digest = _candidate(tmp_path, asset_id, declared=True)
        (tmp_path / "approval.json").write_text(json.dumps({"decision": "approved", "authority": "steward", "asset_id": asset_id, "sha256": digest}), encoding="utf-8")
        # each record needs independently named approval evidence
        sidecar_path = tmp_path / f"{asset_id}.json"
        sidecar = json.loads(sidecar_path.read_text())
        approval_path = f"{asset_id}-approval.json"
        sidecar["canonical"]["steward_approval"] = approval_path
        sidecar_path.write_text(json.dumps(sidecar), encoding="utf-8")
        (tmp_path / approval_path).write_text(json.dumps({"decision": "approved", "authority": "steward", "asset_id": asset_id, "sha256": digest}), encoding="utf-8")
        records.append(record)
    manifest["assets"] = records
    with pytest.raises(PortraitValidationError, match="duplicate canonical"):
        validate_resident_manifest(manifest, root=tmp_path)


def test_steward_review_requires_three_candidates(tmp_path):
    manifest = deepcopy(_manifest())
    manifest["status"] = "steward_review"
    record, _, _, _ = _candidate(tmp_path)
    manifest["assets"] = [record]
    with pytest.raises(PortraitValidationError, match="at least three"):
        validate_resident_manifest(manifest, root=tmp_path)
