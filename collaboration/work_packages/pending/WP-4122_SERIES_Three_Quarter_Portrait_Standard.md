# WP-4122 — Three-Quarter Portrait Standard

## Status
Runtime implementation complete; visual generation and Steward acceptance pending

## Series
Visual Estate Initiative — Campaign 02: Canonical Portrait Library

## Objective
Define the canonical three-quarter portrait angles and capture rules required to keep every resident recognizable from the front-left, front-right, rear-left, and rear-right oblique views most commonly used in portraits and environmental scenes.

## Scope
This package establishes:

- canonical 45-degree front-left and front-right portrait references;
- canonical 45-degree rear-left and rear-right portrait references;
- fixed camera height, camera distance, focal length, crop, and lighting guidance;
- neutral technical pose and resident-specific conversational pose;
- facial, hair, shoulder, torso, posture, and silhouette consistency checks;
- resident visual-fingerprint verification from oblique angles;
- artifact and asymmetry review;
- prompt and negative-prompt fragments for reproducible three-quarter generation;
- metadata, provenance, version, and Steward-review requirements.

## Requirements

### 1. Required views
Each resident must receive at minimum:

1. front-left three-quarter;
2. front-right three-quarter;
3. rear-left three-quarter;
4. rear-right three-quarter.

### 2. Standardized capture conditions
The four views must use the same:

- resident identity source;
- wardrobe set;
- hairstyle;
- lighting rig;
- camera height;
- camera distance;
- focal length or equivalent field of view;
- background;
- image dimensions;
- color treatment;
- neutral body stance unless a deliberately documented alternate stance is being reviewed.

### 3. Natural resident posture
A second resident-specific conversational set may be generated after the technical set. This set may include:

- Evelyn’s slight listening head tilt;
- Grace’s crisp operational posture;
- Helen’s warm but professional stance;
- Alfred’s measured, formal presence;
- other resident-specific posture cues approved in the Visual Bible.

Natural posture must not alter canonical height, proportions, or identity.

### 4. Recognition standard
The resident must remain recognizable when:

- only one eye is fully visible;
- the face is viewed obliquely;
- hairstyle overlaps part of the face;
- the body is rotated away from camera;
- clothing changes within approved wardrobe ranges.

### 5. Rear three-quarter standard
Rear views must preserve:

- hair length, texture, volume, and part;
- shoulder width and posture;
- torso and hip proportions;
- garment fit and hem behavior;
- footwear and heel height;
- resident-specific scale cues.

Rear views are reference assets, not glamour substitutions, and must remain useful for later group scenes, animation, and 360-degree review.

### 6. Quality controls
Reject and regenerate images containing:

- facial drift between left and right views;
- inconsistent eye spacing, nose, jaw, or ear placement;
- changing hairline, hair length, or hair color;
- altered body measurements;
- implausible spine, shoulder, neck, arm, hand, or hip geometry;
- asymmetry not present in the canonical identity;
- camera-angle changes that defeat direct comparison;
- over-stylization that obscures identity.

### 7. Deliverables
For each resident:

- four canonical technical three-quarter portraits;
- optional four-image conversational three-quarter set;
- prompt fragments;
- negative-prompt fragments;
- metadata record;
- QA checklist;
- Steward notes and decision state.

### 8. Repository placement
Store assets and metadata under the Visual Bible and asset-library structure defined by WP-4108. Review candidates must remain separate from canonical locked assets.

## Dependencies

- WP-4108 — Visual Bible Schema and Repository Structure
- WP-4109 — Canonical Physical Specification Standard
- WP-4110 — Facial Geometry and Visual Fingerprint
- WP-4111 — Height, Proportion, and Scale Reference System
- WP-4113 — Wardrobe and Signature Look Library
- WP-4114 — Visual Prompt Engineering Canon
- WP-4115 — Visual Negative Prompt Canon
- WP-4116 — Steward Visual Review and Revision Workflow
- WP-4120 — Full-Body Reference Library
- WP-4121 — Profile and Rear Reference Standard

## Acceptance Criteria

- All four required angles are defined and reproducible.
- Camera and lighting controls permit direct left/right comparison.
- Residents remain recognizable from front and rear oblique views.
- Resident-specific posture is allowed only as a documented secondary set.
- Proportions, height, face, hair, and wardrobe remain consistent.
- Review, rejection, revision, and canonical-lock states are recorded.
- No asset becomes canonical without Steward approval.

## Completion Condition
The Estate possesses a repeatable three-quarter portrait standard that preserves each resident’s identity from the oblique angles most frequently used in portraits, environmental scenes, group photography, and later motion work.
