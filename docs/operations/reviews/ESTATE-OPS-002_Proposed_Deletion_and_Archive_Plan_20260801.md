# ESTATE-OPS-002 Proposed Deletion and Archive Plan

Status: proposal only; no Phase 5 action authorized or performed.

## Required canonical topology — Steward-corrected

The previous proposal is superseded. The post-PR-509 design must converge on
the following separate code, candidate, Live, data, sensitive-data, and backup
roles:

`A:\theestate-common` (backed by one Git common repository)

with one primary Common working tree and exactly two deliberate candidate
worktrees; Live is an immutable release root, not a Git worktree:

| Slot | Proposed path | Branch policy | Runtime ports | Persistent state |
|---|---|---|---|---|
| Common | `A:\theestate-common` | source only; no Live runtime | none | no operational state |
| blue | `A:\theestate-blue` | clean candidate release | candidate/test ports only; proposed 8767/11436/8081 | external shared state |
| green | `A:\theestate-green` | clean peer candidate release | distinct candidate/test ports reserved later | external shared state |
| Live | `A:\theestate-live` | explicit promoted release; never developed directly | Grace 8766, Gateway 11435, WebUI 8080 | external shared state |

All four stable code paths are proposals, not existing paths, and none was
created in this phase. The controller, manifests, Stream Deck bindings, and
rollback records must be updated in a later governed implementation so
Blue/Green are candidate-only and Live owns public ports. Blue and Green must
not become a competing Live system.

Shared state remains:

`A:\AI\OpenWebUI\EstateCanonicalData\webui.db`

No per-slot Open WebUI database, account store, model record, Tool record, or
Filter record may be created. Until the later path migration, the authoritative
controller remains `A:\theestate-wp4233\scripts\canonical_webui_gateway.py`.
The final controller must manage candidate validation and explicit Live
promotion without developing in Live.

Standard persistent data is reserved at `A:\theestate-data`; the current shared
Open WebUI state remains at `A:\AI\OpenWebUI\EstateCanonicalData`. Sensitive
data is reserved at `A:\theestate-sensitive-data` with only the placeholder
levels `restricted`, `highly-restricted`, `classification-pending`, and
`quarantine`. Ingrid later refines classification and access policy. Offline
recovery material is proposed at `A:\theestate-backup`; it is not created here.

## Proposed preservation methods

1. For `A:\theestate-wp4232`, first create a preservation manifest containing
   the 113 unique commit IDs, branch, tree hashes, dirty/untracked hashes, and
   evidence references. Steward-approved preservation should use a named
   archival branch or Git bundle. Do not push generated files, databases,
   credentials, ignored build output, or personal material.
2. For evidence trees, create a read-only archive with a manifest of paths,
   SHA-256 hashes, byte sizes, file counts, and retention reason. Archive
   evidence before considering any removal.
3. For stashes, retain the 16 entries in the common repository. A later
   explicitly named stash decision is required before export or drop.
4. For nested `.git` directories under the dirty common repository, stop and
   resolve repository ownership before any retirement. The independent
   `A:\theestate\.wp4232-worktree` clone has been resolved as a separate
   remote-synchronized WP-4232 clone and is classified archive-evidence.

## Proposed dispositions

### Safe-delete-after-review

Only after the path is confirmed unchanged, no process uses it, no registered
worktree depends on it, its remote branch/PR is retained, and the Steward
approves the named path:

