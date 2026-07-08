# Worker Assignment Board Integration

Status: Implemented  
Classification: Estate Internal

## Purpose

The Worker Assignment Board records who or what is responsible for a specific unit of Estate work right now. It complements provider catalog, provider health, intake, and scheduling records without provisioning workers or executing providers.

## Assignment Model

Assignment records are file-backed JSON artifacts with stable `assignment_id`, timestamps, assignee fields, optional provider/seat/profile metadata, work package/intake/schedule links, classification, priority, state, mission, summary, expected outputs, validation flags, attention/blocking fields, artifact paths, and metadata.

Required classifications are `Public`, `Estate Internal`, `Restricted`, `Steward Only`, and `Local Only`. Priorities are `low`, `normal`, `high`, and `urgent`.

## Assignment States

Supported states are:

- `assigned`
- `accepted`
- `running`
- `blocked`
- `awaiting_approval`
- `reviewing`
- `validation`
- `completed`
- `failed`
- `cancelled`
- `deferred`

## Runtime Artifact Locations

The runtime creates these paths as needed:

- `runtime/workers/assignments/records/`
- `runtime/workers/assignments/status/latest.json`
- `runtime/workers/assignments/status/board.json`
- `runtime/workers/assignments/status/summary.md`

Runtime artifacts are operational state and should not require empty directories to be committed.

## CLI Examples

```powershell
Clear-Host
cd A:\theestate
.\estate.bat worker-assignment-create --work-package-id WP-0608 --assigned-to A2C2 --assigned-by Steward --mission "Implement worker assignment board"
.\estate.bat worker-assignment-update --assignment-id <id> --state running
.\estate.bat worker-assignment-list
```

The list command refreshes Office-readable `board.json` and `summary.md` artifacts. Use `--json` for machine-readable CLI output.

## A2C Terminology

`A2C1`, `A2C2`, and `A2C3` are assignment labels used operationally by the Steward, such as Codex seats or Chrome profiles. The implementation preserves them as labels and assignee metadata but does not hardcode the Estate to only three seats.

## Provider Catalog Integration

When `provider_id` is present and the provider catalog is available, the assignment runtime attempts to enrich missing `provider_type` from `config/providers/catalog.json`. Unknown providers do not block assignment recording; a compatibility warning is stored in record metadata.

## Provider Health Integration

Board summaries include optional provider health/capacity context when provider health artifacts are available. If provider health is unavailable, assignment board generation continues without enrichment.

## Operational Event Integration

Assignment creation and state updates emit compatible operational events when the operational event feed is available. State mappings include `assigned` to `Job Accepted`, `running` to `Execution Started`, `blocked` to `Worker Blocked`, `awaiting_approval` to `Waiting for Approval`, `validation` to `Validation Started`, `completed` to `Execution Complete`, `failed` to `Worker Failed`, and `cancelled` to `Worker Cancelled`.

## Office Consumption Notes

Office surfaces should read `runtime/workers/assignments/status/board.json` for structured display and `summary.md` for a human-readable board. `latest.json` contains the most recently written assignment record.

## Boundary Behavior

Restricted, Steward Only, and Local Only summaries are redacted in board output unless `metadata.summary_safe` is explicitly true. Assignment records must not contain credentials, tokens, raw private prompts, or private source material. Structural fields such as assignment ID, state, provider ID, and work package ID remain visible unless a future boundary rule explicitly restricts them.
