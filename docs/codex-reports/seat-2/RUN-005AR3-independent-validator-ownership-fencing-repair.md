# RUN-005AR3 Independent Validator Ownership Fencing Repair

Package: RUN-005AR3  
Role: C2 Campaign Runner targeted repair writer  
Validated base: `f6fbeaa9d9a8ec35ee651aebb8c291e8884e4870`  
Repair commit: `8e72ad5106ca3b27280799fb751c578a0550a609`  
Verified `origin/main`: `8e72ad5106ca3b27280799fb751c578a0550a609`

## Status

`REPAIR_COMPLETE_READY_FOR_REVALIDATION`

## Exact defect and root cause

RUN-005AR2 correctly fenced the durable dispatch counter and pending state, but
`PackageEngineerLoop` still invoked `independent_acceptance` after
`dispatch_package_acceptance()` returned. Concurrent candidate-ready runners
could both receive the same idempotent count and both call the validator. The
loser failed only during later finalization, which was too late.

## Durable ownership mechanism

Migration `0046_package_acceptance_owner.sql` adds to
`campaign_package_runs`:

- `acceptance_owner_id`;
- `acceptance_lease_generation`;
- `acceptance_lease_expires_at`;
- `acceptance_invocation_started_at`.

`CampaignLifecycleStore.claim_package_acceptance()` locks the package row and
atomically verifies the exact candidate, establishes the owner, increments the
dispatch count, records the lease generation/expiry, and transitions
`candidate_ready` to `awaiting_independent_acceptance`.

The method returns `(owned, dispatch_count)`. Only `owned=True` grants the
caller permission to invoke the validator. A loser returns pending and never
calls the callback. The claim is durable PostgreSQL state, not an in-process
mutex or PowerShell lock.

## Candidate correspondence

Ownership is bound to the exact:

```text
package_run_id
candidate_ref
candidate_version_hash
```

The durable dispatched-candidate fields must match the current candidate. A
different candidate fails closed. Final PASS/FAIL projection requires the same
owner ID when supplied, so a stale owner cannot finalize after lease reclaim.

## First-pass and revalidation ownership

The same claim path is used for every package acceptance callback, including the
new candidate after an independent FAIL repair pass. Therefore first-pass
acceptance and revalidation both have one durable owner and one callback
invocation. The package-level self-repair loop remains unchanged: validator
FAIL defects return to the package engineer, followed by full verification and
one newly owned acceptance claim.

## Crash and lease behavior

The owner lease is recorded before callback invocation. If the owner crashes
before or during invocation, another process cannot invoke while the lease is
valid. After lease expiry, a new owner may reclaim the exact candidate with a
new lease generation. A stale result cannot finalize because finalization checks
the current owner ID.

If the validator result is durably returned before a process dies, the existing
finalization path remains the only state transition; no new callback is
required. Accepted and awaiting states continue to use the RUN-005AR2 terminal
and pending restart short-circuits.

## PostgreSQL proof

`pytest -q tests/test_package_self_repair.py`: 16 passed.

The focused PostgreSQL coverage includes:

- five independently constructed Campaign Runner/lifecycle instances starting
  from one `candidate_ready` package;
- exactly one validator callback;
- durable dispatch count exactly 1;
- no additional package execution or candidate generation;
- concurrent dispatch ownership;
- lease expiry and safe owner reclaim;
- stale original-owner finalization rejection;
- awaiting-acceptance restart with no callback;
- valid accepted restart with no callback;
- malformed accepted-state fail-closed cases;
- independent FAIL, repair, new candidate, and acceptance path.

Additional focused regressions:

- package self-repair and one-go tests passed;
- bounded rename reconciliation tests passed;
- `python -m compileall -q src` passed;
- `git diff --check` passed.

## Preserved behavior

RUN-003 fencing, RUN-004 lifecycle, RUN-004C-R1 rename reconciliation,
RUN-004C-R2 failed-repair recovery, RUN-005A package repair/ledger behavior,
RUN-005AR2 restart semantics, structured defects, history, stale-result safety,
objective isolation, failure safety, and downstream gating were preserved.

## GRC-012

GRC-012/E1 remains paused. `A:\Riverview\main-reconcile` was not modified;
its staged writer-evidence change and bounded test rename remain intact. No E1
execution, lifecycle mutation, manual acceptance, commit, or cleanup occurred.

## Publication

The repair was committed directly to `ppow1/Riverview` `main` with no named
branch and no force push. `origin/main` is verified at
`8e72ad5106ca3b27280799fb751c578a0550a609`.

Next action: independently revalidate RUN-005AR3.
