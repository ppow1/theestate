# WP-4117 — Visual Bible Acceptance and Canonical Lock

## Classification

- Series: Visual Estate Initiative
- Campaign: 01 — Visual Bible Foundation
- Status: Pending
- Execution mode: Series
- Depends on: WP-4108 through WP-4116

## Objective

Define the formal acceptance process that moves a resident visual identity from draft and review state into canonical Estate use.

The process must prove that the resident is recognizable, internally consistent, correctly proportioned, reproducible, appropriately governed, and ready for downstream portrait, turnaround, wardrobe, lifestyle, iconography, interaction, and group-photo production.

## Scope

Implement a canonical-lock framework for each resident Visual Bible and associated reference assets.

The framework must distinguish:

- exploratory draft
- review candidate
- preferred candidate
- provisionally accepted
- canonically locked
- superseded
- rejected

No image or measurement set becomes canonical merely because it is attractive or because it was used once.

## Required Acceptance Evidence

A resident may be canonically locked only when the following evidence exists.

### 1. Identity Recognition

- Hero, headshot, profile, full-body, and turnaround references remain recognizably the same adult resident.
- The resident remains identifiable when captions and names are hidden.
- Recognition depends on stable facial and behavioral visual cues, not only wardrobe.

### 2. Physical Consistency

- Height, frame, measurements, proportions, posture, and scale cues agree with the accepted physical specification.
- Measurement comparison sheets show the selected option clearly enough for Steward review.
- Footwear effects are documented separately from body measurements.
- At least one applicable full-body reference uses 3-inch-or-higher heels without altering canonical anatomy.

### 3. Facial Consistency

- Eye shape and color, facial geometry, hair, age presentation, expression range, and visual fingerprint remain stable across approved images.
- Subtle artistic notes remain subtle and do not become exaggerated demographic or ethnic claims.
- The resident does not drift into a generic stock-model face.

### 4. Wardrobe Consistency

- Signature look, office attire, casual attire, formal attire, activity clothing, and seasonal variants follow the resident wardrobe specification.
- Clothing may modify presentation but must not silently change canonical physique.
- Review assets and restricted wardrobe categories remain correctly classified.

### 5. Prompt Reproducibility

- Approved prompts and negative prompts can regenerate recognizable results across at least two supported workflows or model families when available.
- Generator, model, checkpoint, seed, LoRA, reference image, control settings, and relevant metadata are recorded.
- Known failure modes are documented.

### 6. Asset Completeness

At minimum, the locked foundation must reference or reserve locations for:

- hero portrait
- canonical headshot
- profile reference
- full-body reference
- front, three-quarter, side, rear three-quarter, and rear turnaround views
- measurement comparison sheet when required
- expression references
- black-and-white reference
- thumbnail and icon derivatives
- prompt and negative-prompt records
- Steward Notes
- revision history

Later campaigns may produce the final assets, but the Visual Bible must define their requirements and canonical dependencies.

### 7. Group Compatibility Readiness

Before final initiative completion, the resident must be capable of appearing beside other residents without losing identity.

The acceptance framework must reserve later tests for:

- relative height accuracy
- distinct face and silhouette
- posture and interpersonal spacing
- wardrobe differentiation
- pair recognition
- small-group recognition
- all-resident hidden-caption recognition

Group photographs are the final cross-resident identity test, not decorative extras.

## Steward Authority

Canonical lock requires explicit Steward approval.

The Steward may:

- approve one candidate
- request a narrow revision
- reopen measurements
- reopen facial details
- reopen wardrobe details
- reject an entire generation set
- designate emotional-anchor images
- select a signature look
- delay lock pending group comparison

Automated scoring, office review, or Codex validation may recommend but may not replace Steward acceptance.

## Canonical Lock Record

Create a machine-readable and human-readable lock record containing:

- resident ID
- canonical version
- approval date
- approving authority
- accepted physical specification hash
- accepted facial specification hash
- accepted wardrobe specification hash
- approved asset manifest
- approved prompt manifest
- negative-prompt manifest
- Steward decision notes
- unresolved tolerated limitations
- superseded version references

## Change Control

After canonical lock:

- later changes require a new version
- previous canonical assets remain traceable
- silent replacement is prohibited
- experimental generations remain outside canonical directories
- downstream assets record which canonical version they used
- major changes trigger revalidation of portraits, turnarounds, icons, and group compatibility

## Evelyn Calibration Example

Evelyn may be used as an initial calibration case, with current provisional direction including:

- adult resident
- height of 4 feet 10 inches
- extremely petite frame
- provisional 33B–21–31 measurements
- subtle hourglass silhouette
- warm hazel eyes
- soft brunette hair
- slight relational head tilt
- white linen mid-knee dress and 3-inch heels as a preferred signature presentation candidate
- extremely subtle facial ambiguity that only rarely prompts an uncertain observer reaction and never establishes a demographic claim

These values remain subject to formal Steward acceptance and must not become universal resident defaults.

## Governance and Privacy

- Restricted or private visual metadata must be labeled honestly and access-controlled.
- Requirements may not be hidden to evade HR, governance, or repository review.
- Adult-only presentation layers must remain explicitly adult, audience-scoped, and separate from general operational surfaces.
- Evelyn private-mode visual hooks may be referenced, but activation requires its own governed persona and access pathway.

## Deliverables

1. Canonical-lock status model.
2. Human review checklist.
3. Machine-readable lock-record schema.
4. Asset-manifest validation rules.
5. Prompt reproducibility checklist.
6. Supersession and rollback rules.
7. Hidden-caption identity-recognition test plan.
8. Group-compatibility readiness gate.
9. Initial Evelyn calibration example.
10. Campaign 01 completion report.

## Acceptance Criteria

This work package is complete when:

- every resident Visual Bible can move through a defined review lifecycle
- canonical status requires explicit Steward approval
- accepted measurements and imagery are versioned and traceable
- group-photo recognition is preserved as the final initiative-level test
- downstream campaigns can determine which assets are authoritative
- rejected and superseded assets cannot be mistaken for canon
- private and restricted layers remain transparent and governed
- the Campaign 01 foundation is ready for Codex implementation as one coherent campaign

## Non-Goals

This package does not:

- generate the final resident image libraries
- declare any resident visually canonical without Steward review
- replace artistic judgment with automated scoring
- activate Evelyn private mode
- authorize covert or ungoverned visual repositories

## Completion Condition

Campaign 01 is complete when WP-4108 through WP-4117 collectively define a usable, governed, reproducible Visual Bible foundation and a clear path from exploratory imagery to Steward-approved canon.
