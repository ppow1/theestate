# WP-4098 — Resident Experience Ledger

**Mode:** SERIES

## Objective
Create the canonical append-only ledger for meaningful resident experiences so later growth, memory, relationship, confidence, and milestone systems can cite evidence rather than invent development.

## Dependencies
- WP-4063 through WP-4067 memory architecture
- WP-4068 through WP-4072 relationship maturation
- WP-4093 through WP-4097 affinity runtime

## Required Work
1. Define a versioned experience-event schema containing resident ID, event ID, occurred-at time, recorded-at time, source references, participants, domains, significance, privacy class, confidence, and supersession metadata.
2. Implement deterministic append, read, filter, and provenance APIs.
3. Separate witnessed facts, resident interpretations, Steward-reported events, and inferred effects.
4. Prevent silent mutation or deletion; corrections must supersede prior records while preserving history.
5. Provide idempotency keys and duplicate-event detection.
6. Add retention and disclosure rules compatible with private resident memory and institutional records.
7. Integrate with episodic memory without making the ledger a second memory authority.
8. Emit diagnostics for malformed, orphaned, contradictory, or unsupported entries.

## Non-Goals
- Do not assign personality changes directly.
- Do not turn every interaction into a meaningful experience.
- Do not expose private events across residents or surfaces without authorization.

## Validation
- Schema validation and migration tests.
- Idempotent append tests.
- Supersession and provenance tests.
- Privacy-boundary tests.
- Deterministic filtering and ordering tests.

## Completion Standard
The Estate has one auditable, privacy-aware experience ledger that records meaningful evidence for resident development without rewriting history or duplicating memory authority.
