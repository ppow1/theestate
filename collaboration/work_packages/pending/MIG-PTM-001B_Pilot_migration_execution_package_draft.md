# MIG-PTM-001B — Pilot migration execution package draft

## Status
Pending

## Owner
Chief Architect

## Execution lane
Codex

## Campaign and launch group
- Campaign ID: `PTM-06`
- Launch group: `G06B`
- Campaign instruction: `collaboration/work_packages/campaigns/ptm/PTM-06_Dispatch_Evidence_and_Pilot_Migration.md`
- Integration checkpoint: Gate D — migration/dispatch readiness

## Objective
Draft bounded future package for executing the accepted pilot migration only.

## Accepted authority baseline
This package is promoted from `collaboration/work_packages/planning/ptm_drafts/MIG-PTM-001B_pilot_migration_execution_package_draft.md` under the Steward / Chief Architect acceptance recorded in `docs/architecture/estate_ptm_specification_acceptance.md`. The accepted baseline includes WP-0658, WP-0660, and WP-0661. Codex-only routing is mandatory for this cycle; do not use the local RTX 4090 worker.

## Exact repository scope
future migration tooling

## Required inputs
- `docs/architecture/estate_ptm_specification_acceptance.md`
- `docs/architecture/estate_ptm_parallel_campaign_execution_plan.md`
- `docs/architecture/estate_ptm_dependency_and_parallelism_plan.md`
- `collaboration/work_packages/planning/estate_ptm_package_manifest.json`
- `collaboration/work_packages/planning/estate_ptm_campaign_manifest.json`
- `collaboration/work_packages/planning/estate_ptm_dependency_manifest.json`
- Source planning draft: `collaboration/work_packages/planning/ptm_drafts/MIG-PTM-001B_pilot_migration_execution_package_draft.md`
- collaboration/work_packages/planning/estate_project_task_management_work_package_backlog.md
- collaboration/reports/project_management/WP-0659_execution_lane_parallelism_and_timeline_scenarios.md
- collaboration/work_packages/pending/WP-0660_Correct_PTM_Execution_Decomposition_and_Hour_Scale_Timeline_Model.md

## Bounded implementation deliverables
- One bounded implementation-ready specification or validation artifact for this slice.
- Evidence notes sufficient to promote a future Pending package.
- No production PTM code is authorized by this draft.

## Explicit non-goals and authority boundaries
- Do not perform work outside this package scope or broaden it into a replacement PTM program.
- Do not create a second dispatch queue, second registry, second scheduler, or new governance authority.
- Do not independently alter frozen upstream contracts; open a stop/replan note if a contract change is required.
- Do not merge the pull request unless a separate accepted workflow explicitly authorizes merge.

## Dependencies and readiness gates
- Package dependencies: `MIG-PTM-001A`
- Dependencies accepted or explicitly waived by Chief Architect.
- Current branch rebased and package revalidated against latest manifests.
- No collision with another active package touching the same future contract surface.

## Parallel-safety classification
After slice plan; primary parallel group G06B.

## Shared-file and shared-schema collision controls
Low while this remains a planning draft. Future promotion must check collisions for future migration tooling.
- Shared contracts may not be independently changed by downstream branches after their freeze gate.
- If this package touches a manifest, coordinate through the campaign integration checkpoint to avoid divergent campaign membership.

## Branch and integration expectations
- Branch name guidance: `codex/mig-ptm-001b-pilot_migration_execution_package_draft`.
- Keep commits atomic to this package and include evidence updates in the same branch.
- Open a pull request for Chief Architect review and do not merge it.
- Merge only through the campaign checkpoint order in `docs/architecture/estate_ptm_parallel_campaign_execution_plan.md`.

## Required validation commands and evidence
- `git diff --check`
- Run package-specific tests or documentation validation for any touched executable files.
- Capture validation evidence in `collaboration/work_packages/completions/MIG-PTM-001B_completion_receipt.md`.
- Review changed files with `git diff --check`.
- Run package-specific unit or documentation validation after promotion.

## Acceptance criteria
- Deliverables are complete and source-backed.
- No second queue, second registry, or governance authority is introduced.
- Estimates remain at or below 60 active minutes or document an evidence-based exception.

## Required completion receipt path
`collaboration/work_packages/completions/MIG-PTM-001B_completion_receipt.md`

## Delivery requirement
Open a pull request for Chief Architect review after committing this package. Do not merge it.
