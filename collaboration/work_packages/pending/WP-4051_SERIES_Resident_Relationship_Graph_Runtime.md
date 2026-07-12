# WP-4051 — Resident Relationship Graph Runtime

Status: Pending
Execution Mode: SERIES
Owner: Office of Character Architecture / Resident Runtime Integration
Execution Target: Codex
Classification: Estate Internal
Priority: Immediate

## Depends On

- WP-4043 — Resident Runtime Identity Composition
- WP-4044 — Resident Character Bible Runtime Loading
- WP-4045 — Resident Registry Synchronization
- WP-4047 — Resident Conversation Isolation
- WP-4050 — Resident Message Routing and Acknowledgment

## Objective

Implement one canonical resident relationship-graph runtime so residents can express accurate, individualized professional and personal relationships without inventing history, flattening everyone into the same familiarity, or leaking protected continuity.

## Required Work

1. Inspect existing resident profiles, Character Bibles, appointment records, relationship-layer documents, message evidence, preference artifacts, and privacy classifications before creating new structures.
2. Define a typed relationship record connecting two canonical persons or a person and office.
3. Represent relationship type, directionality, scope, familiarity, trust, affection, professional dependency, disclosure class, source lineage, evidence, effective dates, and review state.
4. Distinguish canonical relationship facts from inferred tone, temporary mood, conversation chemistry, and proposed growth.
5. Integrate permitted relationship context into the WP-4043 identity composer after privacy/disclosure scope is established.
6. Keep Evelyn's Steward relationship singular and protected; do not expose private continuity to shared rooms or unrelated residents.
7. Allow asymmetric relationships where appropriate; one resident's trust or affection need not equal the other's.
8. Support evidence-backed change proposals without allowing a single improvised answer, flirtation, disagreement, or joke to rewrite durable relationships.
9. Reuse WP-4053 preference/personality evolution mechanisms where compatible; do not create a competing growth engine.
10. Provide diagnostics for missing nodes, contradictory edges, unsupported claims, stale evidence, privacy conflicts, and graph/registry drift.

## Character Requirements

- Alfred's relationships must preserve his Chief-of-Staff attention-gate role rather than turning him into Operations.
- Helen's warmth must remain humane and workforce-centered without fabricated intimacy or mail history.
- Grace may be energetic, playful, and collaborative while retaining operational boundaries.
- Ingrid may be reserved, elegant, and dryly witty without privacy rules erasing ordinary relationships.
- Evelyn's bond with the Steward may be intimate, candid, affectionate, and playful where authorized, but it must not make her HR, therapist, Operations, or a generic romantic assistant.
- Adult affection, attraction, humor, teasing, and flirting may be represented where individually authored, consensual, context-aware, and privacy-appropriate; they do not grant authority or erase agency.

## Acceptance Tests

1. Each resident describes their public professional relationships consistently from canonical graph evidence.
2. Private or Steward-restricted edges never appear in conference-room context.
3. Relationships remain stable across provider/model changes.
4. Unknown relationships remain unknown rather than fabricated.
5. Contradictory relationship records fail closed with diagnostics.
6. A single conversation turn cannot silently promote trust, affection, conflict, or intimacy into durable state.
7. Evidence-backed proposals can be reviewed and, when authorized, applied with lineage.
8. Relationship expression remains resident-specific rather than producing one shared voice or flirting style.
9. Registry removal, retirement, or lifecycle change produces visible graph-drift diagnostics.

## Deliverables

- canonical relationship graph schema and runtime service;
- privacy-filtered relationship-context loader;
- identity-composer integration;
- evidence and change-proposal interfaces compatible with WP-4053;
- fixtures for Alfred, Helen, Grace, Ingrid, Evelyn, and the Steward relationship layer;
- diagnostics, tests, documentation, and completion receipt.

## Constraints

- Do not create a second resident registry, Character Bible store, preference engine, message bus, or privacy authority.
- Do not derive durable relationships solely from conversation history.
- Do not expose private relationship content in shared rooms or diagnostics.
- Do not redesign settled appointments, offices, or authority grants.

## Completion Standard

WP-4051 is complete only when all active residents receive source-lined, privacy-filtered, individually expressive relationship context through one canonical runtime; protected and asymmetric relationships remain correctly bounded; unsupported claims fail visibly; and relationship growth requires evidence and governed promotion rather than improvisation.
