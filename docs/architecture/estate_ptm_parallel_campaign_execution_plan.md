# Estate PTM Parallel Campaign Execution and Midpoint Integration Plan
Generated for WP-0661. This plan supersedes any overly serial reading of the WP-0660 outputs and treats the 28 planning drafts as parallelizable work bounded by contract freezes and midpoint integration gates. It does not authorize production PTM implementation.
## Executive decision
Use a contract-first fan-out model: keep `PTM-00`, `PTM-01`, and the event/projection freeze portions of `PTM-02` on the critical path, then run `PTM-03`, `PTM-04`, `PTM-05`, and early `PTM-07` validation planning concurrently with explicit midpoint integration gates. `PTM-06` joins as soon as file-import and dispatch evidence contracts are stable; rollout remains last.
## Contracts that must freeze before fan-out
- **PTM boundary contract:** `SPEC-PTM-001` must freeze the scope, non-goals, and authority model before any downstream package starts.
- **Adapter inventory contract:** `CORE-PTM-001C` must freeze read-only source categories and adapter names before ledger/schema work mutates its assumptions.
- **Event and ID contract:** `CORE-PTM-002A` and `CORE-PTM-002B` must freeze append-only event semantics, hash-chain expectations, ID minting, and command envelope shape.
- **Projection contract:** `CORE-PTM-003A` and `CORE-PTM-003B` must freeze task, portfolio, schedule, financial, and KPI projection fields before final data binding.
- **Intake/dedupe contract:** `INTAKE-PTM-001A` must freeze the governed intake surface before file import and conversation creation paths complete.
- **Workspace deep-link contract:** `UI-PTM-001A` must freeze route IDs and deep-link targets before compact Office cards or Resident command responses bind to them.

## Parallel execution waves
### Wave 0 — root acceptance
- Packages: `SPEC-PTM-001`
- Parallelism: No parallelism. This is the authority gate.
### Wave 1 — inventory split
- Packages: `CORE-PTM-001A, CORE-PTM-001B → CORE-PTM-001C`
- Parallelism: `CORE-PTM-001A` and `CORE-PTM-001B` run concurrently; `CORE-PTM-001C` integrates both inventories.
### Wave 2 — canonical contract spine
- Packages: `CORE-PTM-002A → CORE-PTM-002B → CORE-PTM-003A → CORE-PTM-003B`
- Parallelism: Mostly serial because these freeze shared schemas. Test-planning stubs may observe but not redefine contracts.
### Wave 3 — first fan-out after projections
- Packages: `INTAKE-PTM-001A, UI-PTM-001A, SCHED-PTM-001A, FIN-PTM-001, TEST-PTM-001A draft prep`
- Parallelism: Run concurrently after projection freeze points are satisfied; midpoint gate reconciles event consumers.
### Wave 4 — second fan-out
- Packages: `INTAKE-PTM-001B, FILE-PTM-001A, UI-PTM-001B, CONV-PTM-001, SCHED-PTM-001B, UTIL-PTM-001, DISPATCH-PTM-001`
- Parallelism: Run in parallel subject to intake, route, and schedule gates. Conflicts are reconciled at Midpoint Integration Gate B.
### Wave 5 — closure fan-out
- Packages: `FILE-PTM-001B, UI-PTM-002, KPI-PTM-001, MIG-PTM-001A, TEST-PTM-001B`
- Parallelism: Run once feeder contracts are stable. Migration execution package waits for migration plan.
### Wave 6 — rollout serialization
- Packages: `MIG-PTM-001B → ROLL-PTM-001A → ROLL-PTM-001B`
- Parallelism: Serial acceptance/rollout chain after validation evidence is complete.
## Campaign concurrency matrix
| Campaign | May execute concurrently with | Must wait for | Midpoint integration requirement |
|---|---|---|---|
| PTM-00 | none | none | Freeze scope and authority. |
| PTM-01 | internal split only | PTM-00 | Merge source inventory into adapter contract. |
| PTM-02 | test-plan observation only | PTM-01 | Freeze event, ID, and projection contracts. |
| PTM-03 | PTM-04, PTM-05, TEST-PTM-001A | CORE-PTM-003A and intake gates | Reconcile intake/file import semantics. |
| PTM-04 | PTM-03, PTM-05, TEST-PTM-001A | CORE-PTM-003A/B and intake for CONV | Reconcile routes, cards, and command links. |
| PTM-05 | PTM-03, PTM-04, PTM-06 planning, TEST-PTM-001A | CORE-PTM-003B | Reconcile schedule, utilization, finance, KPI, and dispatch readiness. |
| PTM-06 | PTM-05 dispatch and PTM-03 file import feeders | FILE-PTM-001B and DISPATCH-PTM-001 for execution | Reconcile migration evidence chain before pilot execution. |
| PTM-07 | TEST-PTM-001A can start in Wave 3; rest waits | All build contracts for formal validation; rollout waits for validation | Validation gate then rollout gate. |

