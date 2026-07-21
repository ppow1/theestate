from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

REQUIRED_SLOTS = {"hero", "professional_office", "full_body", "profile_rear", "three_quarter", "expression_sheet", "headshot", "thumbnail"}
MANIFEST_STATES = {"not_started", "candidate_generation", "steward_review", "canonical_locked"}
TERMINAL_NONCANON = {"rejected", "superseded"}
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
    commissioned = {item["id"] for item in _load(root / "data" / "registry" / "residents.json") if item.get("status") == "Active"}
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


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Estate portrait catalog and hero canon")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    validate_catalog(args.root.resolve())
    print("Portrait catalog and WP-4118 hero canon validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
