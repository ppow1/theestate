# Estate PTM Schedule Validation Fixtures and Critical Path Plan

Status: Implementation-ready validation artifact for future PTM schedule tests
Package: `SCHED-PTM-001B`
Campaign: `PTM-05`, launch group `G05B`
Authority baseline: Steward / Chief Architect acceptance of WP-0658, WP-0660, and WP-0661 on 2026-07-16

## Purpose

This artifact defines deterministic validation fixtures for the future schedule dependency and readiness-gate implementation. It is intentionally a planning and validation contract only: it does not implement production PTM code, create a scheduler, create a dispatch queue, or alter governance authority.

The fixtures are designed to prove that a future PTM schedule implementation can:

1. enforce dependency gates before a task can be marked dispatch-ready;
2. calculate a critical path from duration and dependency data;
3. preserve blocked intervals as schedule evidence without treating them as new governance decisions;
4. expose unknown or stale source data as labeled validation failures rather than inferred readiness;
5. reuse the accepted PTM package, campaign, and dependency manifests as source authority.

## Source authority used

- `docs/architecture/estate_ptm_specification_acceptance.md` accepts the PTM planning baseline and requires Codex-only routing for this cycle.
- `docs/architecture/estate_ptm_parallel_campaign_execution_plan.md` places `SCHED-PTM-001B` in launch group `G05B` and Gate C/D reconciliation.
- `docs/architecture/estate_ptm_dependency_and_parallelism_plan.md` defines the critical path and the dependency chain around scheduling, utilization, dispatch, validation, and rollout.
- `collaboration/work_packages/planning/estate_ptm_package_manifest.json` records `SCHED-PTM-001B` as a Codex package with dependency `SCHED-PTM-001A`.
- `collaboration/work_packages/planning/estate_ptm_campaign_manifest.json` records PTM campaign membership and Codex handoff routing.
- `collaboration/work_packages/planning/estate_ptm_dependency_manifest.json` records hard dependencies and parallel-safe group `G05B`.
- `collaboration/reports/project_management/WP-0659_execution_lane_parallelism_and_timeline_scenarios.md` states that critical-path semantics govern dispatch readiness.

## Fixture schema

Future executable tests should represent each fixture with these fields. Field names are stable for validation planning, but the future implementation may map them to the accepted projection contract after `SCHED-PTM-001A` is complete.

| Field | Required | Meaning | Validation expectation |
|---|---:|---|---|
| `fixture_id` | Yes | Stable fixture identifier. | Must be unique in the fixture set. |
| `task_id` | Yes | Canonical PTM task or package identifier. | Must match the accepted ID format once that contract is frozen. |
| `duration_minutes` | Yes | Active work duration used for critical-path calculation. | Must be a positive integer unless the task is a milestone. |
| `dependencies` | Yes | Upstream `task_id` values that must complete first. | Missing or cyclic dependencies fail validation. |
| `readiness_gate` | Yes | Gate label required before dispatch readiness. | Must be satisfied before `dispatch_ready=true`. |
| `gate_state` | Yes | `satisfied`, `blocked`, `unknown`, or `stale`. | Only `satisfied` can permit dispatch readiness. |
| `blocked_intervals` | Yes | Zero or more blocked ranges with reason labels. | Must be evidence only; they cannot grant authority. |
| `expected_earliest_start_minute` | Yes | Earliest start in a deterministic minute-zero model. | Must equal max upstream finish plus eligible blocked delay. |
| `expected_earliest_finish_minute` | Yes | Earliest finish in the same model. | Must equal expected start plus duration. |
| `expected_on_critical_path` | Yes | Whether the task is expected to be on the longest path. | Must match deterministic longest-path calculation. |
| `expected_dispatch_ready` | Yes | Whether future dispatch integration may consume the task. | Must be false unless dependencies and readiness gate pass. |

## Fixture set A — gate enforcement

Minute zero is the start of the validation model. No calendar or timezone behavior is implied by these fixtures.

| fixture_id | task_id | duration_minutes | dependencies | readiness_gate | gate_state | blocked_intervals | expected_start | expected_finish | critical_path | dispatch_ready | Expected validation outcome |
|---|---|---:|---|---|---|---|---:|---:|---|---|---|
| `sched_gate_root_ready` | `CORE-PTM-003B` | 10 | none | `projection_contract_freeze` | `satisfied` | none | 0 | 10 | Yes | Yes | Root schedule input is usable. |
| `sched_gate_ready_after_dep` | `SCHED-PTM-001A` | 12 | `CORE-PTM-003B` | `schedule_contract_ready` | `satisfied` | none | 10 | 22 | Yes | Yes | Dependency and gate both pass. |
| `sched_gate_blocked` | `SCHED-PTM-001B` | 12 | `SCHED-PTM-001A` | `schedule_validation_fixture_ready` | `blocked` | `22-32: waiting for fixture review` | 32 | 44 | Yes | No | Blocked gate prevents dispatch readiness even though timing can be modeled. |
| `sched_gate_unknown` | `DISPATCH-PTM-001` | 10 | `SCHED-PTM-001A` | `dispatch_evidence_contract` | `unknown` | none | 22 | 32 | No | No | Unknown gate state fails closed. |
| `sched_gate_stale` | `TEST-PTM-001A` | 8 | `CORE-PTM-003B`, `SCHED-PTM-001A` | `validation_fixture_current` | `stale` | none | 22 | 30 | No | No | Stale schedule validation data fails closed. |

