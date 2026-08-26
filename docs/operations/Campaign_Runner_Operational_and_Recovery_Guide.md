# Campaign Runner Operational and Recovery Guide

Status: canonical operational reference  
Scope: accepted RUN-003 / RUN-004 / RUN-005 Campaign Runner core  
Canonical implementation line: `ppow1/Riverview` `main`

This guide describes the current PostgreSQL-backed Campaign Runner for
operators, future Codex seats, ChatGPT recovery, Hermes observation, and human
debugging. Current source and PostgreSQL state outrank this guide, transcripts,
terminal windows, and report prose.

## 1. What Campaign Runner is

Campaign Runner is the Estate's governed package-execution mechanism. A
campaign is a PostgreSQL objective; a work package is an objective stage with
ordered dependencies and a validation lifecycle. The runner owns bounded
package engineering, durable attempts, repair history, candidate creation, and
the final independent acceptance boundary. It is not merely a test runner.

It is separate from Grace cognition, provider/model routing, GPU scheduling,
dashboards, notifier redesign, and exceptional arbitration.

## 2. Current normal workflow

```text
objective / stage
  -> package engineer runs the package in one bounded worktree
  -> discover observable defect
  -> diagnose while context is live
  -> repair internally, verify, and record the repair ledger
  -> continue to the next reachable defect
  -> full package verification from the beginning
  -> one coherent candidate
  -> one independently owned acceptance validator
  -> PASS -> accepted
       FAIL -> complete defect set -> repair pass -> full rerun
               -> updated candidate -> one independent revalidation
```

Discovery and first repair remain in the package engineer's live context. A
validator is not dispatched after every internal repair. Independence is
required at the final package acceptance boundary. A validator PASS is not
acceptance by itself: candidate, tree/commit/version, immutable basis,
durable evidence, independent attempt, and blocking-defect state must all pass
the durable gate.

## 3. Defect collection and bounded repair

Do not intentionally stop at the first engineering defect when more safe
observation is reachable. Record and repair all reachable defects, then rerun
the complete internal package matrix. `max_repairs_per_root` limits repeated
attempts against the same root-cause key; it is not a total package-defect
limit. The package pass bound also prevents an infinite loop. Persistent
same-root failure escalates instead of silently accepting.

## 4. Durable repair ledger

`campaign_package_runs` stores the package projection. Each observation is
stored in `campaign_repair_ledger`, including package/objective/stage,
discovery sequence, defect/root-cause identity, checkpoint, command,
observed/expected behavior, evidence references, severity, required repair,
generation, repair description, changed paths, verification, status, and
timestamps.

This ledger is not Git history. Git records repository history; the ledger
records why the package engineer changed the worktree and how the change was
verified. Read it through `CampaignLifecycleStore.package_run()` and
`CampaignLifecycleStore.package_ledger()` before resuming. Validator findings
remain separately durable in `campaign_validation_results` and
`campaign_validation_defects`, linked to their exact writer/repair and
validator/revalidator attempts.

## 5. Git and worktree policy

Riverview implementation authority is `ppow1/Riverview main`. Canonical Estate
documentation authority is `ppow1/theestate main`. A non-main checkout fails
the normal operator/startup expectation unless the current work package
explicitly authorizes that exact branch. Do not routinely create feature
branches. Historical `codex/c484-operator-persistent-service` is evidence only
and must not be reused for development. The existence of a historical branch
does not authorize it or imply that its contents are absent from `main`.

Use one bounded package worktree across internal repairs; a separate Git
commit is not required for each defect. Create one coherent candidate only
after complete internal verification. Detached temporary worktrees are allowed
for safe inspection/independent validation and must be explicitly tracked and
removed afterward.

Preserve unrelated dirty files and worktrees. Never use `git clean`, broad
reset, or destructive checkout casually. Verify the resulting candidate
commit/tree and its reachability from `origin/main`; provider claims and report
directories are not Git authority.

## 6. Durable lifecycle and PostgreSQL authority

The current authoritative tables are:

| Table | Purpose |
| --- | --- |
| `objectives` | Campaign aggregate, status, acceptance state, attention, timestamps, output |
| `objective_stages` | Ordered package state, phase, basis and role-attempt references |
| `objective_stage_dependencies` | Sole stage dependency graph |
| `work_orders` | Writer, validator, repair-writer, and revalidator work |
| `work_order_attempts` | Attempt history and terminal/late-result state |
| `relay_workers` | Worker instance and role/liveness state |
| `execution_envelopes`, `execution_results`, `reconciliation_records` | Fenced execution and reconciliation evidence |
| `river_events` | Idempotent lifecycle history |
| `campaign_validation_bases` | Immutable specification and evidence basis |
| `campaign_validation_results` | PASS/FAIL/BLOCKED validator results |
| `campaign_validation_defects` | Structured validator defects and resolution links |
| `campaign_package_runs` | Package projection, candidate, verification, acceptance, ownership |
| `campaign_repair_ledger` | Ordered package-engineer defect/repair history |

