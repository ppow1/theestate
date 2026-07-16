# Estate PTM Schedule Validation Fixtures and Critical Path Plan

Status: Draft implementation-preparation artifact for PTM-05 Gate C/D
Campaign: PTM-05 — Scheduling, Utilization, Financials, and KPIs
Package: SCHED-PTM-001B
Date: 2026-07-16

## Authority and scope

This validation artifact satisfies SCHED-PTM-001B for future validation fixtures. It depends on the SCHED-PTM-001A schedule dependency and readiness-gate contract and preserves the frozen CORE-PTM-003B `schedule.current_state` projection fields.

The artifact is source-backed by the accepted Steward / Chief Architect PTM baseline, the PTM dependency and parallelism plan, the PTM parallel campaign execution plan, the package, campaign, and dependency manifests, the source SCHED-PTM-001B planning draft, the PTM backlog, WP-0659, WP-0660, SCHED-PTM-001A, and CORE-PTM-003B.

This is a documentation-only validation plan for future fixtures. It does not add production PTM code, execute a scheduler, dispatch work, create a second queue, create a second registry, approve schedules, approve budgets, certify readiness, or introduce a new governance authority.

## Fixture record shape

Future fixtures MUST be deterministic replay inputs and MUST label mock records as fixture data. Production source records, completion receipts, package manifests, and accepted authority records remain authoritative in place.

```yaml
schedule_validation_fixture:
  fixture_id: string
  description: string
  authority_context:
    package_id: SCHED-PTM-001B
    source_contract_refs: [string]
    fixture_only: true
  input_events: [object]
  input_schedule_records: [object]
  expected_schedule_records: [object]
  expected_readiness_states: [object]
  expected_critical_path:
    state: known | unknown | blocked
    task_ids: [string]
    warnings: [string]
  expected_warnings: [string]
  prohibited_side_effects:
    creates_dispatch_queue: false
    creates_registry: false
    creates_scheduler: false
    changes_governance_authority: false
```

Fixture records SHOULD use canonical PTM task IDs when available and otherwise use `FIXTURE-TASK-*` identifiers. Every fixture MUST include enough source references to explain each dependency, waiver, blocked interval, and warning.

## Required fixture set

| Fixture ID | Purpose | Minimum tasks | Required input condition | Expected result |
| --- | --- | ---: | --- | --- |
| `sched_ready_linear` | Linear dependency chain with all gates passing | 3 | A blocks B, B blocks C, all required gates pass | C is ready only after A and B are satisfied; A/B/C are all on the known critical path. |
| `sched_blocked_dependency` | Unsatisfied dependency gate | 2 | A blocks B, A lacks accepted completion or waiver evidence | B readiness is `blocked`; failed check reason is `dependency`. |
| `sched_waived_dependency` | Chief Architect waiver visibility | 2 | A blocks B and B carries an explicit waiver reference | Dependency remains visible with `satisfaction_state=waived`; B may become ready only if all other required gates pass or are waived. |
| `sched_unknown_estimate` | Missing duration evidence | 1 | Active estimate is absent or mandatory duration evidence is missing | Duration remains `null`; warning is emitted; critical-path certainty is `unknown` for affected path. |
| `sched_parallel_paths` | Deterministic longest-path selection | 5 | Two branches converge at a checkpoint with different known durations | Longer branch plus convergence task is critical; shorter branch has positive slack. |
| `sched_blocked_interval_overlap` | Multiple blocker reasons on one task | 1 | Two overlapping blocked intervals use different reason codes | Source intervals are preserved; summaries may group by reason without deleting overlaps. |
| `sched_gate_unknown` | Non-waived unknown readiness gate | 1 | At least one required readiness check is `unknown` and not waived | Readiness state remains `unknown`; dispatch-ready publication is blocked. |
| `sched_cycle_fail_closed` | Cycle detection | 3 | A blocks B, B blocks C, C blocks A | Affected subgraph publishes no known critical path; warning identifies cyclic dependency evidence. |
| `sched_over_60_exception_required` | Steward hour-scale estimate guardrail | 1 | Active estimate expected value exceeds 60 minutes without exception | Readiness publication is blocked until evidence-based exception or explicit authority waiver is present. |
| `sched_stale_projection_input` | Stale or incomplete source evidence | 2 | Projection high-watermark excludes a required dependency or gate event | Readiness and critical-path result are `unknown` or blocked with stale-input warning; no false ready state. |

