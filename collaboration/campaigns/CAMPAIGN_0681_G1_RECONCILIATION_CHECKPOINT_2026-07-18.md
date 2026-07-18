# CAMPAIGN-0681 — G1 Reconciliation and Protected Decision Checkpoint

- Campaign: `CAMPAIGN-0681 — Estate Operationalization`
- Recorded: `2026-07-18`
- Repository root: `A:\theestate`
- Branch: `campaign/0681-estate-operationalization`
- Verified base: `main` / `5c82f1a1e22aec23517fb80fe9c830566afac068`
- Reconciled HEAD before this checkpoint: `56470256de1192b7310987eb0ff0061fe7434b80`
- Gate: `G1 — Canonical and authority freeze`
- State: `implementation and evidence complete; awaiting explicit Chief Architect release`

## Branch reconciliation

The pre-reconciliation campaign branch and `main` had diverged. The campaign side
contained the WP-0688 through WP-0690 bounded work; `main` contained the merged
WP-0691 through WP-0693 work and later repository changes. Commit `56470256`
merged current `main` into the existing campaign branch without replacing the
branch, rebasing package commits, discarding campaign work, or force-pushing.

The only merge conflict was
`scripts/validation/Validate-Campaign0681Package.ps1`. Its resolution preserves
the campaign-side lowercase adopted headings and the broader main-side accepted
forms `Behavior`, `Outputs`, and `Required Validation Commands`. No conflict
markers remain.

## WP-0688 through WP-0690 classification

### WP-0688 — implemented and fully evidenced

- Implementation paths:
  `docs/architecture/estate_operational_current_state_map.md`,
  `docs/architecture/estate_operational_canonical_reuse_map.md`,
  `docs/architecture/estate_operational_authority_map.md`, and
  `operations/departments/engineering/CAMPAIGN_0681_gap_and_conflict_register.md`.
- Bounded package commit: `abe8db0ddbf910e10668e8b5a13ba33d7bca07a8`.
- Authorized prerequisite repair: `6bc80477c113b2b69ec29f3c4dd2b3448c160d2b`.
- Receipt:
  `collaboration/work_packages/completions/WP-0688_completion_receipt.md`.
- Validation evidence: receipt ledger plus the passing current-machine canonical
  package validator recorded below.
- Dependency evidence: no package dependency; G0 authority and baseline ancestry
  remain present.
- Gate evidence:
  `collaboration/campaigns/CAMPAIGN_0681_G1_CHECKPOINT.md` and this checkpoint.
- Branch location: local and remote campaign history before reconciliation; now
  preserved in the reconciled local campaign branch.

### WP-0689 — implemented and fully evidenced

- Implementation paths:
  `src/estate/core/operational_transition_contract.py`,
  `schemas/operations/estate_operational_event_v1.schema.json`,
  `schemas/operations/estate_operational_projection_v1.schema.json`,
  `docs/architecture/estate_operational_state_event_transition_contract.md`,
  fixtures, and `tests/test_operational_transition_contract.py`.
- Bounded package commit: `739977d53662d05150b5d323e30289e2671fa7c9`.
- Receipt:
  `collaboration/work_packages/completions/WP-0689_completion_receipt.md`.
- Validation evidence: receipt ledger, 35-test current G1 focused run, and the
  passing current-machine canonical package validator.
- Dependency evidence: WP-0688 receipt, deliverables, and bounded commit are
  present in the same reconciled history.
- Gate evidence: historical G1 checkpoint and this checkpoint.
- Branch location: preserved on the reconciled campaign branch.

### WP-0690 — implemented and fully evidenced

- Implementation paths:
  `src/estate/core/operational_action_taxonomy.py`,
  `schemas/operations/estate_operational_action_v1.schema.json`,
  `docs/architecture/estate_operational_action_taxonomy.md`, and
  `tests/test_operational_action_taxonomy.py`.
- Bounded package commit: `b24e1b7612426cc669d6900fb9272de09660a619`.
- Receipt:
  `collaboration/work_packages/completions/WP-0690_completion_receipt.md`.
- Validation evidence: receipt ledger, 35-test current G1 focused run, and the
  passing current-machine canonical package validator.
- Dependency evidence: WP-0688 and WP-0689 receipts, deliverables, and commits are
  present in the same reconciled history.
- Gate evidence: historical G1 checkpoint and this checkpoint.
- Branch location: preserved on the reconciled campaign branch.

