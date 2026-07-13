# WP-4114 SERIES — Visual Prompt Engineering Canon

## Status
Pending

## Initiative
Visual Estate Initiative

## Campaign
Campaign 01 — Visual Bible Foundation

## Objective
Establish a canonical, auditable prompt-engineering system for generating consistent resident visuals across approved local image models and workflows.

## Problem
Resident visual prompts are currently at risk of being scattered, model-specific, difficult to reproduce, and prone to identity drift. The Estate requires a structured prompt canon that separates stable identity from scene, wardrobe, pose, camera, and model-specific implementation details.

## Scope
Create the prompt architecture, schema, composition order, versioning, and validation rules used by all later visual-generation campaigns.

The prompt canon must support:

1. Photorealistic portraits and full-body images.
2. Black-and-white, sketch, illustration, icon, and thumbnail variants.
3. 360-degree turnaround and measurement-comparison sheets.
4. Office, casual, formal, fitness, dance, swim, seasonal, environmental, interaction, and group scenes.
5. Single-resident, pair, small-group, leadership-group, and full-Estate compositions.
6. Model-specific adapters without changing canonical identity.
7. Positive prompts, negative prompts, reference images, seeds, ControlNet or equivalent controls, LoRA or identity adapters, and workflow metadata.
8. Public, internal, restricted, and private-audience prompt scopes.

## Canonical Prompt Layers
Prompts must be assembled from explicit layers in this order unless a model adapter requires a documented variation:

1. **Resident identity layer**
   - canonical name and resident identifier
   - adult age presentation
   - height, build, measurements, proportions
   - facial geometry
   - visual fingerprint
   - hair, eyes, skin, distinguishing features

2. **Presence and emotional intent layer**
   - posture
   - expression
   - gaze
   - energy
   - emotional anchor
   - role-specific presence

3. **Wardrobe and grooming layer**
   - approved look identifier
   - garment cut, fabric, fit, color, footwear, accessories
   - hair and makeup treatment
   - presentation effects that must not rewrite canonical physique

4. **Pose and activity layer**
   - standing, seated, walking, working, dancing, reading, conversation, or other activity
   - hand placement
   - weight distribution
   - head angle
   - movement state

5. **Environment and relationship layer**
   - location
   - furniture and scale cues
   - other residents
   - interpersonal distance and body language
   - office or Estate context

6. **Camera and composition layer**
   - shot type
   - lens or focal-length intent
   - camera height and distance
   - aspect ratio
   - depth of field
   - lighting
   - framing
   - turnaround alignment requirements

7. **Rendering and output layer**
   - photorealistic, editorial, cinematic, documentary, monochrome, iconographic, sketch, or other approved style
   - resolution
   - file format
   - transparent background requirements
   - color-management notes

8. **Negative and exclusion layer**
   - canonical negative prompt reference
   - anatomy and artifact exclusions
   - identity-drift exclusions
   - wardrobe and proportion exclusions
   - audience-scope exclusions

9. **Model adapter layer**
   - model name and version
   - scheduler, sampler, CFG, steps, seed, denoise, and resolution where applicable
   - LoRA, embedding, IP-Adapter, ControlNet, pose, depth, face, or reference-image configuration
   - known quirks and compensations

## Stable Identity Rule
The resident identity layer must remain stable across scenes. Scene prompts may change clothing, setting, mood, and activity, but may not silently change:

- canonical height
- age presentation
- facial structure
- eye color
- hair identity
- body measurements
- resident-specific visual fingerprint

Any intentional variant must be labeled review-only and must not overwrite canonical data without Steward approval.

## Prompt Fragment Repository
For each resident, establish or validate:

- `visual_bible/prompts/identity.yaml`
- `visual_bible/prompts/presence.yaml`
- `visual_bible/prompts/wardrobe.yaml`
- `visual_bible/prompts/poses.yaml`
- `visual_bible/prompts/environments.yaml`
- `visual_bible/prompts/camera.yaml`
- `visual_bible/prompts/styles.yaml`
- `visual_bible/prompts/group_compatibility.yaml`
- `visual_bible/prompts/model_adapters/`
- `visual_bible/prompts/generated_prompt_receipts/`

