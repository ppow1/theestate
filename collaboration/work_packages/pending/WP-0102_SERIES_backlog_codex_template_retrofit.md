# SERIES TASK WP-0102 — Backlog Codex Template Retrofit

## Codex Command
Read `collaboration/work_packages/pending/WP-0102_SERIES_backlog_codex_template_retrofit.md` and do exactly what it says.

## Mode
SERIES

## Mission
Retrofit the pending implementation backlog from WP-0086 through WP-0100 so each existing work package conforms to the approved Codex Task Template Standard without changing the original mission or pretending the work has already been implemented or validated.

This is a mechanical standardization package. It updates queued work package instructions so future Codex executions leave the evidence required by the Estate production-readiness validation loop.

## Background
Chief Architect #4 authored the Codex task template standard in:

`collaboration/work_packages/pending/WP-0101_SERIES_codex_task_template_standard.md`

That standard requires future implementation work packages to include reusable validation recipe expectations, complete Codex completion receipt requirements, production-readiness compatibility, known limitation reporting, explicit command surfaces where applicable, and clear lifecycle language.

The Steward has an intentional Codex execution backlog beginning around WP-0086. That backlog is acceptable and expected, but the queued packages must be brought up to the new template standard before Codex executes them.

This package applies the standard to existing pending work package files. It does not implement the underlying work described by those packages.

## Scope
Read the approved Codex task template standard from WP-0101 and mechanically retrofit all existing pending work package files in the WP-0086 through WP-0100 range.

Target range:

- WP-0086
- WP-0087
- WP-0088
- WP-0089
- WP-0090
- WP-0091
- WP-0092
- WP-0093
- WP-0094
- WP-0095
- WP-0096
- WP-0097
- WP-0098
- WP-0099
- WP-0100

For each existing target file, update the package to include the required template structure or clear equivalents:

- Title
- Codex Command
- Mode
- Mission
- Background
- Scope
- Out of Scope
- Required Behavior
- Safety and Authority Constraints
- Required CLI / Command Surface, if applicable
- Required Artifacts
- Tests
- Validation Recipe Requirement
- Codex Completion Receipt Requirement
- Production Readiness Requirement
- Demonstration Requirements
- Completion Signal
- Merge Class

## Out of Scope
Do not implement any work package mission in the WP-0086 through WP-0100 range.

Do not run Codex implementation for those packages.

Do not create validation recipes for the target packages unless the retrofit standard already requires only instruction text inside the pending files. The intent is to update package instructions, not to complete the work.

Do not claim that any pending package is completed, validated, operationally validated, or institutionalized.

Do not rewrite package-specific architecture, mission, or scope except where necessary to add the standard template sections.

Do not alter Chief Architect #4's validation stream semantics for reserved validation packages.

Do not edit `estate_ledger/ledger.md` or `development/devlog.md`.

## Required Behavior
For each target file:

1. Locate the current pending work package file, if it exists.
2. Preserve the original work package ID, title, mission, and core intent.
3. Add missing standard sections required by WP-0101.
4. Add explicit lifecycle language where needed: authored/pending is not implemented, validated, operationally validated, or institutionalized.
5. Add validation recipe requirements where the package is implementation work.
6. If a package is documentation-only or template-only, add explicit validation-recipe not-applicable rationale instead of leaving ambiguity.
7. Add Codex completion receipt requirements including required metadata.
8. Add production-readiness compatibility requirements.
9. Add known limitations and demonstration expectations.
10. Preserve or clarify merge class and escalation triggers.
11. Record any missing target files or reserved numbers in the WP-0102 completion artifact.

## Safety and Authority Constraints
- Do not change governance authority.
- Do not change validation authority.
- Do not automatically approve work packages.
- Do not modify `estate_ledger/ledger.md`.
- Do not modify `development/devlog.md`.
- Do not weaken Git safety behavior.
- Do not stage broad paths.
- Do not mark queued backlog work as implemented.
- Do not mark queued backlog work as validated.
- Preserve local-first operation unless explicitly authorized.
- Preserve Chief Architect #4's reserved validation stream.
- Preserve Steward bottleneck/backlog semantics from WP-0100.

