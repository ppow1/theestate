# PTM-04 — Visibility and command surfaces

## Campaign status and authority basis
Executable campaign handoff. Authority comes from `docs/architecture/estate_ptm_specification_acceptance.md` and the WP-0661 parallel execution model. Execution lane is Codex only.

## Included Pending work-package paths
- `collaboration/work_packages/pending/UI-PTM-001A_Workspace_information_architecture_shell.md`
- `collaboration/work_packages/pending/UI-PTM-001B_Workspace_data_binding_and_navigation_contract.md`
- `collaboration/work_packages/pending/UI-PTM-002_Office_compact_card_and_deep_link_contract.md`
- `collaboration/work_packages/pending/CONV-PTM-001_Resident_governed_PTM_command_contract.md`

## Exact package launch order
1. `UI-PTM-001A` — `collaboration/work_packages/pending/UI-PTM-001A_Workspace_information_architecture_shell.md`
2. `UI-PTM-001B` — `collaboration/work_packages/pending/UI-PTM-001B_Workspace_data_binding_and_navigation_contract.md`
3. `UI-PTM-002` — `collaboration/work_packages/pending/UI-PTM-002_Office_compact_card_and_deep_link_contract.md`
4. `CONV-PTM-001` — `collaboration/work_packages/pending/CONV-PTM-001_Resident_governed_PTM_command_contract.md`

## Package groups that may run simultaneously
- `G04A`: `UI-PTM-001A`
- `G04B`: `UI-PTM-001B`, `CONV-PTM-001`
- `G04C`: `UI-PTM-002`

## Packages that must remain serial
Packages with direct dependencies in this campaign must remain serial: `UI-PTM-001A`, `UI-PTM-001B`, `UI-PTM-002`, `CONV-PTM-001`.

## Prerequisite campaigns and package gates
- Prerequisite campaigns: `PTM-03`
- Package dependencies are controlled by `collaboration/work_packages/planning/estate_ptm_dependency_manifest.json`.

## Contract-freeze requirements
Honor WP-0661 contract freezes. Downstream packages must not redefine frozen event, ID, projection, intake, route, schedule, dispatch, or validation contracts.

## Branch naming guidance
Use `codex/ptm-04-<package-id-or-campaign-slice>` for package branches and `integration/ptm-04-checkpoint` for checkpoint reconciliation.

## Integration branch or checkpoint requirements
Checkpoint: Gate C — route/command surface reconciliation. Use one integration branch per wave and reconcile manifests/evidence once at the checkpoint.

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
codex exec "Read collaboration/work_packages/campaigns/ptm/PTM-04_Visibility_and_Command_Surfaces.md and execute the included Pending work packages exactly as instructed."
```
