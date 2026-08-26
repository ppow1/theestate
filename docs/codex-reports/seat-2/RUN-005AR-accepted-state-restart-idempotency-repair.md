# RUN-005AR Accepted-State Restart Idempotency Repair

Package: RUN-005AR  
Role: C2 Campaign Runner targeted repair writer  
Validated base: `2231f19eafab0183b2d378dfe358853710393575`  
Repair commit: `a64283acae5a6c9e77caf09a516fa2ef2f732a33`  
Verified `origin/main`: `a64283acae5a6c9e77caf09a516fa2ef2f732a33`

## Status

`REPAIR_COMPLETE_READY_FOR_REVALIDATION`

## Root cause

`PackageEngineerLoop.run()` always called the package adapter after
`begin_package_run()` and loaded the durable projection only for repair
generation and acceptance-dispatch counters. It did not treat the durable
`accepted` state as terminal. A newly constructed runner therefore re-executed
the package, regenerated a candidate, and dispatched a second independent
acceptance.

## Authoritative accepted-state predicate

The package-level terminal predicate is the durable
`campaign_package_runs` row for the exact `stage_id` with:

```text
state = 'accepted'
candidate_ref is non-empty
candidate_version_hash is non-empty
acceptance_dispatch_count >= 1
```

The state is written only by `CampaignLifecycleStore.record_package_acceptance`
after the independent acceptance callback has returned accepted. Candidate
evidence and the dispatch count are retained in the same durable projection.
An accepted row without candidate evidence is treated as malformed and fails
closed rather than being treated as accepted.

## Exact repair

Immediately after loading `package_run(stage_id=...)`, `PackageEngineerLoop`
now checks for durable `state == 'accepted'`. It reconstructs the existing
`Candidate` from the stored candidate reference/version and returns an accepted
`PackageRunOutcome` without calling:

- package execution;
- repair;
- local or full verification;
- candidate creation;
- independent acceptance.

No acceptance event or projection update is emitted on this read-only resume.
The existing conditional update in `dispatch_package_acceptance` remains the
concurrency gate: only a `verifying` or `acceptance_failed` row can transition
to `awaiting_independent_acceptance`, so concurrent starters cannot increment
the dispatch count twice.

## Operator and Python paths

The affected operator path remains:

`tools/powershell/campaign/Invoke-RiverviewPackageCampaign.ps1`

It invokes `python -m riverview.campaign.package_runner`. The repaired Python
path is `PackageEngineerLoop.run()`, also exposed through
`CampaignOneGoRunner.run_package(...)`. No PowerShell behavior was bypassed or
duplicated.

## Restart and crash-boundary coverage

The existing package-loop tests continue to cover execution, internal repair,
full verification, candidate creation, independent FAIL return-to-repair, and
escalation. RUN-005AR adds durable coverage for:

1. a newly constructed lifecycle/runner after accepted state;
2. repeated restarts after accepted state;
3. zero package executions, repairs, candidate creations, and validator
   callbacks after accepted state;
4. candidate/dispatch state persisted through PostgreSQL store recreation;
5. two concurrent dispatchers with exactly one authoritative winner.

Pre-terminal states remain on the existing execution path because the
short-circuit is restricted to the exact accepted predicate. Candidate-ready,
acceptance-pending, independent-FAIL, repair, verification, and escalated
states are not converted to terminal success.

## PostgreSQL proof

The focused PostgreSQL tests prove:

- package execution with persisted ledger and candidate;
- independent FAIL with multiple defects, repair, second candidate, and PASS;
- durable accepted projection reload through newly constructed lifecycle
  stores;
- dispatch count `1` before restart and `1` after repeated restart;
- concurrent dispatch attempts produce one successful dispatch and one failed
  conditional transition.

## Regression evidence

- `pytest -q tests/test_package_self_repair.py`: 9 passed.
- `python -m compileall -q src`: passed.
- `git diff --check`: passed.
- Existing RUN-005A package tests remain included in the 9-test focused suite.
- Existing RUN-003, RUN-004C-R1, and RUN-004C-R2 source paths were not changed.

The known shared PostgreSQL stale-lease contamination and missing optional MCP
dependency remain environmental issues documented in the RUN-005A report;
this repair does not alter either boundary.

## GRC-012 preservation

GRC-012 remains paused. The preserved worktree
`A:\Riverview\main-reconcile` was not modified and still contains the staged
writer-evidence modification and the bounded test-file rename. No E1 lifecycle
history was resumed, mutated, manually accepted, committed, or cleaned.

## Publication

Implementation was committed directly to `ppow1/Riverview` `main` with no new
named branch and no force push. `origin/main` resolves to:

`a64283acae5a6c9e77caf09a516fa2ef2f732a33`

Next action: independently revalidate RUN-005AR before any GRC-012 resume.
