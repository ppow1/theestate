# ENG-OPS-004 — Merge PR #504 and Launch Post-Merge Engineering Testing

Status: **AUTHORIZED FOR CODEX EXECUTION**  
Owner: Office of the Steward  
Repository: `ppow1/theestate`  
Execution environment: `A:\theestate-wp4233`  
Date authorized: 2026-07-31

## Steward decision

PR #504 has completed ENG-OPS-001 and ENG-OPS-002, is open, non-draft, mergeable, and has passed its blocking review.

The Steward explicitly authorizes a normal merge of PR #504, followed by post-merge synchronization, acceptance checks, and execution of the previously authored operational testing package:

`collaboration/work_packages/pending/ENG-OPS-003_Post_Merge_Operational_Testing_and_Engineering_Department_Acceptance.md`

This package is intended to move directly from implementation closure into operational testing. Do not stop after the merge merely to report that testing is the next step.

## Required sequence

### 1. Pre-merge verification

Verify all of the following before merging:

- PR #504 targets `main`;
- head branch is `engineering/complete-governed-engineering-first-live-task`;
- head SHA is `b6bce860dbccb9d5576d80a656c708c5a14d4aeb`;
- PR is open, non-draft, mergeable, and has no unresolved blocking review;
- local branch and remote head match;
- worktree is clean;
- all 16 stashes remain preserved;
- `A:\theestate` remains untouched;
- institutional acceptance remains `not_granted`;
- no model download or model mutation has occurred.

If any of these conditions are false, stop and report the exact mismatch. Do not force, rebase, or rewrite history.

### 2. Merge PR #504

Perform a normal merge commit of PR #504 into `main`.

Do not squash unless GitHub policy makes a normal merge impossible. Do not force-push. Do not enable auto-merge.

After merge:

- switch to `main`;
- fetch and fast-forward to `origin/main`;
- confirm local `main` equals `origin/main`;
- record the merge commit SHA;
- confirm PR #504 is closed and merged.

### 3. Post-merge synchronization

Identify every installed or external runtime copy that must be synchronized from repository source for the merged Engineering execution path.

At minimum inspect the established Engineering Worker Runtime synchronization path:

- source: `A:\theestate-wp4233\external\engineering_worker_runtime`
- destination: `A:\AI\Tools\EngineeringWorkerRuntime`
- canonical script: `scripts\Sync-EngineeringWorkerRuntime.ps1`

Run synchronization only if the merged source or manifest requires it. Validate source/destination hashes and runtime manifest consistency afterward.

Do not copy unrelated repository content into external runtime directories.

### 4. Post-merge smoke acceptance

Run a bounded post-merge acceptance sufficient to prove that the merged production path is available from `main` and any synchronized runtime copy.

This smoke acceptance must not repeat the entire ENG-OPS-003 campaign, but it must verify:

- production imports and construction succeed;
- schema registry and Draft 2020-12 references resolve;
- registered `qwen.local.text` provider and adapter remain discoverable;
- configured model remains `qwen3:8b`;
- PTM readiness, Engineering authority, Dispatch handoff, provider receipt, reconciliation, and Grace completion contracts load correctly;
- focused changed-scope tests pass;
- Python compilation, tracked JSON parsing, and `git diff --check` pass;
- worktree remains clean after generated test artifacts are reconciled.

Do not grant institutional acceptance from this smoke check.

### 5. Execute ENG-OPS-003 immediately

After the merge and smoke acceptance pass, read and execute the complete work package:

`collaboration/work_packages/pending/ENG-OPS-003_Post_Merge_Operational_Testing_and_Engineering_Department_Acceptance.md`

Execute it from beginning to end.

This is the next phase of the same campaign. Do not stop to ask whether testing should begin.

ENG-OPS-003 must test repeated and varied operational behavior, including successful Qwen work, Codex routing, capability gaps, stale evidence, prohibited scope, provider failure, idempotency, and a realistic Steward request through Grace.

Follow ENG-OPS-003's own correction and stop boundaries. Correct in-scope production defects encountered during testing rather than merely documenting each correctable failure.

### 6. Repository evidence

Create durable post-merge and testing reports in the repository under the namespaces specified by ENG-OPS-003.

Do not commit raw local logs, caches, temporary worktrees, model data, or unrestricted `A:\AI` runtime directories.

Commit and push any authorized corrections and reports on the branch required by ENG-OPS-003. Open or update draft PRs as specified there. Do not merge testing corrections without separate Steward authorization.

## Preservation requirements

Throughout this package:

- preserve all 16 stashes;
- leave `A:\theestate` untouched;
- do not download, replace, or update any model;
- do not alter historical Qwen evidence;
- do not grant institutional acceptance unless ENG-OPS-003 explicitly reaches and recommends that decision for separate Steward action;
- use the same resumed Codex session and do not open a new Codex window;
- keep repository and external-runtime changes bounded and auditable.

## Final report

Report:

- PR #504 pre-merge state;
- merge method and merge commit;
- synchronized runtime paths and hash results;
- post-merge smoke acceptance results;
- ENG-OPS-003 branch and commits;
- each operational test scenario and result;
- any corrections made;
- live provider invocation counts;
- artifacts, receipts, and hashes;
- Engineering and Grace outcomes;
- institutional acceptance state and recommendation;
- worktree state;
- stash count;
- model preservation;
- confirmation `A:\theestate` remained untouched;
- draft PR number for testing/corrections, if created;
- exact next Steward action.
