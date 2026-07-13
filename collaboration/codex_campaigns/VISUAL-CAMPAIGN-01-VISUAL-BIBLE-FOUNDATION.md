# Visual Campaign 01 — Visual Bible Foundation

## Status
Ready for Codex execution.

## Mission
Implement the Visual Estate foundation defined by WP-4108 through WP-4117 so every commissioned resident can have a governed, reviewable, reproducible Visual Bible and Visual Asset Library.

## Included Work Packages
Execute in strict series:

1. `collaboration/work_packages/pending/WP-4108_SERIES_Visual_Bible_Schema_and_Repository_Structure.md`
2. `collaboration/work_packages/pending/WP-4109_SERIES_Canonical_Physical_Specification_Standard.md`
3. `collaboration/work_packages/pending/WP-4110_SERIES_Facial_Geometry_and_Visual_Fingerprint.md`
4. `collaboration/work_packages/pending/WP-4111_SERIES_Height_Proportion_and_Scale_Reference_System.md`
5. `collaboration/work_packages/pending/WP-4112_SERIES_Measurement_Variant_Review_Workflow.md`
6. `collaboration/work_packages/pending/WP-4113_SERIES_Wardrobe_and_Signature_Look_Library.md`
7. `collaboration/work_packages/pending/WP-4114_SERIES_Visual_Prompt_Engineering_Canon.md`
8. `collaboration/work_packages/pending/WP-4115_SERIES_Visual_Negative_Prompt_Canon.md`
9. `collaboration/work_packages/pending/WP-4116_SERIES_Steward_Visual_Review_and_Revision_Workflow.md`
10. `collaboration/work_packages/pending/WP-4117_SERIES_Visual_Bible_Acceptance_and_Canonical_Lock.md`

## Required Outcomes

- Repository structure for resident Visual Bibles and image assets.
- Machine-readable schemas for canonical physical specifications, facial geometry, height and scale, wardrobe, prompts, negative prompts, review state, provenance, and canonical lock state.
- Separate storage for canonical assets, candidate assets, rejected assets, comparison sheets, thumbnails, group images, and restricted/private layers.
- Support for both written Visual Bibles and actual image libraries.
- Steward Notes preserved as authoritative review input.
- Deterministic naming, versioning, hashes, lineage, and replacement history.
- Validation preventing candidate imagery from silently becoming canonical.

## Measurement Comparison Standard

Implement support for three nearby body-measurement variants when a resident requires visual calibration.

The comparison workflow must require:

- identical resident identity and facial fingerprint;
- identical pose, expression, camera position, focal length, lighting, background, and wardrobe;
- vertically aligned turnaround comparisons so matching angles can be inspected directly;
- front, front three-quarter, side, rear three-quarter, and rear views at minimum;
- at least one applicable comparison set in footwear with heels of 3 inches or more;
- explicit variant labels and measurement metadata;
- regeneration when intended differences are not visually distinguishable;
- Steward selection notes explaining the canonical choice.

Resident-specific calibration must not become a universal body template. Evelyn's narrow calibration range is an example only.

## Visual Identity Rules

- Every resident must have an individual visual fingerprint.
- Group images must preserve resident differentiation, relative height, posture, silhouette, wardrobe language, and interpersonal spacing.
- Visual identity must survive changes in clothing, setting, pose, rendering model, and image style.
- Physical attributes must be recorded as character-specific design decisions, not generic beauty defaults.
- Subtle artistic intent may be documented without asserting ancestry or other sensitive traits from appearance.

## Access and Governance

- Do not hide specifications from HR or governance systems.
- Use explicit visibility classes such as public, internal, restricted, and private.
- Restricted or private persona/visual layers must be separately loadable, auditable, and unavailable by default.
- Evelyn private-mode hooks may be created as governed schema and runtime integration points, but this campaign must not bypass authorization or collapse private material into the public identity layer.

## Implementation Constraints

- Reuse existing resident identity, character architecture, provenance, access-control, and asset-catalog systems where practical.
- Do not replace or weaken canonical resident documents.
- Do not fabricate final resident measurements where the Steward has not approved them.
- Do not generate or commit large binary image sets merely to satisfy tests; provide correct repository plumbing, manifests, schemas, examples, and validation fixtures.
- Keep all generated examples clearly marked as examples or candidates unless explicitly accepted.

## Validation

Add automated tests for:

- schema validation;
- required directory and manifest creation;
- canonical/candidate/rejected state separation;
- provenance and hash integrity;
- measurement-variant comparison metadata;
- vertical angle alignment requirements;
- heel-comparison metadata;
- Steward review and revision history;
- restricted/private access classification;
- canonical lock and unlock controls;
- cross-resident identity separation.

Run focused tests and then the complete test suite.

## Required Reports

Create a campaign report under:

`collaboration/reports/visual_campaign_01/`

The report must include:

- files and systems implemented;
- work-package completion matrix;
- tests run and results;
- unresolved limitations;
- migration or compatibility notes;
- instructions for starting Campaign 02;
- any Steward-local visual review still required.

## Completion Condition

Campaign 01 is complete only when WP-4108 through WP-4117 are implemented, tested, documented, and integrated into one coherent Visual Bible foundation without declaring unreviewed resident imagery canonical.
