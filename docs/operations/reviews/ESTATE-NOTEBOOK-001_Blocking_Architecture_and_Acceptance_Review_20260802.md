# ESTATE-NOTEBOOK-001 Blocking Architecture and Acceptance Review

Review date: 2026-08-02  
Repository: `ppow1/theestate`  
Reviewed base: `origin/main` / `e4e4828855bb468dfe3276730eb1dbe22bb89460`  
Required reviewed head: `915e472eb32181d97fa5549bc2350bca98c7c3c0`  
Review worktree: `A:\review-wp515` (fresh detached worktree at the required head)  
PR: #515, draft, open, mergeable; no merge or auto-merge performed

## Scope and method

This is an independent blocking review. The authoring worktree was not used for
implementation or validation. The required head was fetched and verified, and
all 31 PR files were read completely. The review read the canonical onboarding,
worker-runtime, instruction-precedence, reflection/continuity, dispatch,
reconciliation, PTM, and Estate architecture materials relevant to this
package. The review inspected the implementation, schemas, proof runner,
generated evidence, focused tests, PR metadata, and exact dirty-worktree diff.

## Changed files

The PR contains only the following intentional notebook-package files:

- `collaboration/work_packages/pending/ESTATE-NOTEBOOK-001_Engineering_Notebook_and_Worker_Continuity_Standard.md`
- `docs/engineering_notebook/Acceptance_Report.md`
- `docs/engineering_notebook/Engineering_Notebook_Standard.md`
- `docs/engineering_notebook/Engineering_and_Resident_Integration.md`
- `docs/engineering_notebook/Failure_Analysis_and_Anti_Patterns.md`
- `docs/engineering_notebook/Implementation_Report.md`
- `docs/engineering_notebook/Notebook_Lifecycle_and_Runtime_Contract.md`
- `docs/engineering_notebook/Notebook_Schema_and_Provenance.md`
- `docs/engineering_notebook/Operator_Runbook.md`
- `docs/engineering_notebook/Readiness_Checklist.md`
- `docs/engineering_notebook/Recovery_and_Closure.md`
- `docs/engineering_notebook/Worked_Example_and_Proof.md`
- `experiments/engineering_notebook_001/evidence/handoff.json`
- `experiments/engineering_notebook_001/evidence/notebook.md`
- `experiments/engineering_notebook_001/evidence/notebook_state.json`
- `experiments/engineering_notebook_001/evidence/poc_report.json`
- `experiments/engineering_notebook_001/evidence/receipt-close.json`
- `experiments/engineering_notebook_001/evidence/receipt-html.json`
- `experiments/engineering_notebook_001/evidence/receipt-parser.json`
- `experiments/engineering_notebook_001/evidence/receipt-schema.json`
- `experiments/engineering_notebook_001/input/corpus.md`
- `experiments/engineering_notebook_001/poc_runner.py`
- `experiments/engineering_notebook_001/workspace/workspace/dashboard.html`
- `experiments/engineering_notebook_001/workspace/workspace/parsed.json`
- `experiments/engineering_notebook_001/workspace/workspace/validated.json`
- `schemas/notebook/engineering_notebook_state_v1.schema.json`
- `schemas/notebook/notebook_handoff_v1.schema.json`
- `schemas/notebook/notebook_update_proposal_v1.schema.json`
- `schemas/notebook/notebook_verification_receipt_v1.schema.json`
- `src/estate/core/engineering_notebook.py`
- `tests/test_engineering_notebook.py`

No Grace, Helen, Open WebUI, Gateway, provider, Skill, benchmark, or Estate
runtime file is in the PR diff.

## Worktree and change hygiene

The authoring worktree `A:\theestate-notebook-001` is on
`agent/estate-notebook-001` at the reviewed head and has exactly these five
pre-existing, unstaged tracked modifications:

1. `operations/operations_scheduler/status.md`
2. `operations/residents/helen/Helen_Operational_Readiness_Report.md`
3. `operations/residents/surfaces/helen.json`
4. `runtime/office/steward_participant_board.json`
5. `runtime/residents/helen/readiness.json`

Their diffs are generated timestamp/readiness projections: scheduler and
resident generation timestamps, participant elapsed time, and Helen workforce
assessment counts/readiness fields. The branch reflog shows the branch was
created from `origin/main` at 2026-08-02 00:29 -0400; the notebook commits were
created later at 00:50 and 07:15 -0400. The five files are absent from both PR
commits and absent from the PR diff. Git cannot establish the exact process that
generated them, but their file contents/timestamps demonstrate they appeared
after branch creation and before this review. The notebook proof writes only its
own experiment input/workspace/evidence paths and does not import these runtime
projections; no evidence shows that they affected notebook tests or proof
behavior.

