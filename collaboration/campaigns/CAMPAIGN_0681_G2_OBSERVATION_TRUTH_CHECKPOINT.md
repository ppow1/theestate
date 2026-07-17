# CAMPAIGN-0681 G2 Observation Truth checkpoint

**Recorded:** 2026-07-17 UTC
**Decision:** FAILED / NOT RELEASED
**Gate protection:** G2 is non-protected. This checkpoint grants no protected authority.

## Repository state

- Repository root: `/workspace/theestate`
- Required and current branch: `campaign/0681-estate-operationalization`
- Verification HEAD: `21e0e4ce706aa0e01ac440eecdfd32f80dab29a5`
- Authorization baseline `fadea83d678bb50c30cacd62aa12f5c6010b8e02` is an ancestor of the verification HEAD.
- The working tree was clean before this checkpoint was created.
- No merge, deployment, staffing, spending, disclosure, acceptance, or campaign closure was performed by this verification.

## Package completion evidence

| Package | Bounded completion commit | Receipt | State |
|---|---|---|---|
| WP-0691 | `184d0510a123537e97542f11473eaa84a53d740c` | `collaboration/work_packages/completions/WP-0691_completion_receipt.md` | Present and inspected |
| WP-0692 | `c407cd050f152a8837b1f76af956c05676517e21` | `collaboration/work_packages/completions/WP-0692_completion_receipt.md` | Present and inspected |
| WP-0693 | `896366d57e440b75fb5de5cf907001eec84f21e0` | `collaboration/work_packages/completions/WP-0693_completion_receipt.md` | Present and inspected |

The manifest, the exact three package specifications, all three completion
receipts, and the manifest's G2 and checkpoint policies were read. Recent
history also contains the corresponding bounded package commits and their
integration merge commits.

## Validation record

Executed from `/workspace/theestate` on 2026-07-17 UTC:

| Command | Result |
|---|---|
| `python -m json.tool collaboration/work_packages/planning/CAMPAIGN_0681_manifest.json > /dev/null` | PASS (exit 0) |
| `pwsh -NoProfile -File scripts/validation/Validate-Campaign0681Package.ps1 -PackageId WP-0691` | **FAIL (exit 127): `/bin/bash: line 2: pwsh: command not found`** |
| `pwsh -NoProfile -File scripts/validation/Validate-Campaign0681Package.ps1 -PackageId WP-0692` | **FAIL (exit 127): `/bin/bash: line 3: pwsh: command not found`** |
| `pwsh -NoProfile -File scripts/validation/Validate-Campaign0681Package.ps1 -PackageId WP-0693` | **FAIL (exit 127): `/bin/bash: line 4: pwsh: command not found`** |
| `python -m pytest -q tests/test_campaign_0681_health_signal_integration.py` | PASS: 16 passed |
| `python -m compileall -q src/estate/core` | PASS |
| `python -m pytest -q tests/test_steward_command_center.py` | PASS: 43 passed |
| `pytest -q tests/test_campaign_momentum_observer.py` | PASS: 10 passed |
| `pytest -q tests/test_campaign_momentum_observer.py tests/test_campaign_0681_health_signal_integration.py` | PASS: 26 passed |
| `python -m compileall -q src/estate/core/campaign_momentum_observer.py` | PASS |
| `python -m pytest -q tests/test_operational_blocker_classifier.py` | PASS: 24 passed |
| `python -m pytest -q tests/test_operational_blocker_classifier.py tests/test_campaign_momentum_observer.py tests/test_campaign_0681_health_signal_integration.py` | PASS: 50 passed |
| `python -m compileall -q src/estate/core/operational_blocker_classifier.py` | PASS |
| `git diff --check` | PASS |

The receipt-recorded WP-0692 real-manifest smoke check is described only as an
abbreviated here-document (`python - <<'PY' ... PY`) rather than a reproducible
exact command. Its final recorded run passed with `PYTHONPATH=src`; it cannot be
re-run exactly from the receipt text. This is retained as a residual evidence
risk and is not treated as a substitute for the required validators.

## G2 evidence findings

- Resident/service health integration tests distinguish healthy, degraded,
  unavailable, stale, and unknown, and prove that health affects readiness.
- Momentum observation tests keep observation separate from recommendation and
  execution, and prove dependency and evidence effects on classification.
- Blocker/escalation tests require a reason and authority owner, fail closed on
  ambiguity, and prevent protected escalation bypass.
- The implementations and conflict/reuse evidence consume existing canonical
  seams. No duplicate health registry, scheduler, dispatch queue, mailbox bus,
  or authority source was found in the three package changes.
- Outputs remain observational/recommendational and expressly grant no action
  authority.

## Failure, risks, and gate state

The three required package-validation commands could not execute because this
environment has no `pwsh` executable. Under the manifest's fail-closed
validation policy, that is an incomplete required validation and G2 cannot be
verified or released. No unrelated repair was attempted.

Residual risks are the unexecuted PowerShell validators, the non-reproducible
abbreviated WP-0692 smoke command, and the dependency-evidence discrepancies
already recorded in the package receipts for WP-0688/WP-0689.

- Gate state: **G2 failed verification; not released**.
- Retry state: rerun the three required PowerShell validators in an environment
  providing `pwsh`, then repeat the complete G2 verification.
- Protected decisions pending: none granted or resolved here.
- Next permitted action: **repeat G2 verification only; WP-0694 is not
  permitted while this failed checkpoint remains unresolved**.
