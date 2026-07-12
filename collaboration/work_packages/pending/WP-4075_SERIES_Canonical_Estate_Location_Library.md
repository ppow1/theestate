# WP-4075 — Canonical Estate Location Library

Status: Pending
Execution Mode: SERIES
Owner: Office of Character Architecture / Visual Environment Integration
Execution Target: Codex
Classification: Estate Internal
Priority: Immediate

## Depends On

- WP-4073 — Resident Visual Identity Framework
- Existing Estate location, office, room, and activation records

## Objective

Implement one canonical visual location library so recurring Estate rooms, grounds, offices, and operational spaces remain recognizable across images, avatars, scenes, interfaces, and historical records.

## Required Work

1. Inventory existing canonical location, office, room, estate-map, activation, and visual-reference artifacts before adding new records.
2. Define a typed location record with canonical ID, name, function, occupants, architectural style, dimensions where known, materials, furnishings, lighting, windows, view, access scope, privacy class, and source lineage.
3. Create initial visual references for the Steward's Office, Alfred's workspace, Helen's office, Grace's operations area, Ingrid's privacy/security workspace, Evelyn's authorized spaces, conference rooms, library, great hall, gardens, kitchen, staff lounge, and other verified recurring locations.
4. Distinguish canonical permanent features from movable furniture, seasonal decoration, temporary project materials, environmental storytelling, and generated-image variation.
5. Record approved camera positions, spatial relationships, exterior views, and negative constraints preventing room drift.
6. Integrate occupancy and disclosure boundaries without turning this library into a scheduler, access-control system, or presence authority.
7. Support room versions and renovations with effective dates and historical lineage.
8. Provide provider-neutral prompt fragments and reference assets for visual generation.

## Acceptance Tests

1. A recurring room remains recognizably the same across multiple providers, seasons, and camera angles.
2. Residents appear in spatially plausible locations consistent with canonical office and access records.
3. Temporary decorations or furniture do not silently rewrite the canonical room.
4. Restricted locations and private room details are excluded from unauthorized scenes.
5. A renovation creates a new version with preserved history rather than overwriting the past.
6. Location diagnostics expose missing, conflicting, stale, or inferred attributes.

## Deliverables

- canonical location schema and registry-linked records;
- initial Estate location reference set;
- spatial and camera-reference conventions;
- provider-neutral location adapters;
- versioning, privacy, and drift diagnostics;
- tests, documentation, and completion receipt.

## Constraints

- Do not create a second office, facility, registry, access-control, or presence institution.
- Do not invent precise dimensions, occupants, or authority from visual appearance.
- Do not expose private spaces or restricted details to public or shared outputs.
- Do not overwrite historical location state when rooms change.

## Completion Standard

WP-4075 is complete only when recurring Estate locations have source-lined canonical visual records, remain recognizably stable across supported visual outputs, preserve privacy and historical versions, and can be consumed by image and avatar systems without creating parallel facility or authority state.