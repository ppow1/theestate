# WP-4084 — Dynamic Estate Occupancy Runtime

Status: Pending
Execution Mode: SERIES
Owner: Office of Character Architecture / Resident Presence Integration
Execution Target: Codex
Classification: Estate Internal
Priority: Immediate

## Depends On

- WP-4075 — Canonical Estate Location Library
- WP-4083 — Ambient Resident Activity Runtime

## Objective

Implement one canonical occupancy runtime that answers where residents are, which Estate spaces are occupied, and who is available without exposing private details or inventing physical presence.

## Required Work

1. Define typed occupancy records for resident, location, interval, activity reference, availability, visibility, source, confidence, and freshness.
2. Reconcile explicit check-ins, scheduled events, active sessions, ambient activity, and unknown state through deterministic precedence rules.
3. Support public, staff-only, restricted, private, and undisclosed occupancy visibility.
4. Prevent two incompatible simultaneous locations for one resident unless the source explicitly represents remote or virtual participation.
5. Distinguish physical presence, virtual participation, expected arrival, in transit, unavailable, and unknown.
6. Maintain room-level occupancy summaries without turning generated summaries into canonical source records.
7. Integrate conference rooms, offices, gardens, shared spaces, and off-Estate states through the canonical location library.
8. Expose stale, conflicting, or missing occupancy evidence visibly.

## Acceptance Tests

1. Resident and room occupancy views agree from the same source state.
2. Conflicting location evidence produces a diagnostic rather than silent selection.
3. Restricted occupancy is excluded from unauthorized surfaces.
4. Virtual attendance is not misrepresented as physical presence.
5. Unknown location remains unknown.
6. Expired evidence cannot appear current.
7. Restart reconstructs occupancy deterministically from durable evidence.

## Deliverables

- occupancy and availability schemas;
- occupancy reconciler and precedence policy;
- room and resident status projections;
- privacy, freshness, and conflict diagnostics;
- tests, documentation, and completion receipt.

## Constraints

- Do not create a second calendar, location registry, security tracker, or resident identity system.
- Do not infer sensitive location from private content.
- Do not present stale or simulated occupancy as verified fact.

## Completion Standard

WP-4084 is complete only when the Estate can answer who is where, who is available, and which spaces are occupied through one source-lined, privacy-safe, freshness-aware runtime; conflicts and unknowns remain explicit; and physical, virtual, and simulated presence are never conflated.
