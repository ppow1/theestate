# WP-4217 — Staged Local Git Synchronization Assistant

Status: Pending
Priority: High
Owner: Chief Architect / implementation worker
Classification: Estate Internal, staged operator-assistance extension
Promotes: PL-0019
Authored: 2026-07-26
Base commit: `94d5168e5e1c9a935791b73f316c4efb80a46745`

## Mission

Stage an implementation-ready, read-only Local Git Synchronization Assistant that turns existing repository, publication, readiness, audit, execution-control, and validation evidence into one deterministic operator assessment. It inspects and explains; it does not synchronize or mutate a repository.

The assistant does not replace Git, the Operational Readiness Closure Controller, governed publication, Post-Merge Audit, Execution Control, repository validation, or their records. It must never become another Git wrapper, synchronization engine, publication service, repository state database, scheduler, or authority surface.

## Reconciled baseline and bounded gap

PL-0019 classification at authoring: **partially_implemented**.

Existing capabilities already provide important pieces:

- `operational_readiness_closure` inspects clean/dirty state, branch, revisions, required-commit ancestry, ahead/behind state, fetch and publication evidence; refuses unsafe states; performs only separately authorized controller remediations.
- Its governed publication path performs authorized push plus fetch, upstream containment, and synchronization verification.
- `merge_discovery` fetches configured remotes, records reachability/fetch failure, and discovers against the remote base branch.
- Operational Targets and Post-Merge Audit report active-tree hygiene; Cleanroom Audit isolates validation from dirty active work and never repairs that tree.
- Execution Control rejects unsafe dirty workspaces, and repository/work-package validation remains the validation authority.

The missing capability is one operator-facing, read-only coordination contract that explains local synchronization state, predicts likely conflicts, supplies safe recommendations and bounded remediation guidance, and preserves deterministic diagnostic history with provenance. WP-4217 authors only that gap.

## Required reading and reuse contract

Read before implementation:

- `collaboration/work_packages/pending/WP-0650_Autonomous_Post_Merge_Operational_Readiness_Closure_Loop.md`
- `collaboration/work_packages/pending/WP-0653_Complete_Governed_Publication_and_Production_Readiness_Policy_Enforcement.md`
- `collaboration/work_packages/pending/WP-0618_Background_Operational_Targets_and_Post_Merge_Audit.md`
- `collaboration/work_packages/pending/WP-0626_Cleanroom_Post_Merge_Audit_Service.md`
- `src/estate/core/operational_readiness_closure.py`
- `src/estate/core/merge_discovery.py`
- `src/estate/core/post_merge_audit.py`
- `src/estate/core/audit_workspace_service.py`
- `src/estate/core/work_package_validation.py`
- existing Execution Control modules and CLI projections
- `docs/architecture/local_git_synchronization_assistant.md`

Reuse public projections/helpers where stable. If a reusable read-only Git inspection seam is absent, stage a pure inspector and propose later extraction through the install package; do not modify or import private controller mutation handlers. Publication/readiness/audit/validation verdicts remain authoritative in their own domains. The assistant may link to them and report disagreement, never overwrite them.

## Scope and state inspection

Given an explicitly configured repository target, base branch, and remote, produce one snapshot containing:

1. repository identity and canonicalized local root;
2. local HEAD object ID and symbolic branch, or explicit detached HEAD;
3. configured remote and remote-tracking reference;
4. upstream existence and whether it matches the configured target;
5. porcelain-v2 working-tree/index/untracked/submodule state without file contents;
6. merge, rebase, cherry-pick, revert, bisect, and sequencer-in-progress indicators;
7. last attempted fetch time/result and remote reachability classification;
8. ahead/behind counts and merge-base for HEAD versus upstream after a successful fetch, or explicitly stale/unknown counts;
9. relationship: `synchronized`, `ahead`, `behind`, `diverged`, `unborn`, or `unknown`;
10. fast-forward, merge, rebase, and publication readiness as separate verdicts;
11. conflict prediction, recommendations, diagnostics, provenance, and prior assessment linkage.

