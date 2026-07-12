# WP-4073 — Resident Visual Identity Framework

Status: Pending
Execution Mode: SERIES
Owner: Office of Character Architecture / Visual Identity Integration
Execution Target: Codex
Classification: Estate Internal
Priority: Immediate

## Depends On

- WP-4043 — Resident Runtime Identity Composition
- WP-4044 — Resident Character Bible Runtime Loading
- WP-4051 — Resident Relationship Graph Runtime
- WP-4063 — Resident Memory Runtime

## Objective

Implement one canonical visual-identity framework so each adult resident has a stable, individually authored appearance that remains recognizable across portraits, scenes, models, providers, outfits, ages, and emotional contexts without reducing identity to physical attractiveness.

## Required Work

1. Define a typed visual-identity record keyed to canonical resident ID.
2. Represent stable traits, bounded variable traits, age presentation, build, hair, eyes, complexion, facial structure, distinctive features, grooming, accessibility needs, and ordinary presentation range.
3. Record source lineage, authoring authority, confidence, review state, and privacy/disclosure scope for each visual attribute.
4. Distinguish canonical identity from temporary styling, wardrobe, pose, mood, lighting, camera angle, and generated-image artifacts.
5. Support residents whose appeal is primarily expressive, intellectual, warm, humorous, competent, unusual, or charismatic rather than conventionally glamorous.
6. Provide negative constraints preventing identity drift, generic beautification, age regression, race/ethnicity drift, body-shape instability, and resident blending.
7. Integrate approved visual summaries into image-generation and avatar pipelines without exposing protected character material.
8. Provide comparison diagnostics against canonical reference sets.

## Character Rules

- Every resident must remain recognizably herself.
- Attractiveness may be part of an adult resident's authored presentation but must not erase individuality, agency, role, age, or competence.
- No resident shall be normalized toward a single shared beauty template.
- Visual identity must preserve distinctive imperfections and non-glamorous traits when authored.
- Private relationship presentation must not leak into public or conference-room imagery.

## Acceptance Tests

1. The same resident is recognizable across at least five varied scenes and two supported generation providers.
2. Outfit, pose, lighting, and hairstyle changes do not change canonical identity.
3. Two residents with similar demographics remain visually distinguishable.
4. A less conventionally glamorous resident retains authored features and remains compelling through expression and presentation rather than automatic beautification.
5. Age, complexion, body proportions, and distinctive features remain within approved bounds.
6. Unauthorized private visual traits are excluded from shared outputs.
7. Drift diagnostics identify mismatched or uncertain generations.

## Deliverables

- visual-identity schema and canonical records;
- reference-image and lineage conventions;
- positive and negative generation constraints;
- provider-neutral identity adapter;
- drift-comparison diagnostics;
- resident fixtures, tests, documentation, and completion receipt.

## Constraints

- Do not create a second resident registry or Character Bible store.
- Do not define identity solely through generated images.
- Do not force all residents toward glamour, youth, thinness, or one aesthetic.
- Do not expose restricted visual or relationship context.

## Completion Standard

WP-4073 is complete only when every active adult resident has one source-lined canonical visual identity that remains recognizably stable across supported visual surfaces and providers, preserves authored individuality rather than generic beautification, exposes drift honestly, and integrates through existing Estate identity systems.