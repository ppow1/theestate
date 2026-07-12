# WP-4087 — Resident Presence API

Status: Pending
Execution Mode: SERIES
Owner: Office of Character Architecture / Resident Presence Integration
Execution Target: Codex
Classification: Estate Internal
Priority: Immediate

## Depends On

- WP-4083 — Ambient Resident Activity Runtime
- WP-4084 — Dynamic Estate Occupancy Runtime
- WP-4085 — Passive Resident Interaction Engine
- WP-4086 — Environmental Storytelling Runtime

## Objective

Implement one governed Resident Presence API that exposes current resident activity, occupancy, availability, nearby social context, and visible environmental state to authorized Estate surfaces without creating a new authority or leaking private information.

## Required Work

1. Define typed query and response contracts for resident presence, room presence, availability, activity, nearby participants, and visible environmental details.
2. Return source, confidence, freshness, visibility, simulation status, and uncertainty for every material field.
3. Support per-resident, per-location, conference-room, and Estate-summary queries.
4. Apply caller identity, role, clearance, relationship scope, and location visibility before returning data.
5. Distinguish verified, inferred, simulated, stale, conflicting, and unknown presence states.
6. Prevent the API from granting actions, reserving rooms, changing schedules, altering relationship state, or creating memory.
7. Provide stable machine-readable output and bounded human-readable summaries.
8. Add caching and invalidation rules that cannot present stale occupancy or availability as current.
9. Emit inspectable diagnostics for missing, conflicting, denied, or degraded sources.

## Acceptance Tests

1. Authorized callers receive consistent resident and room presence views.
2. Unauthorized callers receive redacted or denied results without protected metadata leakage.
3. Stale, conflicting, simulated, and unknown states remain explicit.
4. API summaries never invent activity or availability.
5. Cache invalidation removes expired presence promptly.
6. Provider or model changes do not alter canonical resident identity.
7. The API cannot perform privileged actions or mutate canonical state.
8. Estate-wide summaries preserve per-resident individuality and privacy.

## Deliverables

- presence query and response schemas;
- authorization and disclosure adapter;
- resident, location, and Estate summary endpoints;
- cache, freshness, uncertainty, and diagnostic handling;
- tests, documentation, and completion receipt.

## Constraints

- Do not create a second gateway, directory, scheduler, location authority, or identity system.
- Do not expose protected occupancy, activity, relationship, or environmental details.
- Do not hide uncertainty behind polished summaries.

## Completion Standard

WP-4087 is complete only when authorized Estate surfaces can query one privacy-safe, source-lined, freshness-aware presence interface for residents and locations; verified, inferred, simulated, conflicting, stale, and unknown states remain distinguishable; and the API informs presentation without acquiring authority or mutation powers.
