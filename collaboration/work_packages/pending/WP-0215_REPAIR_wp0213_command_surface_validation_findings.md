# REPAIR TASK WP-0215 — Repair WP-0213 Command Surface Validation Findings

## Codex Command
Read collaboration/work_packages/pending/WP-0215_REPAIR_wp0213_command_surface_validation_findings.md and do exactly what it says.

## Mode
REPAIR

## Mission
Repair the validation findings left after WP-0213 installed the real Office command surface.

WP-0213 successfully installed real Office action controls and the required command-surface action payload is present. However, local validation reported findings that must be corrected before WP-0213 can be treated as cleanly accepted.

This package must fix the WP-0213 validation findings without weakening the real-verb acceptance standard.

## Current Evidence
The Steward ran WP-0213 validation locally after pulling the installed command surface.

Required checks passed:

- `python -m pytest tests/test_office_command_surface.py`
- Office command-center JSON action-presence check
- required WP-0213 artifacts exist

The Office payload included actions for these required tabs:

- `ai-services-models`
- `validation`
- `work-packages`
- `notifications`
- `alfred`
- `mission-control`
- `daily-board`

Validation findings remain:

1. `python -m pytest tests/test_steward_command_center.py` exited with code 1.
2. `collaboration/work_packages/completions/WP-0213_codex_done.json` is missing required receipt metadata:
   - `pull_request_url_or_not_applicable_reason`
   - `files_changed`
3. WP-0213 production readiness is therefore false because the receipt is incomplete and the command-center test has a finding.

## Required First Step
Inspect the captured failing test output before changing code.

The local validation output reported the failing command stdout at a path similar to:

`runtime/validation/work_packages/captures/WP-0213_2026-07-06T214448Z0000/command_04_stdout.txt`

If that exact capture is not available in the Codex environment, rerun:

```bash
PYTHONPATH=src python -m pytest tests/test_steward_command_center.py -q
```

Use the actual failure output to determine the fix. Do not guess.

## Scope
In scope:

1. Diagnose and fix the failing `tests/test_steward_command_center.py` finding introduced or exposed by WP-0213.
2. Preserve the WP-0213 real Office command surface behavior.
3. Complete the missing WP-0213 completion receipt metadata.
4. Rerun WP-0213 validation.
5. Add or adjust tests only where they reflect correct behavior.
6. Create a WP-0215 repair report and completion receipt.

## Out of Scope
Do not remove the real Office action controls added by WP-0213.

Do not downgrade real verbs into metadata-only controls.

Do not satisfy tests by hiding or deleting Office action payloads.

Do not mark fake controls as valid.

Do not bypass the WP-0213 standard that every exposed verb must be real, gated, blocked, queued, completed, or failed with a visible outcome.

Do not change Estate authority boundaries.

Do not add cloud calls, telemetry, or remote execution.

Do not edit unrelated work packages.

## Required Repair Behavior

### 1. Fix Steward Command Center Test Finding
Run the failing test and identify the exact assertion or error.

Fix the implementation or test expectation as appropriate.

Acceptable fixes include:

- updating command-center payload generation to include the new action model consistently,
- fixing HTML/rendering changes introduced by action controls,
- adjusting tests to account for legitimate new real-action payload structure,
- preserving backwards compatibility for existing tabs/settings/profile expectations,
- fixing import/path/fixture issues caused by the new command surface.

Unacceptable fixes include:

- deleting tests to make validation pass,
- marking the command-center test non-required without fixing the failure,
- removing Office action controls,
- converting real controls back to metadata-only controls,
- suppressing errors without a deterministic reason.

### 2. Complete WP-0213 Receipt Metadata
Update:

`collaboration/work_packages/completions/WP-0213_codex_done.json`

Add the missing fields required by validation:

- `pull_request_url_or_not_applicable_reason`
- `files_changed`

Use the actual WP-0213 merged PR information if available. If the pull request URL is unavailable in the local environment, provide a clear `pull_request_url_or_not_applicable_reason` value rather than omitting the field.

