from __future__ import annotations

import json
from pathlib import Path

REQUIRED_SLOTS = {"hero", "professional_office", "full_body", "profile_rear", "three_quarter", "expression_sheet", "headshot", "thumbnail"}
TERMINAL_NONCANON = {"rejected", "superseded"}

class PortraitValidationError(Exception):
    """Raised when Campaign 02 portrait governance is violated."""

def _require(condition: bool, message: str) -> None:
    if not condition:
        raise PortraitValidationError(message)

def validate_resident_manifest(manifest: dict, *, root: Path | None = None) -> None:
    _require(manifest.get("schema_version") == "resident_portrait_manifest_v1", "unsupported resident portrait schema")
    _require(manifest.get("resident_id"), "resident_id is required")
    _require(manifest.get("adult_presentation_required") is True, "adult presentation guard is required")
    slots = manifest.get("portrait_slots", {})
    _require(set(slots) >= REQUIRED_SLOTS, "all Campaign 02 portrait slots are required")
    canonical_by_slot: dict[str, list[str]] = {slot: [] for slot in REQUIRED_SLOTS}
    for asset in manifest.get("assets", []):
        slot = asset.get("portrait_type")
        _require(slot in REQUIRED_SLOTS, f"asset {asset.get('asset_id')} has unsupported portrait_type")
        _require(asset.get("metadata_path"), f"asset {asset.get('asset_id')} is missing metadata_path")
        if root and asset.get("asset_path"):
            _require((root / asset["asset_path"]).exists(), f"asset path does not exist: {asset['asset_path']}")
        state = asset.get("review_status")
        canonical = asset.get("canonical_status") == "canonical_locked"
        _require(not (state in TERMINAL_NONCANON and canonical), "rejected or superseded assets cannot be canonical")
        if canonical:
            _require(asset.get("steward_approval", {}).get("approved") is True, "canonical assets require explicit Steward approval")
            canonical_by_slot[slot].append(asset.get("asset_id"))
    for slot, ids in canonical_by_slot.items():
        _require(len(ids) <= 1, f"duplicate canonical assets for {slot}")
    for slot, record in slots.items():
        if record.get("canonical_status") == "canonical_locked":
            _require(record.get("canonical_asset_id"), f"locked slot {slot} must name canonical_asset_id")
            _require(record.get("steward_approval_required") is True, f"locked slot {slot} must preserve Steward approval requirement")

def validate_catalog(root: Path) -> None:
    catalog_path = root / "data" / "portraits" / "estate_portrait_catalog.json"
    _require(catalog_path.exists(), "estate portrait catalog is missing")
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    _require(catalog.get("schema_version") == "portrait_asset_catalog_v1", "unsupported catalog schema")
    _require(catalog.get("validation_rules", {}).get("steward_approval_required_for_canonical") is True, "Steward canonical rule is required")
    residents = catalog.get("residents", [])
    _require(residents, "catalog must include commissioned residents")
    for resident in residents:
        path = root / resident["manifest_path"]
        _require(path.exists(), f"resident manifest missing: {resident['manifest_path']}")
        validate_resident_manifest(json.loads(path.read_text(encoding="utf-8")), root=root)
