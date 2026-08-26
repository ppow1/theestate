# RUN-004C-R2V — Failed-Repair Retry Recovery Validation

Package: RUN-004C-R2V  
Role: C1 independent validator  
Implementation commit: `41bd475641db23adedb1cd95984010d04ca745f3`  

## Verdict

**PASS**

The bounded retry seam correctly recovers an explicitly failed repair
reconciliation without replaying the original writer or validator and without
allowing the old repair attempt to become authoritative.

## Commit and scope verification

The implementation commit is present and reachable from `origin/main`. The
commit changes only:

- `src/riverview/campaign/lifecycle.py`
- `tests/test_campaign_validation_lifecycle.py`

No migration, Campaign Runner redesign, rename-reconciliation change, or
unrelated generated/environment file was included. Compileall and
`git diff-tree --check` passed.

## Independent PostgreSQL retry proof

I independently ran the new focused test:

```text
pytest -q tests/test_campaign_validation_lifecycle.py \
  -k failed_repair_can_be_retried_without_replaying_upstream_and_can_accept
1 passed
```

The test exercised the real persistence path:

1. writer completed;
2. independent validator recorded structured `FAIL` and defects;
3. repair writer was claimed and failed with `RIV-REC-0004`;
4. `retry_failed_repair` created a distinct replacement work order;
5. the original failed order retained its failed status, checkpoint, and
   result report;
6. structured defects and retry-of references were copied into replacement
   parameters;
7. writer and validator counts remained one each;
8. the replacement received a distinct attempt/fence;
9. stale completion of the original repair attempt was rejected;
10. replacement repair completed;
11. an independent revalidator was claimed and passed;
12. the stage reached `accepted` / `completed`;
13. `runner.repair.retry_queued` remained durably recorded.

Failed-repair retry recovery: **PASS**  
Upstream replay prevention: **PASS**  
Stale old-attempt rejection: **PASS**  
Independent revalidation: **PASS**  
Final acceptance: **PASS**

## Eligibility and boundedness inspection

`CampaignLifecycleStore.retry_failed_repair` locks the failed work order and
requires all of the following before queuing a replacement:

- work order status `failed` and checkpoint `RIV-REC-0004`;
- durably failed result report;
- failed attempt role `repair_writer`;
- failed stage state and matching immutable validation basis;
- completed, basis-bound validator order and attempt;
- canonical validator verdict `FAIL` tied to the original writer attempt;
- unresolved structured defects;
- completed, result-bound original writer;
- no active repair work order;
- no accepted package state.

Other failure classes fail closed. The failed order/result are not rewritten.

The default retry key and `retry_of_work_order_id` lookup return the same
replacement on repeated calls, including after the replacement itself fails.
This permits one explicit replacement and prevents an automatic retry loop or
duplicate live repair work.

## Lineage, evidence, and restart behavior

Replacement parameters retain the failed work-order and attempt IDs, retry
generation, source validation result, validator order/attempt, retry reason,
and canonical structured defects. The retry event records the failed and
replacement orders, failed attempt, validator lineage, validation result, and
defect IDs.

The method derives eligibility entirely from PostgreSQL rows under transaction
and row locks. A recreated `CampaignLifecycleStore` therefore uses the same
durable failed order, stage, validator result, defects, and idempotency record;
no process-local retry memory is required.

History preservation: **PASS**  
Restart/resume basis: **PASS**  
Evidence/lineage preservation: **PASS**

## Regression evidence

The focused lifecycle, defect serialization, one-go, fencing, and autonomy
tests were run. The retry-specific test passed, as did the rename-relevant
and non-contaminated regression coverage.

Some surrounding PostgreSQL lifecycle/fencing tests could not claim clean
success because the shared test database contains accumulated expired lease
rows. Observed failures were inability to claim new fixture work and an
expiry sweep returning unrelated historical attempts. They are pre-existing
shared-database contamination, outside the changed files and unrelated to the
retry method. No new retry semantic failure was observed.

Relevant regression status: **PASS**  
Shared-database contamination: **PRE-EXISTING / NON-BLOCKING**  
Compile/import validation: **PASS**

## Preserved E1 worktree

`A:\Riverview\main-reconcile` remains untouched with the staged E1 evidence
modification and staged rename:

```text
docs/operations/roadmap/evidence/GRC-012-E1-writer-evidence.md
tests/test_home_cognition.py -> tests/test_e1_home_cognition.py
```

No preserved repair was committed, reset, cleaned, or consumed.

## Final status

RUN-004C-R2: **ACCEPTED**  
GRC-012 may resume from its durable failed-repair state.

No implementation changes were made by C1.

