# Office Intake Decision Controls

Status: Implemented  
Classification: Estate Internal

## Purpose

Office intake decision controls give the Steward a bounded, local-first way to review pending or blocked Orchestrator intake items and record governed decisions without editing runtime JSON by hand.

This capability does not schedule, assign, dispatch, or execute work. It records decision state for future Orchestrator scheduling.

## Decision Model

Each decision writes one durable JSON artifact under:

- `runtime/orchestrator/intake/decisions/<decision_id>.json`

The artifact contains:

- decision identity (`decision_id`, `intake_id`),
- governed action (`decision`, `next_state`),
- accountable actor and timestamp (`decided_by`, `decided_at`),
- classification and safe-display flags,
- boundary/revision flags,
- optional reason and metadata.

Allowed classifications are `Public`, `Estate Internal`, `Restricted`, `Steward Only`, and `Local Only`.

## Allowed Decisions

Initial allowed actions are intentionally narrow:

- `approve` - marks intake approved for future scheduling only.
- `reject` - records that the intake should not proceed.
- `defer` - keeps the intake visible but not ready for immediate scheduling.
- `request_boundary_review` - records that Ingrid or the Boundary Office must review before proceeding.
- `mark_needs_revision` - records that the intake contract or package needs revision.

Allowed next states are `approved`, `rejected`, `deferred`, `blocked`, and `needs_revision`.

## Runtime Artifact Locations

The decision helper updates these local artifacts:

- `runtime/orchestrator/intake/decisions/<decision_id>.json`
- `runtime/orchestrator/intake/status/latest.json`
- `runtime/orchestrator/intake/status/queue.json`

When operational event support is available, it also records compatible events into the WP-0601 operational status feed, including:

- `runtime/operations/status/latest.json`
- `runtime/operations/status/active.json`
- `runtime/operations/status/recent.json`
- `runtime/operations/events/<date>.jsonl`

## Office Behavior

The Office operational activity panel now includes an Orchestrator Intake Decisions section populated from `runtime/orchestrator/intake/status/queue.json`.

For each pending or blocked item, the Office-consumable surface exposes:

- intake ID,
- work package ID or path,
- source and mission,
- safe summary,
- classification and priority,
- current intake state,
- boundary, approval, and validation requirements,
- available decisions,
- latest decision when present.

The served Office dashboard buttons post to the real local Office action endpoint and call the same decision helper used by the CLI fallback.

## CLI Fallback

Use the local CLI when the Office web surface is not running:

```powershell
Clear-Host
cd A:\theestate
.\estate.bat orchestrator-intake-decide --intake-id <id> --decision approve --decided-by Steward --reason "Approved for scheduling"
```

The Python entry point is equivalent:

```powershell
Clear-Host
cd A:\theestate
python -m estate.cli.main orchestrator-intake-decide --intake-id <id> --decision approve --decided-by Steward --reason "Approved for scheduling"
```

Invalid decisions fail clearly and exit non-zero.

## Boundary Behavior

Restricted, Steward Only, and Local Only summaries are redacted by default unless `metadata.summary_safe` is true.

If an intake item requires boundary review, Office-visible decisions prefer `request_boundary_review`. An approval does not override an incomplete boundary review; the decision is recorded with a blocked next state and boundary-review requirement metadata unless boundary review completion is explicitly supplied.

Decision artifacts must not contain secrets, credentials, or raw private prompts.

## WP-0603 Intake Integration

This capability reuses the WP-0603 intake queue and status artifacts. Decisions can only be recorded for intake IDs currently present in the pending or blocked queue. The helper updates queue membership after decision:

- approved and rejected items leave the pending/blocked queue,
- deferred items remain visible in pending,
- blocked and needs-revision items remain visible in blocked.

## WP-0601 Operational Event Integration

When the shared operational event feed is present, decision recording emits compatible operational events such as `Checkpoint Reached`, `Boundary Review Required`, `Waiting for Approval`, and `Result Returned`. If event recording fails, the durable decision artifact remains the source of truth for later bridging.