## Package-level launch groups
- `G00`: `SPEC-PTM-001`
- `G01A`: `CORE-PTM-001A`, `CORE-PTM-001B`
- `G01B`: `CORE-PTM-001C`
- `G02A`: `CORE-PTM-002A`
- `G02B`: `CORE-PTM-002B`
- `G02C`: `CORE-PTM-003A`
- `G02D`: `CORE-PTM-003B`
- `G03A`: `INTAKE-PTM-001A`, `FILE-PTM-001A`
- `G03B`: `INTAKE-PTM-001B`
- `G03C`: `FILE-PTM-001B`
- `G04A`: `UI-PTM-001A`
- `G04B`: `UI-PTM-001B`, `CONV-PTM-001`
- `G04C`: `UI-PTM-002`
- `G05A`: `SCHED-PTM-001A`, `FIN-PTM-001`
- `G05B`: `SCHED-PTM-001B`, `UTIL-PTM-001`
- `G05C`: `KPI-PTM-001`
- `G06A`: `DISPATCH-PTM-001`, `MIG-PTM-001A`
- `G06B`: `MIG-PTM-001B`
- `G07A`: `TEST-PTM-001A`
- `G07B`: `TEST-PTM-001B`
- `G07C`: `ROLL-PTM-001A`
- `G07D`: `ROLL-PTM-001B`

## Shared-file and shared-schema conflict controls
| Conflict surface | Affected packages | Control |
|---|---|---|
| Canonical event schema | CORE-PTM-002A/002B, INTAKE, FILE, CONV, DISPATCH | Single owner until Wave 2 freeze; downstream packages submit schema-change requests instead of editing contracts independently. |
| Projection fields | CORE-PTM-003A/003B, UI, SCHED, FIN, KPI, TEST | No final UI/KPI/schedule binding before projection freeze; use named stubs only. |
| Workspace/deep links | UI-PTM-001A/B, UI-PTM-002, CONV | Midpoint route review before Office card and Resident commands merge. |
| Schedule readiness and dispatch evidence | SCHED, UTIL, DISPATCH, MIG, TEST | Schedule gate must publish readiness labels before utilization, dispatch, and migration acceptance. |
| Planning manifests | All promoted packages | Integration owner updates manifests once per checkpoint to avoid divergent campaign membership. |

## Midpoint integration checkpoints
1. **Gate A — after CORE-PTM-001C: inventory and adapter merge.** Confirm manifests, dependencies, shared schemas, and validation evidence before merging the next wave.
2. **Gate B — after CORE-PTM-003B: canonical event/projection freeze and broad fan-out authorization.** Confirm manifests, dependencies, shared schemas, and validation evidence before merging the next wave.
3. **Gate C — after INTAKE-PTM-001B, UI-PTM-001B, SCHED-PTM-001B, FIN-PTM-001: cross-surface consumer reconciliation.** Confirm manifests, dependencies, shared schemas, and validation evidence before merging the next wave.
4. **Gate D — after FILE-PTM-001B, DISPATCH-PTM-001, KPI-PTM-001: migration/validation readiness.** Confirm manifests, dependencies, shared schemas, and validation evidence before merging the next wave.
5. **Gate E — after TEST-PTM-001B: rollout go/no-go.** Confirm manifests, dependencies, shared schemas, and validation evidence before merging the next wave.

## Merge strategy
Maintain one integration branch per wave, with package branches merged only at the named midpoint gates. Merge order is: foundational contract branch, fan-out package branches with no shared-schema deltas, integration-owner manifest/docs update, then validation evidence. Any package that changes a frozen contract must stop, replan, and update the affected dependents before merge.
