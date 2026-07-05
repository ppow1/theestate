# SERIES TASK WP-0117 — Repair WP-0106/WP-0107 Validation Failures

## Codex Command

Read collaboration/work_packages/pending/WP-0117_SERIES_repair_wp0106_wp0107_validation_failures.md and do exactly what it says.

## Mode

SERIES

## Mission

Repair the local validation failures for WP-0106 and WP-0107 discovered after WP-0116 merged.

WP-0116 normalized the completion receipts for WP-0106 and WP-0107, quarantined WP-9999 correctly, and passed its own validation. However, the local post-merge verification showed that WP-0106 and WP-0107 are still blocked because their validation recipes fail on pytest commands even though their CLI smoke checks pass.

This work package must identify the cause of those pytest failures, repair the narrowest legitimate defect, and restore WP-0106 and WP-0107 to production-ready status without weakening validation semantics or fabricating evidence.

## Background

After WP-0116 local verification, production-readiness totals were:

- total_work_packages_scanned: 102
- total_production_ready: 91
- total_blocked: 11
- total_missing_recipes: 7
- total_missing_receipts: 3
- total_incomplete_receipts: 3

WP-0116 itself validated successfully and is production-ready.

WP-9999 was correctly quarantined and is not scanned or promoted.

The remaining immediate Helen/Alfred path blockers are WP-0106 and WP-0107.

## Observed Failures

### WP-0106

CLI checks passed:

- `python -m estate.cli.main resident-presence --json`
- `python -m estate.cli.main resident-presence --resident Alfred --json`

The pytest command failed:

```bash
python -m pytest tests/test_resident_presence.py tests/test_resident_cards.py tests/test_steward_command_center.py
```

Validation result:

- validation_status: failed
- production_ready: false
- receipt_status: complete
- blocker: `Execution status blocks readiness: failed.`

### WP-0107

CLI checks passed:

- `python -m estate.cli.main alfred-duty --json`
- `python -m estate.cli.main resident-duty --resident Alfred --json`
- `python -m estate.cli.main resident-presence --resident Alfred --json`

The pytest command failed:

```bash
python -m pytest tests/test_alfred_duty.py tests/test_resident_presence.py tests/test_resident_cards.py
```

Validation result:

- validation_status: failed
- production_ready: false
- receipt_status: complete
- blocker: `Execution status blocks readiness: failed.`

## Scope

In scope:

1. Inspect the captured stderr/stdout artifacts for the failed WP-0106 and WP-0107 pytest commands.
2. Determine whether the failures are caused by:
   - real implementation regression,
   - stale test assumptions,
   - environment/setup mismatch,
   - timestamp/runtime-state drift,
   - missing test dependencies,
   - invalid validation recipe command, or
   - generated runtime artifact behavior.
3. Repair the smallest legitimate cause.
4. Preserve the CLI smoke checks that already pass.
5. Preserve the WP-0106 and WP-0107 receipts unless a receipt field is proven wrong.
6. Re-run WP-0106 validation.
7. Re-run WP-0107 validation.
8. Re-run WP-0116 validation to confirm the final-exception closure still holds.
9. Regenerate production-readiness and coverage artifacts.
10. Create a WP-0117 validation recipe and completion receipt.

Out of scope:

- Weakening validation semantics.
- Removing pytest coverage merely to make validation pass.
- Marking WP-0106 or WP-0107 ready without passing validation.
- Fabricating completion evidence.
- Broadly changing resident duty behavior beyond the failed tests.
- Changing governance, Steward authority, Chief Architect authority, Resident authority, merge authority, or production-readiness policy.
- Reopening broad historical validation sweeps.
- Changing WP-9999 handling except to preserve the WP-0116 quarantine behavior.

## Required Diagnostic Steps

Inspect the current failure artifacts or reproduce the failures locally.

Expected captured failure paths from the local verification are similar to:

- `runtime/validation/work_packages/captures/WP-0106_*/command_03_stderr.txt`
- `runtime/validation/work_packages/captures/WP-0107_*/command_04_stderr.txt`

If those exact captures are not present after reset, reproduce with:

```bash
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0106 --json
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0107 --json
```

Then inspect the newly generated capture files.

## Required Repair Principles

- If the implementation is wrong, fix the implementation.
- If the tests are stale but the implementation is correct, update the tests with evidence.
- If the recipe command is wrong, repair the recipe command without reducing coverage below the original intent.
- If runtime/generated state is causing nondeterminism, make the tests deterministic or isolate generated state safely.
- If timestamps are involved, use current timestamps or stable comparisons rather than fixed stale expectations.
- If the pytest command is running without the needed `PYTHONPATH`, repair the recipe command or test invocation in the existing validation style.

