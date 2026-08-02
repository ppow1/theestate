# WP-4232 Git-History Manifest

Manifest date: 2026-08-02
Source HEAD: `9ed81a20249498327d2f3b1c0ccd5ebd831062e2`
Current retained baseline: `origin/main` at `e4e4828855bb468dfe3276730eb1dbe22bb89460`

## Reachability result

| Query | Result |
|---|---:|
| `git rev-list --count HEAD --not origin/main` | 0 |
| `git rev-list --count HEAD --not --remotes` | 0 |
| `git merge-base --is-ancestor HEAD origin/main` | pass |
| prior ESTATE-OPS-002 reported count | 113 |
| corrected current count | 0 |

The previous 113-commit result is preserved as a historical report, not
repeated as a current fact. Rechecking the cited 2026-08-01 baseline shows
that WP-4232 HEAD is already an ancestor of that baseline too, so 113 was not
a valid WP-4232-only count against that baseline. It is consistent with a
reversed or differently scoped reachability query, not with 113 commits that
were historically unique to WP-4232. The later merge of PR #490
(`93532a72bbe56246a1b14751cc46590362485ad6`, 2026-07-27 08:09 -0400) is the
point at which the WP-4232 branch became reachable from `origin/main`; the
branch tip itself predates that merge. No history rewrite was performed by
this task.

## Protected refs and tree identity

```text
refs/heads/wp-4232-dual-surface-acceptance
  9ed81a20249498327d2f3b1c0ccd5ebd831062e2
refs/remotes/origin/wp-4232-dual-surface-acceptance
  9ed81a20249498327d2f3b1c0ccd5ebd831062e2
HEAD tree
  3bb6ef9212ebb3ff41f68f3fd8622895eb318b91
```

The tree object ID was recorded from the read-only source inspection. No named
archive ref or bundle was created here because the governing report did not
authorize implementation and no approved retention root was identified.

## Required authorized preservation procedure

1. Re-check the branch and worktree identity immediately before action.
2. Create a named immutable preservation ref without rewriting commits.
3. Create a full-history bundle including the protected ref and required
   parents; record its SHA-256 and byte size outside Git.
4. Run `git bundle verify` and restore into a separate temporary repository.
5. Compare commit, tree, ref, and object manifests.
6. Preserve non-Git files separately; a bundle is not sufficient.

No step above was executed by this documentation-only package. The common
object database also contains 862 objects reported unreachable when reflogs
are excluded (105 commits, 455 trees, 302 blobs). These are shared-repository
objects, not a WP-4232-only count; they include reflog-only stash history and
WP-era/abandoned work. They remain protected until bounded classification or
separate preservation authorization.