Inspection must use argument arrays with an explicit working directory, bounded timeouts/output, allowlisted Git commands, and no generated shell. Resolve repository and Git directory safely. Reject an unconfigured path, non-repository, bare repository unless explicitly supported, unsafe ownership response, or path escape with a deterministic diagnostic.

## Fetch and reachability semantics

Fetch is the one potentially network-observing operation, not a synchronization mutation. The staged assistant defaults to a fixture-backed **no-network** mode. A future install package may expose `--fetch` only as an explicit operator request and only by delegating to the established Merge Discovery/readiness fetch seam or an approved read-only adapter.

- Never claim current remote state from cached refs without reporting `fetch_status=cached` and observation age.
- Distinguish missing remote, DNS/transport failure, timeout, authentication failure, authorization failure, remote missing, and generic Git failure when evidence permits; otherwise report `unreachable_unknown` without guessing.
- A failed fetch preserves the last successful observation and marks remote-derived conclusions stale/unknown. It must not zero ahead/behind counts or claim synchronized.
- Fetch must not prune, change remotes, update submodules, write working-tree files, run hooks intentionally, or trigger credentials interactively. Disable terminal prompts and bound elapsed time.
- Record sanitized command identity, exit code, duration, observed remote/ref, and redacted stderr category; never retain credentials or credential-bearing URLs.

## Readiness verdicts

Each verdict is `ready`, `not_ready`, `unknown`, or `not_applicable`, with sorted reason codes and evidence references.

### Merge readiness

Requires an attached expected branch, valid/reachable upstream, no operation in progress, a clean index/worktree unless policy explicitly permits a non-overlapping untracked set, known ancestry, and no predicted conflicts for the proposed upstream merge. Being behind with a fast-forward path is `ready` for fast-forward, not permission to execute it. Divergence or predicted conflicts is `not_ready`.

### Rebase readiness

Requires an attached expected branch, upstream, no operation in progress, clean state, at least one local-only commit, known merge-base, and no predicted replay conflict. Report policy/branch-protection constraints separately. A recommendation may describe an operator-controlled rebase only when allowed by policy; it never executes one.

### Publication readiness

Consume the existing governed-publication assessment where available. At minimum require attached expected branch, clean state, reachable upstream, known ahead/behind, `ahead > 0`, `behind = 0`, attributable/authorized commits, and existing publication authority. `behind > 0`, divergence, missing authority, or unknown remote state is not ready. Already synchronized is `not_applicable`, not ready-to-push. Only the Publication Controller may publish.

Readiness must distinguish technical possibility from authorization and institutional approval.

## Conflict prediction

Prediction is advisory and must not touch the index or working tree.

- For a behind/diverged merge assessment, use a read-only merge-tree computation supported by the installed Git version against immutable object IDs.
- For rebase, inspect the ordered local-only commit range and use a disposable isolated worktree/clone only if merge-tree analysis cannot give adequate evidence. The disposable path must live under the WP-4217 staging root, run with hooks disabled where supported, and be removed or retained according to diagnostic policy.
- Classify `none_predicted`, `conflict_predicted`, `unknown_tooling`, `unknown_missing_objects`, or `unknown_remote_stale`.
- Report affected repository-relative paths only when safe, sorted and optionally redacted; do not expose file contents. Rename, binary, submodule, merge-commit, and recursive-conflict uncertainty must remain explicit.
- A prediction never claims a real operation will be conflict-free and never automatically resolves a conflict.

## Deterministic diagnostics and recommendations

Diagnostics use stable codes, severity, safe summary, evidence IDs, and suggested remediation IDs. Sort by severity rank, code, and stable subject. Volatile timestamps/durations are excluded from `assessment_id`.

Recommendations are ordered, non-executable guidance. Generate only from a versioned decision table. The first recommendation must be the safest next observation or operator action. Examples include:

