# ESTATE-OPS-003 — Common / Candidate / Live / Backup Topology and Estate Comms8 Repository Preparation

Status: Pending execution
Owner: Estate Operations / Engineering
Execution lane: Codex CLI on the Steward's development machine
Execution class: migration-capable, preservation-first, fail-closed

## Steward decision

The Steward selected Option A:

1. Implement the Estate's intended Common / Blue / Green / Live / Backup operating topology first.
2. Preserve continuous operation of the current Estate throughout the migration.
3. Prepare the four relevant ppow1 repositories locally on A: so later Estate Comms8 work can use them in one Codex CLI engineering environment.
4. Do not begin Estate Comms8 implementation in this package.

This package is the first of four total campaign packages. It must not split its defined scope into additional follow-on discovery, migration, repository-preparation, launcher-update, promotion-mechanism, or topology packages. Defects found while completing this package are repaired inside this package unless a stop condition requires Steward direction.

## Required reading

Before changing anything:

1. Read `AI_HINTS.md` and complete the applicable onboarding.
2. Read:
   - `collaboration/work_packages/pending/ESTATE-OPS-001_Restore_Canonical_WebUI_Gateway_Startup_and_Implement_Real_Blue_Green_Control.md`
   - `collaboration/work_packages/pending/ESTATE-OPS-002_Canonical_Blue_Green_Worktree_and_Runtime_Consolidation.md`
   - `docs/operations/reviews/ESTATE-OPS-002_Estate_Directory_and_Worktree_Inventory_20260801.md`
   - `docs/operations/reviews/ESTATE-OPS-002_Proposed_Deletion_and_Archive_Plan_20260801.md`
   - `docs/operations/reviews/ESTATE-OPS-002_Blocking_Architecture_and_Migration_Safety_Review_20260801.md`
3. Inspect the current runtime/controller implementation and verify current facts rather than assuming the August 1 inventory remains exact.

## Governing facts and corrections

The Common / Blue / Green / Live / Backup architecture is approved as the intended model but is not yet implemented.

The current Estate remains transitional and may still be rooted at `A:\theestate-wp4233` on canonical ports. Verify the actual current root, processes, ports, controller, database identity, scheduled tasks, Stream Deck bindings, shortcuts, and launchers before action.

Do not copy the old assumption that one candidate slot permanently owns production ports.

The intended model is:

- `A:\theestate-common` — normal non-bare Git repository and source authority.
- `A:\theestate-blue` — linked non-Live candidate worktree.
- `A:\theestate-green` — linked peer non-Live candidate worktree.
- `A:\theestate-live` — immutable versioned release root with an atomic active-release manifest; not a Git development worktree.
- `A:\theestate-data` — external standard operational data boundary where approved.
- `A:\theestate-sensitive-data` — reserved sensitive-data boundary; do not invent classification or access policy.
- `A:\theestate-backup` — offline/read-only recovery boundary distinct from Live and candidates.
- Existing Open WebUI canonical data remains at its current approved external location unless separately authorized.

## Non-negotiable availability rule

The Estate must not go offline as an implementation technique.

- Do not edit the active transitional source tree in place.
- Do not stop, replace, repoint, or mutate the active Estate until a separately prepared candidate and release are proven.
- Build and validate new mechanisms on non-Live ports.
- Preserve the current active root and its recovery authority through all migration checkpoints.
- Any activation must be transactional and must have a tested rollback to the prior healthy runtime.
- Failure at any checkpoint returns to the prior checkpoint with the current healthy Estate still available.

A brief controlled service transition during an explicitly authorized final activation is permitted only after candidate validation and rollback readiness. An extended outage, in-place development, or using Live as a test environment is forbidden.

## Four-repository engineering environment

Verify these four repositories are available locally on A: and accessible to one Codex CLI engineering session:

1. `ppow1/theestate`
2. `ppow1/CueMastery`
3. `ppow1/ionoge-vps`
4. `ppow1/ionoge-site`

`faqdocs` and `faqdocsold` are explicitly excluded.

For each relevant repository:

- locate any existing local checkout before cloning;
- record absolute local path;
- verify remote URL and repository identity;
- fetch remote state without discarding local work;
- record branch, HEAD, upstream, ahead/behind state, dirty state, stashes, and untracked material as applicable;
- do not reset, clean, overwrite, or blindly pull across local changes;
- clone only if no suitable local checkout exists;
- place or retain the repositories in a layout accessible from A: to Codex CLI;
- produce a machine-readable repository manifest for later Estate Comms8 packages.

Repository roles for this package:

