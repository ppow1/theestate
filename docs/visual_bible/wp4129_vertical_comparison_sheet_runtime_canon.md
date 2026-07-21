# WP-4129 Vertical Comparison Sheet Runtime Canon

**Authority:** Visual Estate Initiative, Campaign 03
**Version:** 1.0 (2026-07-21)
**Runtime schema:** `vertical_comparison_sheet_manifest_v1`

## 1. Purpose and governing rule

A comparison sheet is a single, vertically stacked review surface for inspecting nearby resident variants without remembering another render or arranging windows. Each complete horizontal row is one variant; each column is the same angle. The layout serves visual comparison, never decoration. It is review evidence only when every displayed cell links to genuine, hash-verified source bytes.

A queued manifest or wireframe is **not generated visual evidence**. Missing WP-4128 captures must remain `pending`; generators must fail closed rather than invent, duplicate, relabel, or silently omit images.

## 2. Rows, columns, angles, variants, labels, and order

Rows sort by numeric `order`, contiguously from 1. Variant A/lower is first, B/candidate second, and C/upper third when three are used. Resident-specific ranges are required; Evelyn's calibration must not become a universal range. Columns use exactly one ordered set:

1. five: `front`, `front_left_45`, `left_profile`, `rear_left_45`, `rear`;
2. eight: the five above followed by `rear_right_45`, `right_profile`, `front_right_45`.

The eight-angle set preserves WP-4128 clockwise nomenclature. A five-angle sheet may use the corresponding left-side views but cannot relabel another angle as the preferred view. Front, three-quarter, side, rear-three-quarter, and rear cells share column boundaries, baseline, floor plane, figure centerline, head line, and scale. No cell may be independently enlarged.

Labels live in the row header gutter and captions below cells—outside image evaluation rectangles. Each sheet identifies resident, date, status, model/workflow and reproducibility record. Each row identifies order, variant, exact declared measurements, canonical height, wardrobe, footwear and heel height. Cell captions identify angle and link to the source asset. Labels must never cover anatomy or silhouettes.

## 3. Fixed and intended variables

`variables.intended` is an explicit non-empty list. All other review properties are fixed. `variables.fixed` declares identity/reference and seed where applicable, age presentation, hairstyle, expression, camera geometry, crop, scale, wardrobe and fabric behavior, pose, lighting, background, and footwear. Every cell binds the SHA-256 fingerprint of that record.

Camera, crop, scale, wardrobe, pose, expression, lighting, background, and footwear are identical across cells. Footwear may differ only when `footwear` is the sole intended variable. At least one applicable resident review sheet must present and label a heel of at least 7.62 cm (3 inches); it supplements rather than replaces a neutral/barefoot-equivalent true-height reference.

## 4. Layout, dimensions, spacing, and review behavior

Presets are minimums, not targets when readability demands more:

| preset | normal use | minimum canvas | cells | label gutter | gap |
|---|---|---:|---:|---:|---:|
| portrait | five columns, 2–3 rows | 2400 × 3200 px | 360 × 720 px | 360 px | 24 px |
| landscape | eight columns, 2–3 rows | 5600 × 3000 px | 560 × 960 px | 480 px | 32 px |
| tall three-variant | five columns, 3 rows | 3600 × 6000 px | 560 × 960 px | 520 px | 32 px |

Browser export is self-contained or relative-link HTML with lossless/full-resolution sources, native browser zoom, click-through to each governed source, and no upscaling hidden by CSS. Archival export is lossless PNG/TIFF or PDF at 300 PPI with embedded/sibling manifest, color profile, source hashes, output hash, generator version, and timestamp. Thumbnails are navigation aids only. The rendered figure should occupy at least 80% of cell height at normal display size.

If an intended difference cannot be reasonably seen on one surface at normal size, the comparison fails. Increase resolution or figures, remove decoration, use alignment guides or optional registered silhouettes, or add localized crops while retaining complete figures. Zoom may confirm a difference; it must not be necessary merely to discover it.

## 5. Manifest, source linkage, and consistency

The manifest is the comparison set and layout contract. It contains layout geometry, intended and fixed variables, ordered variants and cells, review record, revision packet, and output record. Every ready cell declares source path, `sha256:…`, WP-4128 capture-manifest reference, and capture-set ID. The source angle, resident, variant, state, crop, controls, and hash must agree. The comparison source-set digest is computed from sorted source hashes.

