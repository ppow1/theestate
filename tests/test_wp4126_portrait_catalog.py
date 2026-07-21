import json
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

from estate.portraits.catalog import build_indexes, deterministic_asset_id, validate_catalog

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/portrait_catalog/valid_catalog.json"


def load():
    return json.loads(FIXTURE.read_text())


def codes(result):
    return {item["code"] for item in result["diagnostics"]}


def test_valid_catalog_hash_approval_and_views_pass():
    payload = load()
    result = validate_catalog(payload, root=ROOT)
    assert result["status"] == "pass"
    aid = payload["assets"][0]["asset_id"]
    assert result["indexes"]["estate"] == [aid]
    assert result["indexes"]["residents"] == {"evelyn": [aid]}


def test_id_is_stable_and_bound_to_revision():
    asset = load()["assets"][0]
    digest = asset["file"]["sha256"]
    assert deterministic_asset_id("evelyn", "hero", 1, digest) == asset["asset_id"]
    assert deterministic_asset_id("evelyn", "hero", 2, digest) != asset["asset_id"]


def test_missing_hash_and_id_collision_are_blocking():
    payload = load()
    duplicate = deepcopy(payload["assets"][0])
    duplicate["portrait_type"] = "headshot"
    payload["assets"].append(duplicate)
    payload["assets"][0]["file"]["sha256"] = "0" * 64
    result = validate_catalog(payload, root=ROOT)
    assert result["status"] == "fail"
    assert {"PAC-HASH-001", "PAC-ID-COLLISION-001", "PAC-ID-MISMATCH-001"} <= codes(result)


def test_missing_file_is_orphaned_record_but_reserved_slot_makes_no_claim():
    payload = load()
    asset = payload["assets"][0]
    asset["file"]["path"] = "does/not/exist.png"
    assert "PAC-FILE-MISSING-001" in codes(validate_catalog(payload, root=ROOT))
    asset["slot_state"] = "reserved"
    asset["canonical_state"] = "candidate"
    asset["review_state"] = "pending"
    asset["file"] = {}
    asset["asset_id"] = "pa_" + "1" * 24
    result = validate_catalog(payload, root=ROOT)
    assert "PAC-FILE-MISSING-001" not in codes(result)
    assert "PAC-RESERVED-001" not in codes(result)


def test_broken_lineage_duplicate_canon_and_approval_are_detected():
    payload = load()
    first = payload["assets"][0]
    second = deepcopy(first)
    second["revision"] = 2
    second["asset_id"] = deterministic_asset_id("evelyn", "hero", 2, second["file"]["sha256"])
    second["duplicate_of"] = first["asset_id"]
    second["lineage"]["source_asset_ids"] = ["pa_" + "f" * 24]
    second.pop("steward_approval")
    payload["assets"].append(second)
    result = validate_catalog(payload, root=ROOT)
    assert {"PAC-LINEAGE-001", "PAC-CANON-DUPLICATE-001", "PAC-APPROVAL-001"} <= codes(result)


def test_orphan_file_scan_and_deterministic_sort(tmp_path):
    orphan = tmp_path / "orphan.png"
    orphan.write_bytes(b"orphan")
    result = validate_catalog(load(), root=ROOT, scan_roots=[tmp_path])
    assert "PAC-ORPHAN-FILE-001" in codes(result)
    assets = [{"asset_id":"b","resident_id":"z"}, {"asset_id":"a","resident_id":"a"}]
    assert build_indexes(assets)["estate"] == ["a", "b"]


def test_cli_writes_traceable_report(tmp_path):
    output = tmp_path / "report.json"
    run = subprocess.run([sys.executable, "-m", "estate.portraits.catalog", str(FIXTURE), "--root", str(ROOT), "--output", str(output)], cwd=ROOT, env={"PYTHONPATH": str(ROOT / "src")}, capture_output=True, text=True)
    assert run.returncode == 0, run.stderr
    assert json.loads(output.read_text())["status"] == "pass"


def test_schemas_canon_and_example_parse():
    for path in ["data/schemas/visual_bible/catalog/portrait_asset_catalog_v1.schema.json", "data/schemas/visual_bible/catalog/portrait_catalog_validation_v1.schema.json", "data/visual_bibles/catalog/estate_portrait_catalog.example.json"]:
        json.loads((ROOT / path).read_text())
    canon = (ROOT / "docs/visual_bible/wp4126_portrait_metadata_asset_catalog_runtime_canon.md").read_text()
    assert "anti-patterns" in canon and "rollback" in canon and "stale" in canon