## Required CLI / Command Surface
This package does not need to create a new user-facing CLI command.

If repository tooling already exists for work package inspection or validation, use it to verify the retrofit. Acceptable verification commands may include local-first commands such as:

```bash
PYTHONPATH=src python -m estate.cli.main validation-production-readiness --json
PYTHONPATH=src python -m estate.cli.main estate-search "Codex Task Template" --json
```

Use actual available commands if names differ.

## Required Artifacts
Update existing pending work package files only in the target range WP-0086 through WP-0100.

Create the completion artifact:

`collaboration/work_packages/completions/WP-0102_codex_done.json`

The completion artifact must include:

- list of files updated
- list of target work package numbers not found
- list of reserved validation packages encountered
- confirmation that original mission/scope was preserved
- confirmation that no implementation work was performed
- tests/checks run
- known limitations
- ready_for_ca_review
- merge_authority

## Tests
Run or document checks proving:

- WP-0101 template standard was read or consulted.
- Each existing target file in WP-0086 through WP-0100 now contains `## Mode`.
- Each existing target file contains a validation recipe requirement or explicit not-applicable rationale.
- Each existing target file contains a Codex completion receipt requirement.
- Each existing target file contains a production-readiness requirement.
- Each existing target file preserves its package ID and mission.
- No target package was marked complete or validated by this retrofit.

If command support exists, run relevant local validation/search checks and record results in the completion artifact.

## Validation Recipe Requirement
This package is a documentation/instruction retrofit package.

If repository validation recipes apply to documentation-only retrofit packages, add or update the validation recipe for WP-0102.

If the existing validation framework does not require recipes for documentation-only retrofit packages, explicitly record the not-applicable rationale in the completion artifact.

For implementation work packages updated by this retrofit, ensure their pending files instruct future Codex runs to add or update their own validation recipes so they do not return `no_recipe` under the production-readiness loop.

## Codex Completion Receipt Requirement
Create:

`collaboration/work_packages/completions/WP-0102_codex_done.json`

with at least:

- `work_package_id`
- `codex_status`
- `completed_at`
- `branch`
- `pull_request_url` or `pull_request_url_not_applicable_reason`
- `summary`
- `files_changed`
- `tests_run`
- `known_limitations`
- `ready_for_ca_review`
- `merge_authority`
- `validation_recipe_status`
- `production_readiness_command_status` if run
- `retrofit_target_range`
- `retrofit_files_updated`
- `retrofit_targets_missing`
- `reserved_validation_packages_preserved`

Missing receipt metadata blocks production-readiness status under the WP-0095 validation standard.

## Production Readiness Requirement
This retrofit must remain compatible with the production-readiness validation loop.

Run or document the equivalent of:

```bash
PYTHONPATH=src python -m estate.cli.main validation-production-readiness --json
```

If production readiness remains blocked because the target backlog has not been implemented or because validation recipes are intentionally future obligations, record that as an expected limitation rather than treating it as a completed readiness claim.

## Demonstration Requirements
Document exact commands run and observed status.

At minimum, provide evidence that target files were inspected and updated.

Recommended checks:

```bash
rg -n "## Mode|Validation Recipe Requirement|Codex Completion Receipt Requirement|Production Readiness Requirement" collaboration/work_packages/pending/WP-00{86,87,88,89,90,91,92,93,94,95,96,97,98,99}_*.md collaboration/work_packages/pending/WP-0100_*.md
```

Use actual shell syntax compatible with the local environment.

## Completion Signal
Create:

`collaboration/work_packages/completions/WP-0102_codex_done.json`

using the standard completion schema.

Set `ready_for_ca_review=true` only if required retrofit edits, receipt metadata, and validation/verification obligations have been satisfied or explicitly waived with reason.

## Merge Class
Class A.

Escalate only if the retrofit changes governance authority, validation authority, merge authority, automatic approval behavior, or the substantive mission of any target work package.
