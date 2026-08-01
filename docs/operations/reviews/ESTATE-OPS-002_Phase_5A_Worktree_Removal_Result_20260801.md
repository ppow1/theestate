# ESTATE-OPS-002 Phase 5A Worktree Removal Result

Date: 2026-08-01  
Reviewed branch: `agent/estate-ops-002-inventory-20260801`  
Phase authorization: explicit Steward authorization for seven named clean
merged worktrees only

## Result

All seven authorized registered linked worktrees passed immediate pre-removal
verification and were removed with `git worktree remove`. No path was skipped.
No additional pruning was necessary: `git worktree prune --dry-run` reported no
stale registrations after the targeted removals.

## Removed paths

| Path | HEAD verified | Branch/identity | Clean | Unique commits outside retained remotes | Work retained |
|---|---|---|---|---:|---|
| `A:\theestate-main` | `f245cd57d19d65de8280eb9ac50ce1d70004f5fb` | `codex/grace-production-campaign-authoring` | yes | 0 | PR #488 merged |
| `A:\theestate-wp4229` | `1c3421b4e2b2d1dd7bf9148699fbf777960762d9` | `codex/wp-4229-production-runtime` | yes | 0 | PR #486 merged |
| `A:\theestate-wp4230` | `8847aa96877b191e39d4e2de02060d6d33b22b36` | `codex/wp-4230-open-webui` | yes | 0 | PR #489 merged |
| `A:\theestate-wp4231` | `bee18d858dec68cd9d388ef52a4c870d5812614b` | `codex/wp-4231-estate-ui` | yes | 0 | PR #487 merged |
| `A:\theestate-wp4231-maincheck` | `7532e5f794fcc45b9e72eb00069fe5678ae77346` | detached checkpoint | yes | 0 | clean validation checkpoint |
| `A:\theestate-wp4232-final` | `b27446c9aeaf161142a3ab878acdfa63c8db7f0a` | `wp-4232-final-bounded-live-acceptance` | yes | 0 | PR #492 merged |
| `A:\theestate-wp4232-u1` | `fb82763bdecff6472e25c06a6a1dce81c84ed578` | `wp-4232-u1-provider-admission` | yes | 0 | PR #491 merged |

The paths had their inventoried timestamps and identities immediately before
removal. No active process command line or current launcher/controller,
Stream Deck binding, manifest, or service reference to these exact paths was
found in the checked active surfaces.

## Space reclaimed

The measured file-byte totals immediately before removal summed to
`717,316,610` bytes, approximately `684.1 MiB`. This is the actual inventoried
file content removed from the seven directories. Shared Git objects remain in
the common repository, so this is a gross directory-content figure rather than
a claim that the same amount of physical storage was released from shared Git
object storage.

No separate free-space baseline was used to attribute unrelated filesystem
activity; the report therefore treats the measured removed file bytes as the
reclaim figure.

## Final registered worktrees

Only these registrations remain:

```text
worktree A:/theestate
  branch refs/heads/feature/evelyn-multimodel-tpose-pipeline

worktree A:/EstateRuntime/bootstrap/estate-main
  detached

worktree A:/theestate-wp4232
  branch refs/heads/wp-4232-dual-surface-acceptance

worktree A:/theestate-wp4233
  branch refs/heads/agent/estate-ops-002-inventory-20260801
```

The WP-4232 linked worktree was not touched. The independent
`A:\theestate\.wp4232-worktree` clone was not touched and still contains its
untracked `.pytest-wp4232` evidence.

## Protected-state verification

- `A:\theestate` still exists; its pre-existing dirty state remains, with 101
  status lines observed after removal.
- `A:\theestate-wp4232` still exists at
  `9ed81a20249498327d2f3b1c0ccd5ebd831062e2`.
- `A:\theestate-wp4233` still exists at the reviewed branch head and was not
  altered by worktree removal.
- All 16 stashes remain.
- `A:\AI\OpenWebUI\EstateCanonicalData\webui.db` remains present.
- Estate Stream Deck/runtime tools remain present.
- Acceptance, campaign, predeploy, and other evidence directories remain
  present.
- No WP-4232 preservation, Common/Blue/Green/Live migration, data movement,
  launcher change, stash action, or service stop was performed.

## Live health

The current transitional Estate remains healthy on active blue:

- Grace runtime: ready on `127.0.0.1:8766`;
- Resident Gateway: ready on `127.0.0.1:11435`;
- Open WebUI: ready on `127.0.0.1:8080`;
- canonical database: `A:\AI\OpenWebUI\EstateCanonicalData\webui.db`.

Phase 5A is complete. No further Phase 5 or migration action is authorized by
this result.
