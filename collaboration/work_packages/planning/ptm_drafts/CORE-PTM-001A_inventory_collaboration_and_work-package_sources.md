# CORE-PTM-001A — Inventory collaboration and work-package sources

## Package ID and Title
CORE-PTM-001A — Inventory collaboration and work-package sources

## Status
Planning Draft — Not Authorized for Execution

## Parent PTM backlog category
Core ledger

## Objective
Read-only inventory of work-package, parking-lot, completion, receipt, promotion, and collaboration sources.

## Bounded deliverables
- One bounded implementation-ready specification or validation artifact for this slice.
- Evidence notes sufficient to promote a future Pending package.
- No production PTM code is authorized by this draft.

## Exact repository scope
collaboration/work_packages/**; collaboration/parking_lot/**; collaboration/promotions/**

## Source inputs
- collaboration/work_packages/planning/estate_project_task_management_work_package_backlog.md
- collaboration/reports/project_management/WP-0659_execution_lane_parallelism_and_timeline_scenarios.md
- collaboration/work_packages/pending/WP-0660_Correct_PTM_Execution_Decomposition_and_Hour_Scale_Timeline_Model.md

## Dependencies
SPEC-PTM-001

## Readiness gates
- Dependencies accepted or explicitly waived by Chief Architect.
- Current branch rebased and package revalidated against latest manifests.
- No collision with another active package touching the same future contract surface.

## Preferred execution lane
Local RTX 4090 worker

## Permitted alternate lanes
Codex

## Prohibited lanes
Production runtime changes

## Local RTX 4090 suitability and justification
Suitable: bounded scope, repository-local evidence, and deterministic drafting make local execution practical unless governance-sensitive decisions are named above.

## Context breadth
Narrow repository audit

## Active execution estimate in minutes
Best: 7; Expected: 12; Conservative: 22. Confidence: High. Estimate basis: bounded draft scope under Steward hour-scale assumptions. Flagged for review/further decomposition: No; expected active execution is 15 minutes or less.

## Validation estimate in minutes
Best: 5; Expected: 8; Conservative: 15.

## Rework allowance
Expected: 5 minutes; conservative: 15 minutes for review comments, contract drift, or fixture correction.

## Expected wall-clock range
Best: 20 minutes; Expected: 25 minutes active plus 0-120 minutes queue/review wait; Conservative: 50 minutes active plus review latency.

## Parallelism classification
Parallel after spec; primary parallel group G01A.

## Shared-file collision risks
Low while this remains a planning draft. Future promotion must check collisions for collaboration/work_packages/**; collaboration/parking_lot/**; collaboration/promotions/**.

## Acceptance criteria
- Deliverables are complete and source-backed.
- No second queue, second registry, or governance authority is introduced.
- Estimates remain at or below 60 active minutes or document an evidence-based exception.

## Validation commands or validation approach
- Review changed files with `git diff --check`.
- Run package-specific unit or documentation validation after promotion.

## Review and acceptance lane
Chief Architect review with Steward acceptance where authority or rollout gates are implicated.

## Prerequisite revalidation requirement before promotion to Pending
Before promotion, revalidate dependencies, manifest membership, active estimate, lane suitability, and collision risk against the latest PTM manifests.
