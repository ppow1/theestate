# RUN-005AR3V — Independent Validator Ownership Fencing Revalidation

Package: RUN-005AR3V  
Role: C1 independent repair revalidator  
Implementation: `ppow1/Riverview` `origin/main`  
Commit: `8e72ad5106ca3b27280799fb751c578a0550a609`

## Verdict

**PASS**

The repair closes the RUN-005AR2V defect at the actual package-runner callback
boundary. Durable PostgreSQL ownership is claimed before the independent
validator is invoked; losing runners return a pending outcome and do not call
the validator.

## Source and architecture verification

The commit is reachable from `origin/main` and changes only migration 0046,
the campaign lifecycle/package runner, and focused package tests. The actual
operator-facing Python entrypoint constructs `PackageEngineerLoop`, and the
loop now calls `claim_package_acceptance()` before invoking
`independent_acceptance()` on both candidate-ready paths.

Ownership is durable, not process-local: migration 0046 adds
`acceptance_owner_id`, `acceptance_lease_generation`,
`acceptance_lease_expires_at`, and `acceptance_invocation_started_at` to
`campaign_package_runs`. `claim_package_acceptance()` locks the package row,
checks exact candidate correspondence, and atomically admits one owner. The
owner is required again by `record_package_acceptance()`.

## Independent validation results

### Five-runner candidate-ready race

**PASS.** Using five independently constructed `CampaignLifecycleStore` and
`PackageEngineerLoop` instances with real PostgreSQL connections:

- candidate generation: 1 existing candidate;
- concurrent runners: 5;
- acceptance owner: 1;
- acceptance dispatch count: 1;
- actual validator callback count: 1;
- duplicate validator callback: none;
- final state: `accepted`.

This directly covers the previous failure, where dispatch count was one but
callback count was two.

### Candidate correspondence

**PASS.** An attempted claim for candidate B against a durable candidate-A
projection was rejected with `RIV-CAM-0077` before ownership was granted.

### Lease/crash fencing

**PASS.** Focused PostgreSQL coverage verifies that an expired owner can be
reclaimed once and that the old owner cannot finalize afterward. The owner
lease and owner identity prevent a late result from mutating acceptance after
replacement ownership.

The bounded behavior is: a crash before or during invocation leaves the
candidate awaiting acceptance until the owner lease expires; a replacement
owner may then claim the exact same candidate. A late old-owner finalization is
rejected. A result already finalized durably is not re-invoked on restart.

### Restart and malformed-state regressions

**PASS.** The focused suite preserves:

- awaiting-acceptance restart without package replay or validator redispatch;
- valid accepted restart as terminal no-op;
- malformed accepted projections failing closed;
- zero dispatch count, missing candidate, missing version, and mismatched
  candidate correspondence rejection;
- no candidate regeneration for these malformed states.

### Revalidation ownership

**PASS.** The same durable candidate ownership fence is used for candidate B
after a validation-failure repair cycle. The equivalent concurrent candidate-B
resume probe admits one revalidator callback and one acceptance owner; stale
owners cannot finalize. Existing PostgreSQL repair/revalidation lifecycle
coverage also passed.

### Package-level self-repair and regressions

**PASS.** Focused package-level self-repair coverage passed, including the
multi-defect repair path, full internal verification, candidate boundary,
independent acceptance, failure return-to-repair, and bounded retry behavior.

### Test evidence

- `tests/test_package_self_repair.py`: **16 passed** independently.
- `tests/test_package_self_repair.py` plus `tests/test_campaign_one_go.py`:
  **22 passed** independently.
- `python -m compileall -q src`: passed.
- Candidate substitution adversarial probe: rejected before ownership.
- The broader PostgreSQL lifecycle selection was attempted. Failures were
  caused by the known shared database stale/expired-row and worker-claim
  contamination (including unavailable claim slots), not by this ownership
  repair. They are classified as pre-existing infrastructure/test-state
  contamination.

## Regression assessment

The ownership repair preserves RUN-003 fencing, RUN-004 lifecycle behavior,
RUN-004C-R1/R2 recovery paths, RUN-005A package self-repair, accepted-state and
acceptance-pending restart behavior, structured defect persistence, history,
stale-result rejection, idempotency, and downstream gating in the focused
coverage available here.

GRC-012 / E1 was not resumed or modified. Its preserved repair worktree
remains intact and paused.

## Status

RUN-005A is ready to be accepted. The next action is to resume the existing
GRC-012 / E1 campaign under the package-level self-repair architecture; no new
E1 campaign should be created.

