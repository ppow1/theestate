# Estate PTM Capacity and Utilization Observation Contract

## Authority and scope

This implementation-ready planning contract satisfies UTIL-PTM-001 for future utilization files. It extends the frozen utilization projection with observation, confidence, and telemetry rules. It is observational only and creates no local-worker routing authority.

## Utilization record

Required fields extend CORE-PTM-003B:

```yaml
utilization_item:
  utilization_item_id: string
  resource_or_lane_ref: object
  period_start: string
  period_end: string
  capacity_minutes: number | null
  committed_minutes: number | null
  available_minutes: number | null
  productive_minutes: number | null
  blocked_minutes: number | null
  idle_minutes: number | null
  validation_rework_minutes: number | null
  overcommit_flag: boolean | null
  source_task_ids: [string]
  observation_refs: [object]
  confidence_label: observed | telemetry_derived | estimated | unknown
  warnings: [string]
```

## Resource and provider references

`resource_or_lane_ref` identifies a lane, provider, worker class, local compute resource, or human review lane without granting authority to route work. Examples include Codex, Chief Architect review, Steward acceptance, or a local compute inventory reference.

## Observation contract

```yaml
utilization_observation:
  observation_id: string
  observed_at: string
  period_start: string
  period_end: string
  subject_ref: object
  metric_name: string
  metric_value: number | string | boolean | null
  metric_unit: minutes | percent | count | bytes | watts | celsius | label
  source_type: event_replay | completion_receipt | provider_report | local_telemetry | manual_review | estimate
  sampling_interval_seconds: number | null
  confidence_label: observed | telemetry_derived | estimated | unknown
  source_refs: [object]
  warnings: [string]
```

## Confidence and quality rules

- Observed values come from accepted events, completion receipts, provider reports, or explicit telemetry records.
- Telemetry-derived values must include sampling interval and source reference.
- Estimated values must label estimate basis and may not be presented as measured capacity.
- Unknown values remain unknown with warnings.
- Stale observations are usable only with `warnings` and must not silently drive overcommit decisions.

## Overcommit calculation

`overcommit_flag=true` when committed minutes exceed capacity minutes for the same resource/lane and period. If either value is unknown, `overcommit_flag=null` with a warning.

## Boundary rules

- This contract observes capacity and utilization; it does not create a scheduling authority or dispatch queue.
- Local compute telemetry is evidence only. It does not authorize the local RTX 4090 worker for this Codex-only cycle.

- No production PTM code is authorized by this contract.
- No new governance authority is introduced.
