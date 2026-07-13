# WP-4127 — Canonical Portrait Acceptance and Lock

## Status
Pending

## Series
Visual Estate Initiative — Campaign 02: Canonical Portrait Library

## Objective
Define and implement the final acceptance, Steward approval, and canonical-lock process for each resident's portrait library.

## Scope
This work package closes Campaign 02 by converting reviewed portrait assets into an authoritative canonical set without losing rejected alternatives, review history, provenance, or the ability to revise later through governed change.

## Required Canonical Slots
Each resident must have approved coverage for:

- hero portrait
- professional office portrait
- full-body standing reference
- profile reference
- rear reference
- front three-quarter reference
- rear three-quarter reference
- expression sheet
- headshot set
- thumbnail set

Additional resident-specific canonical slots may be approved where justified.

## Acceptance Gates
Before lock, verify:

1. Identity recognition remains stable across all required angles.
2. Height and proportions match the approved Visual Bible.
3. Facial geometry and visual fingerprint remain consistent.
4. Wardrobe, posture, expression, and environment fit the resident's role and identity.
5. Small-format thumbnails remain recognizable.
6. No required image contains unresolved generation artifacts.
7. Prompt, negative prompt, model, seed, provenance, and revision metadata are recorded where available.
8. Access classification is correct.
9. The portrait set passes cross-image consistency review.
10. The Steward has explicitly approved the set or recorded required exceptions.

## Steward Review Package
Produce a resident-level review package containing:

- all proposed canonical images
- clearly labeled comparison alternatives
- a concise difference summary
- unresolved questions
- Steward Notes
- acceptance checklist
- proposed canonical identifiers
- rejected and superseded identifiers

The review package must not require the Steward to open multiple unrelated windows to compare subtle differences when a consolidated comparison sheet is practical.

## Canonical Lock
The lock mechanism must:

- mark one approved asset per required canonical slot
- record the approving authority and timestamp
- record the governing Visual Bible revision
- preserve the exact asset checksum
- preserve the prompt and provenance references
- prevent silent replacement
- require a new revision and explicit review to supersede a locked asset
- preserve prior canonical versions for history and rollback

## Change Control
A future visual revision must:

1. create a new candidate revision
2. preserve the current canonical set during review
3. state what changed and why
4. pass the applicable consistency tests
5. receive Steward approval
6. update supersession links
7. leave an auditable history

## Campaign-Level Acceptance
Campaign 02 is complete only when:

- the portrait standards and asset structures exist
- all required catalog and validation mechanisms exist
- a complete example resident workflow is demonstrated
- automated validation passes
- documentation explains generation, review, rejection, approval, locking, supersession, and rollback
- no unapproved image is represented as canonical

## Deliverables

- canonical portrait acceptance checklist
- resident review-package template
- canonical-lock record schema
- supersession and rollback procedure
- campaign completion report template
- automated validation for required slots and lock integrity
- example acceptance and lock records

## Acceptance Criteria

- Canonical status is explicit, unique, auditable, and reversible through governed revision.
- Steward approval is recorded rather than inferred.
- Rejected and superseded images remain available for review history but cannot masquerade as current canon.
- Every required portrait slot has a validated completion state.
- Later campaigns can safely consume the locked portrait set as authoritative input.
- Campaign 02 can be closed without claiming that ungenerated or unreviewed resident imagery already exists.

## Dependencies

- WP-4108 through WP-4117
- WP-4118 through WP-4126

## Out of Scope

- 360-degree measurement comparison acceptance, which belongs to Campaign 03
- lifestyle and environment library acceptance
- group-photo recognition testing
- motion and video identity locks
