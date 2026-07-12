# WP-4077 — Visual Continuity Runtime

Status: Pending
Execution Mode: SERIES
Owner: Office of Character Architecture / Visual Runtime Integration
Execution Target: Codex
Classification: Estate Internal
Priority: Immediate

## Depends On

- WP-4073 — Resident Visual Identity Framework
- WP-4074 — Estate Wardrobe Runtime
- WP-4075 — Canonical Estate Location Library
- WP-4076 — Character Presentation and Pose Framework
- WP-4063 through WP-4067 — Resident Memory Architecture

## Objective

Implement one governed visual-continuity runtime that composes resident identity, wardrobe, location, presentation, time, relationship scope, and verified scene history into reproducible visual requests and inspectable output records.

## Required Work

1. Define typed visual-scene request, generation receipt, continuity state, reference set, and validation result contracts.
2. Compose canonical resident identity, current wardrobe, approved location, pose/presentation, date/time, event, participants, relationship context, and privacy scope into provider-neutral scene specifications.
3. Preserve continuity of appearance, outfit, location, props, injuries where authorized, environmental changes, and participant relationships across related scenes.
4. Record provider/model, seed where available, prompt fragments, references, generation time, source hashes, output path, classification, and review status.
5. Distinguish canonical facts from artistic interpretation, inferred staging, and generated details.
6. Detect identity drift, wardrobe discontinuity, impossible location changes, participant mismatch, timeline conflicts, duplicated residents, and privacy leakage.
7. Support bounded regeneration, correction, comparison, and approval without overwriting prior outputs or treating generated imagery as canonical truth.
8. Integrate with existing repository artifact, generated-artifact, privacy, and validation policies.
9. Produce visual-history hooks for later gallery and timeline packages without implementing those institutions here.

## Acceptance Tests

1. A multi-image sequence preserves resident identity, wardrobe, location, participants, and time-sensitive details.
2. Provider or model changes do not silently replace a resident's appearance.
3. Generated details absent from canonical sources remain labeled artistic or inferred.
4. Private relationship context and restricted locations do not leak into shared scenes.
5. Drift and timeline conflicts block approval or produce explicit diagnostics.
6. Corrections create lineage-linked revisions rather than deleting history.
7. A scene can be independently reconstructed from its receipt and source references within provider limits.
8. Visual outputs do not alter canonical identity, wardrobe, location, relationship, or memory state by themselves.

## Deliverables

- visual scene, continuity, receipt, and validation schemas;
- provider-neutral scene composer;
- reference and source-hash manager;
- continuity checker and drift diagnostics;
- revision and comparison workflow;
- tests, documentation, and completion receipt.

## Constraints

- Do not create a second identity, wardrobe, location, memory, relationship, privacy, or validation authority.
- Do not promote generated imagery into canonical truth without governed review.
- Do not erase failed or superseded generations needed for audit.
- Do not expose restricted references or scene content.

## Completion Standard

WP-4077 is complete only when the Estate can generate and revise source-lined visual scenes whose residents, clothing, locations, presentation, timeline, and privacy scope remain coherent across outputs and providers; drift and inference remain explicit; and generated art stays a governed derivative rather than a new source of institutional truth.