Package-run states are `executing`, `repairing`, `verifying`, `candidate_ready`,
`awaiting_independent_acceptance`, `acceptance_failed`, `accepted`, and
`escalated`. Stage states additionally cover writer/validator/repair/revalidation
pending and running, `defects_found`, `blocked`, `failed`, and `timed_out`.

Database state outranks transcript memory. Inspect the existing objective,
stage, basis, worktree, attempts, candidate, and open defects before creating
anything new.

## 7. Fencing and acceptance ownership

Every active attempt is identified by the exact tuple:

```text
work_order_id, attempt_id, lease_generation, fencing_token, worker_instance_id
```

Claim, heartbeat, progress, completion, reconciliation, and stale-result
handling must preserve it. Expired or superseded results are late/stale and
cannot advance authoritative state.

Final acceptance has a second durable fence. `campaign_package_runs` stores
`acceptance_owner_id`, `acceptance_lease_generation`,
`acceptance_lease_expires_at`, and `acceptance_invocation_started_at`.
`CampaignLifecycleStore.claim_package_acceptance()` atomically claims the exact
`package_run_id`, `candidate_ref`, and `candidate_version_hash`; only the
owner may invoke the independent validator and
`record_package_acceptance()` requires that owner. Five concurrent runners
therefore produce one candidate, one owner, one actual validator invocation,
and one dispatch. Expired ownership can be reclaimed for the same candidate;
late old-owner results are rejected.

## 8. Restart and resume

The same command resumes the same objective/stage; PostgreSQL selects the
incomplete portion:

- `executing` / `repairing` / `verifying`: continue using the existing ledger
  and worktree;
- `candidate_ready`: claim ownership for that exact candidate, and invoke the
  validator only if the claim succeeds;
- `awaiting_independent_acceptance`: wait; do not replay engineering,
  regenerate the candidate, or redispatch validation;
- valid `accepted`: terminal no-op;
- malformed `accepted`: fail closed and expose lifecycle-integrity failure; do
  not replay to normalize it;
- `acceptance_failed`: use persisted validator defects for the next bounded
  repair pass;
- `escalated`: stop and surface operator/external repair responsibility;
- repaired candidate revalidation: require a fresh independent result for the
  exact new candidate.

A valid accepted projection requires non-empty candidate reference/version,
positive dispatch evidence, and exact acceptance-candidate correspondence.

## 9. Package defect versus runner failure

A package engineering defect belongs to the package engineer's bounded
diagnose/repair/verify loop. Corruption or failure of Campaign Runner's own
PostgreSQL persistence, lifecycle transition, fencing, reconciliation,
ownership, or authority boundary is a Campaign Runner infrastructure defect.
It must not be silently converted into a package defect. Preserve evidence and
escalate through governed repair/revalidation. Runner failure must remain a
truthful failure, never package PASS or acceptance.

## 10. Reconciliation and bounded rename support

`ResultReconciler` in `src/riverview/autonomy/control.py` is the authoritative
repository boundary. It validates observed state, allowed paths, required
artifacts, result identity, and publication evidence before authoritative
reconciliation.

The accepted `RIV-REC-*` behavior uses Git-observed rename pairs, not provider
claims. A same-directory replacement of an authorized path may be accepted as
a bounded rename. Traversal, absolute paths, cross-component movement,
ambiguous pairs, unrelated additions, and ownership expansion remain
rejected. Evidence retains `changed_paths`, `rename_pairs`, and
`outside_scope`. Committed results are compared against the approved base and
candidate commit; worktree results use Git status. Publication requires the
resulting commit to be present and reachable from `origin/main`.

## 11. Independent acceptance

The package engineer cannot accept its own candidate. The independent validator
must evaluate the exact candidate and immutable basis under an independent
attempt. PASS is necessary but not sufficient: result/tree/version binding,
durable evidence, exact validation correspondence, and no unresolved blocking
defects are also required. FAIL preserves the complete structured defect set
and returns repair ownership. Revalidation must evaluate the repaired
candidate, not an older result.

For the broader manual rationale, rotating three-seat fallback, and
provider-neutral adversarial-review method, see the [Multi-Seat Adversarial AI
Engineering Method](Multi_Seat_Adversarial_AI_Engineering_Method.md).

## 12. PowerShell and Python entrypoints

Current operator script:

```text
Riverview/tools/powershell/campaign/Invoke-RiverviewPackageCampaign.ps1
```

From the Riverview root, launch or resume with:

```powershell
& .\tools\powershell\campaign\Invoke-RiverviewPackageCampaign.ps1 `
  -ObjectiveId <objective-guid> `
  -StageId <stage-guid> `
  -Worktree <package-worktree-path> `
  -Adapter <python-module:function> `
  -MaxRepairsPerRoot 3
