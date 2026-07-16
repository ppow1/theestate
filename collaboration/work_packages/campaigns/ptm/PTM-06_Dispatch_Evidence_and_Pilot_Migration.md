# PTM-06 — Dispatch evidence and pilot migration

## Campaign status and authority basis
Executable campaign handoff. Authority comes from `docs/architecture/estate_ptm_specification_acceptance.md` and the WP-0661 parallel execution model. Execution lane is Codex only.

## Included Pending work-package paths
- `collaboration/work_packages/pending/DISPATCH-PTM-001_Task_to_dispatch_evidence_chain_contract.md`
- `collaboration/work_packages/pending/MIG-PTM-001A_Pilot_migration_source_slice_plan.md`
- `collaboration/work_packages/pending/MIG-PTM-001B_Pilot_migration_execution_package_draft.md`

## Exact package launch order
1. `DISPATCH-PTM-001` — `collaboration/work_packages/pending/DISPATCH-PTM-001_Task_to_dispatch_evidence_chain_contract.md`
2. `MIG-PTM-001A` — `collaboration/work_packages/pending/MIG-PTM-001A_Pilot_migration_source_slice_plan.md`
3. `MIG-PTM-001B` — `collaboration/work_packages/pending/MIG-PTM-001B_Pilot_migration_execution_package_draft.md`

## Package groups that may run simultaneously
- `G06A`: `DISPATCH-PTM-001`, `MIG-PTM-001A`
- `G06B`: `MIG-PTM-001B`

## Packages that must remain serial
Packages with direct dependencies in this campaign must remain serial: `DISPATCH-PTM-001`, `MIG-PTM-001A`, `MIG-PTM-001B`.

## Prerequisite campaigns and package gates
- Prerequisite campaigns: `PTM-05`
- Package dependencies are controlled by `collaboration/work_packages/planning/estate_ptm_dependency_manifest.json`.

## Contract-freeze requirements
Honor WP-0661 contract freezes. Downstream packages must not redefine frozen event, ID, projection, intake, route, schedule, dispatch, or validation contracts.

## Branch naming guidance
Use `codex/ptm-06-<package-id-or-campaign-slice>` for package branches and `integration/ptm-06-checkpoint` for checkpoint reconciliation.

## Integration branch or checkpoint requirements
Checkpoint: Gate D — migration/dispatch readiness. Use one integration branch per wave and reconcile manifests/evidence once at the checkpoint.

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
codex exec "Read collaboration/work_packages/campaigns/ptm/PTM-06_Dispatch_Evidence_and_Pilot_Migration.md and execute the included Pending work packages exactly as instructed."
```
