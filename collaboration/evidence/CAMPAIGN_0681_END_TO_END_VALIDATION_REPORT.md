# CAMPAIGN-0681 End-to-End Validation Report

Date: `2026-07-18`
Environment: Windows; repository `A:\theestate`; PowerShell `7.5.5`; Python
`3.14.6`; Git `2.55.0.windows.1`.
WP-0707 bounded commit: `6e6098003d1650b45777249a3a00d9cef25cc299`.

## Final result

- The 19 prior package validators for WP-0688 through WP-0706 passed; the WP-0707 validator passed; 20 canonical package validators passed in total.
- The final integrated suite passed: **253 tests in 34 test modules**.
- Manifest JSON parsing passed.
- Every manifest specification and authoritative receipt path through WP-0706
  existed and resolved; WP-0707 evidence is created by its bounded commit.
- `git diff --check` and the WP-0707 canonical validator passed after receipt
  creation and are recorded in the WP-0707 receipt.

## Exact aggregate commands and results

| Command | Exit | Result |
|---|---:|---|
| `foreach ($n in 688..706) { pwsh -NoProfile -File scripts/validation/Validate-Campaign0681Package.ps1 -PackageId ('WP-{0:D4}' -f $n) }` | 0 | all 19 prior canonical validators passed |
| aggregate pytest selection across campaign, transition, taxonomy, health, momentum, blocker, office, Dispatch, recovery, replay, audit, dashboard, readiness, validation, and reconciliation modules | 0 | 226 passed before the historical Windows regression recheck |
| `python -m pytest -q -p no:cacheprovider --basetemp A:\theestate\.tmp\wp0707-readiness tests/test_operational_readiness_dashboard.py tests/test_operational_readiness_closure.py tests/test_operational_validation.py tests/test_validation_reconciliation.py` | 1 | 26 passed, 1 failed: CLI used installed Estate root instead of subprocess cwd |
| same command with basetemp `A:\theestate\.tmp\wp0707-readiness-retry` after passing `Path.cwd()` through the existing CLI seam | 0 | 27 passed |
| final 34-module aggregate command with basetemp `A:\theestate\.tmp\wp0707-final` | 0 | 253 passed in 36.16 seconds |
| `pwsh -NoProfile -File scripts/validation/Validate-Campaign0681Package.ps1 -PackageId WP-0707` | 0 | WP-0707 canonical validator passed; 20 canonical validators passed in total |

The first readiness failure reproduces the historical WP-0698 observation; it is
preserved rather than waived. The one-line integration correction in
`src/estate/cli/main.py` makes the operational-validation CLI honor its invocation
root and does not create a new validator or truth source.

## Behavioral conclusions

The tests prove fail-closed transitions, explicit protected action classes,
truthful degraded/unknown health, dependency-aware momentum, canonical office
routing, guarded mechanical action, deterministic retry/recovery, append-only
audit, derived-only visibility, non-accepting closeout preparation, failure-mode
containment, and the bounded pilot. They do not prove live-provider availability,
production outage recovery, deployment, or institutional acceptance.

Production-like outage, restart, and replay qualification remains required before
operational rollout, alongside live-provider and long-duration qualification.