```

There is no separate resume syntax: rerun the same command. The script sets
`PYTHONPATH=src` and calls `python -m riverview.campaign.package_runner`.
That module's CLI accepts `--objective-id`, `--stage-id`, `--worktree`,
`--adapter`, and `--max-repairs-per-root`. The adapter returns the
`PackageExecutor` and independent-acceptance callable; it must not infer
provider, model, resident, authority, or repair scope from shell prose.

Important source seams:

- `src/riverview/campaign/package_runner.py` — `PackageEngineerLoop`,
  `CampaignLifecycleStore.claim_package_acceptance()`, and `main`;
- `src/riverview/campaign/one_go.py` — `CampaignOneGoRunner` for bounded
  writer/validator/repair/revalidator role progression;
- `src/riverview/campaign/lifecycle.py` — `CampaignLifecycleStore` for bases,
  gates, verdicts, defects, package projection, ledger, and acceptance;
- `src/riverview/relay/store.py` — `RelayStore` for work-order claims,
  attempts, leases, heartbeats, expiry, and fenced completion;
- `src/riverview/autonomy/control.py` — `ResultReconciler` for Git/result
  reconciliation and publication evidence.

## 13. Non-destructive database readiness

From the Riverview root:

```powershell
Set-Location <Riverview-root>
git status --short
git rev-parse --show-toplevel
git rev-parse origin/main
python -m riverview.health database
python -m riverview.roadmap_health
```

Then inspect the objective/stage and package projection read-only. Confirm
basis, worktree, state, active attempts, candidate evidence, and defects.
`Initialize-RiverviewDatabase.ps1` and migration application change state and
are not casual readiness probes.

## 14. Evidence and reports

Implementation source, migrations, tests, and Riverview reports live under:

```text
Riverview/src/riverview/campaign/
Riverview/database/migrations/
Riverview/tests/
Riverview/docs/codex-reports/
```

Estate-facing reports live under `theestate/docs/codex-reports/seat-1/`,
`seat-2/`, and `seat-3/`; canonical operational references live under
`theestate/docs/operations/`. Reports are evidence artifacts, not lifecycle
authority.

Accepted Estate-side validation evidence pointers:

- [RUN-004C-R1 rename validation](../codex-reports/seat-1/RUN-004C-R1V-bounded-rename-reconciliation-validation.md)
- [RUN-004C-R2 retry recovery](../codex-reports/seat-1/RUN-004C-R2V-repair-attempt-retry-recovery-validation.md)
- [RUN-005A validation](../codex-reports/seat-1/RUN-005AV-package-level-self-repair-validation.md)
- [RUN-005AR accepted restart](../codex-reports/seat-1/RUN-005ARV-accepted-state-restart-idempotency-revalidation.md)
- [RUN-005AR2V pending restart](../codex-reports/seat-1/RUN-005AR2V-acceptance-pending-restart-revalidation.md)
- [RUN-005AR3V ownership fencing](../codex-reports/seat-1/RUN-005AR3V-independent-validator-ownership-fencing-revalidation.md)

The accepted RUN-002 specification and implementation-side reports are in the
Riverview repository under `docs/codex-reports/`; inspect them from the
authoritative `main` checkout rather than relying on a copied report.

## 15. Future AI startup checklist

1. Read `AI_HINTS.md`, then this guide.
2. Verify `Riverview/main` and `origin/main` ancestry.
3. Check PostgreSQL health and migration/readiness state without mutating it.
4. Read the package roadmap and accepted predecessor evidence.
5. Inspect the existing objective/stage before creating another.
6. Use package-level self-repair; do not seat-hop on every defect.
7. Preserve the independent acceptance boundary and ownership fence.
8. Preserve unrelated worktrees and avoid destructive cleanup.

## 16. Hermes integration considerations

This is an interface note, not a Hermes integration design. Hermes may rely on
these facts: Campaign Runner has durable package state; PostgreSQL is lifecycle
authority; package and repair history are durable; restart/resume exists; one
independent acceptance boundary exists; `main` is the canonical implementation
line; future durability improvements require an explicit integration package;
and existing durable state must not be silently discarded or reinterpreted.

## 17. Known limitations and follow-up

- Dashboard, notifier improvements, and exceptional arbitration are separate
  scopes, not implicit Campaign Runner core behavior.
- Package-specific execution and independent validation remain explicit adapter
  boundaries.
- Shared PostgreSQL stale/expired test residue can obscure diagnostics; isolate
  test state and classify it before calling it a semantic defect.
- Malformed durable projections fail closed and require governed repair; the
  runner does not reconstruct authority from transcripts or report prose.
- Grace cognition continues independently; Campaign Runner does not select
  models, GPUs, providers, or cognition authority.
