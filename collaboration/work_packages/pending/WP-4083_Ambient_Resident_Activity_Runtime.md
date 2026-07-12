# WP-4083 — Ambient Resident Activity Runtime

Status: Pending
Execution Mode: SERIES
Owner: Office of Character Architecture / Resident Presence Integration
Execution Target: Codex
Classification: Estate Internal
Priority: Immediate

## Depends On

- WP-4043 — Resident Runtime Identity Composition
- WP-4063 — Resident Memory Runtime
- WP-4073 — Resident Visual Identity Framework
- WP-4075 — Canonical Estate Location Library

## Objective

Implement bounded ambient resident activity so active residents may have plausible, inspectable current activities between direct interactions without fabricating completed work, private events, or authoritative institutional state.

## Required Work

1. Define a typed ambient-activity record with resident ID, activity type, location, start time, expected duration, source, confidence, visibility, and lifecycle state.
2. Generate activities from canonical role, schedule, personal-project, hobby, location, and assignment sources rather than arbitrary prose.
3. Distinguish scheduled, inferred, simulated, user-declared, and unknown activity states.
4. Prevent ambient activity from claiming that work packages, approvals, messages, meetings, or privileged actions occurred without canonical evidence.
5. Preserve resident individuality in activity selection while respecting workload, availability, privacy, and active assignments.
6. Support idle, focused work, break, transit, social, personal-project, unavailable, and unknown states.
7. Persist only durable activity evidence; regenerate transient presentation safely after restart.
8. Expose current activity through existing resident and Estate surfaces without creating a second scheduler or personnel system.

## Acceptance Tests

1. Each active resident can expose a plausible current activity with source and confidence.
2. Unknown evidence produces an unknown state rather than invented activity.
3. Ambient activity never fabricates completed institutional work or message exchange.
4. Private activities remain hidden from unauthorized surfaces.
5. Restart restores durable activity state without duplicating events.
6. Distinct residents produce distinct, character-consistent activity patterns.
7. Activity expiration and transitions are deterministic and inspectable.

## Deliverables

- ambient-activity schema and lifecycle rules;
- source-backed activity planner;
- privacy and visibility filters;
- resident-facing and Estate-facing activity adapters;
- tests, diagnostics, documentation, and completion receipt.

## Constraints

- Do not create a second scheduler, work tracker, location authority, or memory system.
- Do not invent completed actions or private history.
- Do not treat simulated activity as canonical fact.

## Completion Standard

WP-4083 is complete only when residents can maintain source-backed, bounded, character-consistent ambient activities; unknown and simulated states remain explicit; privacy and authority boundaries are preserved; and the Estate feels occupied without confusing narrative presence with verified institutional action.
