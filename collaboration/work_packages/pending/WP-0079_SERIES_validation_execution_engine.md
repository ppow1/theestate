# SERIES TASK WP-0079 — Validation Execution Engine

## Codex Command

Read `collaboration/work_packages/pending/WP-0079_SERIES_validation_execution_engine.md` and do exactly what it says.

## Mode

SERIES

## Mission

Complete the validation automation loop that began in WP-0074 by implementing a validation execution engine that can run work-package-specific validation recipes, write reviewable artifacts, and optionally commit/push those artifacts safely.

WP-0074 created useful validation observation, metrics, dashboard, and handoff surfaces. WP-0079 must add the missing execution layer: the Steward should be able to run one short local command for a selected work package and have the Estate produce Markdown and JSON validation reports suitable for Chief Architect review.

## Background

Manual validation currently requires the Steward to paste long PowerShell blocks into a terminal and paste large output back into chat. WP-0074 improved the institutional validation framework but did not provide the reusable PowerShell script workflow, the one-command work-package validation runner, or the safe commit/push loop originally envisioned.

The new workflow should be:

1. Reviewer defines or selects a work package validation recipe.
2. Steward runs a short local command.
3. The Estate executes validation commands locally.
4. The Estate captures stdout, stderr, exit codes, timestamps, and findings.
5. The Estate writes Markdown and JSON validation artifacts.
6. The Estate updates the validation metrics / handoff surfaces where appropriate.
7. Optional wrapper safely commits and pushes only validation artifacts.
8. Reviewer reads the committed validation report from GitHub.

## Scope

Implement the execution layer on top of the WP-0074 validation framework.

Add or complete:

- `operations/validation/scripts/`
- `operations/validation/reports/`
- `runtime/validation/work_packages/`
- a validation recipe registry keyed by work package ID
- a reusable validation execution engine
- a local PowerShell runner
- a safe run-and-commit PowerShell wrapper
- CLI support consistent with the Estate command style

Preferred command surfaces:

```powershell
.\operations\validation\scripts\validate_work_package.ps1 -WorkPackageId WP-0058
.\operations\validation\scripts\run_and_commit_validation.ps1 -WorkPackageId WP-0058
```

and, if consistent with the existing CLI:

```bash
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0058 --json
```

If the CLI name must follow existing style, use the closest explicit name, but document the final command clearly in the completion record.

## Required Behavior

The base validator must:

- accept a work package ID
- resolve the validation recipe for that ID
- run each configured command in order
- capture stdout, stderr, exit code, start time, end time, and duration
- continue or stop according to recipe settings
- write a Markdown report
- write a JSON report
- update a latest pointer
- record missing recipes as a reportable validation condition rather than crashing
- integrate with the validation observations / metrics / handoff surfaces created by WP-0074 where practical

The safe commit wrapper must:

- run `git pull` only when safe
- refuse to continue if unrelated local changes exist
- run the base validator
- stage only expected validation artifacts
- commit with a clear message such as `Validate WP-0058`
- push only when the wrapper is explicitly used
- refuse to stage source code, registry changes, or unrelated runtime files

## Artifact Outputs

For work package `WP-0058`, expected outputs should include:

- `operations/validation/reports/WP-0058_validation.md`
- `runtime/validation/work_packages/WP-0058_validation.json`
- `runtime/validation/work_packages/latest.json`

The exact filenames may include timestamps if needed, but there must also be a stable latest pointer for review.

## Required JSON Report Fields

Each JSON report must include:

- `work_package_id`
- `validation_id`
- `generated_at`
- `git_branch`
- `git_commit_before`
- `git_commit_after` when committed
- `validation_status`
- `recipe_id`
- `commands_run`
- `command_results`
- `stdout_summary`
- `stderr_summary`
- `files_written`
- `warnings`
- `failures`
- `findings`
- `reviewer_recommendation`

Each command result must include:

- `command`
- `started_at`
- `completed_at`
- `duration_seconds`
- `exit_code`
- `stdout_path` or `stdout_excerpt`
- `stderr_path` or `stderr_excerpt`
- `status`

