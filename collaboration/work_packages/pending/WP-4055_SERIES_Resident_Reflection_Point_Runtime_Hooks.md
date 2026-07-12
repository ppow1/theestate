# WP-4055 — Resident Reflection Point Runtime Hooks

Status: Pending
Execution Mode: SERIES
Owner: Office of Character Architecture / Resident Continuity Integration
Execution Target: Codex
Classification: Estate Internal
Priority: Immediate

## Depends On

- WP-4047 — Resident Conversation Isolation
- WP-4051 — Resident Relationship Graph Runtime
- WP-4054 — Multi-Resident Turn Management

## Objective

Add governed runtime hooks that detect and prepare resident and officeholder Reflection Points without treating transcript accumulation as continuity or allowing an implementation vessel to redefine institutional identity.

## Required Work

1. Implement bounded health signals for context congestion, latency, repeated failure, identity drift, hallucination pressure, tool stalls, and renewal readiness.
2. Distinguish represented resident health from implementation-vessel health.
3. Emit a structured Reflection Point recommendation with evidence, severity, source timestamps, and unresolved uncertainty.
4. Capture bounded continuity candidates from canonical identity, facts, relationships, active assignments, and verified execution state.
5. Exclude hidden chain-of-thought, unrestricted transcripts, secrets, and unrelated private context.
6. Require Helen-owned continuity review and Steward initiation/acceptance where governance requires it.
7. Preserve the old implementation as read-only fallback evidence until renewed continuity is validated.
8. Expose diagnostics without allowing the hook to initiate renewal or grant authority by itself.

## Acceptance Tests

1. Congestion and repeated failures produce evidence-backed recommendations.
2. Healthy implementations do not trigger renewal merely because they are old.
3. Identity remains stable when a provider or implementation vessel changes.
4. Private Evelyn continuity is handled under its stricter disclosure scope.
5. Conversation history is not promoted wholesale into continuity.
6. Missing evidence yields uncertainty rather than a confident recommendation.
7. The hook cannot appoint, renew, accept, or retire an officeholder autonomously.

## Deliverables

- Reflection Point signal schema;
- runtime health collector and recommendation engine;
- bounded continuity-candidate interface;
- Helen/Steward review integration points;
- diagnostics, tests, documentation, and completion receipt.

## Constraints

- Do not create a second continuity authority or personnel office.
- Do not preserve hidden reasoning or unrestricted transcripts.
- Do not confuse implementation health with resident identity.

## Completion Standard

WP-4055 is complete only when resident and officeholder runtimes can produce evidence-backed, bounded Reflection Point recommendations and continuity candidates while preserving governance, privacy, identity, and the distinction between an institutional person and the implementation vessel serving that person.