The authoring worktree must be preserved for its owner to reconcile or retire
later. It must not be reset, cleaned, stashed, or included in this PR. The fresh
review worktree is clean and isolated.

## Authority and architecture review

### Passing boundary decisions

The package’s stated architecture correctly keeps the notebook subordinate to
repository canon, work packages, architecture, authorization, PTM, Dispatch,
provider readiness, receipts, validation/reconciliation, and Steward/institutional
acceptance. The documents explicitly say the notebook is a projection and not a
registry, PTM, Dispatch, receipt, reconciliation system, memory diary, or
orchestration loop. The proposed Grace/Helen/Engineering examples are explicitly
procedural and not live routes. No duplicate office, registry, provider path,
Help execution path, or resident production integration was added.

`institutional_acceptance` is constrained to `not_granted` in the schemas,
runtime, evidence, and reports. No model was onboarded or invoked.

### Blocking authority/enforcement findings

The architecture is conceptually sound, but the runtime does not enforce all of
the documented authority boundary:

- `create_notebook` accepts an arbitrary `source_commit` and authorization
  reference without resolving them against repository canon or an authorization
  record.
- `validate_update_proposal` accepts an empty provenance list and an empty
  observed-facts mapping. A caller can therefore submit a complete, valid-shaped
  state update without validator, harness, repository, or operator evidence.
- `apply_verified_update` accepts worker-proposed values whenever their shape
  validates; it does not require every changed top-level field to be present in
  observed facts or require non-worker provenance.
- A proposal can set `freshness.state` to `current`, `status` to `completed`, or
  erase blockers if the resulting structure passes the weak validators.

These are BLOCKING because the implementation can promote unsupported narrative
into verified state and can manufacture a completion/current-state transition.

## Schema review

The four top-level schema objects use `additionalProperties: false`, and the
state’s main nested objects are mostly closed. The schemas include version
constants, authority flags, freshness state, SHA-256-looking source digests,
provenance categories, validation states, retry counters, and institutional
acceptance constants.

The schemas are not coherent or sufficient for the stated contract:

- `safeList` accepts `foo/../bar`; it also does not encode the runtime’s complete
  Windows-drive/normalization rules. The runtime and JSON schema can disagree
  about the same path.
- Runtime validation does not enforce the schema’s date-time formats. A malformed
  `created_at` can pass `validate_notebook` and later fail only when freshness is
  calculated.
- `task.stage_status` is any non-empty string; completed/remaining stages are not
  reconciled; stage transitions are not constrained; and completion does not
  require `stage_status=complete`, no remaining stages, no blocker, or a valid
  terminal stage.
- `evidence.last_results`, `evidence.test_counts`, and receipt
  `observed_facts` are open/untyped objects. Nested secret-like values and
  unsupported claims can pass both schema shape checking and runtime validation.
- Receipt and handoff schemas are closed only at the outer object. Receipt
  identity, observed-fact structure, worker identity, and source binding are not
  sufficiently constrained.
- `create_handoff` accepts `packet_digest="not-a-digest"`, producing an artifact
  that violates its own handoff schema.
- The runtime permits an omitted `institutional_acceptance` field by defaulting
  it to `not_granted`, while the schema requires the field. This is safe in
  direction but demonstrates schema/runtime divergence.
- There is no schema/runtime representation that binds authorization, assigned
  worker, stage-file set, validation outputs, source commit, and source document
  digests into one independently verifiable snapshot.
- There is no archive/closure schema or runtime transition that makes a completed
  packet immutable and auditable.

## Runtime enforcement review

The implementation covers in-memory creation, structural validation, packet
construction, acknowledgment comparison, a freshness calculation, proposal
validation, a deep-copy update, Markdown rendering, and handoff construction.
It does not implement notebook loading, durable verified-state writing, atomic
replacement, archive/closure, resume-from-handoff, or idempotent update replay
protection.

The following directly reproduced fail-open behaviors are BLOCKING:

1. A notebook two hours old with `freshness.state=current` still passes
   `acknowledge`; `detect_freshness` only returns a result and does not bind that
   result to execution authorization.
2. A source digest mismatch returns `conflicted`, but the proof never feeds that
   result into acknowledgment or an update. The mismatch is detected, not
   rejected.
3. A state with an active stage, no remaining-stage proof, and passing evidence
   can be marked `status=completed` through an empty-observation update.
4. A worker at `repair_count == retry_limit` can still acknowledge and continue.
5. A proposal with `provenance=[]` and `observed={}` can change freshness to
   current or status to completed.
6. An invalid handoff digest is accepted by `create_handoff`.
7. Secret-like content nested inside `evidence.last_results` is accepted because
   only selected top-level text fields are scanned.
8. `apply_verified_update` always changes `last_verified_at`, but there is no
   persistent compare-and-swap, proposal idempotency, or replay record. Replaying
   a proposal can duplicate provenance and produce a new state digest.

