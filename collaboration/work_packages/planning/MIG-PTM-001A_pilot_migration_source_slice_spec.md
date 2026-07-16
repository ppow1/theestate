# MIG-PTM-001A Pilot Migration Source Slice Specification

## Status
Implementation-ready planning artifact for Chief Architect review. This artifact does not authorize production PTM code, data mutation, broad migration, merge, rollout, or new governance authority.

## Authority baseline
- Accepted under the PTM baseline covering WP-0658, WP-0660, and WP-0661.
- Execution lane for this cycle is Codex only; the local RTX 4090 worker remains inactive for this package.
- The package remains in launch group `G06A`, parallel with dispatch evidence review, and integrates at Gate D — migration/dispatch readiness.
- Feeder dependencies are `FILE-PTM-001B` and `DISPATCH-PTM-001`; migration execution remains blocked until those package outcomes are accepted or explicitly waived by the Chief Architect.

## Selected pilot portfolio slice
The pilot slice is the existing PTM migration-planning slice represented by `MIG-PTM-001`, limited to planning records and evidence under `collaboration/work_packages/planning`.

### Included source records
| Source | Role in pilot slice | Migration handling |
|---|---|---|
| `collaboration/work_packages/planning/estate_project_task_management_work_package_backlog.md` | Authoritative backlog row for `MIG-PTM-001` as the parent migration pilot concept. | Read only; map the backlog row into a candidate PTM portfolio/work-package record after feeder contracts are accepted. |
| `collaboration/work_packages/planning/ptm_drafts/MIG-PTM-001A_pilot_migration_source_slice_plan.md` | Accepted source draft for this planning package. | Read only; preserve source path, package title, dependencies, estimates, collision risks, and acceptance criteria in the migration candidate. |
| `collaboration/work_packages/pending/MIG-PTM-001A_Pilot_migration_source_slice_plan.md` | Promoted Pending package and current execution instruction. | Read only; use as the controlling package instruction for this artifact and as evidence of current status. |
| `collaboration/work_packages/planning/estate_ptm_package_manifest.json` | Manifest membership and campaign metadata for `MIG-PTM-001A`. | Read only; verify package ID, pending path, launch group, campaign, estimates, and Codex lane. |
| `collaboration/work_packages/planning/estate_ptm_campaign_manifest.json` | Campaign-level PTM-06 membership and handoff metadata. | Read only; verify `MIG-PTM-001A` remains in PTM-06 and G06A. |
| `collaboration/work_packages/planning/estate_ptm_dependency_manifest.json` | Dependency and promoted-path metadata. | Read only; verify hard dependencies and promoted pending path before execution. |

### Explicitly excluded records
- Production PTM ledger, registry, scheduler, dispatch queue, and event-store files.
- Any migration of packages outside the selected `MIG-PTM-001` planning slice.
- Any inferred source that lacks manifest, backlog, or package evidence.

## Source mapping contract
| Candidate field | Source of truth | Required transformation | Acceptance evidence |
|---|---|---|---|
| `package_id` | Pending package and manifests | Preserve exactly as `MIG-PTM-001A`. | Package manifest entry and dependency manifest promoted path agree. |
| `parent_backlog_id` | Backlog row `MIG-PTM-001` | Preserve parent linkage without minting a replacement backlog ID. | Backlog row remains read-only source evidence. |
| `title` | Pending package title | Preserve title casing from Pending package. | Pending path and manifest title are consistent. |
| `campaign_id` | Package and campaign manifests | Preserve `PTM-06`. | Campaign manifest includes package in PTM-06. |
| `launch_group` | Package and dependency manifests | Preserve `G06A`. | Dependency manifest parallel-safe relationship includes package. |
| `dependencies` | Dependency manifest and Pending package | Preserve `FILE-PTM-001B` and `DISPATCH-PTM-001`. | Both dependencies are accepted or explicitly waived before migration execution. |
| `execution_lane` | Accepted baseline and package manifest | Normalize to Codex only for this cycle. | No local RTX 4090 worker route appears in execution output. |
| `active_estimate_minutes` | Source draft and package manifest | Preserve best/expected/conservative estimate: 7/12/22 minutes. | Estimate remains below 60 active minutes. |
| `validation_estimate_minutes` | Source draft and package manifest | Preserve best/expected/conservative estimate: 5/8/15 minutes. | Completion receipt records validation command results. |
| `acceptance_criteria` | Pending package | Preserve all three criteria without broadening scope. | Review confirms no second queue, registry, scheduler, or authority. |
| `source_paths` | This artifact's included source records | Store exact relative paths and content hashes only after FILE-PTM-001B hash mapping is accepted. | Future migration report can reconcile source path and SHA evidence. |

## Duplicate policy
1. Treat `MIG-PTM-001` as the parent backlog concept and `MIG-PTM-001A` as the atomic executable planning package; these are related records, not duplicates.
2. Treat planning draft, Pending package, and manifest entries as multiple source views for the same `MIG-PTM-001A` package; do not create separate package records for each view.
3. Use package ID plus normalized relative source path as the first duplicate key during import-report reconciliation.
4. If two sources claim the same package ID but disagree on dependencies, execution lane, or campaign membership, stop migration execution and open a replan note instead of selecting one silently.
5. Do not dedupe across different atomic package IDs, even when titles share a parent backlog category.

## Rollback plan
1. Keep the pilot read-only until FILE-PTM-001B source/SHA mapping and DISPATCH-PTM-001 evidence-chain outputs are accepted or explicitly waived.
2. Before any future execution, write a migration candidate report containing source paths, source hashes, target candidate IDs, duplicate decisions, and dependency-gate status.
3. If validation fails before commit, discard the generated candidate report and leave source files unchanged.
4. If validation fails after commit but before merge, revert the pilot migration commit on the package branch and preserve the failed validation evidence in the completion receipt.
5. If a duplicate, lane, or authority mismatch is discovered at Gate D, stop the package, do not migrate additional slices, and request Chief Architect replan guidance.

## Readiness checklist for future MIG-PTM-001B
- `FILE-PTM-001B` accepted or explicitly waived by Chief Architect.
- `DISPATCH-PTM-001` accepted or explicitly waived by Chief Architect.
- `MIG-PTM-001A` package manifest, campaign manifest, and dependency manifest entries remain aligned.
- Candidate report contains exact relative source paths and source hashes.
- Duplicate policy is applied without creating a second queue, registry, scheduler, or governance authority.
- Rollback path is executable before migration output is merged.

## Evidence notes
- Current package revalidation found `MIG-PTM-001A` in PTM-06/G06A with hard dependencies on `FILE-PTM-001B` and `DISPATCH-PTM-001`.
- Scope remains limited to `collaboration/work_packages/planning` plus the required completion receipt.
- No production PTM code, runtime data, registry, scheduler, dispatch queue, or governance surface was modified.
- Expected active estimate remains 12 minutes, below the 60-minute exception threshold.
