# PTM-03 — Governed intake and import contracts

## Campaign status and authority basis
Executable campaign handoff. Authority comes from `docs/architecture/estate_ptm_specification_acceptance.md` and the WP-0661 parallel execution model. Execution lane is Codex only.

## Included Pending work-package paths
- `collaboration/work_packages/pending/INTAKE-PTM-001A_Manual_and_Parking_Lot_intake_contract.md`
- `collaboration/work_packages/pending/INTAKE-PTM-001B_Conversation_intake_and_dedupe_confirmation_contract.md`
- `collaboration/work_packages/pending/FILE-PTM-001A_File_import_parser_format_inventory.md`
- `collaboration/work_packages/pending/FILE-PTM-001B_File_import_report_and_SHA_mapping_contract.md`

## Exact package launch order
1. `INTAKE-PTM-001A` — `collaboration/work_packages/pending/INTAKE-PTM-001A_Manual_and_Parking_Lot_intake_contract.md`
2. `INTAKE-PTM-001B` — `collaboration/work_packages/pending/INTAKE-PTM-001B_Conversation_intake_and_dedupe_confirmation_contract.md`
3. `FILE-PTM-001A` — `collaboration/work_packages/pending/FILE-PTM-001A_File_import_parser_format_inventory.md`
4. `FILE-PTM-001B` — `collaboration/work_packages/pending/FILE-PTM-001B_File_import_report_and_SHA_mapping_contract.md`

## Package groups that may run simultaneously
- `G03A`: `INTAKE-PTM-001A`, `FILE-PTM-001A`
- `G03B`: `INTAKE-PTM-001B`
- `G03C`: `FILE-PTM-001B`

## Packages that must remain serial
Packages with direct dependencies in this campaign must remain serial: `INTAKE-PTM-001A`, `INTAKE-PTM-001B`, `FILE-PTM-001A`, `FILE-PTM-001B`.

## Prerequisite campaigns and package gates
- Prerequisite campaigns: `PTM-02`
- Package dependencies are controlled by `collaboration/work_packages/planning/estate_ptm_dependency_manifest.json`.

## Contract-freeze requirements
Honor WP-0661 contract freezes. Downstream packages must not redefine frozen event, ID, projection, intake, route, schedule, dispatch, or validation contracts.

## Branch naming guidance
Use `codex/ptm-03-<package-id-or-campaign-slice>` for package branches and `integration/ptm-03-checkpoint` for checkpoint reconciliation.

## Integration branch or checkpoint requirements
Checkpoint: Gate C — intake/import reconciliation. Use one integration branch per wave and reconcile manifests/evidence once at the checkpoint.

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
codex exec "Read collaboration/work_packages/campaigns/ptm/PTM-03_Governed_Intake_and_Import.md and execute the included Pending work packages exactly as instructed."
```
