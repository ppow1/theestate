# SERIES TASK WP-0079 — Validation Project Continuation

## Codex Command

Read `collaboration/work_packages/pending/WP-0079_SERIES_validation_project_continuation.md` and do exactly what it says.

## Mode

SERIES

## Mission

Complete the Estate validation system by implementing the missing execution layer that connects validation recipes, validation execution, report generation, Git-safe publication, and Chief Architect review into a single operational workflow.

WP-0074 established the institutional validation framework.

WP-0079 reporting work established institutional validation reporting surfaces.

This continuation completes the remaining operational layer so validation becomes an Estate capability instead of a manual conversational procedure.

## Background

Current validation can produce observations, dashboards, metrics, and institutional reports.

However, validation execution still depends too heavily on manual command selection and Steward interaction. The Estate should support reusable validation recipes, one-command execution, standardized validation artifacts, repeatable review, and safe publication of results without requiring large terminal output to be copied into architectural discussions.

The current reporting layer is valuable and should not be replaced. This work package must build on it.

The missing flow is:

1. A validation recipe exists for a work package.
2. The Steward runs one short local command.
3. The Estate executes the validation recipe locally.
4. The Estate captures stdout, stderr, exit codes, timestamps, and findings.
5. The Estate writes Markdown and JSON validation artifacts.
6. The Estate updates the latest validation pointer and relevant metrics inputs.
7. An optional wrapper safely commits and pushes only validation artifacts.
8. The Chief Architect reviews the committed validation report from the repository.

## Scope

Implement the missing Validation Runner / Recipe Engine.

Add or complete:

- validation recipe registry keyed by Work Package ID
- validation runner capable of executing one work package recipe
- validation artifact generator
- Markdown report generation
- JSON report generation
- latest validation pointer
- local PowerShell runner
- safe run-and-commit PowerShell wrapper
- CLI command surface consistent with existing Estate CLI style
- integration with the validation observations, metrics dashboard, and handoff workflow

Do not redesign the existing validation dashboards.

Do not replace the existing observation system.

Do not change validation authority or automatic approval behavior.

## Required Directories

Create or use these directories as appropriate:

- `operations/validation/scripts/`
- `operations/validation/reports/`
- `runtime/validation/work_packages/`
- `runtime/validation/work_packages/stdout/` or equivalent capture location if needed
- `runtime/validation/work_packages/stderr/` or equivalent capture location if needed

## Required Command Surface

Support a short Steward command pattern.

Preferred PowerShell runner:

```powershell
CLS
Set-Location A:\theestate
git pull
.\operations\validation\scripts\validate_work_package.ps1 -WorkPackageId WP-0058
```

Preferred safe commit wrapper:

```powershell
CLS
Set-Location A:\theestate
git pull
.\operations\validation\scripts\run_and_commit_validation.ps1 -WorkPackageId WP-0058
```

If a CLI command is implemented, prefer:

```bash
python -m estate.cli.main validate-work-package --id WP-0058 --json
```

If the existing CLI naming convention requires a different name, use the closest explicit name and document it clearly in the completion record.

## Validation Recipe Registry

Create a simple local registry for validation recipes.

A JSON file, Python mapping, or other lightweight local structure is acceptable.

The registry must be easy to extend.

Each recipe should define:

- work_package_id
- recipe_id
- title
- commands
- required checks
- observational checks
- expected artifacts
- failure criteria
- success criteria
- whether to continue after a failed command

Initial recipes must include at least:

- WP-0056 — Notification Center Workspace
- WP-0057 — Voice Integration Framework
- WP-0058 — Steward Recall Operations View
- WP-0059 — Resident Conversations Workspace
- WP-0060 — Estate Interaction Services and Adapter Registry
- WP-0074 — Validation Handoff Artifact Workflow
- WP-0079 — Validation Project Continuation self-check

## Initial Recipe Expectations

Initial recipes do not need to prove every functional edge case. They should prove that the workflow can execute real Estate validation commands and record results.

Useful commands include:

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

Recipes may classify commands as required or observational.

Required command failures may fail the validation.

Observational command failures must be recorded as findings and should not automatically fail the validation unless the recipe says they are fatal.

## Validation Runner Requirements

The runner must:

