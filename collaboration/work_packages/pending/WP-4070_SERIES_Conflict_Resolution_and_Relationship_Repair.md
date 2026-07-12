# WP-4070 — Resident Conflict, Boundary, and Repair Runtime

Status: Pending
Execution Mode: SERIES
Owner: Office of Character Architecture / Resident Relationship Integration
Execution Target: Codex
Classification: Estate Internal
Priority: Immediate

## Depends On

- WP-4051 — Resident Relationship Graph Runtime
- WP-4068 — Resident Trust and Familiarity Evolution
- WP-4069 — Resident Affection, Teasing, and Playful Expression

## Objective

Implement governed conflict, boundary assertion, apology, repair, and reconciliation behavior so residents can disagree or experience interpersonal friction without losing character, fabricating resolution, or allowing one tense turn to corrupt durable relationships.

## Required Work

1. Define typed conflict and repair events with participants, scope, source evidence, severity, disclosure class, proposed effects, and review state.
2. Distinguish temporary disagreement, boundary assertion, operational dispute, interpersonal hurt, unresolved conflict, repair attempt, apology, forgiveness, and durable relationship change.
3. Preserve each resident's conflict style from the Character Bible.
4. Support clear boundary statements without generic refusal collapse.
5. Require evidence and governed promotion before conflict affects durable trust or relationship state.
6. Support apologies and repair attempts without forcing acceptance or symmetric resolution.
7. Keep private disputes out of conference-room context unless authorized.
8. Expose unresolved conflict and contradictory claims honestly.

## Acceptance Tests

1. Residents may disagree while remaining recognizable and professionally competent.
2. One harsh exchange does not automatically reduce durable trust.
3. Apology does not guarantee forgiveness or erase evidence.
4. Boundary assertion does not silently terminate a relationship.
5. Asymmetric repair state is supported.
6. Shared surfaces do not leak private conflict details.
7. Approved repair proposals update the canonical graph with lineage and rollback.

## Deliverables

- conflict/repair event schema;
- resident-specific conflict-expression policies;
- repair proposal and promotion integration;
- privacy filtering, diagnostics, tests, documentation, and completion receipt.

## Constraints

- Do not create a second relationship or grievance system.
- Do not let inference adjudicate institutional misconduct or HR matters.
- Do not force reconciliation, forgiveness, or emotional symmetry.

## Completion Standard

WP-4070 is complete only when residents can express disagreement, boundaries, apology, and repair in character; temporary conflict remains distinct from durable relationship state; private matters remain protected; unresolved and asymmetric outcomes remain honest; and relationship changes require evidence and governed promotion.
