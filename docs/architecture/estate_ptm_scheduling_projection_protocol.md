# Estate PTM Schedule, Financial, Utilization, KPI, and Timeline Projection Contracts

Status: Draft implementation-preparation artifact for PTM-02 Gate B
Campaign: PTM-02 — Canonical ledger and projection contracts
Package: CORE-PTM-003B
Date: 2026-07-16

## Authority and boundaries

This artifact freezes the CORE-PTM-003B deterministic projection contracts for schedule, financial, utilization, KPI, and timeline read models. It is source-backed by the accepted PTM baseline, the PTM dependency and parallelism plan, the PTM parallel campaign execution plan, the CORE-PTM-003A projection envelope, the WP-0660 hour-scale timeline correction, and the WP-0659 preliminary execution-lane analysis.

This artifact is documentation-only. It does not authorize production PTM code, mutate authoritative source records, dispatch work, approve schedules, approve budgets, certify KPI outcomes, create a second dispatch queue, create a second registry, create a second scheduler, or introduce a new governance authority. Work-package files, Parking Lot records, dispatch evidence, validation reports, resident and operations records, budget approvals, acceptance records, and completion receipts remain authoritative in place.

## Shared replay and envelope requirements

All projection records in this artifact MUST reuse the shared projection envelope frozen by CORE-PTM-003A. Builders may add the domain fields defined below, but they must not change envelope field names, status vocabulary, event provenance requirements, stale handling, or authority-boundary warnings without a stop/replan note at PTM-02 Gate B.

Replay rules:

1. Validate the append-only event stream and hash chain before computing any derived record.
2. Apply source-backed correction events after the corrected event while preserving both in audit traces.
3. Join schedule, financial, utilization, KPI, and timeline records to project/task projections only through canonical PTM IDs, source references, explicit causation/correlation links, or adapter-backed evidence references.
4. Treat absent values as `unknown`, not zero, false, approved, ready, or accepted.
5. Preserve data-quality labels for estimated, optional, stale, conflicting, telemetry-derived, imported, and authority-waived values.
6. Emit `stale: true` whenever the projection was built from an incomplete event set or an input source is known stale.

## Common quality labels

Projection fields that are not directly evented facts MUST expose their quality. The closed set is:

`observed`, `imported`, `estimated`, `derived`, `optional_missing`, `mandatory_missing`, `stale`, `conflicting`, `waived`, `unknown`

Rules:

- `mandatory_missing` blocks readiness, KPI publication, financial approval, or acceptance decisions that require the missing value.
- `estimated` and `derived` values may support planning forecasts but must not masquerade as actuals.
- `waived` requires an explicit authority reference and must remain visible to downstream validation.
- `unknown` is a safe terminal display state for absent data; consumers must not coerce it to zero.

## Schedule projection contract

Projection name: `schedule.current_state`

```yaml
schedule_current_state:
  envelope: ptm_projection_record
  schedule_id: string
  task_id: string
  project_id: string | null
  dependency_ids: [string]
  blocked_by_ids: [string]
  calendar_ref: string | null
  planned_start_at: string | null
  planned_finish_at: string | null
  earliest_start_at: string | null
  earliest_finish_at: string | null
  latest_start_at: string | null
  latest_finish_at: string | null
  active_execution_minutes:
    best: integer | null
    expected: integer | null
    conservative: integer | null
    confidence: low | medium | high | unknown
    basis: string | null
    quality: observed | imported | estimated | derived | optional_missing | mandatory_missing | stale | conflicting | waived | unknown
  validation_minutes:
    best: integer | null
    expected: integer | null
    conservative: integer | null
    confidence: low | medium | high | unknown
    basis: string | null
    quality: observed | imported | estimated | derived | optional_missing | mandatory_missing | stale | conflicting | waived | unknown
  expected_rework_minutes:
    best: integer | null
    expected: integer | null
    conservative: integer | null
    confidence: low | medium | high | unknown
    basis: string | null
    quality: observed | imported | estimated | derived | optional_missing | mandatory_missing | stale | conflicting | waived | unknown
  queue_wait_minutes:
    best: integer | null
    expected: integer | null
    conservative: integer | null
    quality: observed | imported | estimated | derived | optional_missing | mandatory_missing | stale | conflicting | waived | unknown
  review_wait_minutes:
    best: integer | null
    expected: integer | null
    conservative: integer | null
    quality: observed | imported | estimated | derived | optional_missing | mandatory_missing | stale | conflicting | waived | unknown
  blocked_dependency_wait_minutes:
    best: integer | null
    expected: integer | null
    conservative: integer | null
    quality: observed | imported | estimated | derived | optional_missing | mandatory_missing | stale | conflicting | waived | unknown
  critical_path_rank: integer | null
  readiness_state: unknown | not_ready | ready | blocked | dispatched | validating | accepted
  readiness_gate_refs: [string]
  exception_required: boolean
  exception_reason: string | null
  warnings: [string]
```

