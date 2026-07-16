# Estate PTM KPI Registry Quality and Dashboard Contract

## Authority and scope

This implementation-ready planning contract satisfies KPI-PTM-001 for future KPI files. It extends the accepted PTM planning baseline, the frozen KPI projection contract, and the existing KPI, financial, and utilization catalog without flattening unknown data or creating a second registry.

This contract is documentation and validation guidance only. It authorizes future KPI registry files, projection validation, and dashboard consumption rules after the dependent utilization and financial contracts are accepted. It does not authorize production PTM code, a second dispatch queue, a second scheduler, a second KPI registry, or a new governance authority.

## Source-backed requirements

| Requirement | Source basis | Contract decision |
|---|---|---|
| KPI registry and observations depend on utilization and financials. | KPI-PTM-001 pending package and PTM backlog. | KPI definitions must declare utilization and financial source projections when formulas consume capacity, cost, spend, or overcommitment fields. |
| Unknown and stale KPI data must be protected. | PTM backlog acceptance summary and KPI/financial/utilization catalog. | Missing mandatory data publishes `unknown` or suppresses output; stale data publishes `stale` or suppresses output according to definition policy. |
| Dashboards are projections, not authority. | Accepted PTM baseline and generated-artifact policy. | Dashboard cards consume KPI projections only and expose source drilldowns to canonical evidence. |
| Campaign Gate C/D reconciles schedule, finance, KPI, and dispatch readiness. | Parallel campaign execution plan. | KPI definitions may not redefine frozen schedule, financial, utilization, dispatch, event, ID, or projection contracts. |

## KPI registry entry contract

Future registry entries use one canonical definition record per KPI. Registry files may be YAML or JSON, but each entry must preserve these fields and semantics:

```yaml
kpi_definition:
  kpi_id: string                    # Stable KPI-* identifier, never reused.
  kpi_name: string                  # Human-readable dashboard label.
  owner_ref: object                 # Role or accepted owner reference; not new governance authority.
  category: schedule | utilization | financial | validation | acceptance | governance | quality | efficiency
  formula: string                   # Deterministic formula over declared projection fields.
  numerator_definition: string
  denominator_definition: string | null
  unit: count | percent | minutes | hours | currency | ratio | boolean
  measurement_period: daily | weekly | monthly | campaign | package | rolling_7d | rolling_30d
  baseline: number | null           # Null when no accepted historical baseline exists.
  target: number | null             # Null when Chief Architect has not accepted a target.
  thresholds:
    - status: pass | watch | fail
      rule: string
  required_source_projection_refs:
    - projection: task | schedule | utilization | financial | validation | acceptance | audit | dispatch
      fields: [string]
      mandatory: boolean
  required_event_types: [string]
  exclusions: [string]
  freshness_sla_minutes: number | null
  confidence_rule: observed | telemetry_derived | estimated_allowed | observed_only
  unknown_value_behavior: suppress | publish_unknown | publish_with_warning
  stale_value_behavior: suppress | publish_stale | publish_with_warning
  manipulation_controls: [string]
  dashboard_contract_ref: string
```

## KPI projection record contract

KPI projections preserve the CORE-PTM-003B projection shape and add quality metadata needed by dashboards and validation:

```yaml
kpi_projection:
  kpi_item_id: string
  kpi_name: string
  definition_ref: object
  measurement_period: string
  period_start: string
  period_end: string
  numerator: number | null
  denominator: number | null
  value: number | null
  unit: string
  baseline: number | null
  target: number | null
  threshold: object | null
  status: pass | watch | fail | unknown | stale | suppressed
  source_projection_refs: [object]
  source_event_ids: [string]
  data_quality: complete | partial | stale | unknown | suppressed
  confidence_label: observed | telemetry_derived | estimated | unknown
  warnings: [string]
  generated_at: string
```

## Initial implementation-ready KPI catalog

The first future KPI registry should include these source-backed candidates. Baselines and targets remain `null` unless a future accepted package provides historical evidence or explicit Chief Architect targets.

