"""Deterministic, fail-closed vertical comparison-sheet runtime (WP-4129)."""
from __future__ import annotations

import argparse
import hashlib
import html
import json
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "vertical_comparison_sheet_manifest_v1"
ANGLE_SETS = {
    "five": ("front", "front_left_45", "left_profile", "rear_left_45", "rear"),
    "eight": ("front", "front_left_45", "left_profile", "rear_left_45", "rear",
              "rear_right_45", "right_profile", "front_right_45"),
}
FIXED_CONTROLS = ("identity", "age_presentation", "hairstyle", "expression", "camera",
                  "crop", "scale", "wardrobe", "pose", "lighting", "background", "footwear")
SHA_PREFIX = "sha256:"


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def sha256(value: bytes) -> str:
    return SHA_PREFIX + hashlib.sha256(value).hexdigest()


def manifest_hash(manifest: dict[str, Any]) -> str:
    """Hash semantic input while excluding its self-referential output record."""
    content = {k: v for k, v in manifest.items() if k != "output"}
    return sha256(canonical_json(content))


def _diagnostic(items: list[dict[str, str]], code: str, message: str, location: str = "$") -> None:
    items.append({"code": code, "severity": "error", "location": location, "message": message})


def validate_manifest(manifest: dict[str, Any], *, root: Path | None = None) -> dict[str, Any]:
    """Validate ordering, locked controls, source bytes, review and honest output claims."""
    found: list[dict[str, str]] = []
    if manifest.get("schema_version") != SCHEMA_VERSION:
        _diagnostic(found, "VCS-SCHEMA-001", "Unsupported schema version.")
    mode = (manifest.get("layout") or {}).get("angle_set")
    expected_angles = ANGLE_SETS.get(mode)
    if not expected_angles:
        _diagnostic(found, "VCS-LAYOUT-001", "angle_set must be five or eight.", "$.layout.angle_set")
        expected_angles = ()
    layout = manifest.get("layout") or {}
    for key in ("canvas_width_px", "canvas_height_px", "cell_width_px", "cell_height_px",
                "gap_px", "label_gutter_px", "background", "zoomable"):
        if key not in layout:
            _diagnostic(found, "VCS-LAYOUT-002", f"Missing layout field {key}.", "$.layout")
    variables = manifest.get("variables") or {}
    intended = variables.get("intended")
    fixed = variables.get("fixed") or {}
    if not isinstance(intended, list) or not intended:
        _diagnostic(found, "VCS-VARIABLE-001", "At least one intended variable is required.", "$.variables.intended")
        intended = []
    for name in FIXED_CONTROLS:
        if name not in fixed or fixed[name] in (None, "", {}):
            _diagnostic(found, "VCS-FIXED-001", f"Missing fixed control {name}.", f"$.variables.fixed.{name}")
    if "footwear" in intended and set(intended) != {"footwear"}:
        _diagnostic(found, "VCS-FOOTWEAR-001", "Footwear may vary only when it is the sole intended variable.")

    variants = manifest.get("variants") if isinstance(manifest.get("variants"), list) else []
    ids = [v.get("variant_id") for v in variants]
    if len(variants) < 2 or len(ids) != len(set(ids)):
        _diagnostic(found, "VCS-VARIANT-001", "Two or more uniquely identified variants are required.")
    if [v.get("order") for v in variants] != list(range(1, len(variants) + 1)):
        _diagnostic(found, "VCS-ORDER-001", "Variant order must be contiguous and list ordered.")

    materialized = 0
    source_hashes: list[str] = []
    for vi, variant in enumerate(variants):
        base = f"$.variants[{vi}]"
        if not variant.get("label") or not variant.get("measurements"):
            _diagnostic(found, "VCS-LABEL-001", "Variant label and measurements are required.", base)
        cells = variant.get("cells") if isinstance(variant.get("cells"), list) else []
        if tuple(c.get("angle_id") for c in cells) != tuple(expected_angles):
            _diagnostic(found, "VCS-ANGLE-001", "Cells must exactly match deterministic angle order.", base + ".cells")
        for ci, cell in enumerate(cells):
            loc = f"{base}.cells[{ci}]"
            source = cell.get("source") or {}
            state = cell.get("state")
            if state == "pending":
                if source:
                    _diagnostic(found, "VCS-PENDING-001", "Pending cells cannot claim a source asset.", loc)
                continue
            if state != "ready":
                _diagnostic(found, "VCS-STATE-001", "Cell state must be pending or ready.", loc)
                continue
            materialized += 1
            for key in ("path", "sha256", "capture_manifest_ref", "capture_set_id"):
                if not source.get(key):
                    _diagnostic(found, "VCS-SOURCE-001", f"Ready source missing {key}.", loc)
            if source.get("sha256"):
                source_hashes.append(source["sha256"])
            if root and source.get("path"):
                path = root / source["path"]
                if not path.is_file():
                    _diagnostic(found, "VCS-SOURCE-MISSING-001", "Source asset is missing.", loc)
                elif sha256(path.read_bytes()) != source.get("sha256"):
                    _diagnostic(found, "VCS-SOURCE-HASH-001", "Source hash does not match bytes.", loc)
            if cell.get("fixed_fingerprint") != sha256(canonical_json(fixed)):
                _diagnostic(found, "VCS-CONSISTENCY-001", "Cell fixed controls do not match the sheet.", loc)
    required = len(variants) * len(expected_angles)
    complete = required > 0 and materialized == required
    review = manifest.get("review") or {}
    if review.get("status") == "accepted":
        if not complete:
            _diagnostic(found, "VCS-ACCEPT-001", "An incomplete sheet cannot be accepted.")
        if not (review.get("steward_id") and review.get("decided_at") and review.get("annotation_ref")
                and review.get("difference_visible") is True):
            _diagnostic(found, "VCS-REVIEW-001", "Acceptance needs Steward evidence and visible difference confirmation.")
    output = manifest.get("output") or {}
    if output.get("state") == "generated":
        if not complete:
            _diagnostic(found, "VCS-OUTPUT-001", "Output cannot be generated from incomplete inputs.")
        if output.get("input_manifest_sha256") != manifest_hash(manifest):
            _diagnostic(found, "VCS-OUTPUT-HASH-001", "Output input-manifest hash is stale or invalid.")
        if root and output.get("path"):
            path = root / output["path"]
            if not path.is_file() or sha256(path.read_bytes()) != output.get("sha256"):
                _diagnostic(found, "VCS-OUTPUT-BYTES-001", "Output bytes are missing or hash-mismatched.")
    elif output.get("state") != "queued":
        _diagnostic(found, "VCS-OUTPUT-STATE-001", "Output state must be queued or generated.")
    found.sort(key=lambda d: (d["code"], d["location"], d["message"]))
    return {"schema_version": "vertical_comparison_sheet_validation_v1",
            "status": "fail" if found else "pass", "generation_ready": complete and not found,
            "coverage": {"required": required, "materialized": materialized},
            "source_set_sha256": sha256(canonical_json(sorted(source_hashes))), "diagnostics": found}


