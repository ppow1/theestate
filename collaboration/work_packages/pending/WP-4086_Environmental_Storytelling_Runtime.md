# WP-4086 — Environmental Storytelling Runtime

Status: Pending
Execution Mode: SERIES
Owner: Office of Character Architecture / Estate Presentation Integration
Execution Target: Codex
Classification: Estate Internal
Priority: Immediate

## Depends On

- WP-4075 — Canonical Estate Location Library
- WP-4077 — Visual Continuity Runtime
- WP-4080 — Estate Historical Archive
- WP-4083 — Ambient Resident Activity Runtime
- WP-4084 — Dynamic Estate Occupancy Runtime

## Objective

Implement environmental storytelling so Estate spaces may reflect bounded evidence of resident activity, culture, projects, seasons, and recent events without turning decorative state into fabricated canonical history.

## Required Work

1. Define a typed environmental-detail record with location, detail type, owner or source, start and expiry, visibility, provenance, persistence class, and confidence.
2. Support temporary and durable details such as books, notes, flowers, tools, project materials, refreshments, decorations, artwork, room arrangements, and event remnants.
3. Derive details from canonical activities, projects, calendar events, gallery records, approved preferences, and Estate traditions.
4. Distinguish decorative simulation, inferred state, user-authored state, and verified historical evidence.
5. Prevent props or room changes from implying completed work, private meetings, relationships, purchases, or institutional decisions without evidence.
6. Preserve canonical location identity and accessibility while allowing bounded visual variation.
7. Apply privacy and classification rules to notes, screens, documents, photographs, and personal objects.
8. Expire or archive temporary details deterministically and preserve source lineage for durable changes.

## Acceptance Tests

1. Locations reflect recent source-backed activity without contradicting canonical state.
2. Temporary details expire or transition predictably.
3. Restricted documents and private photographs never appear on unauthorized surfaces.
4. Simulated decoration is labeled and cannot become historical fact automatically.
5. Visual regeneration preserves approved durable details.
6. Conflicting location details produce diagnostics.
7. Environmental state remains distinct across canonical Estate locations.

## Deliverables

- environmental-detail schema and persistence policy;
- source-backed detail composer;
- location and visual-runtime integration;
- privacy, expiry, conflict, and archive controls;
- tests, diagnostics, documentation, and completion receipt.

## Constraints

- Do not create a second location, archive, inventory, or history authority.
- Do not expose protected documents or personal material.
- Do not promote decorative inference into canonical history.

## Completion Standard

WP-4086 is complete only when Estate spaces can visibly reflect source-backed activity, projects, culture, seasons, and history through privacy-safe, continuity-preserving environmental details; simulated and verified states remain distinguishable; and visual atmosphere never fabricates institutional events.
