# WP-4079 — Resident Portrait Management

Status: Pending
Execution Mode: SERIES
Owner: Office of Character Architecture / Visual Systems Integration
Execution Target: Codex
Classification: Estate Internal
Priority: High

## Depends On

- WP-4073 — Resident Visual Identity Framework
- WP-4076 — Character Presentation and Pose Framework
- WP-4077 — Visual Continuity Runtime
- WP-4078 — Living Estate Gallery Runtime

## Objective

Implement governed resident portrait management so every active resident has recognizable, versioned, context-appropriate portrait assets without allowing one image, model, or generation error to redefine the resident.

## Required Work

1. Define portrait records for canonical headshot, executive, casual, formal, seasonal, profile, full-body, and relationship-context variants.
2. Bind portraits to canonical resident identity, approved appearance version, wardrobe record, pose/expression profile, location or backdrop, and disclosure class.
3. Support portrait nomination, review, approval, supersession, retirement, and rollback.
4. Produce derivatives and crops deterministically while preserving the approved source artifact and lineage.
5. Detect facial drift, age drift, body-proportion drift, wardrobe mismatch, implausible anatomy, duplicate identity, and resident-to-resident visual convergence.
6. Keep concept exploration separate from approved portrait libraries.
7. Provide surface-specific portrait selection for directories, dashboards, messages, conference rooms, dossiers, and private contexts.
8. Preserve resident dignity and authored individuality; attractiveness, glamour, modesty, and playfulness must follow the resident’s approved character and context rather than a universal template.

## Acceptance Tests

1. Each active resident can have one current canonical headshot plus approved contextual variants.
2. Superseding a portrait updates consuming surfaces without deleting prior lineage.
3. Portraits with identity drift or malformed anatomy fail review.
4. Private or relationship-specific portraits remain restricted.
5. Two residents cannot silently converge onto the same face or visual identity.
6. Provider/model changes preserve the resident’s recognizable appearance.
7. Surface selection honors context, disclosure, and presentation rules.
8. No portrait alone can alter canonical biography, role, authority, or physical definition.

## Deliverables

- portrait schemas and versioning rules;
- nomination, review, approval, and rollback workflow;
- drift and quality diagnostics;
- derivative/crop pipeline;
- surface-selection adapter;
- tests, documentation, and completion receipt.

## Constraints

- Do not create a second resident identity store.
- Do not auto-approve generated portraits.
- Do not use one beauty or body template for all residents.
- Do not expose restricted portraits in public or shared surfaces.

## Completion Standard

WP-4079 is complete only when every active resident can maintain a recognizable, versioned, privacy-scoped portrait library whose approved assets remain consistent across models and surfaces while preserving resident-specific dignity, personality, and presentation.