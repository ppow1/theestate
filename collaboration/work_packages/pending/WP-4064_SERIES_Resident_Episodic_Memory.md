# WP-4064 — Resident Episodic Memory

Status: Pending
Execution Mode: SERIES
Owner: Office of Character Architecture / Resident Runtime Integration
Execution Target: Codex
Classification: Estate Internal
Priority: Immediate

## Depends On

- WP-4063 — Resident Memory Runtime

## Objective

Implement episodic memory so residents can retain bounded, evidence-backed experiences as events with participants, time, place, context, emotional significance, and outcome without converting whole transcripts into memory.

## Required Work

1. Define a typed episode record with canonical participants, event time, source evidence, summary, significance, disclosure scope, and review state.
2. Create deterministic episode extraction from approved messages, appointments, actions, and explicitly promoted conversation events.
3. Preserve the difference between what happened, what a resident felt, what was inferred, and what remains uncertain.
4. Support private, resident-specific, shared, and institutional episodes with Ingrid-governed filtering.
5. Link episodes to relationships and preferences without silently changing either.
6. Support correction, supersession, retirement, and conflicting-evidence diagnostics.
7. Retrieve only bounded relevant episodes for the active resident and context.

## Acceptance Tests

1. A verified event creates one source-lined episode.
2. Raw transcript text is not stored as the episode by default.
3. Different participants may retain distinct perspectives without changing the verified event facts.
4. Private episodes do not leak to shared rooms.
5. Conflicting event evidence produces diagnostics.
6. Retired or corrected episodes retain audit lineage.
7. Provider changes do not erase approved episodes.

## Deliverables

- episodic-memory schema and service;
- approved extraction and promotion adapters;
- relationship and preference links;
- privacy-filtered retrieval;
- diagnostics, tests, documentation, and completion receipt.

## Constraints

- Do not treat all conversation as memorable.
- Do not fabricate emotional significance or participant knowledge.
- Do not replace canonical messages, calendars, or action receipts.

## Completion Standard

WP-4064 is complete only when residents can retain and retrieve bounded, source-lined episodes with accurate participants, perspective, uncertainty, and privacy; transcripts remain noncanonical; and corrections or conflicts remain visible.