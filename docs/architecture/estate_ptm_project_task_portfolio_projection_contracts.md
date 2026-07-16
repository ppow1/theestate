# Estate PTM Project, Task, Portfolio, Status, and Audit Projection Contracts

Status: Draft implementation-preparation artifact for PTM-02 Gate B
Campaign: PTM-02 — Canonical ledger and projection contracts
Package: CORE-PTM-003A
Date: 2026-07-16

## Authority and boundaries

This artifact freezes the CORE-PTM-003A deterministic projection contracts for portfolios, projects, tasks, normalized status, and audit views. It is source-backed by the accepted PTM baseline, the PTM parallel execution plan, the PTM dependency manifests, the CORE-PTM-002A event contract, and the CORE-PTM-002B ID and command contract.

This artifact is documentation-only. It does not authorize production PTM code, mutate authoritative source records, dispatch work, schedule work, accept validation, grant budget authority, create a second dispatch queue, create a second registry, create a second scheduler, or introduce a new governance authority. Existing work-package files, Parking Lot records, dispatch evidence, validation reports, resident and operations records, and acceptance records remain authoritative in place.

## Projection replay model

Future PTM projections MUST be deterministic replay outputs built from canonical PTM events plus read-only adapter source references. Projection builders may cache current-state views, but the cache is disposable and must be rebuildable from the append-only event ledger.

Replay order is:

1. Group events by `stream_id` and validate each stream's CORE-PTM-002A hash chain.
2. Order valid events by stream `sequence_number`, then apply cross-stream correlation only through explicit `correlation_id`, `causation_id`, aggregate references, or payload references.
3. Apply compensating correction events after the corrected event while preserving both in audit output.
4. Preserve adapter warnings, source parse uncertainty, body/path status disagreement, missing optional links, and stale high-watermark state as projection warnings.
5. Emit projection records using the shared projection envelope below.

Projection builders MUST NOT infer authority, ownership, approval, dispatch state, validation acceptance, budget authorization, or schedule readiness when the supporting event or source reference is absent.

## Shared projection envelope

Every projection record defined by this package MUST include this envelope before domain-specific fields are interpreted:

```yaml
ptm_projection_record:
  projection_name: string
  projection_version: string
  record_id: string
  aggregate_type: portfolio | project | task | status | audit
  aggregate_id: string
  source_event_ids: [string]
  source_refs:
    - source_path: string
      source_sha256: string
      adapter_name: string
      adapter_version: string
  computed_at: string
  high_watermark_event_id: string
  high_watermark_recorded_at: string
  stale: boolean
  warnings: [string]
```

### Envelope requirements

| Field | Requirement |
| --- | --- |
| `projection_name` | Stable lower-case dotted name such as `portfolio.current_state`, `project.current_state`, `task.current_state`, `task.status_rollup`, or `audit.event_trace`. |
| `projection_version` | Semantic projection contract version. Future additive fields may increment the minor version; breaking changes require a stop/replan note. |
| `record_id` | Deterministic read-model record ID derived from projection name and aggregate ID, not a new source authority. |
| `aggregate_type` | One of this package's projection aggregate families. |
| `aggregate_id` | Canonical PTM aggregate ID from CORE-PTM-002B. |
| `source_event_ids` | Ordered event IDs that materially support the record. Empty lists are forbidden for current-state records. |
| `source_refs` | Adapter-backed source references inherited from supporting events. |
| `computed_at` | Timestamp for projection build time. It is not source fact time. |
| `high_watermark_event_id` | Last event included in the replay for this projection build. |
| `high_watermark_recorded_at` | `recorded_at` timestamp of the high-watermark event. |
| `stale` | True when replay did not include the latest available event set or a source dependency is known stale. |
| `warnings` | Non-fatal quality, conflict, uncertainty, or authority-boundary warnings. |

## Portfolio current-state projection

Projection name: `portfolio.current_state`

```yaml
portfolio_current_state:
  envelope: ptm_projection_record
  portfolio_id: string
  title: string
  summary: string | null
  status: candidate | pending | ready | claimed | in_progress | blocked | in_review | completed | accepted | rejected | archived | superseded
  owner_refs: [string]
  authority_refs: [string]
  project_ids: [string]
  task_ids: [string]
  task_count_by_status: object
  blocked_task_count: integer
  active_package_count: integer
  completion_receipt_refs: [string]
  risk_warnings: [string]
  latest_event_id: string
```

Portfolio projections summarize a portfolio aggregate without becoming a portfolio registry. `project_ids` and `task_ids` are derived from explicit events or source-backed links only. `task_count_by_status`, `blocked_task_count`, and `active_package_count` are deterministic rollups over included task and project projections at the same high-watermark.

## Project current-state projection

Projection name: `project.current_state`

