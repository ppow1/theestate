# WP-4111 — Height, Proportion, and Scale Reference System

## Series
Visual Estate Initiative — Campaign 01: Visual Bible Foundation

## Status
Pending

## Objective
Establish a canonical system for recording, generating, comparing, and validating resident height, body proportions, and scale across portraits, full-body references, 360-degree turnarounds, environmental scenes, and group photography.

## Problem
Image-generation systems routinely distort apparent height and proportions through camera angle, lens choice, cropping, footwear, pose, furniture scale, and inconsistent body geometry. A resident may appear correct in a headshot while becoming visibly too tall, too short, too broad, or otherwise inconsistent in full-body and group scenes.

## Scope
1. Define canonical height metadata in both imperial and metric units.
2. Define body-proportion descriptors and measurable landmarks, including shoulder line, torso length, waist placement, inseam, arm reach, head-to-body ratio, and stance profile.
3. Define repeatable camera, lens, distance, horizon, and framing standards for scale-sensitive imagery.
4. Define neutral-footwear and heeled-footwear comparison standards.
5. Require at least one full comparison set in footwear of 3 inches or greater where heels are compatible with the resident's wardrobe and mobility profile.
6. Define furniture, doorway, desk, chair, and multi-resident scale references.
7. Define posture and gait notes so height is not confused with slouching, hip tilt, or footwear-induced posture.
8. Define vertical alignment rules for stacked comparison sheets.
9. Define group-photo relative-height validation.
10. Define failure conditions and regeneration requirements.

## Canonical Data Requirements
Each resident Visual Bible must record:

- canonical height in feet/inches and centimeters
- apparent-height range under approved footwear
- footwear height used in each scale-sensitive asset
- head-to-body ratio target
- shoulder-to-waist and waist-to-floor proportion targets
- leg-length and torso-length descriptors
- posture baseline
- gait and stance notes
- approved scale-reference assets
- unresolved proportion questions
- Steward notes and approval state

## Required Reference Assets
Each resident must receive:

1. Neutral front full-body reference in flat or minimal-height footwear.
2. Neutral side full-body reference.
3. Neutral rear full-body reference.
4. Three-quarter front and rear references.
5. One standardized 3-inch-or-greater heel reference when applicable.
6. One seated reference with a standardized chair.
7. One desk or doorway scale reference.
8. One pair or group reference with at least one other canonically sized resident.
9. One annotated scale sheet showing camera and footwear conditions.

## Camera and Layout Standard
Scale-sensitive comparison assets must preserve:

- identical focal length
- identical camera height
- identical camera-to-subject distance
- identical horizon line
- identical crop and canvas dimensions
- identical pose family
- identical lighting
- identical wardrobe category unless wardrobe is the tested variable
- clearly labeled footwear height

Where multiple variants are compared, align them vertically so the same anatomical landmarks occupy the same image coordinates wherever practical.

## Group Photography Requirement
Group scenes must preserve the approved relative-height ordering among residents. No group image may become canonical if resident scale is inferred only from captions or if perspective makes the ordering ambiguous.

## Deliverables
- height and scale metadata schema
- scale-reference rendering specification
- camera and lens preset documentation
- footwear-height comparison protocol
- environmental scale-reference standard
- group-photo relative-height validation rules
- visual QA checklist
- machine-readable validation fields

## Dependencies
- WP-4108 — Visual Bible Schema and Repository Structure
- WP-4109 — Canonical Physical Specification Standard
- WP-4110 — Facial Geometry and Visual Fingerprint

## Acceptance Criteria
1. The system can record and distinguish true height, apparent height, and footwear-adjusted presentation.
2. A resident's height remains consistent across full-body, seated, environmental, and group images.
3. At least one applicable comparison set demonstrates 3-inch-or-greater heels without replacing the resident's canonical barefoot or flat-footwear height.
4. Vertical comparison sheets permit direct landmark-to-landmark review without opening separate browser windows.
5. Group images preserve relative scale among residents.
6. Every canonical scale-sensitive asset records camera and footwear conditions.
7. Failed scale or proportion checks produce a clear regeneration requirement rather than silent acceptance.

## Out of Scope
- final selection of every resident's measurements
- final wardrobe generation
- final group-photo production
- motion capture or skeletal rig implementation

## Completion Condition
WP-4111 is complete when the Estate has a reusable, auditable method for keeping every resident's height and proportions stable across individual and group visual assets.