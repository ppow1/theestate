# WP-4066 — Shared Institutional Memory

Status: Pending
Execution Mode: SERIES
Owner: Office of Character Architecture / Resident Runtime Integration
Execution Target: Codex
Classification: Estate Internal
Priority: Immediate

## Depends On

- WP-4063 — Resident Memory Runtime
- WP-4045 — Resident Registry Synchronization
- WP-4046 — Grounded Estate Fact Provider
- WP-4048 through WP-4050 — Canonical Messaging and Mailbox Runtime

## Objective

Implement shared institutional memory so residents can recall authorized Estate events, decisions, lessons, and operating context from canonical evidence without using private personal memory or conversation recollection as organizational truth.

## Required Work

1. Define institutional-memory records for decisions, lessons learned, milestones, incidents, conventions, and accepted operating context.
2. Require canonical source evidence such as governance, accepted decisions, messages, receipts, validation, activation records, or approved reports.
3. Distinguish current policy, historical practice, superseded decision, unresolved proposal, and inferred lesson.
4. Integrate with the grounded fact provider so current facts remain separate from retained institutional lessons.
5. Apply classification and need-to-know filtering before shared retrieval.
6. Provide deterministic indexes and rebuild procedures from canonical records.
7. Support correction, supersession, and conflict diagnostics without deleting audit lineage.
8. Keep resident-specific private continuity outside shared institutional memory.

## Acceptance Tests

1. Accepted decisions become retrievable with source lineage.
2. Historical or superseded practice is labeled correctly.
3. Private resident memories never appear in institutional retrieval.
4. Missing evidence remains unknown.
5. Contradictory authoritative sources fail visibly.
6. Rebuilding derived indexes produces deterministic results.
7. Conference-room participants receive the same authorized institutional memory.

## Deliverables

- institutional-memory schema and service;
- canonical-source adapters and deterministic indexes;
- fact-provider and conference-room integration;
- privacy and classification enforcement;
- diagnostics, tests, documentation, and completion receipt.

## Constraints

- Do not create a second governance registry, fact provider, or message store.
- Do not promote conversation recollection into institutional truth.
- Do not flatten historical and current states.

## Completion Standard

WP-4066 is complete only when authorized residents can retrieve consistent, source-lined institutional decisions, lessons, and history; current facts remain distinct; private continuity remains excluded; and superseded, conflicting, or uncertain records are labeled rather than silently normalized.