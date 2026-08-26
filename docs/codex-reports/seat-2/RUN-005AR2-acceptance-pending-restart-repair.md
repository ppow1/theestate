# RUN-005AR2 Acceptance-Pending Restart Repair

Package: RUN-005AR2  
Role: C2 Campaign Runner targeted repair writer  
Validated base: `a64283acae5a6c9e77caf09a516fa2ef2f732a33`  
Repair commit: `f6fbeaa9d9a8ec35ee651aebb8c291e8884e4870`  
Verified `origin/main`: `f6fbeaa9d9a8ec35ee651aebb8c291e8884e4870`

## Status

`REPAIR_COMPLETE_READY_FOR_REVALIDATION`

## Validator defects repaired

1. A durable `accepted` projection with candidate fields but
   `acceptance_dispatch_count = 0` was returned as accepted.
2. A restart from `awaiting_independent_acceptance` fell through to package
   execution and dispatched a second acceptance.

## Authoritative state model

`campaign_package_runs` now distinguishes:

- `verifying`: internal verification is still being completed;
- `candidate_ready`: candidate is durably recorded but acceptance has not been
  dispatched;
- `awaiting_independent_acceptance`: the current candidate has one durable
  acceptance dispatch and the validator result is pending;
- `acceptance_failed`: the current acceptance returned defects and a new repair
  pass is allowed;
- `accepted`: terminal accepted state;
- `escalated`: bounded repair could not safely continue.

The valid accepted predicate enforced by `PackageEngineerLoop` is:

```text
state = 'accepted'
candidate_ref is non-empty
candidate_version_hash is non-empty
acceptance_dispatch_count is an integer >= 1
acceptance_candidate_ref == candidate_ref
acceptance_candidate_version_hash == candidate_version_hash
```

An incomplete or mismatched accepted projection raises a lifecycle integrity
error before package execution, repair, candidate creation, or dispatch. It is
not normalized or repaired automatically.

## Exact repair

Migration `0044_package_acceptance_correspondence.sql` adds durable
current-candidate dispatch correspondence. Migration
`0045_package_candidate_ready_state.sql` adds the candidate-ready state to the
projection constraint.

`CampaignLifecycleStore.record_package_candidate()` durably records a candidate
before dispatch and clears correspondence for any previous candidate.
`dispatch_package_acceptance()` atomically binds the dispatch to the current
candidate. A concurrent identical dispatch observes the already-awaiting state
and returns the existing count without incrementing it. A different candidate
cannot reuse the pending dispatch.

`PackageEngineerLoop.run()` now short-circuits before adapter execution for:

- valid `accepted`: returns the existing candidate/outcome;
- valid `awaiting_independent_acceptance`: returns a pending outcome;
- `candidate_ready`: dispatches the one remaining acceptance boundary without
  replaying package engineering.

Malformed accepted state fails closed.

## Restart behavior

For a candidate with dispatch count 1 and pending validator result, a recreated
`CampaignLifecycleStore` and `PackageEngineerLoop` return
`awaiting_independent_acceptance`. Package execution, repairs, candidate
creation, and validator dispatch remain at zero. The state remains pending until
the authoritative validator result arrives.

After a valid PASS is recorded, subsequent restarts return terminal accepted
without any additional acceptance event. The existing independent FAIL path
still records defects, returns to the package repair loop, creates a new
candidate, and binds a new acceptance dispatch to that candidate.

## Concurrency and idempotency

The dispatch update is conditional on the package being in a dispatchable state
and either having no current dispatch correspondence or matching the exact
candidate. PostgreSQL row locking plus the conditional update ensure two
concurrent starts produce one increment: both observers receive count `1`, and
the durable count remains `1`.

## Crash-boundary matrix

- Before execution: existing package execution path resumes.
- During engineering/repair: existing durable package projection and ledger
  resume.
- After repair ledger entry: ledger remains durable and execution continues.
- After full PASS before candidate: candidate creation remains the next step.
- After candidate before dispatch: `candidate_ready` resumes and dispatches
  exactly once.
- After dispatch before result: `awaiting_independent_acceptance` waits without
  replay or redispatch.
- After PASS before finalization: existing acceptance completion remains the
  authoritative transition.
- Valid accepted: terminal no-op.
- Malformed accepted: fail closed.
- Validator FAIL: existing structured-defect repair loop remains active.
- Repaired candidate acceptance: exact candidate correspondence is preserved.

## PostgreSQL evidence

`pytest -q tests/test_package_self_repair.py`: 14 passed.

The focused PostgreSQL tests cover:

- multi-defect package and independent FAIL/recovery;
- accepted restart through recreated lifecycle stores;
- repeated accepted restarts with dispatch count unchanged at 1;
- awaiting-acceptance restart with no adapter execution or redispatch;
- candidate/dispatch correspondence;
- four malformed accepted projections, including missing candidate evidence,
  zero dispatch count, and mismatched dispatched candidate;
- concurrent acceptance dispatch with one durable winner.

`python -m compileall -q src` and `git diff --check` passed.

## Regression and preservation

The RUN-005A package loop, ledger, same-worktree behavior, independent FAIL
repair path, bounded retry, escalation, and existing RUN-003/RUN-004C source
boundaries were preserved. No Campaign Runner fencing or reconciliation code was
changed. Existing shared-database stale-lease contamination and missing MCP
dependency remain unrelated environmental limitations documented previously.

## GRC-012

GRC-012 remains paused. `A:\Riverview\main-reconcile` was not modified; its
staged writer-evidence change and bounded test rename remain intact. No E1
execution, lifecycle mutation, commit, cleanup, or manual acceptance occurred.

## Publication

The repair was committed directly to `ppow1/Riverview` `main`; no named branch
was created and no force push was used. `origin/main` is verified at
`f6fbeaa9d9a8ec35ee651aebb8c291e8884e4870`.

Next action: independently revalidate RUN-005AR2 before resuming GRC-012.
