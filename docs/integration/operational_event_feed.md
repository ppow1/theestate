# Operational Event Feed

Status: Implemented  
Classification: Estate Internal  
Work Package: WP-0601

## Purpose

The operational event feed is the shared visibility substrate for Estate workers and providers. It lets planning providers, execution providers, validation workers, documentation workers, and future Orchestrator components emit structured lifecycle events without creating a new office or UI.

The feed supports this operating line:

`governed dispatch -> visible activity -> structured events -> auditable result -> Steward-visible decision state`

## Event Model

Events are represented by `OperationalEvent` in `src/estate/core/operational_events.py`.

Required fields are:

- `event_id`
- `event_type`
- `state`
- `created_at`
- `classification`
- `message`

Optional/defaulted fields include worker, provider, assignment, work package, request, budget, validation, attention, artifacts, and metadata fields.

Allowed classifications are `Public`, `Estate Internal`, `Restricted`, `Steward Only`, and `Local Only`. Unknown classifications fail validation.

Allowed states are `Planning`, `Waiting`, `Running`, `Reviewing`, `Blocked`, `Awaiting Approval`, `Validation`, `Completed`, `Failed`, `Cancelled`, and `Deferred`. Unknown states fail validation.

Initial event types include job, planning, execution, checkpoint, approval, boundary review, validation, commit, result, completion, blocked, failed, and cancelled lifecycle events. Unknown event types fail by default; the CLI has an explicit `--allow-extension-event-type` option for future extension use.

## Status Model

`ActivityStatus` in `src/estate/core/operational_status.py` derives Office-readable activity from events.

Activity identity is selected in this order:

1. `request_id`
2. `assignment_id`
3. `work_package_id`
4. `worker_id`
5. generated activity ID

The status object includes current state, last event, last message, timing, worker/provider identity, assignment/work package/request identity, classification, budget, validation status, attention marker, and artifact paths.

## Runtime Artifact Locations

Runtime artifacts are created on demand and are not committed as empty directories:

- `runtime/operations/events/`
- `runtime/operations/status/latest.json`
- `runtime/operations/status/active.json`
- `runtime/operations/status/recent.json`
- `runtime/operations/status/summary.md`

`latest.json` contains the most recent event and derived status. `active.json` contains active or blocked work. `recent.json` contains terminal completed, failed, or cancelled work. `summary.md` is a concise human-readable summary.

## CLI Examples

Record an event:

```powershell
Clear-Host
cd A:\theestate
.\estate.bat operations-event-record --event .\runtime\example-event.json
```

Summarize activity:

```powershell
Clear-Host
cd A:\theestate
.\estate.bat operations-status-summary
```

The record command validates input, appends the event log, updates status files, and exits non-zero on invalid input. The summary command exits zero even when there is no activity.

## Boundary Summary Behavior

Restricted, Steward Only, and Local Only event messages are redacted from summaries by default. If an event metadata object includes `"summary_safe": true`, the summary may display its message.

This is an operational visibility safeguard, not full Ingrid enforcement.

## Planning Provider Emission

Planning providers should convert lifecycle milestones into `OperationalEvent` records using the shared model. Recommended events include `Job Accepted`, `Planning Started`, `Checkpoint Reached`, `Waiting for Approval`, `Boundary Review Required`, `Planning Complete`, and validation events. Planning-provider request IDs should be passed as `request_id` so activity remains stable across events.

## Execution Provider Emission

Execution providers should emit `Execution Started`, `Checkpoint Reached`, `Validation Started`, `Validation Passed`, `Validation Failed`, `Commit Created`, `Result Returned`, `Execution Complete`, `Worker Blocked`, `Worker Failed`, or `Worker Cancelled` as appropriate. Work packages should be passed as `work_package_id`; provider implementation identity should be passed as `provider_id` and `provider_type`.

## Office Consumption

The Office of the Steward should read the JSON status files directly:

- read `latest.json` for the most recent state transition,
- read `active.json` for currently active, blocked, deferred, or approval-bound work,
- read `recent.json` for terminal activity,
- optionally display `summary.md` for a human-readable fallback.

Consumers should treat runtime files as operational state, not institutional record. Durable decisions and validated outcomes still belong in the Estate ledger, devlog, work package records, and relevant governance artifacts.
