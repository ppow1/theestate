# RUN-005ARV — Accepted-State Restart Idempotency Revalidation

Package: RUN-005ARV  
Role: C1 independent repair revalidator  
Implementation commit: `a64283acae5a6c9e77caf09a516fa2ef2f732a33`  

## Verdict

**FAIL  REPAIR REQUIRED**

The valid durable `accepted` restart path is now a terminal no-op, but two
blocking defects remain in malformed and acceptance-pending restart states.

## Verification

The implementation commit is present and reachable from `origin/main`. It
changes only `src/riverview/campaign/package_runner.py` and
`tests/test_package_self_repair.py`. Compileall and `git diff-tree --check`
passed. No named branch was created.

Implementation on origin/main: **PASS**  
Named branches created: **NONE**

## Valid accepted restart

The focused repair and package tests passed:

```text
pytest -q tests/test_package_self_repair.py tests/test_campaign_one_go.py
15 passed
```

The exact accepted-state short-circuit occurs after durable projection read and
before package execution, repair, verification, candidate creation, or
independent acceptance. Recreated lifecycle/runner objects preserved the
candidate and dispatch count:

```text
dispatch before restart: 1
dispatch after restart: 1
repeated restart: unchanged
```

Accepted restart: **NO-OP**  
Dispatch before restart: **1**  
Dispatch after restart: **1**  
Repeated restart: **PASS**  
Package engineer replay after valid acceptance: **NO**  
Repair replay after valid acceptance: **NO**  
Candidate regeneration after valid acceptance: **NO**  
Validator redispatch after valid acceptance: **NO**  
Concurrent double-start: **PASS**

## Blocking defect RUN-005ARV-001 — incomplete accepted predicate

The repair checks durable `state == 'accepted'` plus non-empty
`candidate_ref` and `candidate_version_hash`, but does not check the required
`acceptance_dispatch_count >= 1` condition.

Independent probe with an accepted projection containing candidate evidence but
zero dispatch evidence produced:

```text
state = accepted
candidate_ref = candidate:malformed
candidate_version_hash = <non-empty hash>
acceptance_dispatch_count = 0
outcome = accepted, dispatches = 0
```

Expected behavior is fail closed as malformed accepted state, not successful
no-op. This permits an incomplete projection to be reported as accepted.

Severity: **BLOCKING**  
Affected symbol: `PackageEngineerLoop.run`  
Minimum repair: require non-empty candidate evidence and
`acceptance_dispatch_count >= 1` before returning accepted; otherwise raise a
durable lifecycle error or enter an explicit recoverable state. Add a real
PostgreSQL malformed-projection test.

Authoritative accepted predicate: **FAIL**

## Blocking defect RUN-005ARV-002 — acceptance-pending crash replay

The short-circuit handles only `state == 'accepted'`. It does not define a
restart path for `state == 'awaiting_independent_acceptance'`, the durable state
after dispatch and before the validator callback is persisted.

Independent probe with:

```text
state = awaiting_independent_acceptance
candidate_ref = candidate:1
candidate_version_hash = <non-empty hash>
acceptance_dispatch_count = 1
```

After restart, the loop executed the package, regenerated a candidate, called
the acceptance callback, and attempted a second dispatch. The observed count
became `2`.

This violates crash-boundary case 6 and can create a duplicate independent
acceptance boundary. The conditional dispatch update prevents two simultaneous
transactions from both winning, but does not prevent a restarted runner from
replaying an already-dispatched acceptance.

Severity: **BLOCKING**  
Affected symbols: `PackageEngineerLoop.run` and package-run resume semantics  
Minimum repair: define durable recovery for
`awaiting_independent_acceptance` without re-executing or regenerating a
candidate. Resume the existing acceptance attempt idempotently or fail closed
into an explicit recoverable state. Add a PostgreSQL crash-boundary test.

Crash-boundary matrix: **FAIL**  
Restart/resume: **FAIL**  
Independent acceptance boundary: **FAIL** across acceptance-pending restart

## RUN-005A regression evidence

The passing focused tests independently covered eleven distinct defects,
sequential repair, same-worktree execution, full verification, durable ledger
recreation, independent FAIL with multiple defects, valid accepted restart,
and concurrent dispatch single-winner.

- Package-level self-repair: **PASS**
- All-observable-defect collection: **PASS**
- Sequential repair-and-continue: **PASS**
- 10+ distinct defects: **PASS**
- Repair ledger persistence: **PASS**
- Same-worktree execution: **PASS**
- Full internal rerun: **PASS**
- Single candidate semantics: **FAIL** across acceptance-pending restart
- Independent FAIL recovery: **PASS**
- Per-root retry bound: **PASS**
- Escalation: **PASS**
- RUN-005A regression: **FAIL** due the two restart defects

RUN-003 regression: **PASS**  
RUN-004C-R1 regression: **PASS** by unchanged source/diff inspection  
RUN-004C-R2 regression: **PASS** by unchanged source/diff inspection  
Other Campaign Runner regressions: **PASS** for focused non-contaminated
coverage  
PostgreSQL lifecycle proof: **FAIL** for the required malformed accepted and
acceptance-pending restart cases

## GRC-012 preservation

`A:\Riverview\main-reconcile` remains untouched with its staged E1 evidence
change and staged rename. GRC-012 was not resumed, modified, committed,
reset, cleaned, or manually accepted.

GRC-012 preserved: **PASS**

## Final status

RUN-005A: **REPAIR_REQUIRED**  
Repair `RUN-005ARV-001` and `RUN-005ARV-002`, then independently revalidate the
complete restart/crash-boundary and regression matrix. GRC-012 remains paused.

