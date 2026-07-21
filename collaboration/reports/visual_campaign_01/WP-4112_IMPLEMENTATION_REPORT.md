# WP-4112 Implementation Report

## Dependency verification

The repository baseline at `c3e23a0` contains the merged Campaign 01 WP-4108—WP-4111 surfaces: the Visual Bible foundation schema/repositories, versioned physical specification, and height/scale/camera/view/heel metadata. The WP-4112 implementation consumes `scale_profile_id` and `camera_profile_id`; it creates no alternative height, scale, camera, resident ID, or approval registry.

## Implemented and validated behavior

- Strict A/B/C records preserve exact decimal text and units, enforce A ≤ B ≤ C, require B in the center of the primary vertical sheet, reject undeclared changes, and allow only standard or explicitly authorized dimensions.
- Resident-owned bounds support narrow/asymmetric/broad policies without global defaults. Evelyn is guarded as provisional, isolated calibration and cannot request promotion through the example path.
- Equality gates cover identity, facial fingerprint, adult age presentation, pose, camera, lighting, background, wardrobe, footwear/heels, resolution, model/version, seed/equivalent, prompts, and settings.
- Five-angle turnarounds, anatomical guides, non-rescaling alignment, direct normal-size review, a required primary vertical artifact, and supplemental-only matrix are machine checked.
- Opaque, adult-appropriate, non-explicit review wardrobe and the compatible ≥3-inch heel/exemption protocol are enforced. Standing height and body measurement remain separate from footwear-adjusted presentation and posture.
- Provenance, asset links, revision/lineage, privacy, supersession, rejected evidence, diagnostics, deterministic bounded regeneration, Steward decision, and separate versioned promotion records are represented.
- Failed/ambiguous legibility blocks review and requires diagnostics/regeneration. No visual legibility is inferred by automation.
- Only an explicitly approved Steward decision can pass the canonical-promotion validator. Selection alone is noncanonical and rejected/superseded evidence is retained.

## Validation scenarios

Automated tests cover a valid cycle, all approved/custom dimensions, exact imperial/metric data, unauthorized drift, control equality, layout/alignment, heels and exemption, incomplete provenance, legibility failure/regeneration, independent resident ranges, Evelyn isolation, append-only decision history, explicit Steward promotion, schemas, and deterministic/non-mutating output. Fixtures are synthetic record test doubles: no image, resident measurement, or approval is asserted.

## Known limitations

- Visual legibility remains a human/evidence-producing review task; the validator verifies its recorded gate and never fabricates evidence.
- This package does not generate imagery or provide a browser UI. The Steward-facing surface is the specified single-sheet artifact plus governed record/document workflow.
- WP-4127 and later packages are untouched. Final resident measurements and approvals remain outside this implementation.

## Next permitted action

Review this WP-4112 pull request, run Steward-local visual validation when real restricted comparison assets exist, and merge only after repository checks and review pass. Do not begin a later work package on this branch.
