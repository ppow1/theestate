# Estate PTM Capacity and Utilization Observation Contract

Status: Draft implementation-preparation artifact for PTM-05 Gate C/D
Campaign: PTM-05 — Scheduling, Utilization, Financials, and KPIs
Package: UTIL-PTM-001
Date: 2026-07-16

## Authority and scope

This implementation-ready planning contract satisfies UTIL-PTM-001 for future utilization files. It defines the worker, provider, local-compute, telemetry, and confidence-label observation model that downstream utilization and KPI projections may consume.

This contract is source-backed by the accepted PTM baseline, the PTM parallel execution plan, the PTM dependency and parallelism plan, the PTM package/campaign/dependency manifests, the source UTIL-PTM-001 planning draft, the SCHED-PTM-001A readiness-gate contract, the WP-0660 hour-scale timeline correction, and the WP-0659 execution-lane analysis.

This artifact is documentation-only. It does not authorize production PTM code, mutate authoritative source records, route work, dispatch work, approve schedules, approve budgets, certify readiness, create a second queue, create a second registry, create a second scheduler, or introduce a new governance authority. Codex-only routing remains mandatory for this implementation cycle; local RTX 4090 telemetry may be recorded as evidence only and must not be treated as routing authorization.

## Relationship to schedule and projection contracts

Future utilization projections MUST reuse the CORE-PTM-003A shared projection envelope and must consume SCHED-PTM-001A readiness labels without redefining schedule authority. Utilization can explain whether a lane or resource appears available, committed, idle, blocked, or overcommitted; it cannot convert a non-ready schedule item into a ready or dispatched item.

Future builders MUST:

1. Keep minute-scale active execution, validation, rework, blocked, queue, review, and integration values separate.
2. Preserve unknown, stale, estimated, and telemetry-derived values rather than flattening them into observed capacity.
3. Emit warnings instead of inventing utilization, capacity, or provider availability values when evidence is absent.
4. Stop and replan before changing frozen event, ID, projection, schedule, dispatch, registry, scheduler, or governance contracts.

## Utilization item contract

Projection name: `utilization.current_state`

```yaml
utilization_item:
  envelope: ptm_projection_record
  utilization_item_id: string
  subject_ref: object
  subject_type: worker | provider | execution_lane | human_review_lane | local_compute | validation_lane | integration_checkpoint
  period_start: string
  period_end: string
  capacity_minutes: number | null
  committed_minutes: number | null
  available_minutes: number | null
  productive_minutes: number | null
  blocked_minutes: number | null
  idle_minutes: number | null
  queued_minutes: number | null
  validation_rework_minutes: number | null
  maintenance_unavailable_minutes: number | null
  overcommit_flag: boolean | null
  source_task_ids: [string]
  readiness_gate_refs: [object]
  observation_refs: [object]
  confidence_label: observed | telemetry_derived | estimated | mixed | unknown
  stale: boolean
  warnings: [string]
```

### Field rules

| Field | Rule |
| --- | --- |
| `utilization_item_id` | Deterministic projection key derived from subject, period, and projection version; it is not a new source registry ID. |
| `subject_ref` | Reference to an existing worker, provider, execution lane, human review lane, local compute inventory item, validation lane, or integration checkpoint. |
| `capacity_minutes` | Maximum usable minutes in the period when source-backed; `null` when unknown. |
| `committed_minutes` | Source-backed scheduled or accepted commitment minutes in the period. |
| `available_minutes` | `capacity_minutes - committed_minutes - maintenance_unavailable_minutes` only when all operands are known; otherwise `null` with a warning. |
| `productive_minutes` | Accepted active execution evidence only; validation and rework stay separate. |
| `blocked_minutes` | Derived from SCHED-PTM-001A blocked intervals or accepted blocker evidence. |
| `idle_minutes` | Known capacity not committed, productive, blocked, queued, or unavailable; never inferred from missing telemetry. |
| `queued_minutes` | Queue wait evidence only; it does not create or replace a dispatch queue. |
| `validation_rework_minutes` | Validation or rework evidence only; it must not be merged into productive minutes. |
| `overcommit_flag` | `true` only when known committed minutes exceed known capacity minutes for the same subject and period. |
| `confidence_label` | Lowest safe confidence label across material fields, or `mixed` when field-level evidence differs and field-level warnings preserve detail. |

## Resource, provider, and local-compute references

`subject_ref` identifies a source-backed utilization subject without granting routing authority. Valid subject categories are:

- `worker`: named or pseudonymous worker identity from accepted PTM evidence.
- `provider`: external provider, model provider, or managed service referenced by accepted evidence.
- `execution_lane`: Codex, validation, integration, Chief Architect review, Steward acceptance, or similar lane.
- `human_review_lane`: review or approval capacity lane; this is wait-state evidence, not delegated authority.
- `local_compute`: local compute inventory reference, including GPU/CPU/RAM/storage/cache/power/thermal observations.
- `validation_lane`: validation or independent review capacity.
- `integration_checkpoint`: Gate A/B/C/D/E checkpoint capacity or wait-state record.

