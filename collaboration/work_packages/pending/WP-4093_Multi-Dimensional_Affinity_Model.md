# WP-4093 — Multi-Dimensional Resident Affinity Model

Status: Pending
Execution Mode: SERIES
Owner: Office of Character Architecture / Relationship Systems
Execution Target: Codex
Classification: Estate Internal
Priority: Immediate

## Depends On

- WP-4051 — Resident Relationship Graph Runtime
- WP-4068 — Resident Trust and Familiarity Evolution
- WP-4069 — Affection and Playful Expression
- WP-4070 — Conflict Resolution and Relationship Repair
- WP-4072 — Relationship Review and Calibration

## Objective

Implement a canonical, multi-dimensional affinity model that represents distinct forms of regard between residents and between each resident and the Steward without collapsing relationships into one score or creating a parallel relationship system.

## Required Work

1. Extend the canonical relationship graph with typed dimensions including trust, respect, familiarity, warmth, affection, admiration, comfort, playfulness, protectiveness, attraction where explicitly authored, rivalry, and professional confidence.
2. Preserve directional asymmetry so A-to-B and B-to-A may differ.
3. Separate authored baseline, observed evidence, inferred state, private state, and presentation behavior.
4. Define bounded ranges, confidence, freshness, source lineage, and change-rate limits for every dimension.
5. Require explicit privacy and authority checks before exposing protected dimensions.
6. Integrate with the existing preference/personality evolution engine rather than duplicating it.
7. Permit residents to express crushes, fondness, teasing, reserve, or professional distance according to individual Character Bibles and accumulated evidence.
8. Prevent affinity from granting authority, consent, access, or task priority.

## Acceptance Tests

1. Two residents can have high respect but low personal warmth without contradiction.
2. A resident may feel affection for the Steward while remaining professionally uncompromising.
3. Directional asymmetry is preserved.
4. Private attraction or protected relationship data is not exposed to unauthorized surfaces.
5. Missing evidence remains unknown rather than defaulting to positive affinity.
6. A single event cannot create implausible permanent relationship jumps.
7. Affinity changes do not alter institutional authority.

## Deliverables

- affinity dimension schema and graph extensions;
- evidence and confidence model;
- privacy-filtered query and presentation interfaces;
- migration from existing relationship data;
- tests, diagnostics, documentation, and completion receipt.

## Constraints

- Do not create a second relationship graph.
- Do not reduce relationships to a single universal score.
- Do not manufacture attraction, consent, or intimacy from task completion.
- Do not expose Evelyn or other protected relationship state outside authorized contexts.

## Completion Standard

WP-4093 is complete only when the canonical relationship runtime can represent nuanced, directional, evidence-backed affinity across professional, personal, playful, affectionate, and protected dimensions; privacy and uncertainty remain explicit; and affinity never substitutes for consent, authority, or institutional state.