- `A:\theestate-main` (merged PR #488);
- `A:\theestate-wp4229` (merged PR #486);
- `A:\theestate-wp4230` (merged PR #489);
- `A:\theestate-wp4231` (merged PR #487);
- `A:\theestate-wp4231-maincheck` (detached checkpoint);
- `A:\theestate-wp4232-final` (merged PR #492);
- `A:\theestate-wp4232-u1` (merged PR #491).
- `A:\theestate-wp4233` only after Common, Blue, Green, and Live are stable,
  all references are updated, and the current Live release no longer depends
  on the transitional path.

Retirement must use `git worktree remove` only after identity checks, followed
by a separately approved prune. No path above was removed.

### Archive-unique-work

- `A:\theestate-wp4232`: 113 commits are not reachable from remotes. Preserve
  commit history and unique tracked work before any retirement.
- `A:\theestate`: preserve the dirty feature branch, tracked/untracked work,
  common Git object store, and all 16 stashes before migrating to
  `A:\theestate-common`.

### Archive-evidence

- `A:\theestate-acceptance-validation-temp`;
- `A:\theestate-campaign-0681-tmp-20260718`;
- `A:\theestate-predeploy-tests`;
- `A:\theestate-chatgpt-conversation-archive`;
- `A:\EstateRuntime`;
- `A:\EstateValidation`;
- `A:\AI\Tools\EstateStreamDeckPlugin-Archive`;
- `A:\AI\Tools\EstateStreamDeckBuild-PR509-2209`;
- `A:\AI\Tools\EstateStreamDeckBuild-PR509-2214`;
- `A:\AI\Tools\EstateStreamDeckBuild-PR509-2222`;
- historical Estate Chat Walker copies v0.2–v0.4.
- `A:\theestate\\.wp4232-worktree`: independent WP-4232 clone synchronized
  to its remote branch, with untracked `.pytest-wp4232` evidence.

The archive must be read-only, hashed, and must exclude credentials, cookies,
tokens, secret keys, canonical databases, models, and unrelated user data.

### Retain-active (transitional only)

- `A:\theestate` as the shared Git common repository and dirty work/stash
  authority;
- the running `A:\theestate-wp4233` source until stable named paths are proven;
- `A:\AI\Tools\EstateStreamDeckMVP`;
- `A:\AI\Tools\EstateStreamDeckPlugin`;
- `A:\AI\Tools\EngineeringWorkerRuntime`;
- latest `A:\AI\Tools\estate-chat-walker-v0.5`.

### Unresolved-Steward-decision

- `A:\temp`, because it is not demonstrably Estate-only;
- any nested repositories discovered under the dirty common repository;
- any launcher/configuration still referencing `A:\theestate` until a
  transactionally safe canonical replacement is reviewed.

## Common migration proposal

Do not rename or repurpose the dirty `A:\theestate` in place. After explicit
approval, create a clean Git-connected `A:\theestate-common` from retained
remote/main history, verify that only source-controlled code and non-secret
configuration are present, and preserve the old common repository separately.
Then create clean candidate worktrees `A:\theestate-blue` and
`A:\theestate-green` from Common. Create/select `A:\theestate-live` only from
a complete validated candidate release. No runtime data, database, resident
memory, credentials, private documents, or generated output is copied into
Common, Blue, Green, or Live.

## Promotion, rollback, backup, and retirement

Blue or Green is built and semantically validated on candidate ports. A
promotion creates/selects a complete Live release on 8766/11435/8080 and
records the prior Live release. A failed promotion restores the prior Live
release, leaves persistent data unchanged, and re-runs all three readiness
checks. A code rollback never silently rolls back data; data migrations are a
separate governed operation.

The proposed backup contains read-only release manifests, source/tree identity,
controller and launcher manifests, prior Live rollback metadata, and separately
governed persistent-state recovery material. `A:\theestate-backup` is not
created here.

No work-package path is retired until active processes, launchers, services,
scheduled tasks, manifests, status records, and documentation no longer refer
to it; unique commits/evidence are preserved; the replacement path is proven;
and the Steward approves the exact disposition. Gross measurable later
reclaim from the seven clean merged linked worktrees is 717,316,610 bytes
(about 684.1 MiB), excluding shared Git objects. The broader old-worktree
total excluding WP-4232 unique work and current WP-4233 is 988,623,722 bytes
(about 942.9 MiB). Evidence is not counted as reclaimable.

## Stale reference plan

Read-only search found legacy `A:\theestate` references in the inactive
Stream Deck service controller/configuration, operator-deck helpers, and some
older source scripts. Active PR #509 bindings point to
`A:\theestate-wp4233`. Phase 5 must not delete the old root while any active
operator or process reference remains. First produce a reference matrix,
update only approved canonical launchers, reload the active profile, and prove
the three-service lifecycle before retiring any old path.

## Explicit stop point

This plan ends before deletion, archive movement, worktree removal, Git prune,
stash manipulation, or launcher modification. Steward approval must name each
path and disposition before Phase 5 begins.
