# SERIES TASK WP-0086 — Validation Continuation #3: Recipe Expansion

## Codex Command

Read `collaboration/work_packages/pending/WP-0086_SERIES_validation_recipe_expansion.md` and do exactly what it says.

## Mode

SERIES

## Mission

Expand the Estate validation recipe registry so the validation runner created by WP-0079 can validate the next merged work packages instead of producing only `no_recipe` reports.

This work package exists because WP-0079 successfully implemented the validation runner, report generation, latest pointer, and safe commit wrapper, but follow-on validation of WP-0075 and WP-0076 produced `validation_status = no_recipe` because no recipes were registered for those work packages.

WP-0086 must make the pending Codex validation commands function for the next validation pass.

## Background

The current validation runner lives in the Estate validation subsystem and supports recipe-based execution.

Current known recipe coverage includes at least:

- WP-0056
- WP-0057
- WP-0058
- WP-0059
- WP-0060
- WP-0074
- WP-0079

The immediate gap is recipe coverage for:

- WP-0075 — Operational Readiness Dashboard
- WP-0076 — Estate Capability Registry

The Steward and Chief Architect need to continue validation using short local commands such as:

```powershell
.\operations\validation\scripts\validate_work_package.ps1 -WorkPackageId WP-0075
.\operations\validation\scripts\validate_work_package.ps1 -WorkPackageId WP-0076
```

After WP-0086, those commands must execute real validation commands instead of generating `no_recipe` reports.

## Scope

Implement validation recipe expansion only.

Add or update recipes for:

- WP-0075 — Operational Readiness Dashboard
- WP-0076 — Estate Capability Registry
- WP-0086 — Validation Continuation #3 self-check

Do not redesign the validation runner.

Do not redesign the validation report schema.

Do not replace the safe commit wrapper.

Do not create a new validation institution.

## Required Recipe: WP-0075

Create a recipe for:

`WP-0075 — Operational Readiness Dashboard`

The recipe should validate that the operational readiness dashboard can be generated and that its adjacent operational inputs are reachable.

Recommended commands:

```bash
python -m estate.cli.main operational-validation --json
python -m estate.cli.main estate-health --json
python -m estate.cli.main service-readiness --json
python -m estate.cli.main validation-metrics-dashboard --json
```

If any command name differs from the implemented CLI surface, use the actual existing command and document the substitution in the recipe or completion record.

At least one command must be required.

Optional adjacent checks may be observational if they are not part of the exact WP-0075 contract.

The recipe must not return `no_recipe`.

## Required Recipe: WP-0076

Create a recipe for:

`WP-0076 — Estate Capability Registry`

The recipe should validate that the Estate capability registry can be queried and that its service/capability surfaces remain reachable.

Recommended commands:

```bash
python -m estate.cli.main capabilities --json
python -m estate.cli.main services --json
python -m estate.cli.main capability-lifecycle --json
python -m estate.cli.main capability-help --json
```

If the capability registry has a more direct command after WP-0076, use it as a required command.

If any recommended command is only adjacent rather than authoritative, classify it as observational.

The recipe must not return `no_recipe`.

## Required Recipe: WP-0086 Self-Check

Create a self-check recipe for:

`WP-0086 — Validation Continuation #3: Recipe Expansion`

The self-check recipe must confirm that recipe expansion is visible through the validation runner.

Recommended commands:

```bash
python -m estate.cli.main validate-work-package --id WP-0075 --json
python -m estate.cli.main validate-work-package --id WP-0076 --json
```

If the CLI command is not available and the PowerShell runner is the canonical interface, use Python-level or runner-level equivalent checks that prove WP-0075 and WP-0076 recipes are registered and executable.

The self-check must be realistic and must not depend on manual copy/paste output.

## Runner Compatibility

Keep compatibility with the existing runner scripts:

```powershell
.\operations\validation\scripts\validate_work_package.ps1 -WorkPackageId WP-0075
.\operations\validation\scripts\validate_work_package.ps1 -WorkPackageId WP-0076
.\operations\validation\scripts\validate_work_package.ps1 -WorkPackageId WP-0086
```

If the runner implementation does not support WP-0086 self-check execution directly, extend it cleanly without breaking existing recipes.

## Report Expectations

After implementation, these files should be generatable locally:

- `operations/validation/reports/WP-0075_validation.md`
- `operations/validation/reports/WP-0076_validation.md`
- `operations/validation/reports/WP-0086_validation.md`
- `runtime/validation/work_packages/WP-0075_validation.json`
- `runtime/validation/work_packages/WP-0076_validation.json`
- `runtime/validation/work_packages/WP-0086_validation.json`
- `runtime/validation/work_packages/latest.json`

The JSON reports for WP-0075 and WP-0076 must include non-empty `commands_run` and non-empty `command_results`.

The JSON reports for WP-0075 and WP-0076 must not have `validation_status = no_recipe`.

## Safe Commit Wrapper

Do not weaken safe Git behavior.

The existing safe commit wrapper must continue to:

- refuse unrelated local changes
- stage only validation artifacts
- avoid `git add .`
- avoid staging source code unless the work package implementation itself is being committed by Codex on its implementation branch
- push only when explicitly configured or invoked that way

## Tests

Add or update tests to prove:

- WP-0075 recipe exists
- WP-0076 recipe exists
- WP-0086 recipe exists
- WP-0075 validation report is not `no_recipe`
- WP-0076 validation report is not `no_recipe`
- WP-0075 commands are captured
- WP-0076 commands are captured
- existing recipes remain registered
- unknown work package still produces graceful `no_recipe`
- safe wrapper behavior is not weakened

Existing WP-0079 tests must continue to pass.

## Demonstration Requirements

Before completion, run or document the equivalent of:

```powershell
.\operations\validation\scripts\validate_work_package.ps1 -WorkPackageId WP-0075
.\operations\validation\scripts\validate_work_package.ps1 -WorkPackageId WP-0076
.\operations\validation\scripts\validate_work_package.ps1 -WorkPackageId WP-0086
```

The completion record must identify the resulting validation statuses.

## Completion Signal

Create:

`collaboration/work_packages/completions/WP-0086_codex_done.json`

using the standard completion schema.

Include:

- `work_package_id`
- `codex_status = done`
- `completed_at`
- `branch`
- `pull_request_url`
- `summary`
- `files_changed`
- `tests_run`
- `known_limitations`
- `ready_for_ca_review = true`
- `merge_authority = ca_verified_auto_merge_allowed`
- exact validation commands the Steward should run next
- validation statuses observed for WP-0075, WP-0076, and WP-0086 if generated during implementation

## Acceptance Criteria

WP-0086 is complete when:

1. WP-0075 has a registered validation recipe.
2. WP-0076 has a registered validation recipe.
3. WP-0086 has a registered self-check recipe.
4. Running the validator for WP-0075 executes commands instead of returning `no_recipe`.
5. Running the validator for WP-0076 executes commands instead of returning `no_recipe`.
6. Reports and runtime JSON are generated for WP-0075 and WP-0076.
7. Existing validation runner behavior remains intact.
8. Unknown work packages still produce graceful `no_recipe` reports.
9. The safe commit wrapper remains Git-safe.

## Merge Class

Class A.

Escalate only if implementation changes validation authority, governance authority, automatic approval behavior, or Git safety behavior.
