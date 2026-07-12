# WP-4063 — Resident Memory Runtime

Status: Pending
Execution Mode: SERIES
Owner: Office of Character Architecture / Resident Runtime Integration
Execution Target: Codex
Classification: Estate Internal
Priority: Immediate

## Depends On

- WP-4043 — Resident Runtime Identity Composition
- WP-4046 — Grounded Estate Fact Provider
- WP-4047 — Resident Conversation Isolation
- WP-4051 — Resident Relationship Graph Runtime
- WP-4053 — Dynamic Resident Preference and Personality Evolution

## Objective

Implement one canonical resident-memory runtime that distinguishes temporary conversation context, durable personal memory, shared institutional memory, relationship continuity, and proposed character growth without promoting model improvisation into Estate truth.

## Required Work

1. Inspect existing continuity, preference, relationship, message, registry, identity, and fact artifacts before creating structures.
2. Define a typed memory record containing subject, memory class, content, source lineage, evidence, classification, confidence, timestamps, retention, review state, and disclosure scope.
3. Provide explicit write, read, query, supersede, retire, and correction operations through governed interfaces.
4. Require evidence and policy checks before durable promotion.
5. Integrate bounded memory retrieval into the identity composer after privacy and session scope are resolved.
6. Keep provider/model memory, hidden reasoning, and raw transcript accumulation outside canonical memory.
7. Support resident-specific and shared institutional scopes without creating duplicate stores.
8. Expose diagnostics for contradictions, stale records, orphaned subjects, privacy conflicts, and unsupported claims.

## Acceptance Tests

1. A conversation detail remains temporary until a governed promotion occurs.
2. Durable memories retain source lineage and survive provider changes.
3. Private Evelyn memories never appear in shared or conference-room context.
4. Contradictory durable records fail visibly.
5. Memory correction preserves audit history.
6. Unknown memories remain unknown rather than fabricated.
7. Retrieval is bounded and relevant to the active resident, user, surface, and session.

## Deliverables

- canonical memory schema and service;
- governed promotion and correction workflow;
- identity-composer and relationship integration;
- privacy-filtered retrieval;
- diagnostics, tests, documentation, and completion receipt.

## Constraints

- Do not create a second identity, preference, relationship, registry, or fact system.
- Do not store hidden reasoning or unrestricted transcripts.
- Do not let one improvised turn rewrite durable identity.

## Completion Standard

WP-4063 is complete only when residents can retrieve and maintain source-lined, privacy-scoped durable memory through one governed runtime; temporary context remains separate; corrections and contradictions are inspectable; and model behavior cannot silently create Estate truth.