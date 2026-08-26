# RUN-005A Package-Level Self-Repair Implementation

Package: RUN-005A  
Role: C2 Campaign Runner primary implementation writer  
Repository: `ppow1/Riverview`  
Branch: `main`  
Implementation commits: `5ee8e73399f3dbbf7fc59c91208decfab13b8923`, followed by the PostgreSQL proof test commit `2231f19eafab0183b2d378dfe358853710393575`  
Verified `origin/main`: `2231f19eafab0183b2d378dfe358853710393575`

## Result

RUN-005A is implemented and ready for independent validation. The new
package-engineer loop owns bounded diagnosis, first repair, local repair
verification, full package verification, candidate preparation, and the final
independent acceptance boundary. Existing RUN-004 role-by-role behavior remains
available for compatibility.

## Previous and new lifecycle

The previous one-go path advanced a writer to a validator, then dispatched a
repair writer after every validator FAIL and a revalidator after every repair.
That created an external repair/revalidation ping-pong loop.

The new `PackageEngineerLoop` keeps one package worktree and processes every
observable defect returned by a package pass. It records each observation,
repairs it in the same execution context, runs focused verification, performs a
full package verification, and continues. Only after a full internal PASS does
it create a candidate and dispatch independent acceptance. An independent FAIL
is persisted as a package acceptance failure and returned to the same loop for
another bounded repair/full-verification pass.

## PowerShell entrypoint

The operator-facing entrypoint is:

`tools/powershell/campaign/Invoke-RiverviewPackageCampaign.ps1`

It sets the repository `src` path and invokes
`python -m riverview.campaign.package_runner`, requiring explicit objective,
stage, worktree, and package adapter arguments. The adapter is a deliberate
`module:function` boundary; the runner does not infer identity, provider,
resource, or repair authority from shell text.

The Python package surface is `CampaignOneGoRunner.run_package(...)`, which
delegates to `PackageEngineerLoop`. The CLI uses the same loop directly for
PowerShell launches with a fresh lifecycle store.

## Durable repair ledger and restart state

Migration `0042_package_self_repair.sql` adds `campaign_package_runs` and
`campaign_repair_ledger`. Migration `0043_package_ledger_structured_defects.sql`
adds the complete structured defect fields to the ledger. The ledger preserves:

- ordered discovery sequence and package/objective/stage identity;
- root-cause key, checkpoint, command, observed/expected behavior;
- stdout/stderr/evidence references;
- acceptance criterion, severity, required repair, root-cause determination;
- repair description, changed paths, verification text/result;
- repair generation, status, and timestamps.

`campaign_package_runs` preserves the worktree reference, repair generation,
discovery sequence, candidate evidence, internal verification, acceptance
dispatch count, and resumable state. Recreating `CampaignLifecycleStore` after
the package run reconstructs the accepted projection and ledger from
PostgreSQL.

## Repair bounds and escalation

The default bound is three repair attempts per root-cause key. It is not a
package-wide defect count: the test suite records eleven distinct sequential
defects without an intermediate independent validator. A root defect that
exceeds its bound, fails repair verification, or has no structured defects on an
independent FAIL enters `escalated` state with durable evidence and does not
spin.

## Worktree and candidate policy

The package loop carries one bounded `worktree_ref` through execution, repair,
focused verification, and full verification. The ledger records changed paths;
the loop does not create a Git commit for each defect. `create_candidate` is
called only after full internal verification. A validator rejection can produce
one replacement candidate after the next repair pass, but no candidate is
created for an incomplete internal pass.

## Acceptance boundary and existing machinery

The loop uses `CampaignLifecycleStore` for durable state, River events, and
ledger persistence. It does not replace `DefectInput` or the existing
`campaign_validation_defects` records. Final acceptance is delegated to the
independent acceptance callback, and the package projection records one
dispatch per candidate. Existing evidence-bound acceptance remains the
authoritative lifecycle gate when integrated with the normal validator path.

RUN-003 fencing, work-order identity, stale-result rejection, RelayStore,
ResultReconciler, RUN-004 lifecycle/history, structured defects, restart state,
and downstream gating were not weakened. The package loop does not modify
Campaign Runner lease or reconciliation authority.

## Tests and evidence

- `pytest -q tests/test_package_self_repair.py`: 6 passed.
- The package tests include eleven distinct ledger entries, independent FAIL ->
  repair -> second acceptance dispatch, same-root escalation, projection
  restart, and real PostgreSQL persistence/recreation.
- `pytest -q tests/test_package_self_repair.py tests/test_campaign_one_go.py`:
  11 passed.
- `pytest -q tests/test_autonomy_control.py -k 'rename'
  tests/test_generic_same_lineage_recovery.py`: 9 passed, preserving bounded
  rename reconciliation and recoverable RIV-REC-0004 semantics.
- `python -m compileall -q src`: passed.
- `git diff --check`: passed.

The broader PostgreSQL campaign run was not clean in the shared development
database: existing accumulated expired lease rows caused the known stale-lease
contamination failures in RUN-004 lifecycle/fencing tests. This was observed
before any package-loop behavior was exercised and is not changed by RUN-005A.
The broad collection also remains blocked for unrelated MCP tests because the
optional `mcp` dependency is unavailable in this environment. These are
reported for independent validation rather than hidden.

## GRC-012 preservation

The preserved worktree `A:\Riverview\main-reconcile` remains untouched and
contains exactly the staged GRC-012 repair state:

```text
## HEAD (no branch)
M  docs/operations/roadmap/evidence/GRC-012-E1-writer-evidence.md
R  tests/test_home_cognition.py -> tests/test_e1_home_cognition.py
```

GRC-012 was not resumed, accepted, committed, or cleaned during this package.

## Scope and publication

Only the package-run projection/ledger, package loop, PowerShell entrypoint,
and focused tests were committed to Riverview `main`. No named branch was
created and no force push was used. The old Grace feature branch was not
revived. The final remote check returned:

`2231f19eafab0183b2d378dfe358853710393575 refs/heads/main`

Next action: independently validate RUN-005A, then resume GRC-012 under the
new package-level model only after that acceptance.
