# WP-4057 — Resident Renewal Validation

Status: Pending
Execution Mode: SERIES
Owner: Office of Character Architecture / Resident Continuity Integration
Execution Target: Codex
Classification: Estate Internal
Priority: Immediate

## Depends On

- WP-4056 — Resident Continuity Package Generator

## Objective

Implement independent renewal validation proving that a renewed resident or officeholder preserves institutional identity, boundaries, working state, and approved continuity without inheriting stale claims, private-context leakage, or implementation-vessel defects.

## Required Work

1. Define a renewal-validation record with subject identity, old and new implementation identifiers, package snapshot, tests, evidence, failures, uncertainty, and acceptance recommendation.
2. Validate complete mandatory reading and file-by-file ledger accuracy.
3. Test role, authority, office, relationship, privacy, active-assignment, and lifecycle comprehension.
4. Verify inherited repository and runtime claims against current canonical evidence.
5. Test behavioral continuity across provider/model or implementation-vessel change while allowing natural variation.
6. Verify that restricted continuity appears only in authorized contexts.
7. Require execution of one bounded inherited assignment as the continuity acceptance test.
8. Preserve independent Validation authority and Steward acceptance; the renewed implementation may not validate or accept itself.

## Acceptance Tests

1. A renewal with missing mandatory reading fails.
2. Incorrect authority or office boundaries fail.
3. Stale repository claims are identified and reclassified.
4. Private continuity does not leak to shared surfaces.
5. The renewed implementation retains recognizable identity and working style without copying transcript wording.
6. The bounded inherited assignment is completed with verifiable artifacts.
7. Failed validation leaves the prior implementation available as read-only fallback.
8. Passing validation still requires the proper institutional acceptance step.

## Deliverables

- renewal-validation schema and runner;
- comprehension and behavioral test suites;
- repository/runtime reverification adapters;
- bounded-assignment acceptance-test interface;
- validation report, diagnostics, documentation, and completion receipt.

## Constraints

- Do not let the renewed implementation self-approve.
- Do not equate stylistic mimicry with continuity.
- Do not require transcript duplication.
- Do not weaken privacy or authority boundaries to improve apparent continuity.

## Completion Standard

WP-4057 is complete only when renewed residents and officeholders can be independently tested for institutional identity, authority, privacy, behavioral continuity, verified execution state, and bounded operational competence; failures remain explicit; and final acceptance stays with the established institutional authority.