- `theestate`: writable only through the migration branch/worktree created for this package.
- `CueMastery`: read-only donor/reference; verify that Ionoge Comms7 and mailbox/MCP materials are present for the next package.
- `ionoge-vps`: read-only server backup/deployment/rehabilitation reference; verify completeness and local synchronization.
- `ionoge-site`: read-only site/PHP/deployment reference; determine whether it contains relevant Ionoge MCP or server artifacts.

Do not copy donor code into the Estate merely to simplify inspection. Record authoritative locations and source commits. A later package may create a controlled donor snapshot only if inspection proves it necessary.

## Objective

Implement and prove the Estate source, candidate, immutable Live release, rollback, and backup topology while retaining the old transitional Estate as a recovery authority. Prepare the four-repository local engineering environment required by the next Estate Comms8 package.

## Phase 1 — Fresh preservation and identity checkpoint

Before creating or changing target paths:

- identify the actual active Estate source root and active service tree;
- record all active PIDs, commands, ports, environment/config identities, launchers, tasks, shortcuts, Stream Deck references, controller manifests, databases, secret locations, and runtime state locations;
- refresh Git repository/worktree inventory;
- preserve all refs, objects, remotes, branch configuration, hooks/attributes, stashes, and required reflog evidence;
- preserve WP-4232 or any other local-only commits with an explicit commit/ref/tree manifest and valid Git bundle;
- preserve dirty tracked work with patches and hashes;
- preserve approved non-secret untracked evidence separately with hashes;
- explicitly exclude credentials, cookies, tokens, private data, databases, secrets, models, caches, and bulk generated output from ordinary Git/archive handling;
- verify that the current active Estate is healthy before proceeding.

Create a checkpoint receipt that identifies the current recovery authority. Do not rely on a Git bundle alone to preserve non-Git state.

## Phase 2 — Create Common and candidate worktrees

Create `A:\theestate-common` as a clean normal non-bare repository from retained authoritative history.

- Fetch and verify the retained remote refs.
- Recreate required local refs from preservation artifacts.
- Do not copy obsolete `.git\worktrees` administration records.
- Validate object reachability, ref names/OIDs, remotes/fetch rules, branch upstreams, hooks/attributes, and required source files.
- Preserve the old Git authority until final acceptance.

Create Blue and Green with normal Git linked-worktree operations:

- `A:\theestate-blue`
- `A:\theestate-green`

Requirements:

- each is a registered linked worktree of Common;
- each is non-Live;
- each uses assigned candidate-only ports and isolated process/state identities where needed;
- neither may claim canonical public ports during ordinary testing;
- candidate configuration must not silently point at mutable Live data or secrets;
- persistent state boundaries must be explicit and compatible with the approved external state model.

## Phase 3 — Implement immutable Live release control

Create `A:\theestate-live` as a release root, not a Git worktree.

Required shape or an equivalent evidence-backed implementation:

```text
A:\theestate-live\
  releases\<release-id>\
  active-release.json
  rollback\
```

Implement tooling that can:

- export/materialize an immutable release from exactly one clean validated Blue or Green commit;
- compute and record source commit, release tree hash, configuration hash, controller version, state identity/compatibility, validation evidence, and authorization reference;
- atomically select the active release through a manifest/pointer transaction;
- retain the prior release and prior active manifest for rollback;
- start the complete Live service tree from the selected release on canonical ports;
- prevent development or mutation directly inside a materialized release;
- fail closed when release identity, hashes, configuration, state compatibility, or authorization are missing.

Do not migrate databases or secrets merely to complete this package. Keep existing approved persistent state external and record compatibility. Any unavoidable data migration requires a separate explicit decision within this package before execution.

## Phase 4 — Controller, launcher, and reference transaction

Build the new controller and reference model in the candidate environment first.

Inventory and transactionally update all applicable references, including:

- canonical controller/config/manifests;
- Grace, Residential Gateway, and Open WebUI launch paths;
- Stream Deck profiles and installed actions;
- scheduled tasks, including the Estate Operations Runtime Host;
- shortcuts and command files;
- PID/status/runtime-state records;
- operator tooling;
- tests and documentation;
- Codex and work-package instructions that would otherwise direct work into a transitional or Live path.

No reference may be repointed to the new Live root before the release has passed candidate validation and the activation gate is authorized.

## Phase 5 — Candidate validation and rollback proof

Run Blue and Green independently on non-Live ports while the current Estate remains operational.

Prove at minimum:

- both linked worktrees are correctly registered and clean at their selected commits;
- candidate Grace readiness and natural-language behavior;
- candidate Residential Gateway readiness and semantic behavior;
- candidate Open WebUI startup and authenticated semantic path where practical;
- provider/model/tool/filter identities are correct;
- candidate services do not bind canonical ports;
- shared/external state behavior is explicit and safe;
- immutable release creation is deterministic from a validated candidate commit;
- active-release manifest replacement is atomic or transactionally equivalent;
- rollback tooling can select and restart a prior known-good release in an isolated/non-Live proof;
- failure injection does not alter the currently active Estate;
- all commands and results are recorded as acceptance evidence.