Local compute observations for the RTX 4090 or any future local worker are evidence only in this Codex-only cycle. A future package may cite them for capacity planning, but it must not route work locally unless a separate accepted authority changes routing.

## Observation contract

Projection name: `utilization.observation_trace`

```yaml
utilization_observation:
  observation_id: string
  observed_at: string
  period_start: string
  period_end: string
  subject_ref: object
  metric_name: string
  metric_value: number | string | boolean | null
  metric_unit: minutes | percent | count | bytes | watts | celsius | tokens | requests | label
  source_type: event_replay | completion_receipt | provider_report | local_telemetry | validation_report | manual_review | estimate
  sampling_interval_seconds: number | null
  confidence_label: observed | telemetry_derived | estimated | unknown
  source_refs: [object]
  source_event_ids: [string]
  freshness_expires_at: string | null
  warnings: [string]
```

Observation IDs are deterministic for replayed records or source-native where an immutable provider/telemetry ID exists. `source_refs` must include enough provenance to audit the observation without copying mutable external records into a second PTM system.

## Telemetry metric families

Future utilization files may record the following metric families when source evidence exists:

| Family | Example metric names | Required quality notes |
| --- | --- | --- |
| Work minutes | `active_execution_minutes`, `validation_minutes`, `rework_minutes`, `queue_wait_minutes`, `review_wait_minutes`, `blocked_minutes` | Preserve minute categories separately. |
| Provider limits | `quota_remaining`, `rate_limit_remaining`, `provider_availability`, `provider_latency_ms` | Record provider report source and freshness. |
| Local compute | `gpu_active_minutes`, `gpu_reserved_minutes`, `vram_peak_bytes`, `cpu_percent`, `ram_bytes`, `storage_bytes`, `power_watts`, `temperature_celsius`, `model_load_seconds` | Requires sampling interval for telemetry-derived values. |
| Quality | `first_pass_validation_rate`, `failure_count`, `retry_count`, `evidence_completeness_percent` | KPI consumers must preserve confidence and freshness. |
| Cost-efficiency handoff | `accepted_work_per_dollar`, `cost_per_validation_pass`, `throughput_per_compute_hour` | Observational only; budget approval remains FIN-PTM authority. |

## Confidence and quality labels

| Label | Meaning | Publication rule |
| --- | --- | --- |
| `observed` | Directly supported by accepted events, completion receipts, validation reports, or provider reports. | May publish when freshness and required fields pass. |
| `telemetry_derived` | Derived from sampled telemetry or provider counters with source and interval. | Must publish sampling interval and source reference. |
| `estimated` | Based on planning assumptions, forecast, or manual estimate. | Must include estimate basis and must not be presented as measured capacity. |
| `mixed` | Utilization item combines fields with different confidence levels. | Must preserve field-level warnings or observation refs. |
| `unknown` | Required evidence is absent, stale, contradictory, or not authorized for use. | Publish as unknown or suppress downstream KPI publication when required. |

Stale observations are usable only with warnings. Manipulated, contradictory, or unauditable data must be labeled `unknown` or suppressed by downstream KPI rules rather than converted to false precision.

## Overcommit and availability behavior

`overcommit_flag=true` only when committed minutes exceed capacity minutes for the same subject and period and both values are known. If capacity, commitment, or period alignment is unknown, set `overcommit_flag=null` and add a warning.

Availability calculations are advisory planning evidence. They do not dispatch work, reserve capacity, approve budget, or override readiness gates. Dispatch readiness remains governed by the schedule, capacity, budget, privacy/classification, validation-plan, read/write-boundary, and acceptance-owner checks defined by upstream contracts.

## KPI handoff

KPI-PTM-001 may consume utilization items and observations for worker/provider utilization, overcommitment, productive-versus-blocked utilization, throughput per compute hour, accepted work per dollar, and stale/missing ownership indicators. KPI consumers MUST preserve confidence labels, freshness, and unknown-value behavior and MUST NOT publish a KPI whose mandatory utilization inputs are absent.

## Validation expectations for future implementation

Future implementation and TEST-PTM packages should validate at least the following cases:

- committed minutes above known capacity sets `overcommit_flag=true`;
- unknown capacity or commitment sets `overcommit_flag=null` with a warning;
- available minutes are not calculated when an operand is unknown;
- telemetry-derived local compute metrics require source refs and sampling intervals;
- estimated values retain estimate basis and are not displayed as measured utilization;
- stale provider or telemetry observations remain visible through warnings;
- non-ready schedule gates cannot be promoted to ready through utilization availability;
- Codex-only routing is not altered by local RTX 4090 capacity evidence.

## Evidence and collision controls

- This document adds a future utilization contract only.
- No production PTM code is authorized.
- No second dispatch queue, registry, scheduler, or governance authority is introduced.
- No local-worker routing is introduced for this Codex-only cycle.
- Future promotion must coordinate schedule, utilization, finance, KPI, dispatch, and migration readiness evidence through the Gate C/D schedule/finance/KPI reconciliation checkpoint.