## Required Reports

Create:

`operations/validation/backlog_burn_down/WP-0117_wp0106_wp0107_failure_repair_report.md`

Create machine-readable companion:

`runtime/validation/backlog_burn_down/WP-0117_wp0106_wp0107_failure_repair_report.json`

The reports must include:

- production-readiness totals before WP-0117
- production-readiness totals after WP-0117
- exact WP-0106 failure cause
- exact WP-0107 failure cause
- files changed to repair each failure
- whether the repair touched implementation, tests, recipe commands, or generated artifacts
- WP-0106 validation result after repair
- WP-0107 validation result after repair
- WP-0116 validation result after repair
- WP-9999 quarantine status after repair
- Helen path status after repair
- remaining blockers after repair
- recommended next action

## Required Tests

Run:

```bash
PYTHONPATH=src pytest tests/test_work_package_validation.py tests/test_production_readiness_validation.py -q
```

Also run the exact failed pytest groups after repair:

```bash
PYTHONPATH=src python -m pytest tests/test_resident_presence.py tests/test_resident_cards.py tests/test_steward_command_center.py
PYTHONPATH=src python -m pytest tests/test_alfred_duty.py tests/test_resident_presence.py tests/test_resident_cards.py
```

Add or update targeted tests if the repair changes implementation logic or deterministic runtime behavior.

## Required Validation Commands

Run or document equivalent:

```bash
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0106 --json
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0107 --json
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0116 --json
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0117 --json
PYTHONPATH=src python -m estate.cli.main validation-production-readiness --json
```

Also run baseline validations to ensure recent validation infrastructure still holds:

```bash
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0102 --json
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0105 --json
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0111 --json
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0114 --json
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0115 --json
```

## Required Outputs

Update or create as applicable:

- the narrow implementation/test/recipe files required to fix WP-0106 and WP-0107
- validation reports for WP-0106 and WP-0107
- validation report for WP-0116 after repair
- validation report for WP-0117
- `operations/validation/production_readiness_report.md`
- `runtime/validation/production_readiness_report.json`
- `operations/validation/validation_coverage_manifest.md`
- `runtime/validation/validation_coverage_manifest.json`
- `operations/validation/backlog_burn_down/WP-0117_wp0106_wp0107_failure_repair_report.md`
- `runtime/validation/backlog_burn_down/WP-0117_wp0106_wp0107_failure_repair_report.json`
- `collaboration/work_packages/completions/WP-0117_codex_done.json`

## WP-0117 Self-Validation Recipe

Add a recipe for WP-0117 that verifies:

- the human-readable WP-0117 repair report exists
- the machine-readable WP-0117 repair report exists and parses as JSON
- the report identifies the WP-0106 failure cause
- the report identifies the WP-0107 failure cause
- WP-0106 validates successfully after repair
- WP-0107 validates successfully after repair
- WP-0116 validates successfully after repair
- production-readiness validation executes successfully
- WP-9999 remains not promoted
- Helen path status is explicitly reported
- WP-0117 completion receipt is complete

Use cross-platform Python checks only. Avoid Bash-specific loops.

## Completion Artifact

Create:

`collaboration/work_packages/completions/WP-0117_codex_done.json`

It must include:

- `work_package_id = WP-0117`
- `codex_status = done`
- `completed_at`
- `branch`
- `pull_request_url` or `pull_request_url_not_applicable_reason`
- `summary`
- WP-0106 failure cause
- WP-0107 failure cause
- repair classification for each package
- files changed
- tests run
- validation commands run
- production-readiness totals before and after
- Helen path status after repair
- remaining blockers
- known limitations
- `ready_for_ca_review = true`
- `merge_authority = ca_verified_auto_merge_allowed`

## Acceptance Criteria

WP-0117 is complete when:

1. WP-0106 validation passes locally.
2. WP-0107 validation passes locally.
3. WP-0106 and WP-0107 are production-ready unless a real implementation defect remains and is precisely documented.
4. WP-0116 still validates after the repair.
5. WP-9999 remains quarantined/not promoted.
6. Production-readiness totals are regenerated.
7. Existing production-ready packages remain production-ready.
8. WP-0117 validates itself and has a complete receipt.
9. No validation, governance, authority, or production-readiness semantics are weakened.

## Merge Class

Class A.

Escalate only if the work requires changing validation policy semantics, receipt schema semantics, production-readiness meaning, governance authority, Steward authority, Chief Architect authority, Resident authority, or merge authority.
