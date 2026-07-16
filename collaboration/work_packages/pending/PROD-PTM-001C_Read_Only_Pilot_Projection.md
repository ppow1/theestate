# PROD-PTM-001C — Read-only pilot projection

Status: Pending Gate PTM-PROD-G1  
Owner: Chief Architect  
Execution lane: Codex  
Campaign: PTM-PROD-01  
Depends on: PROD-PTM-001A

## Objective

Implement the smallest safe, ephemeral PTM projection pilot over selected source
records and emit a reviewer-readable report with complete provenance.

## Scope

- Project one portfolio, five selected intake/Parking Lot items, two existing
  work packages, one Dispatch evidence chain, one validation result, and one
  acceptance reference where repository-safe fixtures or records exist.
- Calculate only cycle time, audit completeness, and blocked duration, with
  unknown/stale inputs remaining explicitly unknown.
- Rebuild from adapters on demand; do not persist a Phase 2 canonical event log.
- Provide a CLI or existing service entry seam only after confirming it does not
  create a second command surface.
- Emit normalized machine-readable output and a concise reviewer report; protect
  private payloads and include source references/hashes.

## Validation and acceptance

- repeated rebuild equivalence;
- field-level provenance and warning coverage;
- stale/missing/conflicting-source fail-closed tests;
- security and read-only instrumentation evidence;
- targeted and existing regression tests plus `git diff --check`;
- completion receipt distinguishing implementation completion, merge review,
  Gate G2 decision, and institutional acceptance.

## Non-goals and delivery

No source mutation, canonical ledger, workspace UI, dispatch action, rollout, or
acceptance inference. Open a PR for Chief Architect review. Gate G2 remains
pending until PROD-PTM-001B is integrated and all campaign evidence is reviewed.