## Critical-path calculation plan

Future implementations SHOULD validate the following algorithm against the required fixtures:

1. Build a directed dependency graph from `dependency_ref` records where each edge points from blocking task to blocked task.
2. Reject or quarantine any cyclic subgraph before publication; emit warnings and set critical-path state to `unknown` for affected tasks.
3. Preserve source order for equivalent dependency ranks so repeated projection rebuilds are deterministic.
4. Calculate node duration from separated minute fields: active execution, validation, expected rework, integration wait, queue wait, review wait, and currently known blocked dependency wait.
5. Keep `unknown` durations as unknown. Do not coerce `null`, stale, mandatory-missing, or conflicting values to zero.
6. Traverse the acyclic graph in topological order to calculate earliest known starts and finishes.
7. Traverse in reverse topological order to calculate latest known starts and finishes for the selected checkpoint or convergence task.
8. Mark zero-slack tasks on the longest fully known valid path with `critical_path_flag=true` and deterministic `critical_path_rank` values.
9. If any candidate longest path includes unknown duration, stale source evidence, or authority-conflicting evidence, publish `critical_path_rank=null` for affected tasks and include an explanatory warning.
10. Treat waived dependencies as visible graph edges with `satisfaction_state=waived`; waiver evidence may unblock readiness but must remain auditable in path explanations.

Critical-path output is advisory planning evidence only. It may support Traffic Controller / Operations Manager review but MUST NOT dispatch, assign, approve, or execute work.

## Readiness validation assertions

Future fixture tests MUST assert these readiness behaviors:

- A task is `ready` only when every required readiness check is `pass` or explicitly `waived`.
- Any non-waived `fail` produces `blocked` and preserves `failed_check_refs`.
- Any non-waived `unknown` produces `unknown` and prevents dispatch-ready publication.
- Waivers preserve authority references and do not delete dependencies, blocked intervals, or warnings.
- Active execution estimates above 15 minutes are review-labeled.
- Active execution estimates above 60 minutes require an evidence-based exception or explicit authority waiver before ready publication.
- Minute fields remain separated by duration type and are not replaced by day-scale estimates.
- Blocked intervals are append-only projection facts and may overlap by reason code.
- Stale, missing, conflicting, or cyclic dependency evidence emits warnings instead of false critical-path certainty.

## Evidence notes for future Pending promotion

- Dependency revalidation: the current accepted dependency manifest lists `SCHED-PTM-001B` as depending on `SCHED-PTM-001A`; this artifact does not change that dependency.
- Campaign revalidation: the accepted campaign model places `SCHED-PTM-001B` in PTM-05 launch group `G05B`, parallel-safe with `UTIL-PTM-001`, and reconciled through Gate C/D.
- Collision revalidation: the artifact touches only future validation fixture planning and does not mutate manifests, frozen projection schemas, event schemas, dispatch evidence, runtime code, or a shared queue.
- Estimate revalidation: the package remains bounded below 60 active minutes and no exception is required.
- Lane revalidation: Codex-only routing is preserved for this implementation cycle; the local RTX 4090 worker is not used.

## Non-goals and stop/replan triggers

Stop and replan before any future package uses this artifact to:

- redefine the CORE-PTM-003B schedule projection envelope or field names;
- change SCHED-PTM-001A readiness-gate semantics;
- create a runtime scheduler, new dispatch queue, new registry, or new governance authority;
- convert advisory critical-path output into automatic assignment, dispatch, budget approval, or acceptance;
- silently coerce unknown or stale estimates into ready, zero-duration, or on-time states.
