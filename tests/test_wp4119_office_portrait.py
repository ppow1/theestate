import hashlib
import json
from copy import deepcopy
from pathlib import Path

import pytest

from estate.portraits import PortraitValidationError, validate_catalog, validate_office_manifest, validate_office_sidecar

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = json.loads((ROOT / "data/registry/residents.json").read_text())
AUTHORITY = next(r for r in REGISTRY if r["id"] == "evelyn")
MANIFEST = json.loads((ROOT / "data/portraits/residents/evelyn/metadata/office_portrait_manifest.json").read_text())


def sidecar(tmp_path, asset_id="office-a", *, canonical=False, anchor=False):
    image = tmp_path / f"{asset_id}.png"; image.write_bytes(b"test-only-office-image")
    digest = hashlib.sha256(image.read_bytes()).hexdigest()
    data = {
        "schema_version":"office_portrait_asset_metadata_v1", "asset_id":asset_id, "resident_id":"evelyn",
        "office":AUTHORITY["office"], "role":AUTHORITY["role"], "scene":"conversational", "lifecycle_state":"canonical" if canonical else ("anchor" if anchor else "candidate"),
        "asset_path":image.name, "sha256":digest,
        "environment":{"classification":"approved_interpretation", "version":"v1", "source_references":["authority"], "provenance_status":"verified"},
        "wardrobe_reference":"approved-test", "narrative_action":{"action":"listening", "role_bounded":True},
        "physical_fidelity":{}, "technical":{}, "provenance":{}, "review":{}, "hidden_caption_test":{}, "lineage":{},
        "canonical":{"declared":canonical, "steward_approval":"approval.json" if canonical else None},
        "emotional_anchor":{"declared":anchor, "narrative_label":"Attentive welcome" if anchor else None, "truth_rationale":"Resident-specific listening presence" if anchor else None, "steward_approval":"approval.json" if anchor else None},
    }
    (tmp_path / f"{asset_id}.json").write_text(json.dumps(data))
    return data, digest


def test_catalog_integrates_all_honestly_pending_office_manifests():
    validate_catalog(ROOT)
    catalog = json.loads((ROOT / "data/portraits/estate_portrait_catalog.json").read_text())
    assert len(catalog["residents"]) == 8
    for resident in catalog["residents"]:
        manifest = json.loads((ROOT / resident["office_portrait_manifest_path"]).read_text())
        assert manifest["generation_state"] == "pending"
        assert manifest["candidates"] == [] and manifest["canonical_office_portrait"] is None and manifest["emotional_anchors"] == []


def test_missing_authority_is_rejected():
    manifest = deepcopy(MANIFEST); manifest["authority"].pop("source")
    with pytest.raises(PortraitValidationError, match="missing office authority"):
        validate_office_manifest(manifest, root=ROOT, registry_record=AUTHORITY)


def test_incorrect_role_is_rejected():
    manifest = deepcopy(MANIFEST); manifest["resident"]["role"] = "Chief Executive"
    with pytest.raises(PortraitValidationError, match="incorrect role"):
        validate_office_manifest(manifest, root=ROOT, registry_record=AUTHORITY)


def test_absent_environment_provenance_is_rejected():
    manifest = deepcopy(MANIFEST); manifest["environment"]["source_references"] = []
    with pytest.raises(PortraitValidationError, match="absent environment provenance"):
        validate_office_manifest(manifest, root=ROOT, registry_record=AUTHORITY)


def test_duplicate_canon_declarations_are_rejected(tmp_path):
    manifest = deepcopy(MANIFEST); records=[]
    for asset_id in ("office-a", "office-b"):
        data, digest = sidecar(tmp_path, asset_id, canonical=True)
        approval=f"{asset_id}-approval.json"; data["canonical"]["steward_approval"]=approval
        (tmp_path/f"{asset_id}.json").write_text(json.dumps(data))
        (tmp_path/approval).write_text(json.dumps({"authority":"steward", "decision":"approved", "asset_id":asset_id, "sha256":digest}))
        records.append({"metadata_path":f"{asset_id}.json"})
    manifest["candidates"] = records
    with pytest.raises(PortraitValidationError, match="duplicate canonical office"):
        validate_office_manifest(manifest, root=tmp_path, registry_record=AUTHORITY)


def test_unapproved_anchor_promotion_is_rejected(tmp_path):
    data, digest = sidecar(tmp_path, anchor=True)
    (tmp_path/"approval.json").write_text(json.dumps({"authority":"steward", "decision":"pending", "asset_id":"office-a", "sha256":digest}))
    with pytest.raises(PortraitValidationError, match="unapproved anchor promotion"):
        validate_office_sidecar(data, root=tmp_path, authority=AUTHORITY)
