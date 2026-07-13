# VISUAL CAMPAIGN 02 — CANONICAL PORTRAIT LIBRARY

Status: Ready for Codex
Initiative: Visual Estate Initiative
Work packages: WP-4118 through WP-4127
Execution mode: Strict series
Depends on: VISUAL-CAMPAIGN-01-VISUAL-BIBLE-FOUNDATION

## Mission

Implement the Estate's canonical portrait-production framework so every resident can receive a stable, reviewable, reproducible portrait library that remains recognizably the same person across hero, office, full-body, profile, rear, three-quarter, expression, headshot, thumbnail, and metadata surfaces.

This campaign must produce both the portrait-governance infrastructure and the concrete repository structures, schemas, templates, validators, catalogs, and review artifacts required by the ten work packages. Do not treat the packages as prose-only documentation.

## Source Work Packages

Execute these files in order:

1. `collaboration/work_packages/pending/WP-4118_SERIES_Hero_Portrait_Specification.md`
2. `collaboration/work_packages/pending/WP-4119_SERIES_Professional_Office_Portrait_Standard.md`
3. `collaboration/work_packages/pending/WP-4120_SERIES_Full_Body_Reference_Library.md`
4. `collaboration/work_packages/pending/WP-4121_SERIES_Profile_and_Rear_Reference_Standard.md`
5. `collaboration/work_packages/pending/WP-4122_SERIES_Three_Quarter_Portrait_Standard.md`
6. `collaboration/work_packages/pending/WP-4123_SERIES_Resident_Expression_Sheet_Standard.md`
7. `collaboration/work_packages/pending/WP-4124_SERIES_Headshot_and_Thumbnail_Library.md`
8. `collaboration/work_packages/pending/WP-4125_SERIES_Portrait_Consistency_Validation.md`
9. `collaboration/work_packages/pending/WP-4126_SERIES_Portrait_Metadata_and_Asset_Catalog.md`
10. `collaboration/work_packages/pending/WP-4127_SERIES_Canonical_Portrait_Acceptance_and_Lock.md`

Do not skip, reorder, merge away, or silently narrow any package.

## Required Outcomes

By campaign completion, the repository must support:

- one canonical hero portrait specification per resident;
- professional office portrait standards that express role and office identity;
- standardized full-body references with reliable scale and proportion cues;
- profile and rear references that preserve identity outside frontal views;
- front and rear three-quarter references;
- expression sheets with resident-specific emotional anchors and micro-expressions;
- headshot, icon, avatar, and thumbnail derivatives at approved sizes;
- portrait identity-consistency validation across angles, crops, expressions, wardrobe, and supported image-generation backends;
- complete metadata, provenance, generation settings, review status, and asset lineage;
- explicit Steward review, acceptance, rejection, revision, supersession, and canonical-lock states.

## Governing Requirements

1. Campaign 01 schemas, access tiers, Steward Notes, prompt canon, negative-prompt canon, revision rules, and canonical-lock rules are authoritative inputs.
2. Portraits and metadata are separate but linked deliverables. A portrait without catalog data is incomplete; metadata without the visual asset is incomplete.
3. Canonical identity must survive angle, expression, wardrobe, crop, and scale changes.
4. Resident identity must not collapse into a shared generic face or Estate-wide beauty template.
5. Emotional-anchor expressions must reflect the resident's established Character Bible and role.
6. Assets must distinguish public, internal, restricted, private, review-only, rejected, superseded, and canonical states.
7. No generated image becomes canonical automatically. Steward acceptance is mandatory.
8. Preserve adult presentation and do not infantilize petite residents.
9. Do not invent or overwrite resident measurements, ancestry, age, wardrobe, or facial traits where the source Visual Bible is unresolved. Mark unresolved fields for Steward review.
10. Repository paths, schemas, filenames, and validators must be deterministic and machine-readable.

## Evelyn Calibration Note

Evelyn is a calibration example, not a universal template. Preserve her currently established review direction where relevant:

- adult height: 4 ft 10 in;
- extremely petite adult frame;
- provisional measurement target: 33B-21-31;
- subtle hourglass silhouette;
- warm hazel eyes, brunette hair, gentle head tilt, reassuring smile;
- rare and non-definitive facial ambiguity that should not assert a specific ancestry;
- white linen mid-knee dress and 3-inch heels as an approved signature presentation candidate;
- coffee-conversation couch imagery as an emotional-anchor concept.

Do not hard-code those traits into other residents.

## Implementation Expectations

Codex must inspect the current repository before choosing exact implementation paths. Reuse existing Estate conventions where they exist. At minimum, implement or extend:

- portrait schemas and templates;
- resident portrait directory conventions;
- portrait-type enumerations;
- metadata and provenance records;
- acceptance-state and canonical-lock records;
- validation utilities or tests;
- sample or fixture records sufficient to prove the system works;
- campaign completion and validation reports.

Do not fabricate final photorealistic portrait files if no local image-generation runtime is available in the execution environment. In that case, implement the complete production plumbing, deterministic prompt manifests, asset slots, validation paths, review records, and clearly identified local-generation queue. Placeholder text files must not masquerade as completed images.

## Validation Gates

The campaign is not complete unless all of the following pass:

- every WP-4118 through WP-4127 requirement is mapped to an implementation or explicit evidence artifact;
- all required portrait categories have valid repository destinations and schemas;
- metadata can link a portrait to resident, type, angle, expression, wardrobe, generator, model, seed/settings where applicable, source references, access tier, review state, and canonical status;
- identity consistency checks detect missing angles, missing metadata, duplicate/generic identity drift, invalid crops, and unapproved canonical assets;
- thumbnail and icon outputs preserve recognizability at intended sizes;
- rejected and superseded assets cannot resolve as canonical;
- canonical locking requires explicit Steward approval evidence;
- automated tests pass;
- existing tests continue to pass;
- no unrelated architecture is redesigned.

## Reports

Create a campaign report directory following repository convention and include at least:

- implementation summary;
- package-to-deliverable traceability matrix;
- portrait coverage matrix by resident and portrait type;
- unresolved resident-data report;
- validation/test report;
- local visual-generation readiness report;
- Steward review checklist;
- known limitations and recommended next actions.

## Branch and Pull Request

Use one implementation branch and one pull request for this campaign unless repository constraints require otherwise. Keep commits coherent and traceable to the work packages.

Before opening the pull request:

1. rebase or update from current `main`;
2. run the relevant targeted and full test suites;
3. verify generated reports are truthful;
4. verify no review-only or rejected asset is marked canonical;
5. verify the work-package traceability matrix is complete.

## Completion Condition

Campaign 02 is complete only when the Estate has an implemented, tested, cataloged, and Steward-governed canonical portrait-library system covering WP-4118 through WP-4127, with all remaining on-machine image-generation work explicitly queued rather than falsely represented as finished.