## Phase 6 — Steward activation gate and controlled promotion

This package may prepare the complete promotion transaction but must pause before changing the active Estate and present:

- current active identity and health;
- candidate commit and release ID;
- candidate validation results;
- exact canonical-port transition procedure;
- exact rollback procedure;
- active-release and prior-release manifests;
- state/database compatibility evidence;
- list of path-reference changes;
- confirmation that no legacy path will be deleted;
- expected transition duration and stop conditions.

After explicit Steward authorization to activate this named release:

1. Preserve final current-Live state and logs.
2. Materialize or reuse the validated immutable release.
3. Apply the reference/controller transaction.
4. Transition the complete service tree to `A:\theestate-live` on canonical ports.
5. Verify Grace, Gateway, WebUI, provider/model/tool/filter behavior, database identity, and operator status.
6. On failure, immediately restore the prior controller/references and current transitional runtime or prior immutable release.
7. Retain the old transitional source/runtime and all preservation artifacts.

Activation authorization does not authorize deletion.

## Phase 7 — Backup boundary and recovery proof

Create or prepare `A:\theestate-backup` as a distinct recovery boundary according to the approved model.

Keep separately protected sets for:

- Common source/ref/object recovery;
- Live immutable release and manifest recovery;
- approved standard-data recovery;
- approved sensitive-data recovery with separate controls;
- approved WebUI database and secret-key recovery under separate protection.

Do not place plaintext secrets, active sockets/PIDs, caches, unrelated data, models, cookies/tokens, or bulk generated output into ordinary backup sets.

Perform restore testing only in an isolated non-Live environment. Verify hashes and semantic readiness. Backup material must never be treated as an active runtime merely because it exists.

## Explicitly out of scope

- Estate Comms8 implementation.
- MCP/App changes.
- Grace-to-ChatGPT mailbox orchestration.
- Browser turn automation.
- OpenHands/Qwen/Codex orchestration changes.
- Deletion or retirement of any old repository, worktree, runtime tree, evidence directory, stash, backup, or transitional path.
- General A: drive cleanup.
- New Ingrid classification/access policy.
- Moving or rewriting unrelated user data.

## Required deliverables

1. `docs/operations/reviews/ESTATE-OPS-003_Repository_Environment_<date>.md`
2. Machine-readable four-repository manifest containing local paths, remotes, branches, commits, and roles.
3. Updated preservation manifest and recovery receipts.
4. Common/Blue/Green worktree topology report.
5. Candidate port and process-identity map.
6. Immutable Live release specification and implemented controller/tooling.
7. Active-release and rollback manifest schemas.
8. Reference-transaction inventory and result.
9. Candidate validation report for Blue and Green.
10. Steward activation decision record.
11. Live activation and semantic acceptance report, if authorized.
12. Backup/restore validation report.
13. Final closeout report identifying retained transitional paths and remaining non-destructive cleanup candidates.
14. A concise handoff for Package 2: Estate Comms8 core implementation and Grace provider.

## Acceptance criteria

This package is complete only when:

- the four relevant repositories are verified locally on A: and recorded for Codex CLI use;
- Common is the verified source authority;
- Blue and Green are deliberate linked non-Live candidates;
- Live is an immutable release root controlled through an atomic/transactional active-release manifest;
- canonical ports belong only to the active Live service tree after authorized activation;
- candidate ports remain isolated;
- current persistent data and secret identities remain external and correct;
- rollback is proven;
- Backup is distinct and restore-tested in isolation;
- the old transitional Estate remains recoverable and has not been deleted;
- no unrelated repository or data is altered;
- the next Estate Comms8 package can access the Estate, CueMastery, ionoge-vps, and ionoge-site local repositories without new retrieval work.

## Stop conditions

Stop and request Steward direction when:

- the active Estate is unhealthy before migration;
- repository identity or local-path ownership is ambiguous;
- preservation validation fails;
- local-only commits, stashes, dirty content, nested repositories, credentials, databases, private material, or evidence cannot be safely classified;
- candidate services cannot be isolated from canonical ports or active state;
- a required launcher/task/controller reference cannot be transacted and rolled back safely;
- state compatibility cannot be proven;
- activation would require an unapproved data migration;
- any deletion is proposed;
- any path outside the named Estate and four-repository preparation scope would be changed;
- final Live activation lacks explicit Steward authorization naming the release.

## Codex CLI handoff

Read `collaboration/work_packages/pending/ESTATE-OPS-003_Common_Candidate_Live_Backup_Topology_and_Comms8_Repository_Preparation.md` and do exactly what it says.
