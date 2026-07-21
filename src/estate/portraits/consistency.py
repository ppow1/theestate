"""Auditable, non-CV portrait consistency validation for WP-4125.

The validator proves repository structure and evidence integrity.  It deliberately
does not infer visual identity: supplied machine scores are advisory and every
visual decision remains a Steward decision.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REQUIRED_CATEGORIES = {
    "hero", "office", "full_body", "profile", "rear", "front_three_quarter",
    "rear_three_quarter", "expression", "headshot", "thumbnail_32", "thumbnail_64",
}
VISUAL_CHECKS = {
    "identity", "face", "hair", "eyes", "age", "height", "proportion",
    "posture", "wardrobe", "expression", "scale", "resident_separation",
    "thumbnail_recognizability",
}
DECISIONS = {"pass", "fail", "review_required", "not_applicable"}
SEVERITY_ORDER = {"info": 0, "warning": 1, "major": 2, "critical": 3}


@dataclass(frozen=True)
class Diagnostic:
    code: str
    severity: str
    message: str
    resident_id: str | None = None
    asset_id: str | None = None
    remediation: str | None = None


def _hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _diag(items: list[Diagnostic], code: str, severity: str, message: str,
          resident: str | None = None, asset: str | None = None,
          remediation: str | None = None) -> None:
    items.append(Diagnostic(code, severity, message, resident, asset, remediation))


def validate_consistency_manifest(manifest: dict[str, Any], *, root: Path) -> dict[str, Any]:
    """Validate evidence and return a stable result record; never performs CV."""
    diagnostics: list[Diagnostic] = []
    resident = manifest.get("resident_id")
    if manifest.get("schema_version") != "portrait_consistency_manifest_v1":
        _diag(diagnostics, "PCV-SCHEMA-001", "critical", "Unsupported manifest schema.", resident)
    if not resident:
        _diag(diagnostics, "PCV-RESIDENT-001", "critical", "resident_id is required.")

    assets = manifest.get("assets", [])
    present = {a.get("category") for a in assets}
    for category in sorted(REQUIRED_CATEGORIES - present):
        _diag(diagnostics, "PCV-COVERAGE-001", "major", f"Missing required category: {category}.", resident,
              remediation="Generate or register evidence and rerun validation.")

    seen_ids: set[str] = set()
    hashes: dict[str, tuple[str, str]] = {}
    for asset in assets:
        asset_id = asset.get("asset_id")
        if not asset_id or asset_id in seen_ids:
            _diag(diagnostics, "PCV-ASSET-001", "critical", "Asset ID is missing or duplicated.", resident, asset_id)
        if asset_id:
            seen_ids.add(asset_id)
        for field in ("asset_path", "sha256", "source_path", "source_sha256", "workflow"):
            if not asset.get(field):
                _diag(diagnostics, "PCV-PROVENANCE-001", "major", f"Missing {field}.", resident, asset_id)
        path_value = asset.get("asset_path")
        if path_value:
            path = root / path_value
            if not path.is_file():
                _diag(diagnostics, "PCV-FILE-001", "critical", f"Asset does not exist: {path_value}.", resident, asset_id)
            elif asset.get("sha256") != _hash(path):
                _diag(diagnostics, "PCV-HASH-001", "critical", "Asset hash does not match bytes.", resident, asset_id)
        source_value = asset.get("source_path")
        if source_value:
            source = root / source_value
            if not source.is_file():
                _diag(diagnostics, "PCV-SOURCE-001", "major", f"Source does not exist: {source_value}.", resident, asset_id)
            elif asset.get("source_sha256") != _hash(source):
                _diag(diagnostics, "PCV-SOURCE-HASH-001", "critical", "Source hash does not match bytes.", resident, asset_id)
        digest = asset.get("sha256")
        if digest in hashes:
            prior_id, prior_category = hashes[digest]
            permitted = asset.get("duplicate_of") == prior_id
            if not permitted:
                _diag(diagnostics, "PCV-DUPLICATE-001", "major",
                      f"Undeclared duplicate bytes across {prior_category} and {asset.get('category')}.", resident, asset_id)
        elif digest:
            hashes[digest] = (asset_id or "<missing>", asset.get("category", "<missing>"))
        binding = asset.get("identity_binding")
        if binding != resident:
            _diag(diagnostics, "PCV-BINDING-001", "critical", "Identity binding does not match resident.", resident, asset_id)

    reviews = manifest.get("steward_reviews", {})
    missing_reviews = VISUAL_CHECKS - set(reviews)
    for check in sorted(missing_reviews):
        _diag(diagnostics, "PCV-REVIEW-MISSING-001", "major", f"Steward review missing: {check}.", resident,
              remediation="Add a named, dated Steward decision against immutable asset hashes.")
    for check, review in reviews.items():
        if check not in VISUAL_CHECKS or review.get("decision") not in DECISIONS:
            _diag(diagnostics, "PCV-REVIEW-INVALID-001", "major", f"Invalid review record: {check}.", resident)
        if review.get("decision") in {"pass", "fail"} and not all(review.get(k) for k in ("reviewer", "reviewed_at", "evidence_hashes")):
            _diag(diagnostics, "PCV-REVIEW-AUDIT-001", "major", f"Review is not auditable: {check}.", resident)
        if review.get("decision") == "fail":
            _diag(diagnostics, "PCV-VISUAL-FAIL-001", "critical", f"Steward failed visual check: {check}.", resident)
        elif review.get("decision") in {None, "review_required"}:
            _diag(diagnostics, "PCV-REVIEW-REQUIRED-001", "major", f"Steward decision required: {check}.", resident)

    for score in manifest.get("automated_scores", []):
        value = score.get("value")
        if not isinstance(value, (int, float)) or not 0 <= value <= 1 or not score.get("provider") or not score.get("model_version"):
            _diag(diagnostics, "PCV-SCORE-INVALID-001", "major", "Automated score lacks bounded value or provenance.", resident)
        elif value < 0.70:
            _diag(diagnostics, "PCV-SCORE-LOW-001", "major", "Advisory score is below 0.70; Steward review required.", resident)
        elif value < 0.85:
            _diag(diagnostics, "PCV-SCORE-BORDERLINE-001", "warning", "Advisory score is 0.70–0.85; Steward review required.", resident)
        # Scores >= .85 are evidence only and intentionally do not emit/pass a visual decision.

    has_blocker = any(d.severity in {"major", "critical"} for d in diagnostics)
    all_visual_pass = VISUAL_CHECKS <= set(reviews) and all(
        reviews[c].get("decision") in {"pass", "not_applicable"} for c in VISUAL_CHECKS
    )
    status = "pass" if not has_blocker and all_visual_pass else "review_required"
    if any(d.code in {"PCV-SCHEMA-001", "PCV-HASH-001", "PCV-SOURCE-HASH-001", "PCV-BINDING-001", "PCV-VISUAL-FAIL-001"} for d in diagnostics):
        status = "fail"
    packet = [{"diagnostic_code": d.code, "asset_id": d.asset_id, "action": d.remediation or d.message}
              for d in diagnostics if d.severity in {"major", "critical"}]
    return {
        "schema_version": "portrait_consistency_result_v1",
        "resident_id": resident,
        "status": status,
        "canonical_promotion_eligible": status == "pass",
        "structural_validation": "executed",
        "visual_validation": "steward_records_only_no_computer_vision",
        "diagnostics": [asdict(d) for d in sorted(diagnostics, key=lambda x: (-SEVERITY_ORDER[x.severity], x.code, x.asset_id or ""))],
        "remediation_packet": packet,
    }


def validate_estate_separation(manifests: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Detect declared cross-resident convergence; no pixels are compared."""
    diagnostics: list[Diagnostic] = []
    fingerprints: dict[str, str] = {}
    hashes: dict[str, str] = {}
    for manifest in manifests:
        resident = manifest.get("resident_id")
        fingerprint = manifest.get("visual_fingerprint_id")
        if not fingerprint:
            _diag(diagnostics, "PCV-FINGERPRINT-MISSING-001", "major", "Visual fingerprint evidence is missing.", resident)
        elif fingerprint in fingerprints and fingerprints[fingerprint] != resident:
            _diag(diagnostics, "PCV-CONVERGENCE-001", "critical", f"Fingerprint is also assigned to {fingerprints[fingerprint]}.", resident)
        else:
            fingerprints[fingerprint] = resident
        for asset in manifest.get("assets", []):
            digest = asset.get("sha256")
            if digest and digest in hashes and hashes[digest] != resident:
                _diag(diagnostics, "PCV-CROSS-RESIDENT-HASH-001", "critical", f"Asset bytes are shared with {hashes[digest]}.", resident, asset.get("asset_id"))
            elif digest:
                hashes[digest] = resident
    return [asdict(d) for d in diagnostics]


def run(input_path: Path, output_path: Path, *, root: Path) -> dict[str, Any]:
    payload = json.loads(input_path.read_text(encoding="utf-8"))
    manifests = payload.get("residents", [payload])
    results = [validate_consistency_manifest(m, root=root) for m in manifests]
    cross = validate_estate_separation(manifests)
    report = {
        "schema_version": "portrait_consistency_run_v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "implementation_claim": "structural and recorded-evidence validation only; no computer vision",
        "results": results,
        "estate_diagnostics": cross,
        "status": "review_required" if cross or any(r["status"] != "pass" for r in results) else "pass",
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="WP-4125 portrait consistency evidence validator")
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    report = run(args.input, args.output, root=args.root)
    print(json.dumps({"status": report["status"], "output": str(args.output)}))
    return 0 if report["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
