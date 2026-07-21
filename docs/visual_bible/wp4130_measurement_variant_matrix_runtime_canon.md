# WP-4130 Measurement Variant Matrix Runtime Canon

## Authority and scope

This canon governs resident-specific physical-measurement comparisons. A matrix is decision support, never canonical physical data by itself. The resident Visual Bible and explicit Steward decision are authoritative; provenance must name the physical specification and scale profile. A matrix is bound to one `resident_id`, and constraints from another resident fail closed. Evelyn below is calibration evidence, **not** a universal template.

## Model, units, and identifiers

Measurements are normalized as positive decimal SI values: circumferences and height in `cm`, small linear values in `mm`, dimensionless proportions in `ratio`. Display conversions (including cup notation and inches) are labels only; they never replace normalized values. Rounding must not change stored values. Top includes bust/chest/shoulder dimensions; middle includes waist and torso dimensions; bottom includes hip/seat/thigh/leg dimensions. A resident hook may authorize additional categorized dimensions and ranges.

A matrix contains four roles: `baseline` (the authoritative starting record), `lower`, `target` (the proposed/candidate value), and `higher`. IDs follow `<resident>-<category>:<role>:rNNN`; labels are human-readable and include exact values. Lower and higher bracket target as authorized by the work package. Lifecycle is `candidate`, `selected`, `rejected`, `superseded`, or `unresolved`. Baseline may remain unresolved while review is pending; no state implies canon.

## One-variable-at-a-time invariant

Each comparison cycle declares exactly one intended physical variable, its top/middle/bottom category, and a narrative reason. Lower and higher must differ from baseline only in that measurement; target may restate baseline when the proposed target is the current authority. Separate matrices are required to test another measurement or footwear. It is prohibited to change or omit resident height, frame, proportions, posture, face, hair, expression, wardrobe, footwear, camera, lighting, crop, or background. Age presentation and identity are carried by the face/Visual Bible lock. Wardrobe fit, fabric behavior, pose, perspective, heel, crop, or lighting effects must never be reported as anatomy. A canonical-JSON SHA-256 fingerprint over all fixed variables makes unintended drift detectable.

Invalid combinations include multiple intended variables; a pose/wardrobe/camera control named as a measurement; mixed units within a resident range; a value outside its resident range; duplicate/missing roles or IDs; changed height, proportions, posture, wardrobe, or footwear; cross-resident constraint sources; unordered angles; selection without Steward evidence; and rejected/superseded records without reasons.

## Matrix and capture relationships

Rows are ordered baseline, lower, target, higher records; columns are the intended measurement plus locked context and lifecycle. Visual artifacts use WP-4129 vertically aligned rows and the ordered WP-4128 five-angle subset: front, front-left 45°, left profile, rear-left 45°, rear. Each role links to its own capture-set manifest, while one vertical-sheet reference binds the review surface. Eight-angle capture remains available upstream. Capture cells must inherit the fixed fingerprint. Missing genuine captures are queued, not represented by placeholders.

A reviewer records whether the intended difference is discernible at normal review size. Zooming separate windows or relying on memory fails review and requires regeneration. Wardrobe and posture remain constant during regeneration. Anatomical plausibility includes positive normalized values, resident-authorized ranges, coherent frame/proportions and no impossible discontinuity. Constraint hooks may be narrow or broad but must cite that resident's Visual Bible.

## Evelyn calibration (non-universal example)

Evelyn's possible 33B–20–30, 33B–21–31, and 33B–22–32 labels illustrate a narrow range. The fixture deliberately isolates waist while holding hip at baseline; a separate hip matrix is required to evaluate hip. The likely 33B–21–31 target remains unresolved until the Steward decides. These values must never seed another resident.

## Steward decision, revision, lock, and rollback

`selected` requires one matching decision with Steward identity, timestamp, rationale, and normal-size discernibility evidence. Rejection preserves variant, reason, provenance, and assets but cannot promote. Supersession adds a forward reference and retains history. A selected revision may lock only after validation, genuine capture/sheet review, and the Steward decision. Revisions increment monotonically and identify `supersedes`; rollback creates a new revision pointing to a previously validated matrix and never deletes intervening records. Pending and unresolved records remain unlocked. No implementation may fabricate a decision.

## Diagnostics and deterministic validation

The validator emits stable, sorted `MVM-*` diagnostics for schema, resident authority, provenance, intended variable, missing locks, constraints, variants, units/ranges, fixed drift, one-variable-at-a-time violations, selection, integration, disposition, and stale hashes. Canonical JSON sorts keys and removes insignificant whitespace; the manifest digest excludes only its self-referential integrity field. The CLI returns 0 on pass and 2 on failure and can write a deterministic report.

## Testing and anti-patterns

Unit tests cover deterministic hashes, complete locks, OVAT drift, unit/range enforcement, resident isolation, lifecycle evidence, rejected/superseded traceability, and honest queues. Integration tests bind the five ordered angles to capture-set and vertical-sheet references and exercise the CLI. Anti-patterns include: copying Evelyn globally; changing waist and hip together; fitting clothes to exaggerate a result; changing pose or heels; using prose-only measurements; treating a generated image as measurement authority; dropping rejected variants; overwriting revisions; selecting by default; or fabricating captures, discernibility, or Steward review.

## Completion criteria

Repository completion requires the schema, manifest/template example, baseline and comparison records, intended/fixed declarations, constraint hooks, deterministic validator and CLI, capture/sheet links, lifecycle and review records, rejection/supersession behavior, queued generation truth, tests, traceability, acceptance evidence, receipt, and pending-to-implemented transition. Production review remains pending until genuine captures, a generated readable sheet, discernibility assessment, and Steward decision exist; repository implementation can be complete without inventing them.
