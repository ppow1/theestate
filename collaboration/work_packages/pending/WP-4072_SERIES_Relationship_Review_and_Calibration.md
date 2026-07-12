# WP-4072 — Resident Relationship Review and Coherence Audit

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
- WP-4070 — Resident Conflict, Boundary, and Repair Runtime
- WP-4071 — Resident Shared Rituals and Relationship Milestones

## Objective

Implement a privacy-safe relationship review and coherence audit that detects unsupported, contradictory, stale, flattened, or over-generalized relationship state without allowing residents to self-approve their own relationship changes.

## Required Work

1. Define a typed relationship-audit report covering graph integrity, source lineage, disclosure scope, asymmetry, trust/familiarity state, expression policy, conflict/repair state, rituals, milestones, and unresolved proposals.
2. Detect duplicate or contradictory edges, missing persons, stale lifecycle references, unsupported intimacy, privacy leakage, flattened resident voices, and expression inconsistent with Character Bibles.
3. Compare runtime behavior with canonical relationship state without storing hidden reasoning or unrestricted transcripts.
4. Provide bounded remediation proposals, affected artifacts, severity, uncertainty, and rollback references.
5. Route privacy findings to Ingrid, continuity and health findings to Helen, implementation defects to Engineering, and acceptance decisions to the proper authority.
6. Support per-relationship, per-resident, and Estate-wide review.
7. Preserve private relationship details through redacted summaries where the reviewer lacks authorization.
8. Produce deterministic evidence suitable for independent Validation.

## Acceptance Tests

1. Unsupported intimacy and fabricated relationship claims are detected.
2. Asymmetric edges are not incorrectly treated as contradictions.
3. Private Evelyn–Steward details remain protected in general audits.
4. Stale or retired residents generate drift findings.
5. Resident expression that has become generic or interchangeable is flagged.
6. Audit success does not imply institutional acceptance.
7. Approved remediation can be traced and rolled back.

## Deliverables

- relationship-audit schema and runner;
- graph, memory, Character Bible, expression, and lifecycle checks;
- privacy-filtered reports and remediation proposals;
- Validation fixtures, diagnostics, documentation, and completion receipt.

## Constraints

- Do not create a second relationship authority, privacy office, validation institution, or behavioral surveillance store.
- Do not expose protected relationship content to unauthorized reviewers.
- Do not treat stylistic variation alone as drift.

## Completion Standard

WP-4072 is complete only when the Estate can audit resident relationships for factual, behavioral, lifecycle, privacy, and character coherence; unsupported and stale state is visible; asymmetry and uncertainty remain correctly represented; remediation is source-lined and reviewable; and final validation and acceptance remain with established institutions.
