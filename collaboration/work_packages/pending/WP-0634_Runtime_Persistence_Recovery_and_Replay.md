# WP-0634 - Runtime Persistence, Recovery, and Replay

Status: Proposed
Priority: High
Owner: Chief Architect #6
Classification: Estate Internal
Depends on: WP-0627, WP-0628

## Mission

Make Operations Runtime recoverable after crashes, reboots, partial cycles, and interrupted audits without losing work or duplicating side effects.

## Required Implementation

- Persist cycle checkpoints, leases, claims, scheduler state, campaign state, admitted audit state, and last durable event position.
- Detect interrupted work on startup and classify it as resumable, retryable, abandoned, or manual-review-required.
- Support idempotent replay from a durable checkpoint.
- Preserve immutable event/evidence history while allowing state reconstruction.
- Add corruption detection, backup rotation, and safe-state fallback.
- Expose recovery plans before executing destructive repair.

Expected files:

```text
src/estate/core/runtime_recovery.py
src/estate/core/runtime_replay.py
tests/test_runtime_recovery.py
tests/test_runtime_replay.py
docs/integration/runtime_persistence_recovery_and_replay.md
```

## Acceptance

- Kill/restart tests recover an interrupted cycle safely.
- Completed side effects are not repeated.
- Stale leases and claims are resolved deterministically.
- Corrupt state is isolated and reported.
- Office status shows recovery posture and pending actions.
- Completion receipt: `collaboration/work_packages/completions/WP-0634_codex_done.json`.

## Codex Handoff

```text
Read collaboration/work_packages/pending/WP-0634_Runtime_Persistence_Recovery_and_Replay.md and do exactly what it says.
```