- accept a work package ID
- resolve the recipe for that work package ID
- generate a graceful no-recipe report if no recipe exists
- run each configured command in order
- capture stdout
- capture stderr
- capture exit code
- capture started_at
- capture completed_at
- capture duration_seconds
- respect required vs observational command classification
- record warnings
- record failures
- record findings
- write Markdown and JSON reports
- update the latest pointer
- return an appropriate exit code for automation

The runner must not hide failed commands.

The runner must not approve a work package.

The runner must not alter governance or validation authority.

## Artifact Outputs

For work package `WP-0058`, expected outputs should include:

- `operations/validation/reports/WP-0058_validation.md`
- `runtime/validation/work_packages/WP-0058_validation.json`
- `runtime/validation/work_packages/latest.json`

Timestamped filenames are acceptable if useful, but stable latest artifacts or pointers must exist so reviewers can find the latest result without guessing filenames.

## Required JSON Report Fields

Each JSON validation report must include:

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
- `classification` such as required or observational
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

The Markdown report must be readable enough for Chief Architect review without requiring raw terminal output.

## Latest Validation Pointer

Maintain:

- `runtime/validation/work_packages/latest.json`

The latest pointer must identify:

- latest work package ID
- latest validation report path
- latest Markdown report path
- latest JSON report path
- generated_at
- validation_status

## Integration Requirements

Integrate with existing validation surfaces where practical:

- `validation-observations`
- `validation-metrics-dashboard`
- `validation-handoff-artifact-workflow`
- `operational-validation`
- existing validation Markdown outputs under `operations/validation/`
- existing validation runtime JSON under `runtime/validation/`

Do not duplicate existing dashboard logic unnecessarily.

Do not replace the existing handoff packet.

The runner should feed the reporting layer rather than bypass it.

## Safe Git Wrapper Requirements

Provide a wrapper that can run validation and safely publish validation artifacts.

The wrapper must:

1. inspect the working tree before running
2. refuse to continue if unrelated local changes are present
3. run validation
4. stage only expected validation artifacts
5. commit only validation artifacts
6. push only when explicitly invoked through the wrapper
7. clearly report when there is nothing to commit

The wrapper must never use:

```bash
git add .
```

The wrapper may stage only paths like:

- `operations/validation/reports/<work_package>_validation*.md`
- `runtime/validation/work_packages/<work_package>_validation*.json`
- `runtime/validation/work_packages/latest.json`
- documented stdout/stderr capture files under validation runtime directories

The wrapper must refuse unrelated modified, staged, untracked, deleted, or conflicted files.

## Safety Requirements

Do not commit unrelated files.

Do not stage broad paths.

Do not commit source code changes produced by validation.

Do not push from the base validator.

Only the explicit run-and-commit wrapper may commit or push.

Do not hide failed commands.

Do not treat missing optional artifacts as fatal unless the recipe declares them required.

Do not edit:

- `estate_ledger/ledger.md`
- `development/devlog.md`

Do not change validation authority.

Do not automatically approve work packages.

## Tests

Add tests for:

- known work package recipe execution
- unknown work package graceful no-recipe report
- command result capture
- required vs observational command handling
- Markdown report generation
- JSON report generation
- latest pointer update
- safe handling of failed commands
- refusal to commit unrelated modified files
- refusal to stage non-validation files
- no broad staging behavior
- WP-0079 self-check recipe

## Demonstration Requirements

Before completion, demonstrate:

1. validation of one known work package
2. graceful no-recipe handling for one unknown work package
3. generation of Markdown report
4. generation of JSON report
5. update of latest pointer
6. safe wrapper refusal when unrelated changes are present, or a test proving that behavior
7. final exact command the Steward should use

## Completion Signal

Before completion, create:

`collaboration/work_packages/completions/WP-0079_codex_done.json`

using the standard completion schema.

Include:

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
- final Steward validation command

## Acceptance Criteria

WP-0079 is complete when the Steward can execute a single validation command against a work package and the Estate automatically:

1. Executes the validation recipe.
2. Produces Markdown and JSON reports.
3. Updates the latest validation pointer.
4. Records warnings, findings, and failures.
5. Optionally commits only validation artifacts through the explicit safe wrapper.
6. Produces review-ready artifacts without requiring terminal output to be copied into architectural discussion.

## Merge Class

Class A.

Escalate only if implementation changes validation authority, governance authority, or automatic approval behavior.
