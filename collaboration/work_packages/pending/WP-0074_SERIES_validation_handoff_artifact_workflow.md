# SERIES TASK WP-0074 — Validation Handoff Artifact Workflow

## Codex Command

Read `collaboration/work_packages/pending/WP-0074_SERIES_validation_handoff_artifact_workflow.md` and do exactly what it says.

## Mode

SERIES

## Mission

Implement a validation handoff workflow so Estate validation can be run locally, saved as structured artifacts, committed to the repository, and reviewed asynchronously without requiring the Steward to copy large terminal output back into chat.

This mirrors the Codex work package model: the complete validation contract lives in the repository, the Steward runs one short local command, and the results are written back as institutional artifacts.

## Background

Current validation requires the Steward to:

1. Receive a long PowerShell validation block in chat.
2. Paste it into a local terminal.
3. Copy long terminal output.
4. Paste the output back into chat.
5. Wait for architectural review.

This is not scalable.

The Estate already uses work package handoff contracts for Codex. Validation should follow the same institutional pattern.

The desired flow is:

1. A validation script exists in the repo.
2. The Steward pulls the latest repo.
3. The Steward runs one short command.
4. The script runs validation locally.
5. The script writes Markdown and JSON validation artifacts.
6. The script stages, commits, and optionally pushes those artifacts.
7. The reviewer reads the validation report from the repo instead of pasted terminal output.

## Scope

Create a reusable validation handoff framework.

Add:

- `operations/validation/scripts/`
- `operations/validation/reports/`
- `runtime/validation/work_packages/`

Implement a reusable validation runner capable of validating a single work package by ID.

Suggested command surfaces:

- `operations/validation/scripts/validate_work_package.ps1 -WorkPackageId WP-0058`
- `python -m estate.cli.main validate-work-package --id WP-0058 --json`

The runner should:

- run configured validation commands for the requested work package
- capture stdout, stderr, exit codes, timestamps, and command metadata
- write a Markdown report
- write a JSON report
- update a latest validation pointer
- optionally stage, commit, and push generated validation artifacts when explicitly requested by a wrapper

Add a safe convenience wrapper such as:

- `operations/validation/scripts/run_and_commit_validation.ps1 -WorkPackageId WP-0058`

This wrapper may:

- run `git pull`
- run the validation
- stage only expected validation report artifacts
- commit with a clear message
- push

The wrapper must fail safely if the working tree contains unrelated changes.

## Required Local Steward Command Pattern

The validation workflow must support this short local command pattern:

```powershell
CLS
Set-Location A:\theestate
git pull
.\operations\validation\scripts\run_and_commit_validation.ps1 -WorkPackageId WP-0058
```

After the command completes, the repository should contain reviewable artifacts such as:

- `operations/validation/reports/WP-0058_validation.md`
- `runtime/validation/work_packages/WP-0058_validation.json`
- `runtime/validation/work_packages/latest.json`

The Markdown report must be human-readable.

The JSON report must be machine-readable.

## Required JSON Report Fields

The JSON report must include:

- work_package_id
- validation_id
- generated_at
- git_branch
- git_commit_before
- git_commit_after if committed
- validation_status
- commands_run
- command_results
- stdout_summary
- stderr_summary
- files_written
- warnings
- failures
- reviewer_recommendation

Each command result must include:

- command
- started_at
- completed_at
- exit_code
- stdout_path or stdout_excerpt
- stderr_path or stderr_excerpt
- status

## Required Markdown Report Sections

The Markdown report must include:

- title
- timestamp
- work package ID
- local branch
- git commit
- summary result
- commands run
- findings
- warnings
- failures
- generated artifacts
- recommendation for Chief Architect review

## Validation Command Registry

Add a simple local registry for known work package validation command sets.

A lightweight JSON file, Python mapping, or other simple local registry is acceptable.

It should allow future work packages to declare validation steps without rewriting the runner.

Initial validation entries should include at least:

- WP-0056
- WP-0057
- WP-0058
- WP-0059
- WP-0060

If a work package has no registered validation recipe, the runner must still produce a report stating that no recipe exists. It must not crash.

## Initial Recipe Expectations

The first recipes do not need to prove every functional edge case. They should prove that the workflow can execute real Estate validation commands and record results.

Initial recipes may include commands such as:

- `python -m estate.cli.main steward-command-center --json`
- `python -m estate.cli.main assignment-queue --json`
- `python -m estate.cli.main global-search "Notification Center" --json`
- `python -m estate.cli.main global-search "Steward Recall" --json`
- `python -m estate.cli.main global-search "Resident Conversations" --json`
- `python -m estate.cli.main global-search "Interaction Services Adapter Registry" --json`
- `python -m estate.cli.main palette-command notification-center --json`
- `python -m estate.cli.main palette-command steward-recall --json`
- `python -m estate.cli.main palette-command resident-conversations --json`

Recipes should tolerate missing optional command surfaces where the work package contract did not explicitly require them, but the report must record those as findings.

## Safety Requirements

Do not commit unrelated files.

Do not stage broad paths such as the whole repository.

Do not commit source code changes produced by validation.

Do not push unless explicitly requested through the commit wrapper.

Do not hide failed commands.

Do not treat missing optional artifacts as fatal unless the validation recipe declares them required.

Do not edit `estate_ledger/ledger.md` or `development/devlog.md`.

## Git Behavior

The base runner must not automatically push.

The commit wrapper may push only if:

1. The working tree is clean or contains only expected generated validation artifacts.
2. The validation artifacts were generated successfully.
3. The staged files are limited to validation report outputs.
4. The commit message identifies the validated work package.

Suggested commit message:

`Validate WP-0058`

The wrapper must refuse to continue when unrelated modified, staged, untracked, or deleted files are present.

## CLI Integration

If consistent with existing CLI patterns, add a CLI command such as:

`python -m estate.cli.main validate-work-package --id WP-0058 --json`

This CLI command may call the same underlying validation logic.

Do not duplicate logic between PowerShell and Python if avoidable.

PowerShell may act as the local orchestration wrapper around a Python validation module.

## Tests

Add tests for:

- generating a validation report for a known work package
- graceful report generation for an unknown work package
- command result capture
- Markdown report creation
- JSON report creation
- latest pointer update
- safe handling of command failures
- refusal to commit unrelated working tree changes
- refusal to stage non-validation files

## Completion Signal

Before completion, create:

`collaboration/work_packages/completions/WP-0074_codex_done.json`

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

## Acceptance Criteria

WP-0074 is complete when the Steward can run a short local command for a work package validation and the validation output is written as repository artifacts that can be reviewed without copying terminal output into chat.

Minimum acceptable demonstration:

1. Run validation for one known work package.
2. Produce Markdown and JSON reports.
3. Update latest validation pointer.
4. Demonstrate safe no-recipe behavior for an unknown work package.
5. Demonstrate that unrelated local changes are not committed.
6. Provide the exact short command the Steward should use.

## Merge Class

Class A.

This is an operational workflow improvement. Escalate to Class B only if implementation changes governance authority, validation authority, or automatic approval behavior.
