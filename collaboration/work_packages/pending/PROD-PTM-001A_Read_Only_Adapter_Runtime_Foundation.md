# PROD-PTM-001A — Read-only adapter runtime foundation

Status: Pending Gate PTM-PROD-G0  
Owner: Chief Architect  
Execution lane: Codex  
Campaign: PTM-PROD-01

## Objective

Implement the shared, production-quality read-only adapter boundary and a bounded
pilot set of adapters over existing PTM source domains without mutating them or
creating another source of truth.

## Required inputs

- `collaboration/reports/project_management/WP-0677_ptm_transition_baseline.md`
- `docs/architecture/estate_ptm_read_only_source_inventory_and_adapter_contracts.md`
- `docs/architecture/estate_project_task_management_implementation_roadmap.md`
- the current source inventory and canonical mechanisms named by those contracts

## Implementation scope

- Place reusable runtime code in the existing `src/estate` package hierarchy
  after confirming the nearest canonical seam; do not create a parallel service.
- Implement the frozen adapter result envelope, source references, hashes,
  warnings, freshness, and explicit unavailable/conflict states.
- Implement bounded adapters sufficient for the recommended pilot: selected
  Parking Lot/work-package records, one Dispatch evidence chain, validation, and
  acceptance references.
- Enforce repository-root path containment, allowlisted inputs, bounded reads,
  stable ordering, and read-only file access.
- Add unit tests proving that adapter execution does not write sources.

## Non-goals

No event ledger, command handling, source write-back, scheduling, UI, migration,
deployment, second registry/queue/scheduler/validator, or inferred acceptance.

## Acceptance evidence

- contract tests cover valid, missing, malformed, conflicting, stale, escaping,
  and oversized inputs;
- two identical source snapshots produce identical normalized results;
- every returned value carries source provenance or an explicit warning;
- existing tests plus targeted tests pass; `git diff --check` passes;
- a completion receipt records exact commands, results, changed seams, and the
  Gate G1 interface freeze.

## Delivery

Open a PR for Chief Architect review. Do not merge or mark Gate G1 complete
without the protected review action.