```yaml
project_current_state:
  envelope: ptm_projection_record
  project_id: string
  portfolio_id: string | null
  title: string
  summary: string | null
  status: candidate | pending | ready | claimed | in_progress | blocked | in_review | completed | accepted | rejected | archived | superseded
  owner_refs: [string]
  authority_refs: [string]
  source_package_refs: [string]
  dependency_refs: [string]
  milestone_refs: [string]
  task_ids: [string]
  schedule_refs: [string]
  financial_refs: [string]
  kpi_refs: [string]
  dispatch_refs: [string]
  validation_refs: [string]
  audit_summary:
    event_count: integer
    latest_event_id: string
    correction_count: integer
    warning_count: integer
```

Project projections preserve cross-surface links for downstream UI, scheduling, finance, KPI, dispatch, migration, and validation packages. Empty downstream reference arrays mean no source-backed link is present; they must not be treated as approval, completion, or acceptance.

## Task current-state projection

Projection name: `task.current_state`

```yaml
task_current_state:
  envelope: ptm_projection_record
  task_id: string
  project_id: string | null
  portfolio_id: string | null
  title: string
  description: string | null
  status: candidate | pending | ready | claimed | in_progress | blocked | in_review | completed | accepted | rejected | archived | superseded
  readiness_state: unknown | not_ready | ready | blocked | dispatched | validating | accepted
  owner_or_lane_ref: string | null
  authority_refs: [string]
  dependency_refs: [string]
  source_refs: [object]
  schedule_refs: [string]
  financial_refs: [string]
  dispatch_refs: [string]
  validation_refs: [string]
  completion_receipt_refs: [string]
  latest_event_id: string
  warnings: [string]
```

Task projections are the canonical future task read model for PTM consumers. They do not replace work-package files, dispatch queue rows, validation reports, or completion receipts. Dispatch readiness and validation acceptance require explicit supporting events or source references.

## Status normalization contract

Status projections normalize source lifecycle wording into this closed set:

`candidate`, `pending`, `ready`, `claimed`, `in_progress`, `blocked`, `in_review`, `completed`, `accepted`, `rejected`, `archived`, `superseded`

Rules:

1. Preserve both path-derived status and body-declared status when they disagree.
2. Preserve source-native labels in audit details even when a normalized status is emitted.
3. Use `candidate` for unaccepted intake or planning candidates that are not executable work.
4. Use `pending` only when a source-backed package or task is authorized but not yet ready/claimed.
5. Use `ready` only when all declared readiness gates are satisfied or explicitly waived by authority refs.
6. Use `accepted` only when a source-backed acceptance record exists; completion alone is not acceptance.
7. Use `superseded` only when a later source-backed record explicitly replaces the prior item.
8. Emit a warning and choose the least-authoritative non-terminal status when source status signals conflict without a correction event.

## Audit trace projection

Projection name: `audit.event_trace`

```yaml
audit_event_trace:
  envelope: ptm_projection_record
  aggregate_id: string
  event_trace:
    - event_id: string
      event_type: string
      event_version: integer
      stream_id: string
      sequence_number: integer
      occurred_at: string
      recorded_at: string
      actor_ref: string
      authority_refs: [string]
      command_id: string | null
      causation_id: string | null
      correlation_id: string | null
      source_refs: [object]
      correction_of_event_id: string | null
      event_hash: string
      previous_event_hash: string | null
  correction_chains: [object]
  source_conflicts: [object]
  warnings: [string]
```

Audit projections expose provenance and correction chains for review, validation, and migration evidence. They must never hide replaced values, source conflicts, adapter warnings, or command rejection context that was preserved by supporting events.

## Deterministic validation expectations

Future implementation and TEST-PTM packages should validate this contract with fixtures that prove:

- identical event inputs produce byte-for-byte identical portfolio, project, task, status, and audit projection JSON after deterministic key ordering;
- task status rollups match the task events included at the same high-watermark;
- path/body status conflict remains visible in warnings and audit details;
- compensating corrections update current-state fields while preserving prior events in audit traces;
- missing dispatch, validation, financial, or schedule links remain empty/unknown rather than inferred;
- stale high-watermark inputs set `stale: true` and preserve a warning.

## Downstream handoff requirements

- CORE-PTM-003B may add schedule, financial, utilization, KPI, and timeline projection contracts, but it must reuse this shared projection envelope unless it opens a stop/replan note.
- UI, intake, conversation, file import, scheduling, finance, KPI, dispatch, migration, rollout, and validation packages may consume these projections but must not redefine the portfolio, project, task, status, or audit current-state fields.
- Any package requiring an envelope change, status set change, or authority-boundary change must stop and replan at the PTM-02 Gate B checkpoint.

## Evidence note

CORE-PTM-003A is complete when this artifact is committed with a completion receipt and `git diff --check` evidence. The artifact freezes deterministic projection contracts for downstream implementation planning without adding production PTM code or creating a parallel queue, registry, scheduler, or governance authority.
