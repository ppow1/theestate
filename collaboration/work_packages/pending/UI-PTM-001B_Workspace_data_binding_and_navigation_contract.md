# UI-PTM-001B — Workspace data binding and navigation contract

## Status
Pending

## Owner
Chief Architect

## Execution lane
Codex

## Campaign and launch group
- Campaign ID: `PTM-04`
- Launch group: `G04B`
- Campaign instruction: `collaboration/work_packages/campaigns/ptm/PTM-04_Visibility_and_Command_Surfaces.md`
- Integration checkpoint: Gate C — route/command surface reconciliation

## Objective
Bound projection-backed data bindings, detail routes, and large-ledger navigation behavior.

## Accepted authority baseline
This package is promoted from `collaboration/work_packages/planning/ptm_drafts/UI-PTM-001B_workspace_data_binding_and_navigation_contract.md` under the Steward / Chief Architect acceptance recorded in `docs/architecture/estate_ptm_specification_acceptance.md`. The accepted baseline includes WP-0658, WP-0660, and WP-0661. Codex-only routing is mandatory for this cycle; do not use the local RTX 4090 worker.

## Exact repository scope
future Office UI files

## Required inputs
- `docs/architecture/estate_ptm_specification_acceptance.md`
- `docs/architecture/estate_ptm_parallel_campaign_execution_plan.md`
- `docs/architecture/estate_ptm_dependency_and_parallelism_plan.md`
- `collaboration/work_packages/planning/estate_ptm_package_manifest.json`
- `collaboration/work_packages/planning/estate_ptm_campaign_manifest.json`
- `collaboration/work_packages/planning/estate_ptm_dependency_manifest.json`
- Source planning draft: `collaboration/work_packages/planning/ptm_drafts/UI-PTM-001B_workspace_data_binding_and_navigation_contract.md`
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
- Package dependencies: `UI-PTM-001A`, `CORE-PTM-003B`
- Dependencies accepted or explicitly waived by Chief Architect.
- Current branch rebased and package revalidated against latest manifests.
- No collision with another active package touching the same future contract surface.

## Parallel-safety classification
After IA shell; primary parallel group G04B.

## Shared-file and shared-schema collision controls
Low while this remains a planning draft. Future promotion must check collisions for future Office UI files.
- Shared contracts may not be independently changed by downstream branches after their freeze gate.
- If this package touches a manifest, coordinate through the campaign integration checkpoint to avoid divergent campaign membership.

## Branch and integration expectations
- Branch name guidance: `codex/ui-ptm-001b-workspace_data_binding_and_navigation_co`.
- Keep commits atomic to this package and include evidence updates in the same branch.
- Open a pull request for Chief Architect review and do not merge it.
- Merge only through the campaign checkpoint order in `docs/architecture/estate_ptm_parallel_campaign_execution_plan.md`.

## Required validation commands and evidence
- `git diff --check`
- Run package-specific tests or documentation validation for any touched executable files.
- Capture validation evidence in `collaboration/work_packages/completions/UI-PTM-001B_completion_receipt.md`.
- Review changed files with `git diff --check`.
- Run package-specific unit or documentation validation after promotion.

## Acceptance criteria
- Deliverables are complete and source-backed.
- No second queue, second registry, or governance authority is introduced.
- Estimates remain at or below 60 active minutes or document an evidence-based exception.

## Required completion receipt path
`collaboration/work_packages/completions/UI-PTM-001B_completion_receipt.md`

## Delivery requirement
Open a pull request for Chief Architect review after committing this package. Do not merge it.
