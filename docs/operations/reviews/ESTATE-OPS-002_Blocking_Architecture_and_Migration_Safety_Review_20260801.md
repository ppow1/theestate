# ESTATE-OPS-002 Blocking Architecture and Migration-Safety Review

Reviewed head: `a6e6650b51c416ad2ef3404b2d732da4f7b6dcea`  
PR: #510  
Review scope: proposal only; no destructive or runtime mutation

## Verdict

The proposal is safe to present for Steward review after the corrections in
this report. It is not authorization to migrate, delete, archive, create a
worktree, stop a service, or move data.

The review identified and corrected three blocking proposal defects:

1. A Git bundle alone does not preserve dirty tracked changes, untracked
   evidence, worktree registrations, local configuration, or reflogs. The
   migration sequence now requires separate manifests and preservation paths.
2. `A:\theestate-live` was previously ambiguous. Live is now explicitly an
   immutable release-directory root with a transactionally replaced active
   release manifest, not a development worktree and not a candidate that takes
   public ports by promotion-in-place.
3. Source-embedded operational/runtime data was under-specified. The report
   now separates source-controlled authored data from external runtime,
   resident, evidence, WebUI, secret-key, and operational state.

## Current facts checked

- The reviewed branch is clean at the required head and PR #510 remains open
  and draft.
- The current Estate remains healthy on transitional blue:
  Grace 8766, Resident Gateway 11435, Open WebUI 8080.
- The current controller configuration still names
  `A:\theestate-wp4233` as source root and treats 8766/11435/8080 as the blue
  active ports. This is not the final topology and must not be copied into
  the future candidate environments.
- The existing Git common repository is `A:\theestate\.git`, with 566 refs,
  16 stashes, reflogs enabled, registered worktrees, local branch/upstream
  configuration, and a dirty primary working tree.
- The linked `A:\theestate-wp4232` has 113 commits not reachable from retained
  remotes. The independent `A:\theestate\.wp4232-worktree` clone is instead at
  remote branch commit `b064dac95856156a5fd9c1fe35b9959e58abfb10` and has only
  untracked `.pytest-wp4232` content.
- The scheduled task `Estate Operations Runtime Host` points to
  `A:\EstateRuntime\host\estate-main\state\run_operations_runtime_host.ps1`.
  It is a separate runtime/evidence reference and must be included in the
  later path-reference transaction.

## Exact Git-common recommendation

Use a **normal non-bare primary working tree at `A:\theestate-common` with
linked worktrees for Blue and Green**.

This model satisfies the requirement that Common contains source-controlled
code, schemas, policies, documentation, tests, templates, migrations, and
non-secret configuration. Blue and Green are registered linked worktrees from
the Common repository. Live is not a Git development worktree; it is an
immutable exported release root described below.

Operational consequences:

- `A:\theestate-common\.git` is the one Git common directory.
- `A:\theestate-common` is the only normal source editing/checking tree.
- `A:\theestate-blue` and `A:\theestate-green` contain no independent `.git`
  repositories; their `.git` files point to registered common worktrees.
- All refs, remote configuration, hooks/attributes, reflog history, and stash
  objects are maintained by the common Git directory, while worktree admin
  records are recreated for the new named paths.
- A bare repository is rejected because the target Common path must contain the
  source mechanism and source files, and operators need a normal source tree
  for review/build. A separate Git directory with an arbitrary working tree
  would add complexity without improving the required workflow.

## Safe Common migration protocol

The following is the required future protocol, not an action performed here:

1. **Checkpoint A — preserve old authority.** Leave
   `A:\theestate\.git`, all current worktrees, all 16 stashes, and the live
   `A:\theestate-wp4233` source untouched. Record `git fsck`, object database
   counts, every ref/object ID, every stash commit/tree, remote config, branch
   config, worktree list, reflog hashes, hook/attribute files, dirty tracked
   diff, and untracked/ignored inventory. The old root is the recovery point.
2. **Preserve local-only material separately.** A bundle of all refs preserves
   reachable Git objects and commits, but not dirty/untracked content,
   reflogs, or worktree registrations. Preserve WP-4232’s 113 commit IDs in a
   manifest and bundle; preserve dirty tracked changes as a patch plus hashes;
   preserve untracked non-secret evidence in a separate hashed manifest/archive
   approved by the Steward. Do not bundle or push databases, credentials,
   secret keys, private documents, or generated bulk output.