The Markdown renderer labels the notebook as subordinate, which is good, but it
does not escape Markdown/HTML control content in arbitrary narrative fields. It
also renders only a subset of state, so it is a review projection rather than a
complete provenance-preserving archive.

## Provenance and fact classes

The category vocabulary distinguishes `worker_proposed`, `harness_observed`,
`validator_produced`, `operator_authorized`, and `repository_derived`. The
vocabulary is correct, and accepted update provenance is appended to state.

The enforcement is BLOCKING: provenance entries may be empty; categories are
not tied to the actor or operation; source/digest claims are not verified; and
the `observed` argument can omit every changed field. Consequently a worker
claim can be accepted without a supporting validator/harness/repository fact.
Handoffs carry only a packet digest and do not carry or verify the provenance
chain. Markdown omits provenance entirely. Closure/archive is absent.

## Freshness and conflict review

`detect_freshness` checks age and compares the notebook’s known source-digest
keys. It correctly reports a changed digest as `conflicted` and an old timestamp
as `stale` in isolation. It does not persist the result, compare source commit,
authorization, assigned worker, stage files, validation outputs, or expiry, and
it ignores extra authoritative digest keys. A caller can leave the stored state
as `current` and proceed.

Required freshness behavior is therefore BLOCKED:

- stale/conflicted status is visible only as a returned calculation and can be
  silently ignored;
- freshness cannot safely become current without an independently observed
  replacement snapshot;
- authority/safety changes do not fail closed;
- orientation is not separated from executable acknowledgment by an enforced
  gate;
- conflicting authoritative sources are not modeled as a complete conflict set.

## Pre-action acknowledgment

The acknowledgment shape includes objective, current stage, repository, write
scope, blocker, required validation, and prohibited actions, and mismatches are
rejected as errors. This part is directionally correct. However, stage files are
not included in the acknowledgment comparison, freshness is not recomputed, the
source commit is not checked, expiry is not checked, and retry exhaustion is not
checked. Thus a syntactically correct acknowledgment can authorize work from a
stale or otherwise invalid packet. This is BLOCKING.

## Harness continuity proof

The proof establishes only a deterministic scripted state-transition demonstration
in one Python process. It does not establish the requested fresh-session
continuity:

- `WorkerSession` objects are created in a single process; they are not fresh
  processes or independently reloaded workers.
- Each packet’s `state` points to the same mutable in-memory state object; there
  is no serialize/reload boundary proving session isolation.
- The loop updates parser, schema, and HTML sequentially, but creates one handoff
  only after all three stages. Session 3 does not resume from that handoff.
- The stale test supplies an intentionally wrong digest to `detect_freshness` but
  never attempts acknowledgment afterward, so no stale-digest rejection is
  demonstrated.
- Fixture integrity is measured after the runner itself creates the fixture; it
  proves no mutation during the short run, not preservation of a pre-existing
  authoritative fixture.
- The packet-size number is a serialized Python dictionary length, not a model
  token count or an independently measured context reduction against a defined
  full-state baseline.

The reports correctly state that model-specific acceptance is pending, but the
claims “3 fresh sessions,” “fresh-session stage continuation,” and “stale-digest
rejection” overstate what this harness proves. This is BLOCKING for the stated
proof objective. Correct classification is: partial schema/runtime harness
exercise, not genuine fresh-session continuity.

## Proof classification

- A. Schema/runtime continuity only: partially demonstrated.
- B. Harness-level fresh-session continuity: NOT demonstrated by the current
  runner because sessions are not fresh and no handoff-resume boundary exists.
- C. Actual local-model notebook comprehension/continuation: NOT TESTED.
- D. Resident-integrated Estate continuity: NOT TESTED.

The PR must not imply C or D. Devstral, Qwen3-Coder, or another explicitly
authorized worker must perform a real notebook-driven continuation after the
runtime and harness gates are repaired. No such worker was onboarded or invoked
in this review.

## Integration safety

The documentation correctly keeps Grace as a possible bounded summary surface,
Helen as a readiness/fitness consumer, PTM as planning/readiness authority,
Dispatch as assignment authority, receipts/reconciliation as execution evidence,
Skills as procedures, and Help as explanatory only. The PR adds no live
integration, duplicate registry, second task queue, provider route, or Historian
replacement. Architecture-level integration safety passes, subject to the
runtime enforcement blockers above.

## Security review

No credentials or private chain-of-thought are present in the changed artifacts.
The secret scan found only the intentional redaction test literal and the secret
detector regex. Absolute paths and ordinary traversal are rejected by runtime
validation.

