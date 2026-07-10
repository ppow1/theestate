# Governed Execution Session Controller

Status: Implemented for WP-0508  
Classification: Estate Internal

## Purpose

The governed execution session controller composes the existing execution dispatch, adapter handoff, Steward-authorized live execution gate, execution attempt runtime, provider adapter, result reconciliation, and activity/status artifact seams into one auditable operation for one already-authorized dispatch item.

It coordinates approved mechanics only. It does not choose work, select a provider, authorize movement, retry execution, repair a workspace, or grant institutional acceptance.

## Runtime artifacts

The controller writes into the existing execution-adapter runtime tree:

```text
runtime/execution_adapters/sessions/<execution_session_id>.json
runtime/execution_adapters/session_stages/<execution_session_id>.jsonl
runtime/execution_adapters/status/sessions_summary.json
runtime/execution_adapters/reports/<execution_session_id>_session.md
```

## CLI

```bash
python -m estate.cli.main execution-session preview --dispatch-id <id> --authorization <path> --json
python -m estate.cli.main execution-session start --dispatch-id <id> --authorization <path> --confirm-live-execution --json
python -m estate.cli.main execution-session resume --session-id <id> --json
python -m estate.cli.main execution-session status --session-id <id> --json
python -m estate.cli.main execution-session report --session-id <id>
```

Preview validates dispatch, handoff, authorization, workspace, and provider request readiness without acquiring an execution lease or calling a provider. Start requires explicit confirmation and delegates the live provider call to the existing live execution gate.

## Resume safety

Resume loads durable session evidence and only continues from safe boundaries. If a provider call may have occurred but no result reference exists, the controller refuses to repeat the provider call and marks the session for manual review. If a result exists without reconciliation, resume may invoke the existing reconciliation runtime.

## Boundary statement

Provider success, reconciliation, and validation readiness remain evidence only. Institutional acceptance remains not granted unless Chief Architect / Steward review grants it through existing governance.
