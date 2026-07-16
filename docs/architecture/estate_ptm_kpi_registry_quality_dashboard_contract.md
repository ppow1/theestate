# Estate PTM KPI Registry Quality and Dashboard Contract

Package: KPI-PTM-001
Status: Implementation-ready planning contract
Date: 2026-07-16

## 1. Authority and scope

This document satisfies `KPI-PTM-001` by defining the future KPI registry, quality rules, formulas, periods, baselines, targets, stale/unknown handling, and dashboard consumption contract for Estate PTM KPI files.

The contract is source-backed by the accepted PTM baseline, the PTM parallel execution plan, the dependency and parallelism plan, the package/campaign/dependency manifests, the KPI planning draft, the WP-0660 hour-scale correction package, the WP-0659 execution-lane report, the CORE-PTM-003B projection contract, the FIN-PTM-001 financial reconciliation contract, the UTIL-PTM-001 utilization observation contract, and the existing KPI/financial/utilization catalog.

This is a planning and validation artifact only. It does not add production PTM code, authorize spend, approve budgets, select providers, create a second task registry, create a second KPI registry, create a second scheduler, create a second dispatch queue, or introduce a new governance authority.

## 2. Upstream dependency contract

`KPI-PTM-001` is downstream of `UTIL-PTM-001` and `FIN-PTM-001`. A future implementation may publish a KPI only when all mandatory utilization and financial inputs declared by the KPI definition are present, fresh, and traceable, or when the KPI definition explicitly permits an unknown, stale, suppressed, or warning state.

KPI observations consume the frozen CORE-PTM-003B KPI projection surface. Future KPI files may refine definitions, formulas, thresholds, and dashboard display rules, but they must not rename or reinterpret the shared projection envelope, event IDs, command IDs, authority references, source references, or replay semantics.

## 3. Canonical KPI registry entry

Each KPI registry entry must be defined as data, not hard-coded dashboard behavior. The minimum registry shape is:

```yaml
kpi_definition:
  kpi_id: KPI-<stable-id>
  kpi_name: string
  kpi_group: schedule | task | worker_provider | operational | governance_quality | financial_efficiency
  owner_ref:
    actor_id: string
    authority_role: string
  objective: string
  formula: string
  numerator_definition: string
  denominator_definition: string | null
  measurement_period:
    grain: task | work_package | week | month | quarter | campaign | rolling_window
    start_rule: string
    end_rule: string
    timezone: UTC
  baseline:
    value: number | null
    source_ref: object | null
    period_label: string | null
  target:
    value: number | null
    direction: higher_is_better | lower_is_better | in_range
    period_label: string | null
  thresholds:
    pass: object | null
    watch: object | null
    fail: object | null
  required_source_projection_refs:
    - projection_name: string
      field_path: string
      required: true
  optional_source_projection_refs:
    - projection_name: string
      field_path: string
      required: false
  required_event_types:
    - string
  exclusions:
    - string
  freshness_sla_minutes: number | null
  confidence_rule: observed_only | allow_telemetry_derived | allow_estimated_with_warning
  unknown_value_behavior: suppress | publish_unknown | publish_with_warning
  stale_value_behavior: suppress | publish_stale | publish_with_warning
  manipulation_controls:
    - source_integrity_check
    - audit_chain_check
    - exclusion_review
    - outlier_review
```

Registry entries must keep formulas, periods, baselines, targets, exclusions, freshness, confidence, and manipulation controls together so dashboards and validation tests can verify that a KPI is not being presented with false precision.

## 4. KPI projection observation

A KPI observation is a projection derived from canonical events and source projections. It must preserve the CORE-PTM-003B projection relationship and include quality metadata:

```yaml
kpi_projection:
  kpi_item_id: KPI-OBS-<stable-id>
  kpi_definition_id: KPI-<stable-id>
  kpi_name: string
  measurement_period:
    period_start: datetime
    period_end: datetime
    period_label: string
  numerator: number | null
  denominator: number | null
  value: number | null
  baseline_value: number | null
  target_value: number | null
  threshold_status: pass | watch | fail | unknown | stale | suppressed
  publication_state: publish | publish_with_warning | publish_unknown | publish_stale | suppressed
  source_projection_refs:
    - projection_name: string
      projection_id: string
      field_path: string
  source_event_ids:
    - string
  data_quality: complete | partial | stale | unknown | conflicting | suppressed
  confidence_label: observed | telemetry_derived | estimated | unknown
  freshness_checked_at: datetime
  warnings:
    - string
```

The projection must not fabricate zeroes for missing values. `null` remains `null`; unknown remains `unknown`; stale remains `stale`; suppressed values remain visibly suppressed with a warning reason.

## 5. Formula, period, baseline, and target rules

