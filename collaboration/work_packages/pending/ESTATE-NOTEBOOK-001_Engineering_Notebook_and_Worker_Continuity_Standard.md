# ESTATE-NOTEBOOK-001 — Engineering Notebook and Worker Continuity Standard

Status: Draft implementation package
Owner: Engineering, under Steward authority
Scope: verified bounded working state for active assignments

## Mission

Provide a compact, source-bound notebook that lets a fresh worker resume the
current bounded stage without replaying a full transcript. The notebook is a
projection, not repository canon, authority, a registry, memory diary, PTM,
Dispatch, receipt, or reconciliation system.

## Required reading and boundaries

The Worker Runtime Contract, Instruction Precedence, Skills, Help, capability,
PTM, Dispatch, receipt, and reconciliation surfaces remain authoritative. This
package does not add authority, model onboarding, institutional acceptance,
network permission, merge permission, destructive permission, or secret storage.

## Deliverables

- four closed versioned schemas under `schemas/notebook/`;
- bounded runtime under `src/estate/core/engineering_notebook.py`;
- lifecycle, integration, operator, recovery, anti-pattern, and readiness docs;
- isolated three-stage proof under `experiments/engineering_notebook_001/`;
- focused tests and acceptance evidence.

## Acceptance

The package must reject unsafe paths, missing authority, stale/conflicted source
digests, false completion, scope-widening updates, secret-like values, and
worker acknowledgments that do not match the verified packet. It must prove
fresh-session stage continuation, truthful notebook updates, stale detection,
fixture integrity, and no institutional-acceptance change.
