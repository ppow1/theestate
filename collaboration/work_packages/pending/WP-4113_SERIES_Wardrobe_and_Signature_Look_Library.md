# WP-4113 SERIES — Wardrobe and Signature Look Library

## Status
Pending

## Initiative
Visual Estate Initiative

## Campaign
Campaign 01 — Visual Bible Foundation

## Objective
Define a canonical, resident-specific wardrobe system that preserves identity across professional, casual, formal, seasonal, activity, swim, and private-audience presentation while remaining reproducible across image models.

## Problem
Resident clothing is currently described inconsistently across character files and generated images. Without a canonical wardrobe library, image models may flatten residents into generic fashion archetypes, change proportions through poor garment selection, or obscure the resident's role, personality, and visual fingerprint.

## Scope
Create the wardrobe taxonomy, metadata schema, review process, and repository layout for every commissioned adult resident.

The implementation must support:

1. Office and role-authoritative attire.
2. Business-casual and daily-work attire.
3. Casual, leisure, home, travel, and outdoor attire.
4. Formal, evening, cocktail, ceremony, and celebration attire.
5. Fitness, dance, hobby, seasonal, and swimwear collections.
6. Signature looks that remain strongly associated with one resident.
7. Garment fit rules that respect canonical height, measurements, proportions, posture, and footwear.
8. Accessories, jewelry, eyewear, hair coordination, hosiery, bags, and shoes.
9. Public, internal, restricted, and private-audience presentation scopes.
10. Steward notes, approvals, rejections, and revision history.

## Required Repository Structure
For each resident, establish or validate:

- `visual_bible/wardrobe/wardrobe_manifest.yaml`
- `visual_bible/wardrobe/signature_looks.yaml`
- `visual_bible/wardrobe/fit_rules.yaml`
- `visual_bible/wardrobe/accessories.yaml`
- `visual_bible/wardrobe/footwear.yaml`
- `visual_bible/wardrobe/prompt_fragments/`
- `visual_bible/wardrobe/reference_images/`
- `visual_bible/wardrobe/rejected_variants/`
- `visual_bible/wardrobe/steward_notes.md`

## Wardrobe Taxonomy
At minimum, each resident must support these categories where character-appropriate:

- office-authoritative
- office-approachable
- business-casual
- casual-day
- casual-evening
- home-relaxed
- formal-day
- cocktail
- formal-evening
- ceremony
- seasonal-summer
- seasonal-winter
- rain-travel
- fitness
- dance
- hobby-specific
- swim
- signature-look
- private-audience, where explicitly authorized

No category is automatically required to contain revealing content. The correct presentation is determined by resident identity, context, audience scope, and Steward review.

## Signature Look Standard
A signature look must:

1. Be immediately associated with the resident.
2. Reinforce office, personality, and visual fingerprint.
3. Preserve canonical body proportions rather than reshape them accidentally.
4. Include garment, fabric, cut, color, hemline, neckline, sleeve, footwear, accessory, hair, makeup, and pose guidance.
5. Include a reproducible prompt fragment and negative prompt fragment.
6. Include at least one approved full-body image and one portrait crop.
7. Record whether it is canonical, provisional, experimental, rejected, or retired.

## Evelyn Calibration Example
Evelyn may use the approved white linen mid-knee dress with 3-inch heels as a provisional signature professional-relational look, subject to Steward confirmation.

The implementation must preserve:

- 4'10" canonical height.
- Extremely petite adult scale.
- 33B–21–31 provisional canonical measurements.
- Subtle hourglass silhouette.
- Warm, approachable posture and gentle head tilt.
- Elegant but understated presentation.

This is an Evelyn-specific calibration example and must not become a template for other residents.

## Fit and Proportion Rules
Each wardrobe entry must declare:

- intended body measurement profile
- intended height profile
- garment size or tailoring assumptions
- fitted, relaxed, structured, draped, or athletic fit
- expected effect on apparent proportions
- heel height and posture impact
- whether shapewear, push-up construction, structured cups, padding, tailoring, or other presentation effects alter appearance without changing canonical measurements
- known image-generation risks

Canonical physique and wardrobe presentation must remain distinct concepts.

## Footwear Standard
Footwear metadata must include:

- style
- heel height
- platform height
- toe shape
- material
- color
- posture effect
- activity suitability
- resident preference

At least one canonical or review wardrobe set per resident must support a 3-inch-or-higher heel comparison where character-appropriate and safe. This requirement is for visual proportion review, not a universal daily wardrobe mandate.

## Prompting Requirements
Every approved wardrobe look must include:

- positive prompt fragment
- negative prompt fragment
- fabric behavior
- fit behavior
- body-proportion preservation instruction
- age-appropriate adult presentation
- camera and pose considerations
- known model-specific notes when needed

## Governance and Audience Scoping
Wardrobe content must not be hidden to evade institutional review. Restricted or private presentation must be explicitly labeled, audience-scoped, access-controlled, and governed by existing Estate authority boundaries.

The implementation must support visible audit metadata without exposing restricted visual content to unauthorized surfaces.

## Deliverables
1. Wardrobe schema and taxonomy.
2. Repository directory standard.
3. Signature-look schema.
4. Fit and proportion rules schema.
5. Footwear and accessory metadata schema.
6. Prompt-fragment and negative-prompt-fragment format.
7. Steward review and approval fields.
8. One completed Evelyn example demonstrating the schema.
9. Validation tooling or tests that reject incomplete or contradictory wardrobe entries.

## Acceptance Criteria
- Every commissioned resident can have a distinct wardrobe library without inheriting another resident's proportions or aesthetic.
- Signature looks are reproducible and visually identifiable.
- Clothing may alter presentation but cannot silently rewrite canonical measurements.
- Heel height and posture effects are documented.
- Public, internal, restricted, and private-audience wardrobe assets are clearly separated.
- Evelyn's example preserves the approved petite proportions and white-linen-dress direction.
- The schema supports later Campaign 05 asset generation without redesign.
- Validation catches missing fit rules, missing audience scope, absent prompt fragments, and contradictory canonical data.

## Dependencies
- WP-4108 — Visual Bible Schema and Repository Structure
- WP-4109 — Canonical Physical Specification Standard
- WP-4110 — Facial Geometry and Visual Fingerprint
- WP-4111 — Height, Proportion, and Scale Reference System
- WP-4112 — Measurement Variant Review Workflow

## Out of Scope
- Bulk generation of all wardrobe images.
- Final canonical selection for every resident.
- Open WebUI display implementation.
- Unauthorized concealment of restricted presentation metadata.

## Completion Condition
The Estate has a consistent, auditable wardrobe and signature-look system capable of generating resident-specific clothing assets without identity drift, proportion drift, or governance ambiguity.