- commit or deliberately remove/stage local work according to operator intent;
- abort or finish the already-pending Git operation using normal Git guidance;
- attach/switch to the expected branch after preserving work;
- configure/verify an upstream through an authorized repository administrator;
- retry explicit fetch after connectivity or credentials are restored;
- use a normal fast-forward only after the tree is clean and policy permits;
- review predicted conflict paths before an operator-controlled merge/rebase;
- send an authorized ahead-only state to the existing Publication Controller.

Never recommend or execute force push, reset, clean, stash as routine flow, automatic branch deletion, remote mutation, history rewriting, conflict resolution, or discarding work. Where intent cannot be inferred, say so and request operator review rather than prescribing a destructive command.

## Assessment contract

The staged schema must include at least:

```json
{
  "schema_version": "local-git-sync-assessment-v1",
  "assessment_id": "sha256-of-canonical-stable-evidence",
  "repository": {"target_id": "estate-main", "root_id": "redacted-stable-id"},
  "head": {"oid": "hex", "branch": "main", "detached": false},
  "working_tree": {"clean": true, "index_changes": 0, "worktree_changes": 0, "untracked": 0},
  "operation": {"state": "none"},
  "upstream": {"remote": "origin", "ref": "origin/main", "configured": true},
  "fetch": {"status": "succeeded", "observed_at": "2026-07-26T00:00:00Z"},
  "relationship": {"state": "behind", "ahead": 0, "behind": 2, "merge_base": "hex"},
  "conflict_prediction": {"state": "none_predicted", "method": "merge-tree"},
  "readiness": {"fast_forward": "ready", "merge": "ready", "rebase": "not_applicable", "publication": "not_applicable"},
  "recommendations": [{"id": "review_fast_forward", "rank": 10}],
  "diagnostics": [],
  "provenance": {"inspector_version": "v1", "input_evidence_ids": []},
  "history": {"previous_assessment_id": null}
}
```

Canonical JSON uses UTF-8, sorted object keys, stable list ordering, normalized booleans/enums, and object IDs rather than mutable ref names in computed evidence. The same repository/object/ref evidence and decision-table version must yield the same `assessment_id`, diagnostics, readiness, and recommendations.

## Synchronization history and provenance

Do not create another repository state database. Append immutable, bounded assessment records to the existing appropriate operational evidence/history mechanism selected by the install package. In staging, use fixture-local JSONL under `collaboration/workstreams/WP-4217/fixtures/output/` only.

Each record links previous/current assessment IDs, target ID, inspector/schema/decision-table versions, Git version, sanitized command evidence, local/upstream object IDs, fetch evidence, consumed controller/audit/validation evidence IDs, producer, start/end times, and redaction policy. Store recommendations and observations, not claims that an operator acted. Retention, compaction, and Office projection must reuse existing evidence policy. Timestamps are provenance, never state-order authority.

## Operator guidance and presentation

The staged output must provide both canonical JSON and a deterministic human summary:

- one-line state: branch, clean/dirty, relationship, remote freshness;
- blockers before opportunities;
- separate merge/rebase/publication readiness;
- predicted-conflict confidence and limitations;
- safest next recommendation with rationale;
- links/IDs for existing publication, readiness, audit, execution, and validation evidence;
- explicit “no action performed.”

The later install package may project this into the existing CLI/Office only. It must not create a dashboard or fake action button. Any action offered must route to an existing authorized controller and preserve preview/confirmation/authority gates.

## Staging and parallel-safety boundary

All implementation is initially confined to:

```text
collaboration/workstreams/WP-4217/
  proposed/
  schemas/
  fixtures/
  tests/
  integration_notes.md
  validation_notes.md
  install_manifest.json
```

The staged implementation may contain a pure inspector, parsers, decision table, deterministic renderer, fake remotes/repositories, and conflict-prediction harness. It must not modify `src/estate/**`, `tests/**`, `operations/**` runtime artifacts, existing controllers, CLI, shared schemas, or production Office assets. No production Git behavior is permitted. Installation requires a later reviewed install package with file hashes, exact reuse seams, migration/rollback, and shared test impact.

## Prohibited behavior

