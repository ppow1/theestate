# WP-4232 Recovery Runbook

This runbook is preparatory. It does not authorize destructive action.

## Git recovery

1. Preserve the shared common directory and all registered worktrees.
2. Confirm `git show-ref` contains both WP-4232 refs and record their OIDs.
3. Obtain the separately retained bundle from the approved evidence root.
4. Run `git bundle verify <bundle>`.
5. Restore into a new isolated repository, never into `A:\theestate` or
   `A:\theestate-wp4232`.
6. Verify the branch tip, parent chain, tree IDs, commit manifest, and bundle
   SHA-256.
7. Recreate a disposable linked worktree only after all checks pass.

## Non-Git recovery

1. Obtain the separately retained evidence archive and checksum manifest.
2. Verify the archive checksum before extraction.
3. Extract into a new temporary path outside all Estate runtime roots.
4. Recompute every file hash against the source-path manifest.
5. Keep generated files separate from authored institutional evidence.

## Safety rules

Do not reset, clean, overwrite, prune, drop stashes, alter launchers, stop
services, or delete a worktree during recovery. Do not place databases,
credentials, secret keys, private documents, models, or benchmark material in
the package. The benchmark workspace under `A:\AI\Benchmarks\...` is outside
scope.
