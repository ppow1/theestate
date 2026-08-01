# ESTATE-OPS-002 Proposed Deletion and Archive Plan

Status: proposal only; no Phase 5 action authorized or performed.

## Required canonical topology

The post-PR-509 design should converge on one Git common repository:

`A:\theestate\.git`

with exactly two deliberate deployment worktrees:

| Slot | Proposed path | Branch policy | Runtime ports | Persistent state |
|---|---|---|---|---|
| blue | `A:\theestate-wp4233` | `main` or approved release commit; clean and pinned | Grace 8766, Gateway 11435, WebUI 8080 | shared canonical DB |
| green | `A:\theestate-wp4233-green` | candidate release worktree; clean and pinned | Grace 8767, Gateway 11436, WebUI 8081 | same shared canonical DB |

`A:\theestate-wp4233-green` is a proposal, not an existing path and was not
created in this phase. The controller, manifests, Stream Deck bindings, and
rollback records remain authoritative; blue/green must not become a second
independent service system.

Shared state remains:

`A:\AI\OpenWebUI\EstateCanonicalData\webui.db`

No per-slot Open WebUI database, account store, model record, Tool record, or
Filter record may be created. The authoritative controller remains
`A:\theestate-wp4233\scripts\canonical_webui_gateway.py` and manages Grace,
Gateway, and WebUI together.

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
4. For nested `.git` directories and `A:\theestate\.wp4232-worktree`, stop
   and resolve repository ownership before any retirement.

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

Retirement must use `git worktree remove` only after identity checks, followed
by a separately approved prune. No path above was removed.

### Archive-unique-work

- `A:\theestate-wp4232`: 113 commits are not reachable from remotes. Preserve
  commit history and unique tracked work before any retirement.

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

The archive must be read-only, hashed, and must exclude credentials, cookies,
tokens, secret keys, canonical databases, models, and unrelated user data.

### Retain-active

- `A:\theestate` as the shared Git common repository and dirty work/stash
  authority;
- `A:\theestate-wp4233` as canonical blue;
- `A:\AI\Tools\EstateStreamDeckMVP`;
- `A:\AI\Tools\EstateStreamDeckPlugin`;
- `A:\AI\Tools\EngineeringWorkerRuntime`;
- latest `A:\AI\Tools\estate-chat-walker-v0.5`.

### Unresolved-Steward-decision

- `A:\temp`, because it is not demonstrably Estate-only;
- `A:\theestate\.wp4232-worktree`, because it contains nested Git content;
- any nested repositories discovered under the dirty common repository;
- any launcher/configuration still referencing `A:\theestate` until a
  transactionally safe canonical replacement is reviewed.

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