## Fixture set B — critical path calculation

This set validates longest-path behavior independent of dispatch readiness. All gates are satisfied unless explicitly noted.

| fixture_id | task_id | duration_minutes | dependencies | gate_state | blocked_intervals | expected_start | expected_finish | critical_path | dispatch_ready | Expected validation outcome |
|---|---|---:|---|---|---|---:|---:|---|---|---|
| `crit_root_spec` | `SPEC-PTM-001` | 10 | none | `satisfied` | none | 0 | 10 | Yes | Yes | Root authority gate starts the longest path. |
| `crit_inventory_a` | `CORE-PTM-001A` | 12 | `SPEC-PTM-001` | `satisfied` | none | 10 | 22 | Yes | Yes | One branch of parallel inventory. |
| `crit_inventory_b` | `CORE-PTM-001B` | 9 | `SPEC-PTM-001` | `satisfied` | none | 10 | 19 | No | Yes | Shorter parallel branch is not critical. |
| `crit_inventory_merge` | `CORE-PTM-001C` | 15 | `CORE-PTM-001A`, `CORE-PTM-001B` | `satisfied` | none | 22 | 37 | Yes | Yes | Merge waits for the later branch. |
| `crit_event_schema` | `CORE-PTM-002A` | 12 | `CORE-PTM-001C` | `satisfied` | none | 37 | 49 | Yes | Yes | Continues contract spine. |
| `crit_projection_schedule` | `CORE-PTM-003B` | 14 | `CORE-PTM-002A` | `satisfied` | none | 49 | 63 | Yes | Yes | Projection freeze gates schedule work. |
| `crit_schedule_contract` | `SCHED-PTM-001A` | 12 | `CORE-PTM-003B` | `satisfied` | none | 63 | 75 | Yes | Yes | Schedule contract is on the critical path. |
| `crit_schedule_fixture` | `SCHED-PTM-001B` | 12 | `SCHED-PTM-001A` | `satisfied` | none | 75 | 87 | Yes | Yes | Fixture package remains critical for Gate C/D validation. |
| `crit_util_parallel` | `UTIL-PTM-001` | 7 | `SCHED-PTM-001A` | `satisfied` | none | 75 | 82 | No | Yes | Shorter G05B sibling is not critical in this fixture. |
| `crit_dispatch` | `DISPATCH-PTM-001` | 11 | `SCHED-PTM-001A` | `satisfied` | none | 75 | 86 | No | Yes | Dispatch is near-critical but shorter than validation fixture branch. |
| `crit_validation` | `TEST-PTM-001B` | 10 | `SCHED-PTM-001B`, `DISPATCH-PTM-001` | `satisfied` | none | 87 | 97 | Yes | Yes | Final validation waits for the later schedule fixture branch. |

## Negative validation cases

Future package-specific tests should include these invalid fixtures and assert explicit validation errors.

| Case | Invalid input | Expected error class | Required behavior |
|---|---|---|---|
| `missing_dependency` | A fixture depends on `PTM-NOT-REAL`. | `missing_dependency` | Fail validation; do not infer a placeholder task. |
| `cycle_detected` | `A` depends on `B`; `B` depends on `A`. | `cycle_detected` | Fail validation before calculating critical path. |
| `negative_duration` | `duration_minutes=-1`. | `invalid_duration` | Fail validation; do not normalize to zero. |
| `dispatch_ready_with_blocked_gate` | `expected_dispatch_ready=true` while `gate_state=blocked`. | `readiness_gate_violation` | Fail validation; readiness gates fail closed. |
| `blocked_interval_without_reason` | Blocked range lacks a reason label. | `invalid_blocked_interval` | Fail validation; all blocked time requires evidence. |

## Critical-path algorithm expectation

Future executable validation should use a deterministic directed acyclic graph calculation:

1. validate that every dependency references an existing fixture task;
2. reject cycles before schedule calculation;
3. calculate earliest start as the maximum earliest finish among dependencies;
4. apply blocked interval delay only when the interval overlaps the modeled earliest start-to-finish window;
5. calculate earliest finish as adjusted earliest start plus duration;
6. mark critical-path membership by walking backward from the latest project finish through predecessor edges that determine the longest path;
7. keep dispatch readiness separate from critical-path membership.

A task can be on the critical path and still not be dispatch-ready when a readiness gate is `blocked`, `unknown`, or `stale`.

## Promotion notes for a future Pending package

- The future implementation package should convert this artifact into machine-readable fixtures only after `SCHED-PTM-001A` freezes the schedule projection contract.
- Any machine-readable fixture path should remain under a validation or test-fixture tree and must not become a second PTM registry.
- Fixture IDs should remain stable to support evidence comparisons across Gate C/D reconciliation.
- Dispatch integration must consume readiness evidence from the accepted schedule contract; it must not create independent readiness authority.