## Required Markdown Report Sections

Each Markdown report must include:

- title
- timestamp
- work package ID
- local branch
- git commit
- validation status
- recipe used
- commands run
- findings
- warnings
- failures
- generated artifacts
- reviewer recommendation

## Validation Recipe Registry

Create a simple registry for validation recipes.

A JSON file, Python mapping, or other local registry is acceptable, but it must be easy to extend.

Initial recipes must include at least:

- WP-0056 — Notification Center Workspace
- WP-0057 — Voice Integration Framework
- WP-0058 — Steward Recall Operations View
- WP-0059 — Resident Conversations Workspace
- WP-0060 — Estate Interaction Services and Adapter Registry
- WP-0074 — Validation Handoff Artifact Workflow
- WP-0079 — Validation Execution Engine self-check

Initial recipes should use real Estate commands such as:

- `python -m estate.cli.main steward-command-center --json`
- `python -m estate.cli.main assignment-queue --json`
- `python -m estate.cli.main validation-handoff-artifact-workflow --json`
- `python -m estate.cli.main validation-observations --json`
- `python -m estate.cli.main validation-metrics-dashboard --json`
- `python -m estate.cli.main global-search "Notification Center" --json`
- `python -m estate.cli.main global-search "Steward Recall" --json`
- `python -m estate.cli.main global-search "Resident Conversations" --json`
- `python -m estate.cli.main global-search "Interaction Services Adapter Registry" --json`
- `python -m estate.cli.main palette-command notification-center --json`
- `python -m estate.cli.main palette-command steward-recall --json`
- `python -m estate.cli.main palette-command resident-conversations --json`

Recipes may classify commands as required or observational. Observational command failures should appear as findings, not necessarily fatal failures.

## Safety Requirements

Do not commit unrelated files.

Do not stage broad paths such as `.` or the repository root.

Do not commit source code changes produced by validation.

Do not push from the base validator.

Only the explicit run-and-commit wrapper may commit or push.

Do not hide failed commands.

Do not treat missing optional artifacts as fatal unless the recipe declares them required.

Do not edit `estate_ledger/ledger.md` or `development/devlog.md`.

Do not change validation authority or automatically approve work packages.

## Git Safety Rules

The commit wrapper must fail safely when unrelated modified, staged, untracked, deleted, or conflicted files are present.

The wrapper may stage only:

- `operations/validation/reports/<work_package>_validation*.md`
- `runtime/validation/work_packages/<work_package>_validation*.json`
- `runtime/validation/work_packages/latest.json`
- any explicitly documented validation stdout/stderr capture files under a validation runtime subdirectory

If there is nothing to commit after validation, the wrapper should report that clearly and exit without error.

## Tests

Add tests for:

- known work package recipe execution
- unknown work package report generation
- command result capture
- required vs observational command handling
- Markdown report generation
- JSON report generation
- latest pointer update
- safe handling of failed commands
- refusal to commit unrelated modified files
- refusal to stage non-validation files
- no broad staging behavior
- self-check recipe for WP-0079

## Completion Signal

Before completion, create:

`collaboration/work_packages/completions/WP-0079_codex_done.json`

with:

- work_package_id
- codex_status = done
- completed_at
- branch
- pull_request_url
- summary
- files_changed
- tests_run
- known_limitations
- ready_for_ca_review = true
- merge_authority = ca_verified_auto_merge_allowed

Include the final exact Steward command for running and committing validation.

## Acceptance Criteria

WP-0079 is complete when the Steward can run one short local command to validate a work package and have the validation report written as repository artifacts without pasting large terminal output into chat.

Minimum demonstration required:

1. Validate one known work package and produce Markdown and JSON reports.
2. Validate one unknown work package and produce a graceful no-recipe report.
3. Update the latest validation pointer.
4. Demonstrate the safe wrapper refuses unrelated local changes.
5. Demonstrate the wrapper stages only validation artifacts.
6. Provide the final exact command the Steward should use.

## Merge Class

Class A.

This is an operational workflow improvement. Escalate to Class B only if implementation changes validation authority, governance authority, or automatic approval behavior.