## WP-0691 through WP-0693 reconciliation

The three implementations and receipts were merged into `main` and are now also
present on the reconciled campaign branch:

| Package | Bounded implementation commit | Receipt |
|---|---|---|
| WP-0691 | `184d0510a123537e97542f11473eaa84a53d740c` | `collaboration/work_packages/completions/WP-0691_completion_receipt.md` |
| WP-0692 | `c407cd050f152a8837b1f76af956c05676517e21` | `collaboration/work_packages/completions/WP-0692_completion_receipt.md` |
| WP-0693 | `896366d57e440b75fb5de5cf907001eec84f21e0` | `collaboration/work_packages/completions/WP-0693_completion_receipt.md` |

Their historical receipt warnings accurately described isolated checkouts that
lacked WP-0688/WP-0689 receipts and PowerShell. Those warnings are not rewritten.
The reconciled branch now contains the dependencies and receipts, and the current
Windows environment provides PowerShell. The prior failed cloud G2 checkpoint is
preserved at commit `39bee2633818bdc8c68ef427f5d1f9d006dbb3a8`;
its missing-PowerShell validation gap has been rerun successfully below. That
historical checkpoint did not and does not release G1 or G2.

## Current validation ledger

Environment: Windows PowerShell 7.5.5, Python 3.14.6, repository root
`A:\theestate`. Pytest used isolated basetemp directories inside the repository;
they were removed after the successful run.

| Exact command | Exit | Result |
|---|---:|---|
| `python -m pytest -q -p no:cacheprovider --basetemp A:\theestate\.tmp\campaign0681-g1 tests/test_operational_action_taxonomy.py tests/test_operational_transition_contract.py` | 0 | 35 passed |
| `python -m pytest -q -p no:cacheprovider --basetemp A:\theestate\.tmp\campaign0681-g2 tests/test_operational_blocker_classifier.py tests/test_campaign_momentum_observer.py tests/test_campaign_0681_health_signal_integration.py` | 0 | 50 passed |
| `pwsh -NoProfile -File scripts/validation/Validate-Campaign0681Package.ps1 -PackageId WP-0688` | 0 | package validation passed |
| `pwsh -NoProfile -File scripts/validation/Validate-Campaign0681Package.ps1 -PackageId WP-0689` | 0 | package validation passed |
| `pwsh -NoProfile -File scripts/validation/Validate-Campaign0681Package.ps1 -PackageId WP-0690` | 0 | package validation passed |
| `pwsh -NoProfile -File scripts/validation/Validate-Campaign0681Package.ps1 -PackageId WP-0691` | 0 | package validation passed |
| `pwsh -NoProfile -File scripts/validation/Validate-Campaign0681Package.ps1 -PackageId WP-0692` | 0 | package validation passed |
| `pwsh -NoProfile -File scripts/validation/Validate-Campaign0681Package.ps1 -PackageId WP-0693` | 0 | package validation passed |
| `python -m json.tool collaboration/work_packages/planning/CAMPAIGN_0681_manifest.json` | 0 | manifest parsed |
| `git diff --check` and `git diff --cached --check` | 0 | no whitespace errors |

## Gate decision and resume boundary

Repository-wide and all-ref searches found no explicit Chief Architect G1 release.
The merges of WP-0691 through WP-0693 into `main` are implementation history and
must not be inferred to be the missing protected decision. The historical G1
checkpoint remains truthful: G1 has been reached but is not released.

Decision required from: **Chief Architect**.

Choices:

1. **Release G1** — accept the canonical-reuse, operational-transition, and
   action-taxonomy freeze for continued campaign execution.
2. **Request changes** — identify the exact deficient package, evidence, or
   architectural boundary; the campaign remains stopped at G1.
3. **Reject G1** — identify the controlling contradiction or unacceptable risk;
   the campaign remains stopped and later packages are not executed.

Recommended choice: **Release G1**, because all three bounded implementations,
receipts, dependency evidence, G1 deliverables, current validators, and focused
tests are present and passing, and no conflicting release evidence was found.

After an explicit durable G1 release, the next mechanically permitted sequence is:
record the G1 decision, reconcile the now-passing G2 retry evidence without
rewriting historical receipts, determine the G2 release state under its recorded
authority, and then execute WP-0694 if the gate evidence permits.

This checkpoint grants no gate release, architecture acceptance, merge,
deployment, staffing, spending, disclosure, institutional acceptance, or campaign
closure authority.
