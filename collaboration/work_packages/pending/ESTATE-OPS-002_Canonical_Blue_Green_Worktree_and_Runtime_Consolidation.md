# ESTATE-OPS-002 — Canonical Blue/Green Worktree and Runtime Consolidation

Status: Pending Steward execution authorization after PR #509 is stable and merged
Owner: Estate Operations / Engineering
Execution class: destructive-capable, inventory-first, fail-closed

## Objective

Consolidate Codex-created Estate repositories, worktrees, test copies, and temporary Estate directories on A: into a deliberate canonical blue/green operating layout without deleting unique work, active evidence, approved archives, tools, models, backups, or non-Estate data.

This package is limited to Estate-related repository/worktree/runtime copies created during Codex and work-package execution. It does not authorize general A: drive cleanup.

## Preconditions

- PR #509 must be merged and its cold-boot Stream Deck/Open WebUI/Gateway baseline proven stable.
- Canonical source, blue slot, green slot, persistent Open WebUI state, startup controller, and rollback path must be recorded.
- No active Codex session may be using a candidate directory selected for retirement.
- A full inventory and deletion plan must be reviewed before destructive action.

## In-scope locations

Inventory at minimum:

- A:\theestate
- A:\theestate-main
- A:\theestate-wp*
- A:\theestate-*temp*
- A:\theestate-*test*
- A:\theestate-*validation*
- A:\theestate-*campaign*
- A:\AI\Tools runtime copies tied to the Estate
- Git worktrees reported by the canonical repository
- Codex-created pytest basetemp and worktree directories inside Estate copies
- stale Estate launcher/runtime state that refers to retired trees

Explicitly out of scope unless separately authorized:

- A:\AI models, tools, datasets, archives, downloads, backups, and user projects
- Open WebUI canonical persistent state
- EstateEvidence and retained acceptance evidence
- unrelated repositories
- current canonical blue and green slots

## Phase 1 — Read-only inventory

For every candidate directory, record:

- absolute path;
- type: repository, linked worktree, ordinary copy, temp tree, validation tree, runtime copy, archive, or unknown;
- size and file count;
- Git common directory and worktree identity;
- branch, HEAD, upstream, ahead/behind/divergence;
- clean/dirty state;
- tracked, untracked, ignored, and nested-repository counts;
- unique commits not reachable from origin;
- open PR or branch references;
- stash relationships where determinable;
- active process, launcher, service, manifest, scheduled task, shortcut, or Stream Deck references;
- unique runtime evidence or artifacts;
- last meaningful modification time;
- duplicate-content or supersession relationship;
- proposed disposition.

Produce a machine-readable inventory and human review report.

## Phase 2 — Classification

Each candidate must receive exactly one disposition:

1. canonical-blue;
2. canonical-green;
3. retain-active;
4. archive-unique-work;
5. archive-evidence;
6. safe-delete-after-review;
7. unresolved-Steward-decision.

No path may be deleted merely because its name contains temp, test, final, main, or a work-package number.

## Phase 3 — Unique-work preservation

Before any deletion:

- fetch all remotes;
- identify commits not reachable from origin/main or any retained remote branch;
- identify dirty tracked and untracked content;
- identify open PR branches and unmerged local branches;
- export a preservation manifest containing path, branch, commit, hashes, and reason;
- preserve unique work by an approved method: commit to a named archival branch, bundle, patch set, or read-only archive;
- do not create meaningless bulk commits of generated/runtime files;
- never push secrets, credentials, databases, personal data, transient runtime state, or ignored build outputs.

Stashes are inventoried and reported but are not dropped by this package without a separate explicit Steward decision naming the stash.

## Phase 4 — Canonical layout

Establish and document exactly:

- one canonical Git common repository;
- one blue worktree;
- one green worktree;
- branch/commit policy for each slot;
- one persistent shared state policy for Open WebUI and other stateful services;
- one authoritative startup controller and manifest;
- no launcher, Stream Deck action, service, scheduled task, or runtime manifest referencing a retired path.

The final slot names and paths must match the post-PR-509 canonical deployment design. Do not invent a second blue/green system.

## Phase 5 — Controlled retirement

For each approved safe-delete path:

- verify it is not the current directory of any process;
- verify no registered Git worktree depends on it;
- remove worktrees using Git worktree commands where applicable;
- prune only after successful removal;
- delete ordinary copies only after preservation and hash/inventory capture;
- remove stale launcher/runtime references transactionally;
- stop on access-denied, identity mismatch, reparse-point ambiguity, nested repository, or changed-since-inventory conditions;
- never follow junctions/symlinks outside the approved path.

Destructive execution requires an explicit Steward checkpoint after presentation of the inventory and proposed deletion list. The executor may complete inventory and planning without that checkpoint but must stop before deletion.

## Validation

After approved consolidation:

- Git worktree list contains only intended retained worktrees;
- canonical blue and green paths are clean and synchronized as designed;
- no retained launcher or config references a deleted path;
- cold-boot Stream Deck startup succeeds from the canonical active slot;
- semantic Gateway/Open WebUI/Grace checks pass;
- promotion and rollback pass;
- all retained branches and unique commits remain recoverable;
- disk space before/after is reported;
- deletion manifest contains every removed path and disposition;
- rollback instructions exist for archived material;
- no changes are made to models, tools, user archives, or unrelated data.

## Deliverables

- docs/operations/reviews/ESTATE-OPS-002_Estate_Directory_and_Worktree_Inventory_<date>.md
- runtime or docs machine-readable inventory JSON in an approved evidence location
- docs/operations/reviews/ESTATE-OPS-002_Proposed_Deletion_and_Archive_Plan_<date>.md
- explicit Steward deletion decision record
- docs/operations/reviews/ESTATE-OPS-002_Consolidation_Result_<date>.md
- canonical blue/green topology and rollback map

## Stop conditions

Stop and request Steward direction for:

- unique unpushed commits;
- ambiguous dirty content;
- unknown nested repositories;
- active process references;
- uncertain evidence-retention requirements;
- any requested deletion outside the defined Estate-related scope;
- any candidate containing credentials, databases, personal material, or unrelated projects;
- PR #509 baseline not stable.

## Completion criteria

The Estate has one deliberate repository source with exactly two intended deployment worktrees, all startup/runtime references point to them, obsolete Codex-created Estate copies are retired or explicitly archived, unique work is preserved, stashes remain separately governed, and the final cold-boot blue/green operational test passes.
