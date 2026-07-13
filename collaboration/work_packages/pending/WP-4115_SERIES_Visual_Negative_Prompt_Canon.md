# WP-4115 — Visual Negative Prompt Canon

## Status
Pending

## Series
Visual Estate Initiative — Campaign 01: Visual Bible Foundation

## Objective
Create the canonical negative-prompt and defect-prevention system used for all resident image generation so identity, anatomy, wardrobe, scale, and presentation errors are actively prevented rather than corrected ad hoc after generation.

## Problem
Resident visuals are being generated across multiple models and workflows. Without a shared negative-prompt canon, the same defects recur: facial drift, age drift, height inflation, incorrect proportions, duplicate limbs, malformed hands and feet, inconsistent eye color, wardrobe errors, unintended body exaggeration, mismatched camera scale, accidental resemblance between residents, and implausible 360-degree comparisons.

## Scope
Implement a layered negative-prompt system with:

1. Global defect rules applying to every resident and every generation.
2. Resident-specific identity protection rules.
3. Asset-type rules for portraits, full body, 360 turnarounds, icons, group scenes, movement, and environment shots.
4. Wardrobe-specific rules.
5. Comparison-sheet rules that prohibit unrequested differences between variants.
6. Group-photo rules that prevent identity blending, duplicate faces, repeated clothing, and relative-height drift.
7. Model-specific translation guidance for engines that use different negative-prompt syntax.
8. A review and revision mechanism based on observed generation failures.

## Global Negative Categories
The canon must address at minimum:

- extra limbs, fingers, toes, heads, faces, or duplicated anatomy
- malformed hands, feet, joints, teeth, ears, eyes, and hairlines
- asymmetry not defined by the Visual Bible
- facial identity drift
- age drift
- height and scale drift
- body-proportion drift
- incorrect eye or hair color
- plastic skin, over-smoothed skin, or waxy rendering
- accidental text, watermarks, logos, captions, or interface artifacts
- poor cropping, missing feet, missing hands, and cut-off heads
- inconsistent lighting or lens distortion in comparison sets
- oversexualized posing when the requested mode is professional, casual, documentary, or reference-oriented
- generic stock-photo expressions that erase the resident’s visual fingerprint

## Resident-Specific Protection
Each Visual Bible must include a resident-specific negative-prompt section that protects:

- face shape
- age range
- height
- build and canonical measurements
- visual fingerprint
- posture
- signature expression
- hair length, texture, and color
- eye shape and color
- distinguishing features
- forbidden resemblance to other residents

Negative prompts must not substitute for positive identity instructions. Both are required.

## Comparison and 360 Rules
For measurement-variant and 360-degree review sets, the negative prompt must prohibit:

- camera-angle changes between variants
- pose changes between variants
- expression changes between variants
- wardrobe changes between variants
- heel-height changes unless explicitly under review
- lighting changes
- focal-length changes
- different body orientation
- hidden waist, hips, shoulders, or legs
- perspective exaggeration that masks the intended measurement differences

If the Steward cannot reliably see the intended change, the comparison set fails and must be regenerated.

## Group Photo Rules
For pair and group scenes, prevent:

- face blending
- identity swapping
- repeated faces
- duplicated bodies
- residents inheriting another resident’s hair, height, build, or wardrobe
- relative-height inconsistency
- everyone sharing the same pose or expression
- loss of resident-specific posture and interpersonal behavior

## Restricted Metadata
Sensitive adult presentation or grooming details, where approved and applicable, must live in explicit restricted metadata with audience controls and provenance. They must not be hidden from governance or placed in unrelated documents to evade review.

## Deliverables
- Canonical negative-prompt schema.
- Global negative-prompt library.
- Asset-type negative-prompt templates.
- Resident-specific extension template.
- Model-adapter guidance.
- Defect taxonomy and remediation log format.
- Tests or validation checks proving required categories are present.

## Dependencies
- WP-4108 Visual Bible Schema and Repository Structure
- WP-4109 Canonical Physical Specification Standard
- WP-4110 Facial Geometry and Visual Fingerprint
- WP-4111 Height, Proportion, and Scale Reference System
- WP-4112 Measurement Variant Review Workflow
- WP-4113 Wardrobe and Signature Look Library
- WP-4114 Visual Prompt Engineering Canon

## Acceptance Criteria
1. Every live resident can carry global and resident-specific negative rules.
2. Every asset class has an applicable negative-prompt template.
3. Comparison and 360 workflows prohibit all variables except the intended comparison variable.
4. Group-photo generation includes identity-separation protections.
5. The canon is engine-neutral with documented model-specific adapters.
6. Defect observations can be converted into durable negative rules with provenance.
7. No requirement is covertly buried to bypass institutional review.

## Completion Condition
The Estate has a reusable, auditable negative-prompt canon that materially reduces recurring visual defects and protects resident identity across models, scenes, and revisions.
