# WP-4112 — Measurement Variant Review Workflow

## Series
Visual Estate Initiative — Campaign 01: Visual Bible Foundation

## Status
Pending

## Objective
Create a repeatable review workflow for comparing nearby body-measurement variants before a resident's canonical proportions are locked.

## Problem
Small changes in bust, waist, hip, shoulder, torso, or leg measurements may be difficult to judge when variants are generated separately, shown at different scales, or affected by changes in pose, clothing, camera, lighting, or footwear. The Steward must be able to compare subtle alternatives directly and determine which version best fits the resident's identity.

## Governing Principle
Measurement variants are review candidates, not alternate resident identities. The workflow exists to make small differences visible enough for a deliberate canonical choice.

## Scope
1. Define a three-variant comparison workflow for top, middle, and bottom measurements.
2. Allow flexibility by resident: some residents may require tightly bounded variants, while others may need wider exploratory ranges.
3. Require the baseline or most likely candidate to appear in the center position when practical.
4. Require identical generation conditions across variants.
5. Require vertically stacked or vertically aligned comparison layouts optimized for same-angle inspection.
6. Require one applicable comparison set in 3-inch-or-greater heels.
7. Define neutral, fitted, and silhouette-revealing wardrobe standards that remain non-explicit and suitable for proportion review.
8. Define labels, provenance, seed, model, prompt, negative prompt, camera, footwear, and revision metadata.
9. Define Steward review notes and canonical-selection records.
10. Define re-render and escalation rules when the intended difference is not visually legible.

## Three-Variant Standard
For each review cycle, define:

- Variant A — lower or narrower candidate
- Variant B — center or preferred candidate
- Variant C — higher or fuller candidate

The tested dimension may include:

- bust or chest
- waist
- hips
- shoulder width
- torso length
- leg length
- overall build
- another explicitly approved physical parameter

Only the selected variables may change within a comparison set. All other canonical traits must remain locked.

## Layout Standard
The preferred comparison artifact is a tall sheet containing three complete turnarounds stacked vertically:

1. Variant A turnaround
2. Variant B turnaround
3. Variant C turnaround

Each turnaround must use the same ordered angles:

- front
- front three-quarter
- side
- rear three-quarter
- rear

A secondary matrix may place identical angles in aligned columns, but the primary artifact must support quick vertical comparison without requiring multiple browser windows.

## Rendering Controls
All variants in a set must preserve:

- resident identity and facial fingerprint
- age presentation
- hairstyle
- expression
- pose
- camera distance and height
- focal length
- lighting
- background
- wardrobe cut and material
- footwear and heel height
- image dimensions
- generation model and major settings

## Heel Requirement
Where compatible with the resident's design, at least one comparison cycle must use heels of 3 inches or greater. The review must distinguish footwear-induced posture from actual body-measurement differences.

## Legibility Rule
If the Steward cannot reasonably identify the intended difference while viewing the comparison sheet at normal review size, the set fails. The implementation must then improve layout, clothing, annotation, resolution, or measurement spread before asking for a canonical decision.

## Review Record
Each decision record must include:

- resident ID
- comparison-set ID
- exact measurements for A, B, and C
- tested variable or variables
- generation provenance
- chosen candidate
- rejected candidates
- Steward notes
- rationale for selection
- confidence level
- unresolved concerns
- approval timestamp
- superseded comparison links

## Evelyn Calibration Example
Evelyn is a tightly constrained example rather than a universal template.

Current provisional calibration:

- height: 4 feet 10 inches / 147 cm
- build: extremely petite adult
- likely canonical measurements: 33B–21–31
- silhouette: subtle hourglass
- comparison candidates may remain narrowly spaced because larger bust or hip changes would conflict with the established design intent

Other residents may use broader ranges where their character design allows more flexibility.

## Deliverables
- measurement-comparison schema
- three-variant generation template
- vertically stacked 360-degree sheet specification
- same-angle alignment specification
- heeled-comparison protocol
- review decision record
- legibility failure and regeneration workflow
- Evelyn calibration example
- automated completeness checks

## Dependencies
- WP-4108 — Visual Bible Schema and Repository Structure
- WP-4109 — Canonical Physical Specification Standard
- WP-4111 — Height, Proportion, and Scale Reference System

## Acceptance Criteria
1. The system supports three clearly labeled nearby measurement variants.
2. Variants differ only in approved tested dimensions.
3. Full turnaround sets are presented in a directly comparable vertical layout.
4. At least one applicable set uses 3-inch-or-greater heels.
5. Provenance and exact measurements are preserved.
6. The Steward can record a selection and rationale without overwriting rejected evidence.
7. A visually indistinguishable comparison is marked failed and regenerated.
8. Resident-specific flexibility is supported; Evelyn's narrow specification does not become a universal body template.
9. The chosen measurements can be promoted into the canonical Visual Bible only after explicit Steward approval.

## Out of Scope
- deciding every resident's final measurements
- generating final canonical image libraries
- explicit imagery
- changing identity traits unrelated to the tested measurements

## Completion Condition
WP-4112 is complete when the Steward can compare subtle measurement alternatives in one aligned review artifact, select a canonical result with confidence, and preserve the complete decision history.