3. **Create Common from retained history.** In a future approved window,
   create a clean normal repository at `A:\theestate-common` from the retained
   remote/main source, fetch all retained remote refs, recreate all required
   local refs, and import the explicitly preserved local-only refs. Do not copy
   the old `.git\worktrees` directory: those records contain obsolete paths.
   Recreate Blue and Green registrations with `git worktree add` only after
   their commits are verified.
4. **Validate metadata before cutover.** Compare object reachability, ref
   names/OIDs, remote URLs/fetch rules, branch upstreams, hooks and attributes,
   and required source files. Reflogs in the new Common begin at migration;
   the old `.git\logs` remains preserved as the historical reflog authority
   until acceptance. This avoids falsely claiming a bundle imported reflogs.
5. **Checkpoint B — Common recovery.** If migration stops, abandon only the
   unactivated new Common candidate and resume from the untouched old Common
   and current Live source. Do not alter the old worktrees to repair a partial
   new migration.

## Exact Live-release recommendation

Use `A:\theestate-live` as a **release root containing immutable versioned
release directories and an atomic active-release manifest**, not as a Git
worktree and not as a mutable development tree.

Proposed shape, not created here:

```text
A:\theestate-live\
  releases\<release-id>\       immutable exported code/config release
  active-release.json           source commit, release ID, config/state identity
  rollback\                     release metadata only, not live mutable data
```

Each release ID is created once from exactly one validated Blue or Green source
commit and records source commit, release tree hash, configuration hash,
controller version, candidate validation evidence, state compatibility, and
Steward authorization. The Live controller starts services from the selected
release directory on 8766/11435/8080. A pointer/manifest replacement is the
activation boundary; the previous manifest and release remain available for
rollback. No code is developed directly in Live.

Promotion sequence:

1. Build an immutable release from a clean Blue or Green commit.
2. Validate all three candidate services and the authenticated semantic path.
3. Verify state compatibility without changing persistent data.
4. Obtain explicit Steward promotion authorization.
5. Materialize/reuse the release directory and atomically replace the Live
   active-release manifest.
6. Start the complete Live service tree and verify Grace, Gateway, WebUI,
   model/tool/filter, database identity, and operator status.
7. Record prior release, new release, source commit, state identity, and
   validation evidence.

Rollback sequence:

1. Stop admission of the new Live release and preserve its logs/manifest.
2. Replace the active-release manifest with the prior known-good release.
3. Restart the complete three-service tree from the prior release.
4. Re-run semantic readiness and bounded authenticated checks.
5. Keep persistent data unchanged. If a data migration exists, it must have a
   separate compatibility and rollback decision; code rollback must never
   silently restore an old database.

## Data-path boundaries

The following source-embedded paths require eventual externalization or an
explicit retain-in-Common decision:

- `runtime/production/grace_momentum`: Grace runtime persistence/state →
  `A:\theestate-data` or a separately governed sensitive location.
- `runtime/resident_interactions`, `runtime/resident_conversations`, private
  ingestion, attachments, and resident memory/session state → sensitive
  external data; never Blue/Green/Common.
- `runtime/residents`, `runtime/mailboxes`, `runtime/operations`,
  `runtime/execution_*`, `runtime/engineering_*`, `runtime/codex_bridge`,
  `runtime/mission_control`, `runtime/notifications`, `runtime/validation`,
  and runtime service/provider state → external operational data/evidence;
  classify per existing governance, without inventing Ingrid policy here.
- `runtime/openwebui` and any WebUI runtime state → the current
  `A:\AI\OpenWebUI\EstateCanonicalData` boundary unless separately migrated.
- `A:\AI\OpenWebUI\.webui_secret_key` → sensitive external secret; never Git,
  Common, Blue, Green, or Live release content.
- `A:\AI\Tools\EstateStreamDeckMVP\Core\state\canonical-runtime` →
  external operator/runtime state, not source release content.
- `collaboration/status`, mailboxes, runtime receipts, generated reports,
  validation output, and evidence trees → retain authored governance in
  Common, externalize generated/private state and preserve evidence separately.
- Source-authored `data/character-architecture`, registries, schemas, policy,
  and visual manifests remain source-controlled where they are canonical
  definitions rather than runtime state.

## Sensitive placeholders and backup model