Schedule projections express timing and readiness. They do not dispatch work or create a scheduler. `active_execution_minutes.expected` above 15 minutes must be flagged for review, and above 60 minutes requires an evidence-based exception. Calendar and dependency records are advisory projections until separately accepted by the schedule packages.

## Financial projection contract

Projection name: `financial.current_state`

```yaml
financial_current_state:
  envelope: ptm_projection_record
  financial_record_id: string
  task_id: string | null
  project_id: string | null
  portfolio_id: string | null
  budget_authority_refs: [string]
  approval_refs: [string]
  estimate_records:
    - estimate_id: string
      cost_type: local_compute | external_provider | staff_time | tooling | other
      amount: number | null
      currency: string | null
      unit: dollars | minutes | hours | credits | tokens | unknown
      basis: string | null
      quality: observed | imported | estimated | derived | optional_missing | mandatory_missing | stale | conflicting | waived | unknown
  actual_records:
    - actual_id: string
      cost_type: local_compute | external_provider | staff_time | tooling | other
      amount: number | null
      currency: string | null
      unit: dollars | minutes | hours | credits | tokens | unknown
      source_ref: string
      quality: observed | imported | estimated | derived | optional_missing | mandatory_missing | stale | conflicting | waived | unknown
  variance:
    amount: number | null
    percent: number | null
    quality: observed | imported | estimated | derived | optional_missing | mandatory_missing | stale | conflicting | waived | unknown
  reconciliation_state: unknown | unreconciled | pending_review | reconciled | rejected | waived
  budget_ready: boolean | null
  budget_ready_reason: string | null
  warnings: [string]
```

Financial projections expose budget, estimate, actual, approval, and reconciliation evidence without granting spending authority. `budget_ready` may be true only when source-backed budget gates or explicit authority waivers are present; otherwise it must be false or null with warnings.

## Utilization projection contract

Projection name: `utilization.current_state`

```yaml
utilization_current_state:
  envelope: ptm_projection_record
  utilization_record_id: string
  subject_type: worker | provider | local_compute | lane | project | task
  subject_ref: string
  period_start_at: string
  period_end_at: string
  capacity_minutes: integer | null
  committed_minutes: integer | null
  productive_minutes: integer | null
  blocked_minutes: integer | null
  idle_minutes: integer | null
  validation_rework_minutes: integer | null
  overcommitted_minutes: integer | null
  queued_minutes: integer | null
  local_compute_metrics:
    gpu_active_minutes: integer | null
    gpu_reserved_minutes: integer | null
    vram_peak_mb: integer | null
    cpu_active_minutes: integer | null
    storage_gb_hours: number | null
    power_kwh: number | null
  provider_metrics:
    provider_name: string | null
    quota_used: number | null
    quota_limit: number | null
    rate_limit_events: integer | null
    availability_state: available | degraded | unavailable | unknown
  data_quality_by_field: object
  utilization_state: unknown | underutilized | balanced | saturated | overcommitted | unavailable
  warnings: [string]
```

Utilization projections measure capacity and telemetry labels for workers, providers, lanes, and local compute. They are observational and must not assign work, reserve compute, or override Traffic Controller or Operations decisions.

## KPI projection contract

Projection name: `kpi.observation`

```yaml
kpi_observation:
  envelope: ptm_projection_record
  kpi_id: string
  kpi_name: string
  kpi_category: project | task | worker_provider | operational | governance_quality | financial_efficiency
  owner_ref: string
  period_start_at: string
  period_end_at: string
  formula_ref: string
  numerator:
    value: number | null
    quality: observed | imported | estimated | derived | optional_missing | mandatory_missing | stale | conflicting | waived | unknown
    source_event_ids: [string]
  denominator:
    value: number | null
    quality: observed | imported | estimated | derived | optional_missing | mandatory_missing | stale | conflicting | waived | unknown
    source_event_ids: [string]
  value: number | string | null
  unit: percent | count | minutes | dollars | ratio | state | unknown
  baseline_value: number | string | null
  target_value: number | string | null
  trend: improving | stable | worsening | not_applicable | unknown
  thresholds:
    warning: number | string | null
    critical: number | string | null
  exclusions: [string]
  freshness_state: fresh | stale | unavailable | unknown
  confidence: low | medium | high | unknown
  publication_state: publishable | publish_with_warning | suppressed | unknown
  suppression_reason: string | null
  manipulation_controls: [string]
  warnings: [string]
```

