# Execution Attempt Lease, Cancellation, and Recovery

Status: Implemented for WP-0507  
Classification: Estate Internal

## Purpose

The execution attempt runtime adds operational controls around the existing governed live-provider path. It prevents duplicate execution leases for the same dispatch item, records stable attempt identity, persists cancellation requests, supports cooperative process-control seams, classifies recovery state, and generates retry-eligibility evidence without starting a retry.

## Boundaries

The runtime preserves the institutional stack:

```text
Runtime computes.
Operations conducts.
Traffic Controller constrains.
Execution Providers implement.
Steward governs.
```

A lease prevents duplicate execution; it does not authorize execution. A cancellation request records operator intent; it does not prove provider rollback. Retry eligibility is evidence for review; it is not retry authorization.

## Runtime artifacts

Artifacts are written under the existing execution-adapter tree:

```text
runtime/execution_adapters/attempts/<execution_attempt_id>.json
runtime/execution_adapters/leases/<dispatch_id>.json
runtime/execution_adapters/cancellations/<execution_attempt_id>.json
runtime/execution_adapters/recovery/<dispatch_id>.json
runtime/execution_adapters/status/attempts_summary.json
runtime/execution_adapters/reports/<execution_attempt_id>_attempt.md
```

The runtime does not create a second dispatch queue, provider registry, scheduler, or event system.

## CLI

```bash
python -m estate.cli.main execution-attempt status --dispatch-id <id> --json
python -m estate.cli.main execution-attempt cancel-request --dispatch-id <id> --attempt-id <id> --reason <text> --json
python -m estate.cli.main execution-attempt inspect-recovery --dispatch-id <id> --json
python -m estate.cli.main execution-attempt release-stale --dispatch-id <id> --attempt-id <id> --confirm-stale-release --json
python -m estate.cli.main execution-attempt retry-eligibility --dispatch-id <id> --json
```

`release-stale` requires explicit confirmation and only releases leases classified as stale-safe by recovery inspection. There is intentionally no retry-start command.

## Live gate integration

`CodexLiveExecutionGate.execute` acquires an execution-attempt lease immediately before the provider adapter submit call and releases that lease after completed, failed, or blocked provider outcomes. Preview remains non-executing and does not acquire an attempt lease.

## Cancellation and process control

Cancellation is two-stage:

1. Persist a cancellation request artifact.
2. Optionally call an injected process controller that verifies attempt/process ownership before signaling.

Tests use fake process controllers. The default controller reports unknown process state and never terminates operating-system processes.

## Recovery and retry evidence

Recovery inspection distinguishes healthy running attempts, stale heartbeats, missing processes, cancellation-unknown state, completed-unreconciled attempts, confirmed failures, confirmed cancellations, completed-and-reconciled attempts, stale-release safety, and manual-review cases.

Retry eligibility records blocking reasons, required authorization, prior attempt identity, side-effect risk, and manual-review requirements. It never starts another provider call.

## Late results

Late results for cancelled, stale, abandoned, or superseded attempts are preserved as evidence, marked for attention, and tied to the exact attempt identity. They do not overwrite a current active attempt.
