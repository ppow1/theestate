# Estate PTM KPI Registry Quality and Dashboard Contract

## Authority and scope

This implementation-ready planning contract satisfies KPI-PTM-001 for future KPI files. It extends the frozen KPI projection and existing KPI, financial, and utilization catalog without flattening unknown data or creating a second registry.

## KPI registry entry

```yaml
kpi_definition:
  kpi_id: string
  kpi_name: string
  owner_ref: object
  formula: string
  numerator_definition: string
  denominator_definition: string | null
  measurement_period: string
  baseline: number | null
  target: number | null
  thresholds: [object]
  required_source_projection_refs: [object]
  required_event_types: [string]
  exclusions: [string]
  freshness_sla_minutes: number | null
  confidence_rule: string
  unknown_value_behavior: suppress | publish_unknown | publish_with_warning
  manipulation_controls: [string]
```

## KPI projection record

KPI projections preserve CORE-PTM-003B fields and add quality metadata:

```yaml
kpi_projection:
  kpi_item_id: string
  kpi_name: string
  definition_ref: object
  measurement_period: string
  numerator: number | null
  denominator: number | null
  value: number | null
  threshold: object | null
  status: pass | watch | fail | unknown | stale
  source_projection_refs: [object]
  source_event_ids: [string]
  data_quality: complete | partial | stale | unknown | suppressed
  confidence_label: observed | telemetry_derived | estimated | unknown
  warnings: [string]
```

## Formula and quality rules

- Required source projections and event types must be declared before publication.
- Missing mandatory data yields `status=unknown` or suppression according to `unknown_value_behavior`.
- Stale source projections yield `status=stale` unless the KPI definition suppresses stale output.
- Estimated and telemetry-derived values must carry confidence labels.
- Manipulation controls define exclusions, outlier handling, source integrity checks, and audit-chain checks.

## Dashboard contract

Dashboards consume KPI projections only. A dashboard card contains:

```yaml
dashboard_kpi_card:
  card_id: string
  kpi_ref: object
  display_name: string
  period_label: string
  value_display: string
  status: pass | watch | fail | unknown | stale
  confidence_label: observed | telemetry_derived | estimated | unknown
  source_drilldown_refs: [object]
  warning_badges: [string]
```

Dashboard views must make stale, unknown, estimated, and suppressed states visible. They may not coerce unknown values to zero.

## Initial KPI groups

Initial future registry candidates include schedule variance, blocked percentage, validation pass rate, acceptance pass rate, utilization/overcommitment, cost variance, cost per accepted task, audit-chain integrity, and freshness compliance.

## Boundary rules

- This contract adds KPI definition and dashboard consumption rules only.
- No second KPI registry or governance authority is introduced.
- No production PTM code is authorized.
- No second dispatch queue or second scheduler is introduced.
