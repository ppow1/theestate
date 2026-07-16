# PTM-05 — Scheduling utilization financials and KPIs

## Campaign status and authority basis
Executable campaign handoff. Authority comes from `docs/architecture/estate_ptm_specification_acceptance.md` and the WP-0661 parallel execution model. Execution lane is Codex only.

## Included Pending work-package paths
- `collaboration/work_packages/pending/SCHED-PTM-001A_Schedule_dependency_and_readiness_gate_contract.md`
- `collaboration/work_packages/pending/SCHED-PTM-001B_Schedule_validation_fixture_and_critical_path_plan.md`
- `collaboration/work_packages/pending/UTIL-PTM-001_Capacity_and_utilization_observation_contract.md`
- `collaboration/work_packages/pending/FIN-PTM-001_Budget_cost_approval_and_reconciliation_contract.md`
- `collaboration/work_packages/pending/KPI-PTM-001_KPI_registry_quality_and_dashboard_contract.md`

## Exact package launch order
1. `SCHED-PTM-001A` — `collaboration/work_packages/pending/SCHED-PTM-001A_Schedule_dependency_and_readiness_gate_contract.md`
2. `SCHED-PTM-001B` — `collaboration/work_packages/pending/SCHED-PTM-001B_Schedule_validation_fixture_and_critical_path_plan.md`
3. `UTIL-PTM-001` — `collaboration/work_packages/pending/UTIL-PTM-001_Capacity_and_utilization_observation_contract.md`
4. `FIN-PTM-001` — `collaboration/work_packages/pending/FIN-PTM-001_Budget_cost_approval_and_reconciliation_contract.md`
5. `KPI-PTM-001` — `collaboration/work_packages/pending/KPI-PTM-001_KPI_registry_quality_and_dashboard_contract.md`

## Package groups that may run simultaneously
- `G05A`: `SCHED-PTM-001A`, `FIN-PTM-001`
- `G05B`: `SCHED-PTM-001B`, `UTIL-PTM-001`
- `G05C`: `KPI-PTM-001`

## Packages that must remain serial
Packages with direct dependencies in this campaign must remain serial: `SCHED-PTM-001A`, `SCHED-PTM-001B`, `UTIL-PTM-001`, `FIN-PTM-001`, `KPI-PTM-001`.

## Prerequisite campaigns and package gates
- Prerequisite campaigns: `PTM-04`
- Package dependencies are controlled by `collaboration/work_packages/planning/estate_ptm_dependency_manifest.json`.

## Contract-freeze requirements
Honor WP-0661 contract freezes. Downstream packages must not redefine frozen event, ID, projection, intake, route, schedule, dispatch, or validation contracts.

## Branch naming guidance
Use `codex/ptm-05-<package-id-or-campaign-slice>` for package branches and `integration/ptm-05-checkpoint` for checkpoint reconciliation.

## Integration branch or checkpoint requirements
Checkpoint: Gate C/D — schedule/finance/KPI reconciliation. Use one integration branch per wave and reconcile manifests/evidence once at the checkpoint.

## Merge order
Merge prerequisite campaign PRs first, then package PRs without shared-schema deltas, then checkpoint manifest/evidence updates. Do not merge implementation PRs without Chief Architect review.

## Validation required before the next fan-out or final integration
- `git diff --check`
- Verify every included package has a completion receipt.
- Verify no local-worker routing, second queue, second registry, second scheduler, or new governance authority was introduced.

## Stop/replan conditions
- dependency failure
- shared-file collision
- estimate exceeds 60 active minutes
- new governance authority required
- Any need to change a frozen upstream contract.

## Exact Codex handoff command
```bash
codex exec "Read collaboration/work_packages/campaigns/ptm/PTM-05_Scheduling_Utilization_Financials_and_KPIs.md and execute the included Pending work packages exactly as instructed."
```