Inputs are classified before generation:

- **missing:** path or capture record absent → remain queued and emit `VCS-SOURCE-MISSING-001`;
- **mismatched:** bytes/hash, angle, resident, variant, or fixed fingerprint differs → fail;
- **stale:** source/revision changed after recorded input-manifest hash → regenerate, never overwrite accepted evidence;
- **invalid:** schema, ordering, layout, labels, controls, or provenance fails → quarantine from generation;
- **pending:** honest enumerated slot without bytes → valid planning data but never generation-ready.

Determinism requires canonical JSON, stable variant and angle order, stable labels, relative paths, fixed geometry, and SHA-256 metadata. A repeated run on identical inputs must produce byte-identical output except where the export format embeds time; such time must be provided as manifest input.

## 6. Steward review, annotations, and revisions

Annotations are records, not pixels baked over evaluation areas. Each has annotation ID, Steward/reviewer ID, timestamp, variant and angle targets, normalized coordinates when spatial, category, comment, and resolution status. Acceptance requires an explicit Steward identity, decision time, annotation packet reference, and `difference_visible: true`. Review states are `pending`, `in_review`, `changes_requested`, `accepted`, `rejected`, or `superseded`.

A revision packet records revision number, predecessor/superseded artifact, change summary, changed intended values or sources, unchanged fixed fingerprint, author, time, validation report, and new hashes. Accepted exports are immutable. Corrections create a new revision; they never replace the prior manifest or output. Superseded revisions remain traceable.

## 7. Export and archive

Working manifests live with the campaign queue; generated outputs live in a revision-specific directory. Archive together: manifest, schema/version reference, source-link inventory and hashes, rendered output and hash, validation report, review/annotation record, revision packet, generator version, and production receipt. Relative source links must resolve from the archived review bundle or be accompanied by a resolver map. Retention follows the resident visual-bible policy; canonical acceptance never deletes candidates needed for audit.

## 8. Diagnostics and validation

Validation is fail-closed and deterministic. Codes cover schema/layout, variable declarations, footwear constraints, variant/order/angle/label errors, pending-source claims, missing/hash-mismatched sources, control drift, incomplete acceptance, absent Steward evidence, stale input hashes, and missing/mismatched output bytes. Diagnostics sort by code, JSON location, and message. `generation_ready` means all required cells are materialized and validation has no errors; a valid pending manifest can pass while readiness is false.

Before Steward review verify: row and column order; same-angle alignment; genuine links and hashes; all fixed-control fingerprints; exact measurement/height/heel labels; labels outside evaluation areas; readable intended difference; normal-size full figures; zoom and click-through; output and manifest hashes; revision and annotation packets; and explicit review status.

## 9. Tests

Unit tests cover canonical orders/hashes, valid pending queues, fixed-variable and angle drift, footwear rules, missing and mismatched bytes, incomplete acceptance, stale output metadata, deterministic rendering, CLI reports, schema parsing, and the honest generation queue. Integration uses small synthetic byte fixtures solely to test linkage/render mechanics; such fixtures must be labeled test-only and never presented as resident evidence.

## 10. Anti-patterns

Forbidden: contact sheets with variants in columns; sorting by filename; mixing angles or camera setups; per-cell crops/scales; labels over bodies; unlabeled heels; changing wardrobe to emphasize a measurement; decorative frames that shrink figures; screenshots without source links; lossy archival masters; stale hashes; accepting incomplete rows; silently substituting a capture; treating a queue, mockup, placeholder, or synthetic test asset as visual evidence; and forcing one resident's measurement interval on another.

## 11. Completion criteria

The standard is complete when the schema and canon are versioned; deterministic validation and generation tooling exist; portrait, landscape, and tall geometry are specified; ordering, labeling, linkage, variables, review, revision, export, archive, and diagnostics are enforced; example fixtures and unit/integration tests pass; and a production queue truthfully reports readiness. A particular sheet is complete only after all hash-verified sources exist, generation succeeds, differences are visible, and the Steward explicitly accepts the revision.

## 12. Current production status

The WP-4128 capture-set model, schema, runtime, and eight-angle queues are present. Its completion receipt reports **0 of 64 images materialized**. Therefore WP-4129 supplies the complete deterministic manifest and queue, but produces no resident comparison sheet and claims no visual evidence. Generation becomes ready when genuine, consistent WP-4128 captures and authoritative measurement variants are linked and pass validation.
