# PTM-00 — Governance acceptance

## Campaign status and authority basis
Executable campaign handoff. Authority comes from `docs/architecture/estate_ptm_specification_acceptance.md` and the WP-0661 parallel execution model. Execution lane is Codex only.

## Included Pending work-package paths
- `collaboration/work_packages/pending/SPEC-PTM-001_Accept_PTM_specification_and_boundaries.md`

## Exact package launch order
1. `SPEC-PTM-001` — `collaboration/work_packages/pending/SPEC-PTM-001_Accept_PTM_specification_and_boundaries.md`

## Package groups that may run simultaneously
- `G00`: `SPEC-PTM-001`

## Packages that must remain serial
Packages with direct dependencies in this campaign must remain serial: none beyond prerequisite gates.

## Prerequisite campaigns and package gates
- Prerequisite campaigns: none
- Package dependencies are controlled by `collaboration/work_packages/planning/estate_ptm_dependency_manifest.json`.

## Contract-freeze requirements
Honor WP-0661 contract freezes. Downstream packages must not redefine frozen event, ID, projection, intake, route, schedule, dispatch, or validation contracts.

## Branch naming guidance
Use `codex/ptm-00-<package-id-or-campaign-slice>` for package branches and `integration/ptm-00-checkpoint` for checkpoint reconciliation.

## Integration branch or checkpoint requirements
Checkpoint: Gate 0 — authority acceptance. Use one integration branch per wave and reconcile manifests/evidence once at the checkpoint.

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
codex exec "Read collaboration/work_packages/campaigns/ptm/PTM-00_Governance_Acceptance.md and execute the included Pending work packages exactly as instructed."
```
