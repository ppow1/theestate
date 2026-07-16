# PTM Executable Campaign Handoff Index

## Campaign documents in dependency order
- `PTM-00` — `collaboration/work_packages/campaigns/ptm/PTM-00_Governance_Acceptance.md`
- `PTM-01` — `collaboration/work_packages/campaigns/ptm/PTM-01_Read_Only_Source_Inventory.md`
- `PTM-02` — `collaboration/work_packages/campaigns/ptm/PTM-02_Canonical_Contracts.md`
- `PTM-03` — `collaboration/work_packages/campaigns/ptm/PTM-03_Governed_Intake_and_Import.md`
- `PTM-04` — `collaboration/work_packages/campaigns/ptm/PTM-04_Visibility_and_Command_Surfaces.md`
- `PTM-05` — `collaboration/work_packages/campaigns/ptm/PTM-05_Scheduling_Utilization_Financials_and_KPIs.md`
- `PTM-06` — `collaboration/work_packages/campaigns/ptm/PTM-06_Dispatch_Evidence_and_Pilot_Migration.md`
- `PTM-07` — `collaboration/work_packages/campaigns/ptm/PTM-07_Validation_and_Rollout.md`

## Exact Codex handoff commands
### PTM-00
```bash
codex exec "Read collaboration/work_packages/campaigns/ptm/PTM-00_Governance_Acceptance.md and execute the included Pending work packages exactly as instructed."
```
### PTM-01
```bash
codex exec "Read collaboration/work_packages/campaigns/ptm/PTM-01_Read_Only_Source_Inventory.md and execute the included Pending work packages exactly as instructed."
```
### PTM-02
```bash
codex exec "Read collaboration/work_packages/campaigns/ptm/PTM-02_Canonical_Contracts.md and execute the included Pending work packages exactly as instructed."
```
### PTM-03
```bash
codex exec "Read collaboration/work_packages/campaigns/ptm/PTM-03_Governed_Intake_and_Import.md and execute the included Pending work packages exactly as instructed."
```
### PTM-04
```bash
codex exec "Read collaboration/work_packages/campaigns/ptm/PTM-04_Visibility_and_Command_Surfaces.md and execute the included Pending work packages exactly as instructed."
```
### PTM-05
```bash
codex exec "Read collaboration/work_packages/campaigns/ptm/PTM-05_Scheduling_Utilization_Financials_and_KPIs.md and execute the included Pending work packages exactly as instructed."
```
### PTM-06
```bash
codex exec "Read collaboration/work_packages/campaigns/ptm/PTM-06_Dispatch_Evidence_and_Pilot_Migration.md and execute the included Pending work packages exactly as instructed."
```
### PTM-07
```bash
codex exec "Read collaboration/work_packages/campaigns/ptm/PTM-07_Validation_and_Rollout.md and execute the included Pending work packages exactly as instructed."
```

## Submit now
Run `PTM-00` first. It must complete before `PTM-01`.

## Submit together
After `PTM-02` contract freeze, `PTM-03`, `PTM-04`, `PTM-05`, and the `TEST-PTM-001A` slice of `PTM-07` may run simultaneously in separate Codex tasks when their package dependencies are satisfied.

## Submit after midpoint integration
After Gate C, submit closure fan-out work in `PTM-06` and the remaining eligible validation work in `PTM-07` as dependencies permit.

## Submit after final validation
After Gate E and `TEST-PTM-001B`, submit rollout packages `ROLL-PTM-001A` then `ROLL-PTM-001B` through `PTM-07`.

## Midpoint integration commands or campaign documents
Use the campaign documents above as checkpoint commands; reconcile Gate A through Gate E on integration branches before launching dependent groups.

## Operator checklist
- Confirm campaign PRs cite accepted authority and package receipts.
- Confirm validation commands passed and evidence was committed.
- Confirm manifests point to Pending paths and Codex-only routing.
- Confirm no frozen contract was changed without a replan.
- Confirm no second queue, registry, scheduler, or governance authority was introduced.
