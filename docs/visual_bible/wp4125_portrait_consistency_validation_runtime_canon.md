# WP-4125 Portrait Consistency Validation Runtime Canon

## 1. Authority and boundary

This canon governs consistency evidence for hero, professional-office, full-body, profile/rear, front/rear three-quarter, expression, headshot, thumbnail, crop, wardrobe, and supported model/workflow variants. It validates repository facts and recorded observations. **It contains no computer vision and a machine score never establishes identity.** The Steward is the final authority for identity, presence, attractiveness, emotional accuracy, and resident distinction.

A run is auditable only from an immutable input manifest, asset/source hashes, model/workflow receipts, result record, and named/dated Steward reviews. `pass` permits a promotion recommendation but does not perform canonical promotion.

## 2. Required input and comparison artifacts

Each commissioned resident supplies one manifest with resident and visual-fingerprint bindings; a canonical anchor; every required category; asset/source paths and SHA-256 hashes; asset status; crop/angle/category; wardrobe; model/version, workflow, seed when supported, prompt/negative-prompt versions, reference hashes and adapter/LoRA versions; and Steward review records. Required categories are hero, office, full body, profile, rear, both front and rear three-quarter, expression, headshot, and native 32×32 and 64×64 thumbnails.

The human-review packet must include an adjacent, labeled comparison board with stable face scale and documented crops/status, the canonical anchor beside each row, a single-canvas variant comparison where feasible, an unlabeled all-resident recognition grid, native-size thumbnail previews on light/dark backgrounds, and cross-model controlled-prompt results where multiple supported workflows actually exist. An unavailable second workflow is recorded `not_applicable` with rationale; it is never invented.

## 3. Checks and ownership

### Deterministic structural checks

The runner checks schema version, unique asset IDs, required categories/angles, resident binding, paths, current asset and source hashes, provenance/workflow presence, declared duplicates, cross-resident identical bytes, unique declared fingerprint IDs, review completeness/audit fields, score range/provenance, and promotion eligibility. It does not inspect pixels, dimensions, poses, or faces. Category-specific WP-4118–4124 validators remain authoritative for dimensions, naming, crop receipts, camera and lifecycle rules.

### Steward visual checks

The Steward records `pass`, `fail`, `review_required`, or justified `not_applicable` for identity; face geometry/landmarks and visual fingerprint; hair color/texture/length/silhouette; eye color/shape; apparent age and skin-tone continuity; visible height, body proportion, posture and scale; wardrobe compatibility/change; expression authenticity; crop/lens effects; anatomy/artifacts; cross-model stability; resident separation/generic-face convergence; and thumbnail recognizability. Ethnicity/ancestry overstatement is reviewed as harmful drift, never inferred by automation.

## 4. Scoring, thresholds, and uncertainty

External scores are accepted only in `[0,1]` with provider and model version. `<0.70` is a major diagnostic; `0.70–<0.85` is warning/review-required; `>=0.85` remains advisory and cannot create a visual pass. Unsupported, uncalibrated, or missing scores are not silently converted to zero. Every threshold band requires Steward judgment.

A false positive (machine flags visually faithful work) is retained with the score receipt, Steward override/rationale, evidence hashes and reviewer; tune only a versioned future threshold. A false negative (machine misses visible drift) is a Steward failure decision, critical remediation, and regression fixture. Disagreement always resolves toward `review_required`, never automatic acceptance.

## 5. States, severity, and missing evidence

Diagnostics use `info`, `warning`, `major`, and `critical`. Missing category/provenance/review is major; missing files, stale hashes, cross-resident binding, failed Steward visual review, and convergence/shared bytes are critical where indicated by their diagnostic. Any major/critical issue blocks promotion. `fail` is reserved for integrity/identity binding or recorded visual failure; incomplete evidence is `review_required`. Missing assets remain explicitly pending and cannot prove acceptance.

Key codes are `PCV-COVERAGE-001`, `PCV-HASH-001`, `PCV-SOURCE-HASH-001`, `PCV-PROVENANCE-001`, `PCV-BINDING-001`, `PCV-DUPLICATE-001`, `PCV-CROSS-RESIDENT-HASH-001`, `PCV-CONVERGENCE-001`, `PCV-REVIEW-REQUIRED-001`, `PCV-VISUAL-FAIL-001`, and `PCV-SCORE-{LOW,BORDERLINE,INVALID}-001`.

## 6. Reports, revision, and remediation

Each run emits a versioned per-resident result, estate separation diagnostics, explicit `structural_validation` and `visual_validation` claims, status, promotion eligibility, and a remediation packet mapping blocking diagnostics to asset/action. A revision packet retains prior asset ID/hash, failure class, affected views, Steward notes, prompt/workflow deltas, target category, owner, due state, and new asset/hash; superseding never overwrites history. Reports must classify facial geometry, age, eye, hair, proportion, expression, ancestry overstatement, scale, wardrobe/crop identity loss, model-style drift, and artifact/anatomy failure where observed.

## 7. Supported workflows and anti-patterns

A workflow is supported only when its executable/version and receipts are available. Record exact model/version, seed support, references, adapters and prompt versions. Never claim pixel similarity, face embedding, landmark, color, anatomy, or cross-model analysis unless a separately governed implementation actually ran.

Forbidden: treating scores as approval; self-attested identity; hashes as visual proof; reusing one file across required angles; captions in recognition grids; undocumented crop/wardrobe/model changes; fabricated provenance; missing evidence labeled pass; generic-face checks based only on names; silent threshold tuning; or promotion with unresolved major drift.

## 8. Verification and completion

Fixtures cover a structurally valid, Steward-reviewed set and invalid missing/stale/cross-resident cases. Unit tests exercise categories, hashes, bindings, review gates, score bands, convergence and remediation; integration executes JSON input to report. Acceptance requires every commissioned resident board/category, classified repair queue, successful unlabeled and thumbnail Steward reviews, documented applicable cross-model runs, no unresolved major/critical drift, valid hashes/provenance, and passing targeted/full relevant tests. WP-4125 implementation may be complete while portrait-library validation remains `review_required`; the work package's visual completion condition is met only after all those human evidence requirements pass.
