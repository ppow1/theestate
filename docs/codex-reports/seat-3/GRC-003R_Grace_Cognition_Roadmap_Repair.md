# GRC-003R — Grace Cognition Roadmap Repair

Package: GRC-003R  
Role: C3 — targeted roadmap repair  
Date: 2026-08-25  
Source roadmap: docs/codex-reports/seat-3/GRC-003_Grace_Cognition_Implementation_Decomposition.md  
Validation report used: docs/codex-reports/seat-2/GRC-003V_Grace_Cognition_Roadmap_Validation.md

## Repair status

REPAIR_COMPLETE_READY_FOR_GRC-004

This was a documentation-only targeted repair. The accepted GRC-002
architecture was not reopened and no alternate architecture was introduced.

## Exact corrections made

### 1. F4 dependency/concurrency correction

Changed GRC-003 section 4.2 so F1, F2, and F3 may have non-dependent
preparation in parallel, while F4 is explicitly a dependent package.

The roadmap now states that:

- F1 is the predecessor contract for F4;
- F4 implementation must not be built against an unfrozen F1 contract;
- F4 implementation acceptance waits for accepted F1;
- only useful non-dependent scaffolding may proceed in parallel.

No other F1/F4 package design content was changed.

### 2. E3 alternate-path dependency correction

Changed GRC-003 section 4.1 and the E3 package card so E3 depends on accepted
F1, F2, F4, P1, and P2 contracts rather than completed E2 runtime
implementation.

The roadmap now states that:

- E2 and E3 are parallel alternate execution paths after common contracts;
- E3 may reuse common/E2-compatible result-envelope shapes;
- completed E2 runtime implementation is not an E3 prerequisite;
- E4 integrates accepted high and external result forms without requiring one
  operational path to precede the other.

The existing no-silent-fallback, explicit escalation, advisory authority,
classification/egress, provenance, and correlation requirements remain
unchanged.

### 3. Acceptance test-field label correction

Renamed the package-card field in GRC-003-A2 and GRC-003-A3 from:

Tests/scenarios required

to:

Tests required

The existing acceptance scenario content was retained without substantive
change.

## Dependency graph after repair

The repaired graph is:

- F1 -> F4.
- F1/F2/F4/P1/P2 -> E3.
- F1/F2/F4/P1/P2 -> E2.
- E2 and E3 are parallel alternate execution paths after common prerequisites.
- E4 depends on accepted E2 and E3 result forms, plus F3/F4, and integrates
  both without operational precedence between E2 and E3.
- E4 -> E5.
- F2/E1/E2/E4 -> I1.
- E1/E2/E3/P3/I1 -> I2.
- A1 follows the implementation packages; A2 follows A1 and approved
  provider/resource configuration; A3 follows A2, P3, and I1.

No circular dependency was introduced.

## Scope confirmation

- No runtime code changed.
- No migration was created.
- No model was selected.
- No GPU assignment was made.
- No routing or CME behavior was implemented or changed.
- No unrelated roadmap content was changed.

The only roadmap edits are the three corrections requested by GRC-003V:
F4 concurrency/dependency wording, E3/E4 dependency wording, and A2/A3 test
field labels.
