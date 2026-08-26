# RUN-004C-R2 Repair Attempt Retry Recovery

## Result

Repair status: `REPAIR_COMPLETE_READY_FOR_VALIDATION`

Implementation was committed directly to `ppow1/Riverview` `main`.

- Original blocker: failed repair result could not be retried
- Implementation commit: `41bd475641db23adedb1cd95984010d04ca745f3`
- Verified `origin/main`: `41bd475641db23adedb1cd95984010d04ca745f3`
- Named branches created: none

## Lifecycle limitation and repair

The existing validator FAIL path created structured defects and one
`repair_writer` work order. If that repair execution failed, `_fail_if_current`
truthfully preserved the failed work order and attempt but moved the stage to
`failed`. No campaign-specific transition could return the stage to
`repair_pending`; generic Relay retry did not validate campaign basis, defect,
or validator lineage.

`CampaignLifecycleStore.retry_failed_repair` is now the explicit recovery seam.
It performs one transactional, fail-closed recovery operation for the
recoverable `RIV-REC-0004` case.

## Eligibility predicates

The operation requires:

- existing repair work order and failed repair attempt;
- terminal work-order/result state `failed` with checkpoint `RIV-REC-0004`;
- failed attempt role `repair_writer`;
- stage state `failed`, matching objective and immutable validation basis;
- the original validator work order/attempt remains completed and basis-bound;
- the canonical validator result is `FAIL`;
- unresolved structured defects remain present;
- the original writer attempt remains a completed, valid result binding;
- no active repair work order exists;
- the package has not reached acceptance.

Other failure classes are rejected rather than silently retried. The failed
attempt and its result report are never rewritten.

## Replacement semantics

The operation creates one new `repair_writer` work order with:

- a new work-order ID;
- normal Relay claim/attempt/fence generation;
- the same objective, stage, validation basis, validator source order, and
  validator source attempt;
- retry-of work-order and attempt references;
- retry generation and reason;
- the canonical structured defect payloads;
- source validation result and defect lineage.

The stage transitions transactionally from `failed` to `repair_pending` and
clears only the failed attempt's active projection. A River event
`runner.repair.retry_queued` records the failed order/attempt, replacement
order, validator lineage, validation result, defect IDs, and retry generation.

## Idempotency and bounded retry

The default retry key is derived from the failed repair work order. Existing
replacement orders are returned on repeated calls, including after a
replacement itself has failed. This permits one explicit replacement and
prevents an automatic retry loop or duplicate live repair work.

Active repair stages, accepted stages, missing defects, mismatched basis/stage,
invalid validator lineage, and non-recoverable failure checkpoints fail closed.

## Evidence and PostgreSQL proof

The isolated PostgreSQL lifecycle proof passed:

1. writer completed;
2. independent validator recorded structured FAIL;
3. repair attempt failed with `RIV-REC-0004`;
4. explicit retry created a replacement work order;
5. original failure remained failed with its checkpoint and report;
6. defects were preserved in replacement parameters;
7. writer and validator were not replayed;
8. replacement claimed a distinct attempt/fence;
9. stale completion from the old repair attempt was rejected;
10. replacement repair completed;
11. independent revalidator completed and PASSed;
12. stage reached accepted/completed;
13. retry event remained durable.

Restart semantics are database-derived: a new `CampaignLifecycleStore` call
uses the persisted failed order, stage, defects, and idempotent replacement
order rather than process memory.

## Regression results

- Retry-specific PostgreSQL proof: PASS
- Pure Campaign Runner one-go tests: PASS
- Defect serialization tests: PASS
- Autonomy/control tests: PASS
- Runner policy tests: PASS
- Generic recovery tests: PASS
- Compile/import validation: PASS
- RUN-003 fencing code/regression: unchanged; predecessor PostgreSQL tests
  retain the known accumulated expired-row contamination pattern
- RUN-004A/004B lifecycle behavior: unchanged except the new explicit repair
  recovery seam
- RUN-004C-R1 bounded rename reconciliation: unchanged and preserved

Some broader lifecycle PostgreSQL tests were affected by the pre-existing
shared-database expired-row claim contamination. The targeted retry proof was
isolated by unique objective/stage data and passed; no new retry-related
failure was observed.

## Preserved E1 worktree

`A:\Riverview\main-reconcile` remains intact and untouched:

- detached at the pre-repair main state;
- staged `docs/operations/roadmap/evidence/GRC-012-E1-writer-evidence.md`;
- staged rename `tests/test_home_cognition.py` to
  `tests/test_e1_home_cognition.py`;
- no preserved E1 changes were committed or used as the retry result.

GRC-012 remains paused pending independent validation of RUN-004C-R2.
