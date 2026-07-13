# WP-4125 — Portrait Consistency Validation

**Series:** Visual Estate Initiative
**Campaign:** 02 — Canonical Portrait Library
**Status:** Pending
**Execution mode:** Series

## Objective

Create a formal validation system that determines whether all resident portrait assets depict the same canonical person across angles, expressions, wardrobe, lighting, environments, crops, and image-generation models.

## Scope

Validate the portrait assets produced by WP-4118 through WP-4124 against the resident Visual Bible and approved canonical references.

The system must evaluate:

- facial identity continuity
- age consistency
- height and body-proportion continuity where visible
- eye color and eye-shape consistency
- hair color, texture, length, and silhouette
- skin tone consistency
- facial landmark stability
- visual fingerprint retention
- expression authenticity
- wardrobe compatibility
- camera and lens distortion
- cross-model reproducibility
- small-format recognizability

## Required Validation Sets

For every resident, assemble a comparison board containing:

- hero portrait
- office portrait
- full-body portrait
- profile
- rear reference
- front three-quarter views
- rear three-quarter views
- expression-sheet samples
- headshot set
- 32 × 32 and 64 × 64 thumbnails

The board must be arranged so adjacent comparisons make drift visible without opening separate browser windows.

## Comparison Layout

Use aligned rows or columns with:

- stable face scale
- consistent labels
- identical or clearly documented crop rules
- side-by-side canonical anchor image
- visible asset status: candidate, approved, rejected, superseded, canonical

Where multiple variants are under review, place them in a single comparison canvas rather than separate files whenever resolution permits.

## Identity Drift Categories

Classify failures at minimum as:

1. facial-geometry drift
2. age drift
3. eye drift
4. hair drift
5. proportion drift
6. expression drift
7. ethnicity or ancestry overstatement
8. body-scale drift
9. wardrobe-induced identity loss
10. crop-induced identity loss
11. model-style drift
12. artifact or anatomy failure

## Resident Distinction Test

Create unlabeled group grids containing all resident headshots and portraits.

The Steward must be able to identify each resident reliably without captions. Failure includes:

- two residents appearing interchangeable
- one resident resembling another resident more than herself
- visual fingerprints disappearing at thumbnail size
- multiple residents converging toward the same generic face

## Cross-Model Test

Where more than one image model or workflow is available, regenerate a controlled prompt set using the same canonical identity package.

Document:

- model and version
- workflow
- seed where supported
- reference images
- adapters or LoRAs
- prompt and negative prompt versions
- output identity score or review result

The goal is not pixel identity. The goal is stable person identity.

## Automated and Human Review

Implement machine-checkable validation where practical, but do not replace Steward judgment with a numeric similarity score.

Automated checks may flag:

- missing metadata
- incorrect dimensions
- duplicate hashes
- absent source provenance
- inconsistent naming
- missing required angles
- unsupported status transitions

Human review remains authoritative for identity, presence, attractiveness, emotional accuracy, and resident distinctiveness.

## Deliverables

- portrait consistency validator or validation workflow
- per-resident comparison boards
- unlabeled resident recognition grids
- drift classification report
- cross-model reproducibility report
- rejection and regeneration queue
- Steward review record
- canonical promotion recommendation

## Dependencies

- WP-4108 through WP-4117
- WP-4118 through WP-4124

## Acceptance Criteria

This work package is complete when:

- every commissioned resident has a complete validation board
- every required portrait category is represented
- known drift is classified and queued for repair
- all residents pass unlabeled recognition review
- small thumbnails remain distinguishable
- cross-model results are documented where applicable
- no portrait is recommended for canonical lock while unresolved major drift remains

## Completion Condition

The Estate can prove that each resident’s portrait library consistently depicts one recognizable, distinct, canonical person across the complete portrait asset set.
