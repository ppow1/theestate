# Runtime Persistence, Recovery, and Replay

The Operations Runtime persists restart-critical state under `runtime/operations_runtime/persistence/`.
Each checkpoint is checksum-protected and contains cycle checkpoints, active leases, claims,
scheduler state, campaign state, admitted audit state, completed side-effect identifiers, and
the last durable event position.

## Recovery posture

`RuntimeRecoveryManager.inspect_startup()` loads the latest checkpoint and writes a recovery
status document. Interrupted work is classified as:

- `resumable` when a cycle can continue or status can be reconstructed.
- `retryable` when stale leases or unfinished claims can be deterministically released or requeued.
- `abandoned` is reserved for future retention-expired artifacts.
- `manual-review-required` when state is malformed, unknown, or unsafe to repair automatically.

Corrupt checkpoints are not repaired in place. They are reported as safe-state plans, and
operators may isolate them into `runtime/operations_runtime/persistence/corrupt/` before restart.
Destructive repairs are never executed by inspection; the plan exposes pending actions first.

## Replay

`RuntimeReplayEngine.replay_from_checkpoint()` starts from the checkpoint's last durable event
position and replays immutable persistence events. Side effects whose identifiers already appear
in `completed_side_effects` are skipped, which prevents duplicate external effects while allowing
mutable scheduler, campaign, claim, lease, and audit state to be reconstructed.

## Backups

When a checkpoint is overwritten, the previous envelope is copied to
`runtime/operations_runtime/persistence/backups/`. Backup rotation keeps the newest configured
set and removes older copies.

## Office status integration

The recovery status JSON contains `recovery_posture`, `pending_actions`, and
`safe_state_fallback`. Office status surfaces can read this file directly or call
`load_recovery_status(root)` to display the current recovery posture and operator actions.
