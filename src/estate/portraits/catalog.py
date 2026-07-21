"""Deterministic portrait asset catalog and validator (WP-4126)."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "portrait_asset_catalog_v1"
ACCESS = {"public", "internal", "restricted", "private"}
REVIEW = {"pending", "in_review", "approved", "rejected"}
CANONICAL = {"candidate", "canonical", "superseded", "retired", "rejected"}
SLOT_STATES = {"materialized", "reserved", "pending"}


def deterministic_asset_id(resident_id: str, portrait_type: str, revision: int,
                           source_sha256: str) -> str:
    """Mint a stable ID from immutable identity inputs, never a filename."""
    value = f"v1\0{resident_id}\0{portrait_type}\0{revision}\0{source_sha256.lower()}"
    return "pa_" + hashlib.sha256(value.encode()).hexdigest()[:24]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _diagnostic(items: list[dict[str, Any]], code: str, severity: str,
                message: str, asset_id: str | None = None) -> None:
    items.append({"code": code, "severity": severity, "message": message,
                  "asset_id": asset_id})


def validate_catalog(catalog: dict[str, Any], *, root: Path,
                     scan_roots: list[Path] | None = None) -> dict[str, Any]:
    """Validate records, bytes, lineage, lifecycle, collisions, and orphans."""
    diagnostics: list[dict[str, Any]] = []
    if catalog.get("schema_version") != SCHEMA_VERSION:
        _diagnostic(diagnostics, "PAC-SCHEMA-001", "error", "Unsupported schema version.")
    assets = catalog.get("assets")
    if not isinstance(assets, list):
        _diagnostic(diagnostics, "PAC-SCHEMA-002", "error", "assets must be an array.")
        assets = []

    by_id: dict[str, dict[str, Any]] = {}
    by_hash: dict[str, str] = {}
    canonical_slots: dict[tuple[str, str, str], str] = {}
    recorded_paths: set[Path] = set()
    required = {"asset_id", "resident_id", "resident_display_name", "portrait_type",
                "angle", "crop", "expression", "wardrobe", "footwear", "environment",
                "camera", "lighting", "generation", "prompts", "file", "lineage",
                "access_tier", "review_state", "canonical_state", "slot_state",
                "revision", "created_at", "updated_at"}
    now = datetime.now(timezone.utc)
    for asset in assets:
        aid = asset.get("asset_id")
        missing = sorted(required - set(asset))
        if missing:
            _diagnostic(diagnostics, "PAC-REQUIRED-001", "error", f"Missing fields: {', '.join(missing)}.", aid)
        if not aid or aid in by_id:
            _diagnostic(diagnostics, "PAC-ID-COLLISION-001", "error", "Asset ID is missing or duplicated.", aid)
        elif aid:
            by_id[aid] = asset
        state = asset.get("slot_state")
        file_record = asset.get("file") or {}
        digest = file_record.get("sha256", "")
        if all(asset.get(k) is not None for k in ("resident_id", "portrait_type", "revision")) and digest:
            expected = deterministic_asset_id(asset["resident_id"], asset["portrait_type"], asset["revision"], digest)
            if aid != expected:
                _diagnostic(diagnostics, "PAC-ID-MISMATCH-001", "error", f"Expected deterministic ID {expected}.", aid)
        if state == "materialized":
            rel = file_record.get("path")
            if not rel:
                _diagnostic(diagnostics, "PAC-FILE-001", "error", "Materialized record requires file.path.", aid)
            else:
                path = (root / rel).resolve()
                recorded_paths.add(path)
                if not path.is_file():
                    _diagnostic(diagnostics, "PAC-FILE-MISSING-001", "error", f"Missing file: {rel}.", aid)
                elif not digest or _sha256(path) != digest:
                    _diagnostic(diagnostics, "PAC-HASH-001", "error", "File hash does not match bytes.", aid)
        elif state not in {"reserved", "pending"}:
            _diagnostic(diagnostics, "PAC-SLOT-001", "error", "Invalid slot_state.", aid)
        elif file_record.get("path") or digest:
            _diagnostic(diagnostics, "PAC-RESERVED-001", "error", "Reserved/pending slots cannot claim file bytes.", aid)
        if digest:
            prior = by_hash.get(digest)
            if prior and (asset.get("duplicate_of") != prior):
                _diagnostic(diagnostics, "PAC-DUPLICATE-001", "error", f"Duplicate bytes already owned by {prior}.", aid)
            else:
                by_hash[digest] = aid
        if asset.get("access_tier") not in ACCESS or asset.get("review_state") not in REVIEW or asset.get("canonical_state") not in CANONICAL:
            _diagnostic(diagnostics, "PAC-LIFECYCLE-001", "error", "Invalid access/review/canonical state.", aid)
        if asset.get("canonical_state") == "canonical":
            approval = asset.get("steward_approval") or {}
            if asset.get("review_state") != "approved" or not all(approval.get(k) for k in ("decision_id", "steward_id", "approved_at", "evidence_sha256")):
                _diagnostic(diagnostics, "PAC-APPROVAL-001", "error", "Canonical asset lacks Steward approval evidence.", aid)
            key = (asset.get("resident_id"), asset.get("portrait_type"), asset.get("angle"))
            if key in canonical_slots:
                _diagnostic(diagnostics, "PAC-CANON-DUPLICATE-001", "error", f"Canonical slot also claimed by {canonical_slots[key]}.", aid)
            else:
                canonical_slots[key] = aid
        if asset.get("canonical_state") in {"superseded", "retired", "rejected"} and asset.get("review_state") == "approved":
            _diagnostic(diagnostics, "PAC-STATE-CONFLICT-001", "error", "Inactive asset cannot remain approved.", aid)
        try:
            updated = datetime.fromisoformat(asset.get("updated_at", "").replace("Z", "+00:00"))
            if (now - updated).days > catalog.get("stale_after_days", 365):
                _diagnostic(diagnostics, "PAC-STALE-001", "warning", "Metadata exceeds freshness threshold.", aid)
        except (TypeError, ValueError):
            _diagnostic(diagnostics, "PAC-TIMESTAMP-001", "error", "updated_at is not ISO-8601.", aid)

    for aid, asset in by_id.items():
        lineage = asset.get("lineage") or {}
        for relation in ("source_asset_ids", "derivative_asset_ids", "supersedes"):
            for target in lineage.get(relation, []):
                if target not in by_id:
                    _diagnostic(diagnostics, "PAC-LINEAGE-001", "error", f"Broken {relation} reference: {target}.", aid)
                if target == aid:
                    _diagnostic(diagnostics, "PAC-LINEAGE-CYCLE-001", "error", "Self-referential lineage.", aid)

    for scan_root in scan_roots or []:
        base = scan_root if scan_root.is_absolute() else root / scan_root
        if base.exists():
            for path in sorted(p.resolve() for p in base.rglob("*") if p.is_file() and not p.name.endswith((".json", ".md"))):
                if path not in recorded_paths:
                    display = path.relative_to(root) if path.is_relative_to(root.resolve()) else path
                    _diagnostic(diagnostics, "PAC-ORPHAN-FILE-001", "warning", f"Uncataloged file: {display}.")

    diagnostics.sort(key=lambda d: (d["code"], d.get("asset_id") or "", d["message"]))
    return {"schema_version": "portrait_catalog_validation_v1",
            "status": "fail" if any(d["severity"] == "error" for d in diagnostics) else "pass",
            "asset_count": len(assets), "diagnostics": diagnostics,
            "indexes": build_indexes(assets)}


def build_indexes(assets: list[dict[str, Any]]) -> dict[str, Any]:
    """Return sorted Estate-wide and resident views with deterministic keys."""
    ordered = sorted(assets, key=lambda a: (a.get("resident_id", ""), a.get("portrait_type", ""),
                                            a.get("angle", ""), a.get("canonical_state", ""),
                                            a.get("revision", 0), a.get("asset_id", "")))
    residents: dict[str, list[str]] = {}
    lookup: dict[str, list[str]] = {}
    for asset in ordered:
        aid = asset.get("asset_id", "")
        resident = asset.get("resident_id", "")
        residents.setdefault(resident, []).append(aid)
        key = "|".join(str(asset.get(k, "")) for k in ("resident_id", "portrait_type", "angle", "canonical_state"))
        lookup.setdefault(key, []).append(aid)
    return {"estate": [a.get("asset_id") for a in ordered],
            "residents": dict(sorted(residents.items())), "lookup": dict(sorted(lookup.items()))}


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate and index a WP-4126 portrait catalog")
    parser.add_argument("catalog", type=Path)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path)
    parser.add_argument("--scan-root", action="append", type=Path, default=[])
    args = parser.parse_args()
    result = validate_catalog(json.loads(args.catalog.read_text()), root=args.root, scan_roots=args.scan_root)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"status": result["status"], "diagnostics": len(result["diagnostics"])}))
    return 0 if result["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
