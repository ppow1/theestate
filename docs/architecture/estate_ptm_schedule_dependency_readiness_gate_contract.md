# Estate PTM Schedule Dependency and Readiness Gate Contract

## Authority and scope

This implementation-ready planning contract satisfies SCHED-PTM-001A for future schedule projection files. It extends the frozen CORE-PTM-003B schedule projection without redefining the shared projection envelope, event envelope, command envelope, ID minting, dispatch queue, registry, scheduler, or governance authority.

## Schedule item identity

Schedule records use deterministic projection IDs derived from canonical task IDs and source event high-watermarks.

Required fields:

- `schedule_item_id`: `SCHED-{task_id}-{projection_version}` or equivalent deterministic projection key.
- `task_id`: canonical PTM task identifier.
- `project_id`: canonical PTM project identifier when known.
- `dependency_ids`: ordered dependency references.
- `readiness_gate`: readiness gate state object defined below.
- `critical_path_flag`: boolean calculated by a downstream critical-path projection.
- `blocked_reason`: normalized blocked reason or `null`.
- `active_estimate_minutes`, `validation_estimate_minutes`, `rework_allowance_minutes`, `queue_wait_minutes`, `review_wait_minutes`, and `expected_wall_clock_minutes`.
- `blocked_intervals`: ordered blocked interval objects.
- `date_window`: nullable date window object.
- `warnings`: projection warnings.

## Date and duration rules

- `date_window.not_before`, `date_window.target_start`, `date_window.target_finish`, and `date_window.not_after` are ISO-8601 dates or timestamps.
- Active, validation, rework, queue, review, blocked, and integration durations are stored separately in minutes.
- Day-based values are display-only secondary conversions and may not replace minute fields.
- Unknown estimates remain `null` with a warning; projections must not infer false precision.
- Expected wall-clock equals active execution plus validation, expected rework, integration, queue, review, and currently known blocked dependency wait.

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

## Evidence and collision controls

- This document adds a future projection contract only.
- No production PTM code is authorized.
- No second dispatch queue, registry, scheduler, or governance authority is introduced.
