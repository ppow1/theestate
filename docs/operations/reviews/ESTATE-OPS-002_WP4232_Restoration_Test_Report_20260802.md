# WP-4232 Restoration-Test Report

Result: **NOT RUN for a preservation artifact; source-clone smoke test incomplete**.

No Git bundle or non-Git archive exists because ESTATE-OPS-002 authorization
was proposal-only for WP-4232 preservation and no approved external retention
root was supplied. It would be misleading to claim restoration of an artifact
that was never created.

The source-based checks that did run passed:

- `origin/main` was fetched and resolved to
  `e4e4828855bb468dfe3276730eb1dbe22bb89460`.
- WP-4232 HEAD is an ancestor of current `origin/main`.
- The branch and remote branch resolve to the same WP-4232 HEAD.
- The source worktree had no tracked, staged, or ordinary untracked changes.
- The 21 ignored files were hash-inventoried without modification.

A temporary `git clone --no-local` reached the expected WP-4232 HEAD, but its
checkout was interrupted by the bounded command timeout before a clean working
tree could be verified. It is not claimed as a successful restoration test.
The temporary path is outside the Estate worktrees and contains no service or
runtime state; it must be handled separately before the next task.

An authorized follow-up must restore the bundle into a fresh temporary
repository, restore the evidence archive into a separate temporary path, and
compare all hashes before any worktree removal is considered.