KPI projections protect against false operational confidence. Mandatory missing values, stale source windows, conflicting inputs, or formula violations must set `publication_state` to `suppressed` or `publish_with_warning`; they must not publish fabricated zeroes. KPI IDs and formulas may be cataloged by KPI-PTM-001, but this contract fixes the observation shape consumed by validation and dashboards.

## Timeline scenario projection contract

Projection name: `timeline.scenario`

```yaml
timeline_scenario:
  envelope: ptm_projection_record
  scenario_id: string
  scenario_name: conservative | balanced | aggressive | custom
  scope_refs: [string]
  assumptions: [string]
  active_execution_minutes:
    best: integer | null
    expected: integer | null
    conservative: integer | null
  validation_minutes:
    best: integer | null
    expected: integer | null
    conservative: integer | null
  rework_minutes:
    best: integer | null
    expected: integer | null
    conservative: integer | null
  integration_minutes:
    best: integer | null
    expected: integer | null
    conservative: integer | null
  queue_wait_minutes:
    best: integer | null
    expected: integer | null
    conservative: integer | null
  human_review_wait_minutes:
    best: integer | null
    expected: integer | null
    conservative: integer | null
  blocked_dependency_wait_minutes:
    best: integer | null
    expected: integer | null
    conservative: integer | null
  machine_active_minutes:
    best: integer | null
    expected: integer | null
    conservative: integer | null
  wall_clock_elapsed_minutes:
    best: integer | null
    expected: integer | null
    conservative: integer | null
  secondary_wall_clock_days:
    best: number | null
    expected: number | null
    conservative: number | null
    basis: string | null
  critical_path_refs: [string]
  parallel_group_refs: [string]
  confidence: low | medium | high | unknown
  warnings: [string]
```

Timeline scenarios use minutes and hours as the primary planning units. Days may appear only as secondary wall-clock conversions when external wait, queue, or review latency justifies them. This contract intentionally rejects the prior day-scale model as authoritative and preserves hour-scale active execution assumptions for PTM planning.

## Cross-projection invariants

- Schedule readiness depends on explicit readiness gate references and must not be inferred from a task status label alone.
- Financial readiness depends on approval or waiver authority references and must not be inferred from a positive estimate or low variance.
- Utilization records must label mandatory, optional, estimated, observed, and telemetry-derived data independently for each material field.
- KPI observations must trace numerator and denominator inputs to events or immutable evidence; incomplete traceability suppresses publication when mandatory.
- Timeline scenarios must identify active execution, validation, rework, integration, queue wait, human review wait, blocked dependency wait, machine-active time, and wall-clock elapsed time separately.
- Downstream UI, scheduling, finance, utilization, KPI, dispatch, migration, validation, and rollout packages may consume these projections but must not redefine their field semantics after PTM-02 Gate B.

## Deterministic validation expectations

Future implementation and TEST-PTM packages should validate this contract with fixtures that prove:

- identical event inputs produce byte-for-byte identical schedule, financial, utilization, KPI, and timeline projection JSON after deterministic key ordering;
- missing mandatory schedule or budget evidence blocks readiness and preserves warning details;
- estimated financial and utilization values remain labeled and are not promoted to actuals;
- KPI observations suppress or warn on mandatory missing, stale, conflicting, or unknown inputs;
- hour-scale timeline calculations remain separate from external queue/review wall-clock waits;
- stale high-watermark inputs set `stale: true` and preserve the triggering source or event references.

## Downstream handoff requirements

- SCHED-PTM-001A/B may implement schedule dependency, readiness gate, fixture, and critical-path details using `schedule.current_state` without redefining the PTM projection envelope.
- FIN-PTM-001 may implement budget, cost, approval, and reconciliation workflows using `financial.current_state` without implying delegated budget authority.
- UTIL-PTM-001 may implement capacity and telemetry observations using `utilization.current_state` without creating a scheduler or dispatch queue.
- KPI-PTM-001 may implement formula registry and dashboard rules using `kpi.observation` without flattening unknown or stale data.
- TEST-PTM packages must treat this document and CORE-PTM-003A as the Gate B projection freeze unless a stop/replan note changes the contract.

## Evidence note

CORE-PTM-003B is complete when this artifact is committed with a completion receipt and `git diff --check` evidence. The artifact freezes deterministic schedule, financial, utilization, KPI, and timeline projection contracts for downstream implementation planning without adding production PTM code or creating a parallel queue, registry, scheduler, or governance authority.