| KPI ID | Name | Formula | Period | Baseline | Target | Quality rule | Dashboard status rule |
|---|---|---|---|---|---|---|---|
| `KPI-SCHED-001` | Schedule variance | `actual_finish_or_as_of - planned_finish` in days for closed or active tasks. | package, campaign, rolling_30d | `null` until schedule history is accepted | `null` until accepted | Requires schedule projection planned and actual/as-of dates; missing planned dates publish `unknown`. | `pass` when variance <= accepted threshold; `watch`/`fail` only after thresholds are configured. |
| `KPI-SCHED-002` | Blocked work percentage | `blocked_task_count / active_task_count * 100`. | daily, weekly, campaign | `null` | `null` | Requires task status and blocker state; if active denominator is zero, publish `unknown` with zero-denominator warning. | Never coerce zero denominator to 0%. |
| `KPI-VAL-001` | Validation pass rate | `passed_validation_runs / completed_validation_runs * 100`. | package, campaign, rolling_30d | `null` | `null` | Requires validation projection outcomes; pending or missing validation evidence is excluded and warned. | Unknown until at least one completed validation run exists. |
| `KPI-ACC-001` | Acceptance pass rate | `accepted_packages / reviewed_packages * 100`. | campaign, rolling_30d | `null` | `null` | Requires acceptance records; review-pending packages are excluded from denominator and shown as warning count. | Dashboard must separate validation success from institutional acceptance. |
| `KPI-UTIL-001` | Utilization or overcommitment | `committed_capacity / available_capacity * 100`. | daily, weekly, rolling_7d | `null` | `null` | Requires UTIL-PTM-001 capacity labels; estimated capacity publishes with `estimated` confidence. | `stale` when capacity telemetry exceeds freshness SLA. |
| `KPI-FIN-001` | Cost variance | `(actual_cost - approved_budget) / approved_budget * 100`. | package, campaign, monthly | `null` | `null` | Requires approved budget and actual/reconciled cost; missing budget publishes `unknown`. | Budget authority must remain outside Helen/Grace unless separately accepted. |
| `KPI-FIN-002` | Cost per accepted task | `total_reconciled_cost / accepted_task_count`. | campaign, monthly | `null` | `null` | Requires accepted task count and reconciled costs; zero accepted denominator publishes `unknown`. | Show currency unit and source reconciliation warnings. |
| `KPI-AUDIT-001` | Audit-chain integrity | `items_with_valid_event_and_evidence_chain / audited_items * 100`. | package, campaign | `null` | `null` | Requires event IDs, evidence refs, hash-chain validation, and causation refs; missing mandatory evidence publishes `fail` only when validation completed, otherwise `unknown`. | Dashboard links to evidence gaps instead of summarizing them away. |
| `KPI-QUAL-001` | Freshness compliance | `fresh_projection_count / required_projection_count * 100`. | daily, campaign | `null` | `null` | Requires freshness SLA per consumed projection; missing timestamps publish `unknown`. | Stale and unknown counts must be visible as badges. |

## Formula, period, baseline, and target rules

1. Formulas must be deterministic expressions over declared projection fields and immutable evidence references.
2. Measurement periods must be explicit and must include period start/end in projections.
3. Baselines remain `null` until historical data is accepted; future implementations must not invent baselines from partial migrations.
4. Targets remain `null` until accepted by the Chief Architect, Steward, or another already-authorized owner for that KPI domain.
5. A KPI with `baseline=null` or `target=null` may display current value, but dashboard copy must state that no accepted baseline or target exists.
6. Denominator zero, missing mandatory fields, malformed timestamps, and missing evidence references are quality events, not numeric zeros.

## Stale, unknown, and confidence rules

| Condition | Required projection behavior | Required dashboard behavior |
|---|---|---|
| Mandatory source field missing | `data_quality=unknown`; `status=unknown` or `suppressed`. | Show `Unknown` or hide the card only when definition says `suppress`; never show zero. |
| Mandatory source projection stale | `data_quality=stale`; `status=stale` or `suppressed`. | Show stale badge with age and source drilldown. |
| Optional source field missing | `data_quality=partial`; warning added. | Show warning badge without changing value if formula remains valid. |
| Estimated source value used | `confidence_label=estimated`. | Show estimated badge and link to source. |
| Telemetry-derived value used | `confidence_label=telemetry_derived`. | Show telemetry badge and sampling/freshness warning when available. |
| Formula denominator is zero or null | `value=null`; `status=unknown`; warning added. | Show denominator warning; do not render as 0%, infinity, or pass. |
| Integrity check fails after validation completes | `status=fail` when the KPI definition declares the check mandatory. | Show fail and source drilldown; do not allow dashboard-only override. |

## Dashboard contract

Dashboards consume KPI projections only. They are generated views and may not become canonical task, finance, schedule, utilization, or acceptance sources.

A dashboard card contains:

```yaml
dashboard_kpi_card:
  card_id: string
  kpi_ref: object
  display_name: string
  period_label: string
  value_display: string
  baseline_display: string | null
  target_display: string | null
  status: pass | watch | fail | unknown | stale | suppressed
  confidence_label: observed | telemetry_derived | estimated | unknown
  source_drilldown_refs: [object]
  warning_badges: [string]
  generated_at: string
```

Dashboard views must:

- make stale, unknown, estimated, telemetry-derived, partial, and suppressed states visible;
- provide drilldowns to source projections, event IDs, and evidence refs;
- distinguish validation outcomes from acceptance outcomes;
- distinguish approved budget, estimated cost, actual cost, and reconciled cost;
- avoid new approvals, routing decisions, budget authority, or queue state transitions;
- avoid coercing `unknown`, stale, suppressed, or zero-denominator values into passing values.

## Validation artifact expectations for future packages

Future implementation packages should include a small validation fixture covering:

1. complete observed KPI projection;
2. missing mandatory source field producing `unknown`;
3. stale utilization or financial source producing `stale`;
4. zero denominator producing `unknown` rather than zero;
5. estimated capacity or cost carrying an `estimated` confidence label;
6. dashboard card preserving warning badges and source drilldown refs.

## Boundary rules

- This contract adds KPI definition and dashboard consumption rules only.
- No second KPI registry, dispatch queue, scheduler, projection authority, or governance authority is introduced.
- No production PTM code is authorized by this package.
- Frozen upstream event, ID, projection, schedule, utilization, financial, dispatch, and validation contracts must not be redefined by KPI files.