The `files_changed` list must reflect the active files changed by WP-0213, including the command surface implementation, command-center wiring, tests, validation recipe, report/audit artifacts, and completion artifact where applicable.

Do not fabricate unknown values. If a precise value cannot be recovered, provide the most accurate local evidence and document the limitation in the WP-0215 report.

### 3. Confirm WP-0213 Still Meets Real-Verb Standard
After repair, verify that the Office command-center JSON still exposes real or gated actions for:

- `ai-services-models`
- `validation`
- `work-packages`
- `notifications`
- `alfred`
- `mission-control`
- `daily-board`

Each exposed action must have an availability state consistent with the WP-0213 acceptance model.

Do not regress the real-verb behavior.

## Required Report
Create:

`operations/steward/WP-0215_wp0213_command_surface_validation_repair_report.md`

The report must include:

1. Summary of the WP-0213 validation findings.
2. Exact failing `tests/test_steward_command_center.py` output or summarized root cause.
3. Files changed.
4. How the failure was fixed.
5. What WP-0213 receipt metadata was added.
6. Confirmation that WP-0213 Office actions remain present.
7. Tests run.
8. Validation commands run.
9. Remaining warnings or limitations.
10. Manual verification steps for the Steward.

## Required Completion Artifact
Create:

`collaboration/work_packages/completions/WP-0215_codex_done.json`

It must include:

- `work_package_id`: `WP-0215`
- `codex_status`
- `completed_at`
- `branch`
- `pull_request_url` or `pull_request_url_or_not_applicable_reason`
- `summary`
- `root_cause`
- `files_changed`
- `wp0213_receipt_fields_repaired`
- `tests_run`
- `validation_commands_run`
- `remaining_findings`
- `ready_for_ca_review`: true
- `merge_authority`: `ca_verified_auto_merge_allowed`

## Required Tests
Run:

```bash
PYTHONPATH=src python -m pytest tests/test_office_command_surface.py
PYTHONPATH=src python -m pytest tests/test_steward_command_center.py
PYTHONPATH=src python -m estate.cli.main steward-command-center --json
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0213 --json
```

Also run any narrower tests directly related to the root cause.

If `tests/test_office_actions.py tests/test_office_*actions.py` is valid in the environment, run it as well.

## Required Validation
After fixes, rerun WP-0213 validation.

The desired result is:

- no failing required commands,
- `tests/test_steward_command_center.py` passes or any remaining issue is explicitly non-blocking with justification,
- WP-0213 receipt no longer reports missing `pull_request_url_or_not_applicable_reason` or `files_changed`,
- WP-0213 command surface actions remain present,
- production-readiness status for WP-0213 improves accordingly.

Then validate WP-0215 itself if a recipe exists or the local validation runner supports it:

```bash
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0215 --json
```

## Manual Verification Requirement
The repair report must tell the Steward how to verify locally:

1. Pull the repair.
2. Run the WP-0213 validation command.
3. Confirm `tests/test_steward_command_center.py` no longer fails.
4. Confirm the Office JSON contains `office_actions` for the required tabs.
5. Start the Office in served mode.
6. Click at least one WP-0213 real Office action and confirm it reports `completed`, `queued`, `blocked`, or `failed` with visible details.

## Acceptance Criteria
WP-0215 is complete when:

1. The root cause of the `tests/test_steward_command_center.py` finding is identified and repaired.
2. WP-0213 completion receipt contains the missing required metadata fields.
3. WP-0213 command-surface actions remain installed and visible in Office JSON.
4. Required tests pass or any remaining non-blocking finding is justified in the report.
5. WP-0213 validation is rerun and no longer reports the same receipt metadata gaps.
6. WP-0215 repair report exists.
7. WP-0215 completion receipt exists.

## Merge Class
Class B if active implementation or test files are changed.

Class A only if the repair is limited to receipt/report metadata and no active runtime/test code is changed.
