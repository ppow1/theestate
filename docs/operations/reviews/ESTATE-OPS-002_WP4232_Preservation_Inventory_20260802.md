# ESTATE-OPS-002 WP-4232 Preservation Inventory

Inventory date: 2026-08-02
Source path: `A:\theestate-wp4232`
Inspection mode: read-only
Implementation branch: `agent/wp4232-preservation-retirement-prep-20260802`

## Identity

| Field | Observed value |
|---|---|
| repository root | `A:/theestate-wp4232` |
| common Git directory | `A:/theestate/.git` |
| worktree admin directory | `A:/theestate/.git/worktrees/theestate-wp4232` |
| branch | `wp-4232-dual-surface-acceptance` |
| HEAD | `9ed81a20249498327d2f3b1c0ccd5ebd831062e2` |
| upstream | `origin/main` |
| current origin/main | `e4e4828855bb468dfe3276730eb1dbe22bb89460` |
| working state | clean tracked state; no staged or ordinary untracked files |
| ignored files | 21; listed and hashed in the non-Git manifest |
| submodules | none reported by `git submodule status` |
| LFS | configured; shared LFS object store at `A:\theestate\.git\lfs\objects`; no WP-specific LFS claim established |
| stashes | 16 shared-repository entries; not changed |

The implementation worktree is a separate linked worktree at
`A:\theestate-wp4232-preservation`, based directly on the fetched
`origin/main`. Neither `A:\theestate` nor `A:\theestate-wp4232` was edited,
reset, cleaned, stashed, or removed. The benchmark workspace under
`A:\AI\Benchmarks\...` was not inspected or touched.

## Reconciliation of the reported 113 commits

The current authoritative result is **0 commits reachable from WP-4232 but
not from current `origin/main`**:

```text
git rev-list --count 9ed81a20249498327d2f3b1c0ccd5ebd831062e2 --not origin/main
0
git merge-base --is-ancestor 9ed81a20249498327d2f3b1c0ccd5ebd831062e2 origin/main
success
```

The earlier ESTATE-OPS-002 report recorded 113 against its then-observed
remote-ref set. That result is not reproducible against the fetched current
repository or even against its cited retained baseline
`2417654679c6db1221b18e7a44384e0a13751364`: WP-4232 HEAD is an ancestor of
that baseline as well. The corrected preservation count is therefore 0;
WP-4232 history is already reachable from the retained remote history. The
local branch and its remote branch remain protected until a separate
retirement decision.

## Classification

| Item | Classification | Reason |
|---|---|---|
| WP-4232 commits and tree | already present on `origin/main` | HEAD is an ancestor of current main |
| `origin/wp-4232-dual-surface-acceptance` | reachable protected branch | remote branch remains available |
| tracked working changes | none observed | clean status |
| 21 ignored files | generated/reproducible material; protected pending decision | caches, bytecode, and one generated fixture; not treated as disposable |
| shared reflog-only/unreachable objects | unresolved and therefore protected | shared common object store contains many unclassified unreachable objects |
| local Git/worktree configuration | separate preservation requirement | not represented by a Git bundle or repository tree |
| active path references | not fully proven absent | broad external scan timed out; targeted tracked scan found none |

## Authorization boundary

The canonical ESTATE-OPS-002 reports authorize only the seven named clean
merged-worktree removals already completed in Phase 5A. They explicitly state
that WP-4232 preservation remained proposal-only and that no archive branch,
bundle, or evidence archive was created. This package therefore records the
facts and the required next action but performs no external archival,
worktree removal, registration pruning, stash operation, or Git garbage
collection.