def render_html(manifest: dict[str, Any], root: Path) -> tuple[Path, str]:
    """Create a zoomable deterministic HTML review surface; never render pending evidence."""
    result = validate_manifest(manifest, root=root)
    if not result["generation_ready"]:
        raise ValueError("manifest is not generation-ready: " + ", ".join(d["code"] for d in result["diagnostics"]))
    layout = manifest["layout"]
    rows = []
    for variant in manifest["variants"]:
        cells = "".join(f'<figure><img src="{html.escape(c["source"]["path"])}" alt="{html.escape(variant["label"])} {c["angle_id"]}"><figcaption>{html.escape(c["angle_id"])}</figcaption></figure>' for c in variant["cells"])
        rows.append(f'<section><header><strong>{html.escape(variant["label"])}</strong><pre>{html.escape(json.dumps(variant["measurements"], sort_keys=True))}</pre></header><div class="cells">{cells}</div></section>')
    title = html.escape(manifest["sheet_id"])
    document = f'''<!doctype html><meta charset="utf-8"><title>{title}</title><style>
body{{margin:0;background:{layout["background"]};font-family:system-ui;color:#111}} main{{width:{layout["canvas_width_px"]}px;margin:auto}} section{{display:grid;grid-template-columns:{layout["label_gutter_px"]}px 1fr;gap:{layout["gap_px"]}px;border-bottom:1px solid #777;padding:{layout["gap_px"]}px 0}} .cells{{display:grid;grid-template-columns:repeat({len(ANGLE_SETS[layout["angle_set"]])},{layout["cell_width_px"]}px);gap:{layout["gap_px"]}px}} figure{{margin:0}} img{{width:{layout["cell_width_px"]}px;height:{layout["cell_height_px"]}px;object-fit:contain}} figcaption{{text-align:center}} header{{overflow-wrap:anywhere}} pre{{white-space:pre-wrap}}</style><main><h1>{title}</h1>{''.join(rows)}</main>'''
    output = root / manifest["output"]["path"]
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(document, encoding="utf-8")
    return output, sha256(output.read_bytes())


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate or render a WP-4129 comparison sheet")
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--validation-output", type=Path)
    parser.add_argument("--render", action="store_true")
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text())
    result = validate_manifest(manifest, root=args.root)
    if args.validation_output:
        args.validation_output.parent.mkdir(parents=True, exist_ok=True)
        args.validation_output.write_text(json.dumps(result, indent=2) + "\n")
    if args.render:
        render_html(manifest, args.root)
    print(json.dumps({"status": result["status"], "generation_ready": result["generation_ready"], "coverage": result["coverage"]}))
    return 0 if result["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