## 360-Degree and Measurement Comparison Prompt Standard
Turnaround prompts must lock:

- identical resident identity
- identical hairstyle and grooming
- identical neutral expression unless otherwise specified
- identical wardrobe within a comparison set
- identical camera, focal-length intent, distance, lighting, background, and scale
- front, front-three-quarter, side, rear-three-quarter, and rear angles
- vertical stacking of measurement variants for direct same-angle comparison
- explicit variant labels
- at least one applicable set in 3-inch-or-higher heels

The only intended difference between measurement variants must be the declared top, middle, or bottom measurement change. Uncontrolled changes invalidate the sheet.

## Group Prompt Standard
Group prompts must preserve each resident independently.

Every group prompt must include:

- resident roster with canonical identity references
- relative height map
- spatial placement
- posture and body-language intent
- wardrobe identifiers
- face and hair locks
- no-face-merging instruction
- no-body-homogenization instruction
- interaction intent
- hidden-caption recognition-test metadata

Group images must not produce multiple residents who look like variations of the same person.

## Emotional Anchor Prompting
Each resident must support prompts for emotional-anchor images that express who they are, not merely what they wear.

For Evelyn, examples may include:

- leaning slightly forward on a couch with a coffee mug
- relaxed shoulders
- gentle head tilt
- direct but soft attention
- the feeling that the viewer has just entered and been invited to sit

These examples are provisional character calibrations and must not be copied onto unrelated residents.

## Reproducibility Receipt
Every generated asset must be able to record:

- resident ID
- prompt version
- fully composed positive prompt
- fully composed negative prompt
- model and model hash where available
- workflow version
- seed
- image dimensions
- sampler and scheduler
- steps and guidance
- reference-image identifiers
- adapter identifiers and weights
- generation date
- review state
- canonical, provisional, rejected, or retired status

## Prompt Safety and Governance
Prompt scopes must be explicit. Restricted or private-audience prompts must be stored and executed through approved access boundaries, never hidden to evade review.

All residents represented in these visual systems must be unambiguously adults. Prompts must avoid age ambiguity and must preserve adult professional identity even for petite residents.

## Deliverables
1. Canonical prompt schema.
2. Prompt composition engine or deterministic composition specification.
3. Resident prompt-fragment repository standard.
4. Model-adapter interface.
5. Reproducibility receipt schema.
6. Turnaround and measurement-comparison prompt templates.
7. Group-scene prompt template.
8. Emotional-anchor prompt template.
9. Validation rules and tests.
10. One completed Evelyn example and one contrasting resident example to prove the canon is not Evelyn-specific.

## Acceptance Criteria
- A resident can be regenerated across multiple approved models without losing canonical identity.
- Stable identity is cleanly separated from scene, wardrobe, pose, camera, and style.
- Turnaround variants change only the declared measurement variable.
- Group prompts preserve distinct faces, bodies, heights, posture, and presence.
- Every canonical asset has a reproducibility receipt.
- Prompt fragments are versioned and traceable.
- Restricted prompt scopes are governed and auditable.
- Validation rejects prompts missing resident identity, adult-age clarity, audience scope, or reproducibility metadata.

## Dependencies
- WP-4108 — Visual Bible Schema and Repository Structure
- WP-4109 — Canonical Physical Specification Standard
- WP-4110 — Facial Geometry and Visual Fingerprint
- WP-4111 — Height, Proportion, and Scale Reference System
- WP-4112 — Measurement Variant Review Workflow
- WP-4113 — Wardrobe and Signature Look Library

## Out of Scope
- Final negative-prompt taxonomy, owned by WP-4115.
- Bulk asset generation.
- Final resident visual approval.
- Installation of specific image models or ComfyUI nodes.

## Completion Condition
The Estate has one canonical prompt-engineering system capable of producing reproducible, resident-specific, multi-model visual assets without silent identity, measurement, wardrobe, or governance drift.
