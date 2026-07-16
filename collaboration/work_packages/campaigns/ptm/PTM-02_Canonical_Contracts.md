# PTM-02 — Canonical ledger and projection contracts

## Campaign status and authority basis
Executable campaign handoff. Authority comes from `docs/architecture/estate_ptm_specification_acceptance.md` and the WP-0661 parallel execution model. Execution lane is Codex only.

## Included Pending work-package paths
- `collaboration/work_packages/pending/CORE-PTM-002A_Define_append_only_event_schema_and_hash_chain.md`
- `collaboration/work_packages/pending/CORE-PTM-002B_Define_PTM_ID_minting_and_command_contracts.md`
- `collaboration/work_packages/pending/CORE-PTM-003A_Project_task_and_portfolio_projection_contracts.md`
- `collaboration/work_packages/pending/CORE-PTM-003B_Schedule_financial_KPI_projection_contracts.md`

## Exact package launch order
1. `CORE-PTM-002A` — `collaboration/work_packages/pending/CORE-PTM-002A_Define_append_only_event_schema_and_hash_chain.md`
2. `CORE-PTM-002B` — `collaboration/work_packages/pending/CORE-PTM-002B_Define_PTM_ID_minting_and_command_contracts.md`
3. `CORE-PTM-003A` — `collaboration/work_packages/pending/CORE-PTM-003A_Project_task_and_portfolio_projection_contracts.md`
4. `CORE-PTM-003B` — `collaboration/work_packages/pending/CORE-PTM-003B_Schedule_financial_KPI_projection_contracts.md`

## Package groups that may run simultaneously
- `G02A`: `CORE-PTM-002A`
- `G02B`: `CORE-PTM-002B`
- `G02C`: `CORE-PTM-003A`
- `G02D`: `CORE-PTM-003B`

## Packages that must remain serial
Packages with direct dependencies in this campaign must remain serial: `CORE-PTM-002A`, `CORE-PTM-002B`, `CORE-PTM-003A`, `CORE-PTM-003B`.

## Prerequisite campaigns and package gates
- Prerequisite campaigns: `PTM-01`
- Package dependencies are controlled by `collaboration/work_packages/planning/estate_ptm_dependency_manifest.json`.

## Contract-freeze requirements
Honor WP-0661 contract freezes. Downstream packages must not redefine frozen event, ID, projection, intake, route, schedule, dispatch, or validation contracts.

## Branch naming guidance
Use `codex/ptm-02-<package-id-or-campaign-slice>` for package branches and `integration/ptm-02-checkpoint` for checkpoint reconciliation.

## Integration branch or checkpoint requirements
Checkpoint: Gate B — canonical event/projection freeze. Use one integration branch per wave and reconcile manifests/evidence once at the checkpoint.

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
codex exec "Read collaboration/work_packages/campaigns/ptm/PTM-02_Canonical_Contracts.md and execute the included Pending work packages exactly as instructed."
```