`A:\theestate-sensitive-data` is only a reserved boundary with the four
temporary names `restricted`, `highly-restricted`, `classification-pending`,
and `quarantine`. No access policy, classification standard, or automatic
grant is created by this package. Ingrid later refines classification and
access policy. Until then, no release or service inherits access merely from
the directory name.

The proposed offline/read-only `A:\theestate-backup` is not created here and
must remain distinct from Live and all candidate paths. It should contain,
under separate protected sets:

- source/ref/object recovery: Common refs, bundles, commit manifests, and
  migration metadata;
- Live release recovery: immutable release trees, active-release manifests,
  config hashes, prior-release records, and logs;
- standard-data recovery: separately governed operational data snapshots;
- sensitive-data recovery: separately encrypted/access-controlled snapshots;
- WebUI recovery: approved `webui.db` backup plus separately protected
  `.webui_secret_key` recovery, never in Git or ordinary release archives.

Backups exclude active sockets/PIDs, caches, generated bulk output, unapproved
models, credentials in plaintext, cookies/tokens, and unrelated data. Restore
testing must use an isolated non-Live environment, verify hashes, validate
semantic readiness, and prove that backup material cannot be treated as an
active runtime. Retention and destruction require a later Steward decision.

## WP-4232 preservation

The 113 unique commits are recoverable from the current linked worktree and
common object database today, but not guaranteed by a bundle alone. Required
future preservation is:

- a commit/ref/tree manifest for all 113 commits;
- a Git bundle containing those commits and required parent objects;
- a separate patch/hash record for any dirty tracked content;
- a separate hashed, non-secret evidence archive for untracked content;
- a separate credential/database/private-data exclusion review.

The independent `.wp4232-worktree` clone has no commits outside its remote and
has only untracked `.pytest-wp4232`; it must not be confused with the linked
worktree’s 113 commits. No unique work is pushed or deleted by this review.

## Seven clean-worktree review

The seven proposed removals (`theestate-main`, `wp4229`, `wp4230`, `wp4231`,
`wp4231-maincheck`, `wp4232-final`, `wp4232-u1`) are independently clean,
merged/retained or detached checkpoints, and can be retired in a separate
low-risk phase after each path is rechecked for active processes, worktree
registration, changed state, evidence, and remote recoverability. They do not
need to wait for the Common/Blue/Green/Live migration, but the Steward must
authorize each named path. Removal must use Git worktree operations where
applicable and must not prune shared objects until all worktrees are safe.

## Reference matrix and checkpoints

Eventual path updates must cover Stream Deck profiles and installed actions,
canonical controller/config/manifests, command files, tests, documentation,
the `Estate Operations Runtime Host` scheduled task, shortcuts, service state,
PID/status records, and Codex/work-package instructions. The current active
bindings and controller remain transitional; no reference was changed here.

Migration checkpoints:

- **A:** current Live healthy; old common/worktrees/stashes preserved.
- **B:** preservation manifest and recovery bundle verified; old common still
  authoritative.
- **C:** Common metadata/ref/object comparison passes; no services switched.
- **D:** Blue and Green candidate environments validate without public ports.
- **E:** immutable Live release and external state compatibility pass; explicit
  Steward promotion authorization recorded.
- **F:** Live activation and rollback test pass; old transitional root still
  retained until reference audit completes.
- **G:** only then consider low-risk worktree retirement, separately authorized.

At every failed checkpoint, leave the current healthy Estate in place and
return to the prior checkpoint. No checkpoint authorizes destructive action by
itself.

## Final destructive-authorization checklist

Before any Phase 5 action, Steward approval must explicitly name each path and
disposition and confirm:

- Common preservation of refs, objects, remotes, branches, worktrees, reflogs,
  hooks/attributes, dirty content, and all 16 stashes;
- WP-4232 commit bundle plus non-Git evidence preservation;
- no active process, task, shortcut, service, Stream Deck action, or document
  references the path;
- Blue/Green are candidate-only and Live owns public ports;
- Live release identity and rollback record exist;
- data and secret boundaries remain external and unchanged;
- no credentials, database, private material, generated bulk output, or model
  is pushed or deleted;
- the current Estate remains recoverable at every checkpoint.

The first destructive phase that could be separately authorized is **Phase 5A:
retire one individually approved clean merged linked worktree after a fresh
identity/state/evidence check**. Common migration, Live creation, data movement,
and bulk evidence archival require separate later authorization and are not
covered by that low-risk approval.
