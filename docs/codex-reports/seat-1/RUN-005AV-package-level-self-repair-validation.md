# RUN-005AV — Package-Level Self-Repair Validation

Package: RUN-005AV  
Role: C1 independent Campaign Runner architecture validator  
Exact implementation validated: `2231f19eafab0183b2d378dfe358853710393575`  

## Verdict

**FAIL**

The package-level self-repair path is present and the focused PostgreSQL proof
passes, but restart/resume is not idempotent after package acceptance. A
restarted loop can execute the package again and dispatch a second independent
acceptance. This violates the required single acceptance boundary and prevents
RUN-005A acceptance.

## Operator path

`tools/powershell/campaign/Invoke-RiverviewPackageCampaign.ps1` is the only
campaign PowerShell entrypoint in the validated `main` commit. It sets
`PYTHONPATH` to the repository `src` directory and invokes:

```text
python -m riverview.campaign.package_runner
```

The Python CLI loads the explicit `module:function` adapter and constructs
`PackageEngineerLoop` with a fresh `CampaignLifecycleStore`. The package
surface is therefore connected to the operator script rather than being only
an unused helper.

Actual PowerShell operator path: **PASS**  
Real package-level self-repair path: **PASS**

## Self-repair behavior independently verified

The focused suite passed:

```text
pytest -q tests/test_package_self_repair.py tests/test_campaign_one_go.py
12 passed
```

The implementation and tests independently demonstrate:

- sequential repair of eleven distinct defects with one acceptance dispatch;
- no intermediate independent validator after internal repairs;
- same-worktree propagation through execution, repair, focused verification,
  and full verification;
- per-root repair bound of three and escalation without spinning;
- independent acceptance FAIL returning multiple defects to package repair;
- second candidate and independent revalidation after that repair;
- durable PostgreSQL package ledger and store recreation;
- structured defect, changed-path, verification, generation, and status
  persistence.

Accordingly:

- All-observable-defect collection: **PASS**
- Sequential repair-and-continue: **PASS**
- 10+ distinct defect handling: **PASS**
- Repair ledger persistence: **PASS**
- Same-worktree execution: **PASS**
- Full internal package rerun: **PASS** for the exercised repair/full-verify
  paths
- Single candidate semantics: **PASS** within one uninterrupted run
- Independent FAIL return-to-repair: **PASS**
- Per-root-defect bounded retry: **PASS**
- Escalation: **PASS**

## Blocking defect: restart duplicates final acceptance

Source evidence:

`PackageEngineerLoop.run()` calls `begin_package_run`, reads the projection’s
generation and dispatch count, and then unconditionally enters the package
execution loop. It does not short-circuit when the durable projection state is
`accepted`, nor when it is `awaiting_independent_acceptance`.

`CampaignLifecycleStore.begin_package_run` uses `ON CONFLICT(stage_id) DO
NOTHING` and returns the existing package run, including an already accepted
run. `dispatch_package_acceptance` increments
`acceptance_dispatch_count` whenever the state is `verifying` or
`acceptance_failed`.

Independent reproduction with the actual `PackageEngineerLoop` and a durable-
projection-equivalent lifecycle fake:

```text
first run:  accepted, acceptance_dispatches=1
second run on same objective/stage: accepted, acceptance_dispatches=2
dispatches: ['candidate:1', 'candidate:1']
```

The second run also called the executor and independent acceptance callback.
Thus a process restart after final acceptance can create a duplicate
acceptance dispatch and reprocess an already accepted package. A crash after
dispatch but before callback has the same unresolved ambiguity for
`awaiting_independent_acceptance`.

This violates:

- exactly one independent acceptance dispatch;
- restart/resume restoration of final acceptance state;
- no duplicate acceptance or candidate processing;
- the requirement that the complete package is accepted only once at the
  independent boundary.

Defect ID: `RUN-005AV-001`  
Severity: **BLOCKING**  
Affected symbols: `PackageEngineerLoop.run`,
`CampaignLifecycleStore.begin_package_run`,
`CampaignLifecycleStore.dispatch_package_acceptance`  
Minimum repair boundary: make durable package-run state authoritative on
resume; return the existing terminal outcome for `accepted`, and define a
durable, idempotent recovery path for `awaiting_independent_acceptance`
without re-executing or dispatching a second candidate. Add restart tests for
accepted and acceptance-dispatched states.  
Required revalidation: repeat this probe plus the full PostgreSQL package
repair, independent FAIL/revalidation, and regression matrix.

Restart/resume: **FAIL**  
Single independent acceptance boundary: **FAIL**  
Package engineer cannot self-accept: **PASS**

## Other validation and regressions

The exact implementation commits are reachable from `origin/main`, with no
new named branch. The two implementation commits are bounded to the package
runner, lifecycle/migrations, PowerShell entrypoint, exports, and focused
tests. Compileall and `git diff --check` passed.

The PostgreSQL proof for the uninterrupted multi-defect and independent-F​​AIL
repair/revalidation lifecycle passed, but the complete required PostgreSQL
lifecycle including restart after terminal acceptance is **FAIL** because of
`RUN-005AV-001`.

RUN-003 fencing, RUN-004C-R1 rename reconciliation, and RUN-004C-R2 retry
recovery were not weakened by the changed source according to diff and focused
regression inspection. Existing shared PostgreSQL expired-row contamination
remains a separate known test-environment issue and is not used to explain the
restart defect.

- RUN-003 regression: **PASS**
- RUN-004C-R1 regression: **PASS**
- RUN-004C-R2 regression: **PASS**
- Other Campaign Runner regressions: **PASS** for non-contaminated focused
  coverage
- Runner/package defect separation: **PASS**
- PostgreSQL lifecycle proof: **FAIL** due to the blocking restart defect

## GRC-012 preservation

`A:\Riverview\main-reconcile` remains untouched with the staged E1 evidence
change and staged rename:

```text
M  docs/operations/roadmap/evidence/GRC-012-E1-writer-evidence.md
R  tests/test_home_cognition.py -> tests/test_e1_home_cognition.py
```

GRC-012 was not resumed, committed, reset, cleaned, or manually accepted.

GRC-012 preserved: **PASS**

## Final status

RUN-005A: **REPAIR_REQUIRED**  
GRC-012 remains paused until the durable terminal/acceptance resume defect is
repaired and independently revalidated.

