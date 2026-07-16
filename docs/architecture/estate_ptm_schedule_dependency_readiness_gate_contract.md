# Estate PTM Schedule Dependency and Readiness Gate Contract

Status: Draft implementation-preparation artifact for PTM-05 Gate C/D
Campaign: PTM-05 — Scheduling, Utilization, Financials, and KPIs
Package: SCHED-PTM-001A
Date: 2026-07-16

## Authority and scope

This implementation-ready planning contract satisfies SCHED-PTM-001A for future schedule projection files. It extends the frozen CORE-PTM-003B `schedule.current_state` projection without redefining the shared projection envelope, event envelope, command envelope, ID minting, dispatch queue, registry, scheduler, or governance authority.

The contract is source-backed by the accepted PTM baseline, the PTM dependency and parallelism plan, the PTM parallel campaign execution plan, the PTM package/campaign/dependency manifests, the WP-0660 hour-scale timeline correction, and the WP-0659 execution-lane analysis. It is documentation-only: it does not authorize production PTM code, mutate authoritative source records, dispatch work, approve schedules, approve budgets, certify readiness, or merge any implementation branch.

## Relationship to CORE-PTM-003B

CORE-PTM-003B remains the frozen authority for the shared `schedule.current_state` projection shape. SCHED-PTM-001A adds the behavior required to compute and validate date, duration, dependency, critical-path, blocked-interval, and readiness-gate fields inside future schedule projections.

Future builders MUST:

1. Reuse the CORE-PTM-003A projection envelope and CORE-PTM-003B schedule field names wherever they already exist.
2. Treat this document as a behavioral contract for the schedule-specific subrecords and algorithms below.
3. Emit warnings instead of inventing values when required source evidence is absent.
4. Stop and replan before changing frozen upstream projection, event, dispatch, registry, scheduler, or governance contracts.

## Schedule item identity

Schedule records use deterministic projection IDs derived from canonical task IDs and source event high-watermarks.

Required fields:

- `schedule_item_id`: `SCHED-{task_id}-{projection_version}` or equivalent deterministic projection key.
- `task_id`: canonical PTM task identifier.
- `project_id`: canonical PTM project identifier when known.
- `dependency_ids`: ordered dependency references.
- `readiness_gate`: readiness gate state object defined below.
- `critical_path_flag`: boolean calculated by a downstream critical-path projection.
- `critical_path_rank`: integer or `null`; lower values represent earlier critical-path ordering.
- `blocked_reason`: normalized active blocked reason or `null`.
- `active_estimate_minutes`, `validation_estimate_minutes`, `rework_allowance_minutes`, `queue_wait_minutes`, `review_wait_minutes`, `integration_wait_minutes`, `blocked_dependency_wait_minutes`, and `expected_wall_clock_minutes`.
- `blocked_intervals`: ordered blocked interval objects.
- `date_window`: nullable date window object.
- `warnings`: projection warnings.

## Date and duration rules

- `date_window.not_before`, `date_window.target_start`, `date_window.target_finish`, and `date_window.not_after` are ISO-8601 dates or timestamps.
- Active, validation, rework, queue, review, blocked, and integration durations are stored separately in minutes.
- Day-based values are display-only secondary conversions and may not replace minute fields.
- Unknown estimates remain `null` with a warning; projections must not infer false precision.
- Expected wall-clock equals active execution plus validation, expected rework, integration, queue, review, and currently known blocked dependency wait.
- Active execution estimates above 15 minutes require review labeling; active execution estimates above 60 minutes require an evidence-based exception and MUST NOT publish as ready without that exception or an explicit authority waiver.
- Review latency, queue wait, merge delay, Steward availability, failed validation, rework, and blocked dependencies are reported separately from active execution time.

## Dependency contract

Dependency entries contain:

```yaml
dependency_ref:
  dependency_id: string
  dependency_type: blocks | blocked_by | finish_to_start | start_to_start | evidence_required | approval_required
  source_task_id: string
  target_task_id: string
  source_event_ids: [string]
  authority_refs: [object]
  satisfaction_state: unsatisfied | satisfied | waived | unknown
  waiver_ref: object | null
  warnings: [string]
```

