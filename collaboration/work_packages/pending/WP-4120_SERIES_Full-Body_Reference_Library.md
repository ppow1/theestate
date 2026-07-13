# WP-4120 — Full-Body Reference Library

## Status
Pending

## Series
Visual Estate Initiative — Campaign 02: Canonical Portrait Library

## Objective
Create a standardized full-body reference library for every resident so stature, silhouette, posture, limb proportions, footwear, wardrobe behavior, and visual identity remain consistent across later generations.

## Dependencies
- WP-4108 Visual Bible Schema and Repository Structure
- WP-4109 Canonical Physical Specification Standard
- WP-4110 Facial Geometry and Visual Fingerprint
- WP-4111 Height, Proportion, and Scale Reference System
- WP-4113 Wardrobe and Signature Look Library
- WP-4114 Visual Prompt Engineering Canon
- WP-4115 Visual Negative Prompt Canon
- WP-4118 Hero Portrait Specification
- WP-4119 Professional Office Portrait Standard

## Scope
For each resident, define and produce a reviewable full-body reference set containing at minimum:

1. Neutral standing front view.
2. Relaxed standing front view.
3. Three-quarter standing view.
4. Full side profile.
5. Rear standing view.
6. Natural walking pose.
7. Seated full-body pose where role-appropriate.
8. One resident-signature full-body pose.
9. One scale-reference image with fixed environmental cues.
10. One standardized footwear variant.

## Standardization Requirements
- Preserve canonical height and resident-specific proportions.
- Use a controlled camera distance, focal length, eye level, and floor plane.
- Avoid perspective distortion that changes apparent height or limb length.
- Keep the entire figure visible, including footwear and crown of head.
- Use consistent lighting and neutral backgrounds for comparison references.
- Record footwear type and heel height in metadata.
- At least one applicable reference for adult female residents must use heels of 3 inches or greater so posture and leg-line effects can be evaluated.
- Wardrobe must reveal silhouette accurately without becoming explicit or clinically nude.
- Do not use one resident’s physical template as the default for another resident.

## Deliverables
- Per-resident full-body reference directory.
- Canonical and review-candidate image slots.
- Full-body prompt templates.
- Full-body negative prompt templates.
- Camera and lens metadata.
- Pose metadata.
- Wardrobe and footwear metadata.
- Scale-reference metadata.
- Steward review notes.
- Validation report covering height, proportion, posture, and identity consistency.

## Repository Targets
Use the Visual Bible structure established by WP-4108. Store documents and metadata under the resident’s governed visual-bible path, and keep review candidates separate from canonical assets.

## Acceptance Criteria
- Every active resident has the required reference categories represented or explicitly marked pending generation.
- Height and scale cues agree with the resident’s canonical specification.
- Full-body identity is recognizable without relying only on facial close-ups.
- Footwear and heel effects are documented rather than silently changing posture.
- No image crops feet, hair, or major body regions required for evaluation.
- Review assets cannot be mistaken for canon.
- Steward notes can approve, reject, or request revision for each reference.

## Non-Goals
- This package does not perform the three-variant 360-degree measurement comparison; that belongs to Campaign 03.
- This package does not lock final group-photo relative scaling.
- This package does not authorize unrestricted private-mode imagery.

## Completion Condition
The Estate has a governed, repeatable full-body reference standard and per-resident library structure capable of preserving stature, silhouette, posture, and visual identity across future image generation.