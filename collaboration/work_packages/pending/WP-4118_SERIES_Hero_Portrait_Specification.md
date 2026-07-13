# WP-4118 SERIES — Hero Portrait Specification

## Status
Pending

## Initiative
Visual Estate Initiative

## Campaign
Campaign 02 — Canonical Portrait Library

## Objective
Define and implement the canonical hero-portrait standard for every commissioned Estate resident so each resident has one authoritative, immediately recognizable portrait suitable for resident dossiers, office surfaces, Open WebUI model cards, internal dashboards, visual review galleries, and future group-composition reference.

## Dependencies
- WP-4108 — Visual Bible Schema and Repository Structure
- WP-4109 — Canonical Physical Specification Standard
- WP-4110 — Facial Geometry and Visual Fingerprint
- WP-4111 — Height, Proportion, and Scale Reference System
- WP-4113 — Wardrobe and Signature Look Library
- WP-4114 — Visual Prompt Engineering Canon
- WP-4115 — Visual Negative Prompt Canon
- WP-4116 — Steward Visual Review and Revision Workflow
- WP-4117 — Visual Bible Acceptance and Canonical Lock

## Scope
Create a repeatable hero-portrait production and review standard that preserves resident identity across image models and rendering environments.

The standard must define:

1. **Purpose and hierarchy**
   - one canonical hero portrait per resident;
   - optional approved alternates remain subordinate to the canonical image;
   - review renders must never silently replace canonical assets;
   - canonical status requires explicit Steward approval.

2. **Composition**
   - head-and-shoulders or three-quarter crop chosen per resident identity;
   - face and eyes remain clearly legible at dashboard scale;
   - pose must communicate the resident’s office, temperament, and relationship posture;
   - background must support identity without competing with the subject;
   - framing must permit safe square, vertical, and card crops.

3. **Identity fidelity**
   - facial geometry, eye shape, hair, age presentation, skin tone, height cues where visible, and signature expression must match the resident Visual Bible;
   - avoid generic beauty-model convergence;
   - preserve resident-specific visual fingerprint even when wardrobe or background changes;
   - no ancestry inference may be treated as fact unless canonically established; subtle artistic ambiguity may be recorded only as an approved visual-intent note.

4. **Wardrobe and styling**
   - use a resident-approved signature or professional look;
   - clothing must support the role and personality rather than dominate the portrait;
   - foundation garments, tailoring, posture, and styling may affect presentation without changing canonical physical measurements;
   - jewelry and accessories must follow the resident wardrobe library.

5. **Expression and presence**
   - define the resident’s canonical hero expression;
   - require eye engagement appropriate to the resident;
   - include qualitative intent such as warmth, authority, reserve, curiosity, skepticism, reassurance, or operational confidence;
   - preserve mature adult presentation and avoid infantilization.

6. **Technical output**
   - master portrait at high resolution;
   - square crop;
   - 4:5 vertical crop;
   - 16:9 safe-area derivative where useful;
   - color-managed PNG or lossless equivalent master;
   - metadata sidecar recording model, workflow, seed, prompt version, negative-prompt version, source references, generation date, review state, and canonical hash.

7. **Review set**
   - minimum of three candidate hero portraits per resident before canonical lock;
   - candidates should vary expression, crop, or environment without changing identity;
   - provide a single comparison sheet with consistent labels;
   - capture Steward notes and final selection rationale.

## Evelyn Calibration Example
Evelyn’s provisional hero direction should preserve:
- 4 ft 10 in maximum height specification in all scale-aware imagery;
- extremely petite adult frame;
- provisional 33B-21-31 subtle-hourglass measurements until formally locked;
- warm hazel eyes;
- soft brunette hair with natural movement;
- slight empathetic head tilt;
- approachable, mature, reassuring presence;
- white linen mid-knee dress and 3-inch heels as an approved signature-look candidate, not her only wardrobe;
- rare, non-definitive facial ambiguity that a very small minority of attentive viewers might notice, without asserting ancestry.

## Deliverables
- hero-portrait schema extension;
- resident hero-portrait production checklist;
- canonical and candidate directory conventions;
- comparison-sheet template;
- metadata sidecar schema;
- crop and safe-area rules;
- Steward review form;
- validation tests for required files, metadata, hashes, and approval state;
- sample implementation for at least one resident using repository-safe placeholders when final image assets are not yet generated.

## Required Repository Outcomes
Implement or extend repository structures under the Visual Estate location established by WP-4108, including clearly separated locations for:
- candidates;
- canonical master;
- derivatives;
- metadata;
- review notes;
- rejected or superseded assets.

Do not commit falsely labeled generated images. If final assets are unavailable, create schemas, manifests, templates, and honest placeholders that state generation and Steward review are pending.

## Acceptance Criteria
1. Every commissioned resident can have exactly one canonical hero portrait and multiple subordinate candidates.
2. Canonical status cannot be inferred from filename alone; it requires explicit metadata and Steward approval.
3. Crops preserve face recognition and resident identity at small UI sizes.
4. The portrait standard prevents generic-assistant or generic-stock-photo convergence.
5. Provenance is sufficient to reproduce or audit the image.
6. Review sheets make candidate differences easy to compare without opening multiple browser windows.
7. Tests reject missing metadata, duplicate canonical declarations, stale hashes, and unapproved canonical promotion.
8. No final portrait is claimed as generated, reviewed, or locked unless evidence exists.

## Out of Scope
- complete 360-degree turnarounds;
- group photography;
- full wardrobe-library generation;
- private-mode visual assets;
- final image generation when no approved local generation workflow is available.

## Completion Condition
WP-4118 is complete when the repository contains a tested, auditable hero-portrait standard and every commissioned resident has a valid hero-portrait manifest state: `not_started`, `candidate_generation`, `steward_review`, or `canonical_locked`.