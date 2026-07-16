# MIG-PTM-001B Pilot Migration Execution Validation Specification

## Status
Implementation-ready validation artifact for Chief Architect review. This artifact does not authorize production PTM code, data mutation, broad migration, merge, rollout, or new governance authority.

## Authority baseline
- Accepted under the PTM baseline covering WP-0658, WP-0660, and WP-0661.
- Execution lane for this cycle is Codex only; the local RTX 4090 worker remains inactive for this package.
- The package remains in launch group `G06B` and integrates at Gate D — migration/dispatch readiness.
- Execution is bounded to the accepted pilot migration only and depends on `MIG-PTM-001A` acceptance or explicit Chief Architect waiver.

## Execution scope
The future execution package may validate and produce a pilot migration candidate for the single slice selected by `MIG-PTM-001A`: the existing PTM migration-planning evidence set rooted in `collaboration/work_packages/planning` and represented by the atomic package `MIG-PTM-001A`.

### Required source inputs for future execution
| Source | Required use | Execution guard |
|---|---|---|
| `collaboration/work_packages/planning/MIG-PTM-001A_pilot_migration_source_slice_spec.md` | Controlling selected-slice specification, duplicate policy, source mapping contract, and rollback plan. | Must exist and remain reviewed before candidate generation. |
| `collaboration/work_packages/pending/MIG-PTM-001B_Pilot_migration_execution_package_draft.md` | Current package instruction, non-goals, validation commands, and completion receipt path. | Must remain scoped to future migration tooling and no production PTM code. |
| `collaboration/work_packages/planning/estate_ptm_package_manifest.json` | Package metadata, estimates, campaign ID, launch group, execution lane, and Pending path for `MIG-PTM-001B`. | Must show Codex-only lane and `G06B`. |
| `collaboration/work_packages/planning/estate_ptm_campaign_manifest.json` | PTM-06 campaign membership and handoff metadata. | Must include `MIG-PTM-001B` in `PTM-06`. |
| `collaboration/work_packages/planning/estate_ptm_dependency_manifest.json` | Hard dependency and promoted Pending path evidence. | Must show `MIG-PTM-001B` depends on `MIG-PTM-001A`. |
| `docs/architecture/estate_ptm_parallel_campaign_execution_plan.md` | Gate D and Wave 6 merge/order controls. | Must preserve serial chain `MIG-PTM-001B → ROLL-PTM-001A → ROLL-PTM-001B`. |

## Future validation workflow
1. Revalidate that `MIG-PTM-001A` is accepted or explicitly waived by the Chief Architect before any pilot execution candidate is produced.
2. Re-read the package, campaign, and dependency manifests and confirm that `MIG-PTM-001B` still maps to `PTM-06`, `G06B`, Codex-only execution, and Gate D.
3. Load the selected-slice source mapping contract from `MIG-PTM-001A` and reject any source outside the selected pilot evidence set.
4. Generate a candidate migration report, not production runtime data, containing source paths, source hashes when the hash-mapping feeder is available, target candidate IDs, duplicate decisions, dependency-gate status, and rollback instructions.
5. Validate the candidate report against the checks in this specification.
6. If any manifest, dependency, source hash, duplicate policy, or authority check fails, stop the execution package and record a replan note instead of choosing a fallback mapping.
7. Commit only the bounded candidate report and completion evidence for Chief Architect review; do not merge without a separately accepted workflow.

## Candidate report minimum fields
| Field | Requirement | Failure handling |
|---|---|---|
| `pilot_package_id` | Must be `MIG-PTM-001A` for this accepted pilot. | Stop/replan if any other package is selected. |
| `execution_package_id` | Must be `MIG-PTM-001B`. | Stop/replan if missing or different. |
| `campaign_id` | Must be `PTM-06`. | Stop/replan if campaign membership drifted. |
| `launch_group` | Must be `G06B` for execution package evidence. | Stop/replan if launch group drifted. |
| `dependency_status` | Must record `MIG-PTM-001A` accepted or explicitly waived. | Do not generate candidate output if unresolved. |
| `source_paths` | Must use exact repository-relative paths from the accepted source-slice spec. | Reject inferred or broad wildcard sources. |
| `source_hashes` | Must use FILE-PTM-001B hash mapping when available; otherwise record the feeder as unresolved and keep output non-mutating. | Do not promote to executable migration without hashes or waiver. |
| `duplicate_decisions` | Must apply the MIG-PTM-001A duplicate policy: package views are not separate package records, and parent backlog concept is not a duplicate of the atomic package. | Stop/replan on conflicting package identity, dependencies, lane, or campaign. |
| `rollback_plan` | Must restate the reversible branch-level rollback procedure before merge. | Stop/replan if rollback is not executable. |
| `authority_confirmations` | Must confirm no second dispatch queue, registry, scheduler, or governance authority. | Stop/replan on any new authority surface. |

## Acceptance checks for future execution tooling
- The future candidate report is documentation/evidence only unless a later accepted package authorizes production PTM data writes.
- The package must not create or modify a second dispatch queue, second registry, second scheduler, or governance authority.
- The execution path must reuse the accepted dispatch evidence and file-import/hash mapping feeders instead of defining replacement feeders.
- The active execution estimate remains best 7, expected 12, conservative 22 minutes; no estimate exceeds the 60-minute exception threshold.
- The completion receipt must record `git diff --check` and any package-specific documentation validation used for touched executable files.

## Evidence notes
- Current manifest revalidation shows `MIG-PTM-001B` in `PTM-06`, launch group `G06B`, with hard dependency on `MIG-PTM-001A`.
- Current PTM parallel plan places `MIG-PTM-001B` in Wave 6 before rollout packages, preserving the serial acceptance and rollout chain.
- This package creates only a validation specification and completion receipt; it does not execute the pilot migration, create production PTM code, or broaden the selected slice.