The assistant must not perform automatic or implicit push, pull, fetch, rebase, merge, conflict resolution, force push, reset, clean, stash, checkout/switch, branch creation/deletion, commit, tag, remote modification, submodule update, worktree repair, or credential change. The only future optional network observation is an explicit bounded fetch through an approved existing seam. Tests must fail if mutation command tokens appear in executed-command evidence.

## Required staged deliverables

1. Versioned assessment/evidence schemas and decision table.
2. Pure repository-state inspector and safe Git result parser.
3. Deterministic readiness/recommendation engine.
4. Read-only conflict-prediction adapter with explicit unknown states.
5. Deterministic JSON and operator-summary renderer.
6. Fixture-local append-only history/provenance demonstration.
7. Fake local/bare remote repository factory and required scenario fixtures.
8. `integration_notes.md` mapping every reused controller/projection and identifying any proposed helper extraction.
9. `install_manifest.json` proposing—not applying—production integration and rollback.
10. `validation_notes.md` with exact commands/results and no-mutation/no-network proof.

## Required tests

Tests must prove:

1. clean synchronized repository;
2. dirty repository, including staged, unstaged, untracked, and submodule summaries;
3. detached HEAD;
4. ahead-only state;
5. behind-only/fast-forward state;
6. diverged state;
7. missing and mismatched upstream;
8. unreachable remote and failed-fetch stale-truth behavior;
9. pending merge and each other recognized in-progress operation;
10. rebase required/readiness, including zero-local-commit not-applicable behavior;
11. merge conflict predicted and prediction-unknown behavior;
12. safe recommendation generation for every state;
13. deterministic diagnostics, assessment IDs, summaries, and stable ordering under repeated runs;
14. publication readiness delegates/aligns with existing governed publication evidence;
15. dirty/detached/diverged/unknown states never produce an unsafe action recommendation;
16. no repository files, refs, index, stash list, remotes, or configuration change during inspection;
17. no push/pull/rebase/merge/reset/clean/stash/checkout/remote mutation subprocess is executed;
18. fixture-only tests make no external network/provider/GPU calls and never prompt for credentials;
19. history links prior assessments and preserves provenance without becoming authoritative state;
20. malformed Git output, timeouts, missing Git, unsupported merge-tree, path escape, and unsafe repository fail safely.

Use temporary repositories with local bare remotes and fixed identities/timestamps. Snapshot refs/config/status/stashes before and after every scenario and compare them byte-for-byte where practical.

## Validation recipe and acceptance

The staged completion receipt must record exact results for:

```text
python -m pytest -q collaboration/workstreams/WP-4217/tests
python -m json.tool <each schema/fixture/manifest JSON>
git diff --check
```

Also run existing focused compatibility tests selected in `integration_notes.md` for Operational Readiness publication, Merge Discovery fetch failure/remote truth, Cleanroom Audit dirty-tree isolation, Post-Merge Audit, Execution Control dirty rejection, and work-package validation. No live remote, production repository, provider, or credential may be used for staged acceptance.

Acceptance evidence must show identical repeated assessments, correct state matrices, immutable repository snapshots, redacted diagnostics, explicit stale/unknown remote behavior, and `action_performed=false` in every result.

## Completion, lifecycle, and rollback

The implementation receipt must enumerate staged files, tests, limitations, versions, base/branch/commit, evidence, and assertions:

```text
reused_operational_readiness_controller: true
reused_publication_controller: true
reused_post_merge_audit: true
reused_execution_control: true
reused_repository_validation: true
new_git_wrapper_or_sync_engine_created: false
new_publication_system_created: false
new_repository_state_database_created: false
automatic_git_mutation_performed: false
production_or_shared_files_modified: false
```

Staging rollback removes `collaboration/workstreams/WP-4217/`. The later install package must define file-by-file restore and projection removal while leaving all existing controllers/evidence intact.

PL-0019 remains **Promoted** while this package is authored or staged. Only a later production implementation package, merged with passing tests, validation evidence, install receipt, and confirmed reuse, may mark PL-0019 Closed.
