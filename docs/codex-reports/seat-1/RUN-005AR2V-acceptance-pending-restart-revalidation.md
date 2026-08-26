# RUN-005AR2V — Acceptance-Pending Restart and Malformed Accepted-State Revalidation

Package: RUN-005AR2V  
Role: C1 independent repair revalidator  
Implementation validated: `f6fbeaa9d9a8ec35ee651aebb8c291e8884e4870`  
Repository/branch: `ppow1/Riverview`, `main` / `origin/main`  

## Verdict

**FAIL  REPAIR REQUIRED**

The two defects reported by RUN-005ARV are resolved for sequential execution,
but a new reachable concurrency defect remains in the repaired
`candidate_ready` resume path. Two concurrent runners can both invoke the
independent validator for one candidate. The database dispatch counter remains
one, but the validator side effect is duplicated and the losing runner later
fails while recording acceptance. This violates the required single-winner,
no-duplicate-validator behavior.

## Repository verification

- The implementation commit exists and is reachable from `origin/main`.
- The commit changes only the two package-acceptance migrations, the campaign
  lifecycle/package runner implementation, and the focused package tests.
- The implementation worktree was clean at the validated commit.
- The preserved `A:\Riverview\main-reconcile` worktree remains untouched and
  paused, with its staged E1 evidence modification and rename intact.
- No named branch was created.

## Independent results

### RUN-005ARV defect 1: malformed accepted projection

**RESOLVED.** `PackageEngineerLoop._candidate_from_projection(...,
require_dispatch=True)` rejects missing candidate reference, missing version,
zero/negative/non-integer dispatch count, and mismatched dispatched candidate
correspondence before invoking the package adapter.

The real PostgreSQL parametrized malformed-projection tests passed, including
the critical `state='accepted'` with candidate evidence and dispatch count
zero case. No package execution or candidate generation occurred.

### RUN-005ARV defect 2: awaiting-acceptance restart replay

**RESOLVED for sequential restart.** A durable
`awaiting_independent_acceptance` projection is returned as a waiting outcome;
the package adapter and acceptance callback are not invoked, and dispatch
count remains one. The independent PostgreSQL restart test passed.

### Valid accepted restart

**PASS / NO-OP.** A valid accepted projection requires non-empty candidate
reference and version, dispatch count at least one, and exact persisted
acceptance-candidate correspondence. The accepted restart regression passed;
execution, candidate creation, and dispatch counts remained unchanged across
recreated lifecycle/runner objects and repeated restart.

### Concurrent resume defect

**FAIL.** Independent real-PostgreSQL probe:

1. Created one `candidate_ready` package projection with one candidate.
2. Started two `PackageEngineerLoop` instances concurrently.
3. Paused both acceptance callbacks so both reached the callback boundary.
4. Observed two independent-acceptance callback invocations for the same
   candidate.

Observed result:

```text
calls 2
results ['accepted']
errors ['LifecycleGateError:RIV-CAM-0070: package acceptance state is stale.']
acceptance_dispatch_count = 1
state = accepted
```

The SQL dispatch operation correctly has one durable winner, but its fallback
for the losing caller returns the existing count when the row is already
`awaiting_independent_acceptance`. `PackageEngineerLoop.run` then unconditionally
calls `independent_acceptance` in both callers. Thus the dispatch counter alone
does not fence the validator invocation.

This violates the required concurrent-resume invariants:

- no duplicate validator work;
- one authoritative acceptance boundary;
- the losing resume must observe pending state without invoking the validator;
- no later stale-finalization exception as the normal concurrency outcome.

Minimum repair boundary: make the candidate-ready dispatch operation return an
explicit dispatch-owner/already-awaiting result (or equivalent durable claim),
and have only the owner invoke the independent validator. Preserve the existing
single-winner SQL transition and do not replay package engineering for an
already-awaiting candidate. Add a real PostgreSQL concurrent runner regression.

## Focused evidence

- `tests/test_package_self_repair.py`: **14 passed** independently.
- `tests/test_campaign_one_go.py`: **6 passed** independently.
- `python -m compileall -q src`: passed.
- The existing concurrent dispatch unit test passes, but it tests the lower
  lifecycle dispatch method and does not cover the higher-level validator
  callback boundary; the independent probe above covers that missing boundary.
- The broader lifecycle suite was attempted. Failures were dominated by the
  known shared PostgreSQL environment condition (`too many clients already`)
  and stale/expired shared rows, so those are classified as infrastructure /
  pre-existing contamination, not evidence for or against this targeted
  defect.

## Regression assessment

The sequential repaired paths preserve malformed accepted-state fail-closed
behavior, valid accepted restart idempotency, awaiting restart behavior, the
one-go focused suite, and the previously accepted fencing/acceptance seams as
far as independently executable in the available database environment. Full
RUN-005A acceptance is nevertheless blocked by the concrete concurrent
candidate-ready validator duplication above.

GRC-012/E1 remains preserved and paused. It must not resume until this repair is
independently revalidated.

## Required revalidation

Re-run the malformed accepted-state matrix, sequential accepted and awaiting
restart tests, and a real PostgreSQL concurrent candidate-ready resume test.
The required pass condition is exactly one validator invocation, one dispatch,
and safe no-op/awaiting observation by the losing runner, followed by successful
single acceptance or truthful pending state.