1. **Formula declaration:** Every KPI must declare numerator, denominator when applicable, formula text, required source projections, required event types, and exclusions before publication.
2. **Period declaration:** Every KPI must declare its measurement grain and period start/end rules. Dashboards may display friendly period labels, but period computation remains registry-defined.
3. **Baseline declaration:** Baselines may be null when no accepted baseline exists. A missing baseline must not block publication if the KPI definition does not require one, but the dashboard must show `baseline unavailable` rather than implying zero.
4. **Target declaration:** Targets may be null when Chief Architect or Steward authority has not accepted a target. Missing targets must show `target unset` and must not convert into pass/fail status by default.
5. **Threshold computation:** Pass/watch/fail thresholds may only be computed when the required target or threshold data exists and is fresh enough for the KPI definition.
6. **Exclusions:** Exclusions must be explicit, reviewable, and traceable to a registry entry; hidden exclusions are not permitted.
7. **Auditability:** Each observation must retain source projection references and source event IDs sufficient for a reviewer to reproduce the KPI.

## 6. Stale, unknown, and confidence quality rules

| Condition | Required result |
|---|---|
| Mandatory source projection missing | `publication_state=suppressed` or `publish_unknown`, according to the KPI definition. |
| Mandatory field present but null | `data_quality=unknown`; value remains `null`. |
| Source data older than `freshness_sla_minutes` | `threshold_status=stale` or suppressed according to `stale_value_behavior`. |
| Optional source missing | Publish only if the formula does not require it; add a warning when it affects confidence. |
| Estimated value used | `confidence_label=estimated` and warning badge required. |
| Telemetry-derived value used | `confidence_label=telemetry_derived` and telemetry source/sampling warning required. |
| Conflicting source events or projection values | `data_quality=conflicting`; suppress or publish with warning until reconciled. |
| Audit-chain or source-integrity check fails | Suppress the KPI and open validation evidence; do not display pass/fail as if trustworthy. |

KPI rules must preserve the Estate catalog requirement that mandatory fields block KPI publication when absent, optional and estimated fields publish only with confidence labels, telemetry-derived fields record source and sampling interval, and stale or manipulated data causes warning or suppression rather than false precision.

## 7. Initial KPI registry candidates

The initial future registry should include, at minimum, these source-backed KPI candidates:

| KPI group | Candidate KPI | Primary source dependency | Quality concern |
|---|---|---|---|
| Schedule | Schedule variance | Schedule projection | Missing accepted dates must remain unknown. |
| Schedule | Blocked percentage | Schedule and task state projections | Blocked intervals must be traceable to events. |
| Validation | Validation pass rate | Validation evidence and task outcomes | Pending validation must not count as pass. |
| Acceptance | Acceptance pass rate | Acceptance records | Missing acceptance owner or evidence blocks publication. |
| Utilization | Utilization / overcommitment | UTIL-PTM-001 observations | Telemetry-derived values require confidence labels. |
| Financial | Cost variance | FIN-PTM-001 reconciled costs | Estimates must not be treated as actuals. |
| Financial | Cost per accepted task | FIN-PTM-001 and acceptance outcomes | Denominator zero or unknown suppresses value. |
| Governance | Audit-chain integrity | Event hash-chain and evidence refs | Integrity failure suppresses green status. |
| Operations | Freshness compliance | Projection freshness metadata | Stale projections must show stale, not pass. |

These are registry candidates, not an exhaustive list. Future additions must use the same registry entry and projection observation shapes.

## 8. Dashboard contract

Dashboards consume KPI projections only; they must not recompute formulas privately, maintain side lists, or bypass the canonical projection model.

A dashboard card contains:

```yaml
dashboard_kpi_card:
  card_id: string
  kpi_definition_id: KPI-<stable-id>
  kpi_observation_id: KPI-OBS-<stable-id>
  display_name: string
  group_label: string
  period_label: string
  value_display: string
  baseline_display: string
  target_display: string
  threshold_status: pass | watch | fail | unknown | stale | suppressed
  publication_state: publish | publish_with_warning | publish_unknown | publish_stale | suppressed
  confidence_label: observed | telemetry_derived | estimated | unknown
  source_drilldown_refs:
    - object
  warning_badges:
    - unknown
    - stale
    - estimated
    - telemetry_derived
    - suppressed
    - conflicting
```

Dashboard views must visibly distinguish pass, watch, fail, unknown, stale, suppressed, estimated, and telemetry-derived states. They may aggregate cards into portfolio, campaign, task, worker/provider, operational, governance, and financial-efficiency views only by consuming published KPI observations and preserving the weakest material quality label in rollups.

## 9. Validation expectations for future implementation

Future implementation packages should validate this contract with documentation or unit checks proving that:

- each KPI definition declares formula, period, source projections, freshness, confidence, unknown behavior, stale behavior, and manipulation controls;
- mandatory missing inputs suppress or publish unknown rather than becoming zero;
- stale inputs produce stale or suppressed outputs;
- estimated and telemetry-derived values carry confidence labels;
- dashboard cards consume KPI projections rather than recomputing formulas; and
- source projection refs and source event IDs are retained for replay and audit review.

`git diff --check` remains the required documentation hygiene check for this package.

## 10. Boundary and promotion notes

This package remains bounded to future KPI files and dashboard contract behavior. Any future change that would alter CORE-PTM-003B projection fields, FIN-PTM-001 authority boundaries, UTIL-PTM-001 confidence semantics, dispatch readiness, scheduler behavior, budget authority, or governance roles must stop and open a replan note instead of modifying this contract independently.