Dependencies are satisfied only by accepted completion evidence, explicit Chief Architect waiver, or another frozen authority record. A waiver does not delete the dependency; it changes `satisfaction_state` and preserves `waiver_ref`.

For SCHED-PTM-001A itself, the governing package dependency is `CORE-PTM-003B`. Downstream packages consuming this contract include SCHED-PTM-001B, UTIL-PTM-001, DISPATCH-PTM-001, and TEST-PTM-001A through the accepted dependency manifest.

## Critical-path behavior

Future critical-path projections MUST:

1. Build a directed acyclic dependency graph from canonical task IDs and `dependency_ref` records.
2. Preserve source order for equivalent dependency ranks to keep rebuilds deterministic.
3. Mark `critical_path_flag=true` for tasks whose expected duration and dependency chain determine the longest known path to the relevant integration checkpoint.
4. Set `critical_path_rank=null` and emit a warning when dependency evidence is cyclic, missing, stale, or authority-conflicting.
5. Treat waived dependencies as visible edges with `satisfaction_state=waived`; they may unblock readiness but remain auditable in path explanations.

Critical-path output is advisory planning evidence only. It may inform Traffic Controller / Operations Manager review but must not dispatch, assign, approve, or execute work.

## Readiness gate behavior

Readiness gate state contains:

```yaml
readiness_gate:
  state: not_ready | ready | blocked | waived | unknown
  evaluated_at: string
  required_checks:
    dependency_gate: pass | fail | waived | unknown
    schedule_gate: pass | fail | waived | unknown
    capacity_gate: pass | fail | waived | unknown
    budget_gate: pass | fail | waived | unknown
    validation_plan_gate: pass | fail | waived | unknown
    read_write_boundary_gate: pass | fail | waived | unknown
    acceptance_owner_gate: pass | fail | waived | unknown
  failed_check_refs: [object]
  waiver_refs: [object]
  source_event_ids: [string]
  warnings: [string]
```

A task is `ready` only when every required check is `pass` or explicitly `waived`. Any `fail` produces `blocked`; any non-waived `unknown` produces `unknown` and prevents dispatch-ready publication.

Readiness labels used by future dispatch, utilization, migration, and validation packages MUST be derived from this gate state. No consumer may convert `unknown`, `not_ready`, or `blocked` into `ready` without accepted source evidence or an explicit waiver reference.

## Blocked interval contract

Blocked intervals are append-only projection facts built from canonical events:

```yaml
blocked_interval:
  blocked_interval_id: string
  task_id: string
  started_at: string
  ended_at: string | null
  reason_code: dependency | capacity | budget | validation | authority | source_missing | other
  source_event_ids: [string]
  authority_refs: [object]
  active: boolean
```

Intervals may overlap when different reason codes apply. Projections may summarize total blocked minutes by reason but must preserve the source intervals.

An interval is active when `ended_at` is `null` or later than the projection high-watermark. Closing an interval requires source evidence showing the dependency, capacity, budget, validation, authority, or source-missing condition was resolved or waived.

## Validation expectations for future implementation

Future implementation packages that build or consume this contract must validate at least the following cases:

- ready publication is blocked when any required readiness check is `fail`;
- ready publication is blocked when any required readiness check is non-waived `unknown`;
- waived dependencies remain visible in dependency and critical-path explanations;
- minute-scale active, validation, queue, review, integration, and blocked durations remain separated;
- active estimates above 15 minutes are review-flagged and estimates above 60 minutes require an exception;
- blocked intervals are append-only and can overlap by reason code;
- cycles or missing dependency evidence produce warnings instead of false critical-path certainty.

## Evidence and collision controls

- This document adds a future projection contract only.
- No production PTM code is authorized.
- No second dispatch queue, registry, scheduler, or governance authority is introduced.
- Future promotion must coordinate SCHED-PTM-001A/DISPATCH-PTM-001 readiness-gate collisions through the Gate C/D schedule/finance/KPI reconciliation checkpoint.