Security remains BLOCKED for production use because the JSON schema accepts some
paths the runtime rejects, nested evidence values are not scanned for secrets,
Markdown control content is not escaped, authority references are not resolved,
and the package has no durable tamper-resistant load/write/archive path. A
prompt-injection string placed in a narrative field is not authority by design,
but the runtime has not provided a complete trusted/untrusted field boundary or
role-limited rendering contract.

## Test quality and results

The seven focused tests cover creation, one acknowledgment mismatch, unknown
fields, one unsafe path, stale calculation, manually set conflict state, one
observed update, scope widening, one false-completion mismatch, redaction
rejection, handoff construction, and schema meta-schema parseability. They do not
cover the fail-open cases listed above, schema-instance validation, persistence,
archive/closure, retry exhaustion, source-commit changes, stage-file changes,
worker reassignment, expiry, authority changes, replay/idempotency, or a real
handoff/resume boundary.

Observed review validation at the required head:

- Focused notebook tests: **7 passed**.
- Small relevant worker/assignment/task-visibility integration subset:
  **18 passed**.
- Python compilation: **passed**.
- Changed-file `git diff --check`: **passed**.
- Four schema documents: meta-schema checks passed; this does not validate the
  runtime contract or adversarial instances.
- Changed JSON artifacts: parseable.
- All tracked repository JSON: 1,487 examined; two pre-existing malformed
  fixtures outside the PR were reported by the broad scan:
  `collaboration/workstreams/WP-4219/fixtures/malformed_queue_input.json` and
  `collaboration/workstreams/WP-4227/fixtures/malformed_inputs.json`.
- Secret scan: no actual secret found in the package.
- Full repository suite: not run to completion and not claimed as passed.

## Blocking corrections required

Before merge, the package requires, at minimum:

1. Bind freshness/conflict/expiry/source-commit/authorization/worker/stage-file
   and validation-output checks to acknowledgment and execution; stale or
   conflicted state must fail closed and cannot be reset to current by a worker
   update.
2. Require observed facts for every changed field and at least one trusted
   non-worker provenance category; reject empty provenance/observation updates.
3. Enforce completion and stage-transition invariants, blocker preservation, and
   retry-limit stop behavior.
4. Close and align schemas with runtime path, timestamp, digest, nested evidence,
   receipt, provenance, identity, and handoff validation.
5. Add safe durable load/write/archive behavior or narrow the package claims so
   no unsupported persistence/closure contract is advertised; protect writes
   against partial replacement and replay.
6. Replace the scripted proof with independently serialized fresh sessions and
   an actual handoff/resume boundary, and exercise stale/conflict rejection rather
   than only returning a diagnostic result.
7. Add adversarial tests for every blocking case and update acceptance language
   to distinguish harness evidence from model and resident acceptance.

These corrections remain within the notebook package. They do not authorize
Grace/Helen production integration, model benchmarking, or institutional
acceptance.

## Non-blocking observations

- The package’s documentation is concise and consistently says institutional
  acceptance remains `not_granted`.
- The operator commands are labeled procedural rather than live, which is safe.
- The proof’s explicit “model-specific acceptance pending” language is correct
  once the overbroad fresh-session/stale-rejection wording is narrowed.
- Full repository JSON validation is currently noisy because the repository
  intentionally contains two malformed fixture inputs; package-local JSON is
  parseable.
- The authoring worktree’s five generated modifications should be reconciled or
  retired by its owner after this review, but they are not PR blockers when kept
  out of the branch.

## Model acceptance still pending

No Devstral, Qwen3-Coder, or other coding model was onboarded or invoked. After
the blocking runtime and harness corrections, model acceptance must use a real
worker/session that receives only the verified packet, acknowledges the exact
scope, resumes after serialization/handoff, handles stale/conflicted state by
stopping, and produces independently validated evidence. That is a separate
acceptance gate and must not change institutional acceptance.

## Institutional acceptance

`not_granted`. This review does not grant, imply, or recommend automatic
institutional acceptance.

## Merge-readiness decision

**NOT READY.** PR #515 must remain draft. Do not merge and do not enable
auto-merge. The existing branch and authoring worktree must be preserved; no
runtime or resident integration should proceed until the blocking corrections
are implemented and independently re-reviewed.

## Final decisions

1. Architecture: **PASS** for the documented authority/integration boundaries;
   implementation enforcement remains blocking.
2. Schema/runtime implementation: **BLOCKED**.
3. Harness continuity proof: **BLOCKED**.
4. Actual local-model notebook acceptance: **NOT YET TESTED**.
5. Resident integration: **NOT YET TESTED**.
6. PR #515: **NOT READY**.

## Review disposition

No implementation correction was applied during this independent review. The
only intended review artifact is this report. The five unrelated dirty files in
`A:\theestate-notebook-001` were not modified, staged, reset, cleaned, stashed,
or discarded.
