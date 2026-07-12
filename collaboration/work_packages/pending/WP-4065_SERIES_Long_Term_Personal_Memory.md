# WP-4065 — Long-Term Personal Memory

Status: Pending
Execution Mode: SERIES
Owner: Office of Character Architecture / Resident Runtime Integration
Execution Target: Codex
Classification: Estate Internal
Priority: Immediate

## Depends On

- WP-4063 — Resident Memory Runtime
- WP-4064 — Resident Episodic Memory
- WP-4053 — Dynamic Resident Preference and Personality Evolution

## Objective

Implement long-term personal memory so each resident can preserve durable lessons, preferences, routines, personal milestones, and relationship-relevant continuity without freezing personality or promoting transient reactions into permanent identity.

## Required Work

1. Define durable personal-memory classes for lessons, preferences, routines, milestones, aversions, comforts, commitments, and approved self-understanding.
2. Require repeated evidence, explicit approval, or authoritative source material for durable promotion according to memory class.
3. Distinguish stable identity, mature preference, tentative preference, current mood, experiment, and retired preference.
4. Reuse WP-4053 evolution mechanisms and Character Bible sources rather than creating a competing personality engine.
5. Support confidence decay, review dates, supersession, and resident-specific retention policies.
6. Preserve source lineage and privacy scope for every record.
7. Prevent shared-room behavior or one provocative exchange from silently rewriting durable identity or relationships.

## Acceptance Tests

1. Repeated evidence can create a reviewable preference proposal but not automatic durable truth.
2. Approved long-term memories survive model and runtime changes.
3. Temporary mood and experimentation remain separate from durable identity.
4. Retired preferences are not returned as current.
5. Resident-specific private memories remain correctly scoped.
6. Contradictory evidence produces review state rather than silent overwrite.
7. Character Bible and memory records remain reconcilable and source-lined.

## Deliverables

- long-term personal-memory types and policies;
- promotion, decay, review, and retirement workflows;
- WP-4053 and Character Bible integration;
- privacy and lineage enforcement;
- diagnostics, tests, documentation, and completion receipt.

## Constraints

- Do not create a second preference or personality engine.
- Do not make identity static or rewrite it from isolated turns.
- Do not infer private preferences from suggestive conversation alone.

## Completion Standard

WP-4065 is complete only when each resident can preserve durable personal continuity through governed, source-lined memory; temporary states remain separate; preference evolution reuses existing architecture; and no isolated interaction can silently redefine the resident.