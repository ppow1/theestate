# WP-4116 — Steward Visual Review and Revision Workflow

## Status
Pending

## Series
Visual Estate Initiative — Campaign 01: Visual Bible Foundation

## Objective
Create the authoritative Steward review workflow for evaluating, comparing, revising, approving, rejecting, and canonizing resident visual assets and Visual Bible decisions.

## Problem
Visual refinement currently depends on scattered conversational observations and side-by-side browser comparisons. Important decisions such as height, proportions, facial cues, emotional presence, wardrobe, and signature looks can be lost or inconsistently applied. The Estate needs a durable review process that preserves the Steward’s exact judgments and converts them into canonical specifications and regeneration instructions.

## Scope
Implement a review system covering:

1. Review queues for draft assets.
2. Side-by-side and vertically stacked comparison sheets.
3. Three-variant measurement review where appropriate.
4. 360-degree review.
5. Facial identity and visual-fingerprint review.
6. Wardrobe and signature-look review.
7. Emotional-anchor image review.
8. Icon and thumbnail review.
9. Pair and group-photo review.
10. Approval, provisional approval, revision, rejection, and canonical lock states.

## Review Principles
- The Steward is the final visual acceptance authority.
- Generated assets remain noncanonical until explicitly accepted.
- A visual may be emotionally correct but technically imperfect; both dimensions must be recorded separately.
- Review notes must preserve exact intent, not reduce feedback to generic labels.
- Only the intended variable should change during controlled comparisons.
- Resident-specific flexibility is allowed; Evelyn’s narrow calibration is not a universal template.

## Required Review States
Each reviewed asset or comparison set must support:

- `draft`
- `pending_steward_review`
- `revision_requested`
- `provisionally_approved`
- `canonical`
- `rejected`
- `superseded`

State changes must include date, reviewer, reason, source asset identifiers, and any replacement relationship.

## Steward Notes
Every resident Visual Bible must include a Steward Notes ledger capable of recording observations such as:

- preserve this exact eye warmth
- retain the slight head tilt
- reduce hips by one inch
- age presence slightly without losing approachability
- this outfit is a signature look
- this image captures the resident emotionally even if it is not technically perfect
- the resident is too tall relative to the furniture or group
- the difference between variants is too subtle to evaluate

Notes must be linkable to specific images, variants, angles, prompts, and revisions.

## Controlled Comparison Standard
The review interface or generated review package must support:

- vertically stacked variant rows
- aligned front, 45-degree, side, rear-45, and rear views
- identical crop, pose, camera, lighting, wardrobe, expression, and background
- clear labels outside the image area
- at least one applicable 3-inch-or-higher heel set
- zoomable original-resolution assets
- a difference summary naming only the intended variables

The workflow must not require the Steward to open multiple unrelated browser windows to identify a small difference.

## Emotional Anchor Review
The workflow must distinguish technical references from emotional-anchor images. An emotional anchor may be approved because it captures the resident’s presence, such as Evelyn leaning forward with a coffee cup in a conversational posture, even if another image is used as the technical facial or body reference.

Each resident must support:

- technical anchor
- facial anchor
- body/proportion anchor
- signature-look anchor
- emotional-presence anchors

## Group Review
Pair and group images must be reviewed for:

- immediate resident recognizability
- relative height and scale
- face and body separation
- posture and expression distinctiveness
- interpersonal spacing and chemistry
- role-appropriate behavior
- wardrobe differentiation
- absence of identity blending

The final group-photo test must allow captions to be hidden so the Steward can verify recognition without labels.

## Revision Packets
A revision request must produce a structured packet containing:

- source asset IDs
- approved elements to preserve
- defects to correct
- exact requested changes
- unchanged variables
- applicable positive prompt fragments
- applicable negative prompt fragments
- comparison layout requirements
- acceptance test for the next pass

## Deliverables
- Review-state schema.
- Steward Notes ledger schema.
- Comparison review manifest.
- Revision-packet format.
- Canonical approval record.
- Supersession and rollback mechanism.
- Sample review records using Evelyn’s visual refinement as a nonbinding example.
- Validation checks for provenance and required metadata.

## Dependencies
- WP-4108 through WP-4115

## Acceptance Criteria
1. Every generated asset has a clear lifecycle and review state.
2. The Steward can compare variants without reconstructing context manually.
3. Exact visual feedback is preserved and attached to the relevant assets.
4. Controlled comparisons identify intended and fixed variables.
5. Emotional-anchor images can be approved independently of technical references.
6. Revision requests are directly actionable by a human artist or generation workflow.
7. Canonical locks are explicit, versioned, reversible, and auditable.
8. Group-photo recognition can be tested with labels hidden.

## Completion Condition
The Estate has a durable Steward-centered workflow that turns visual judgment into precise revisions, canonical specifications, and traceable asset decisions.
