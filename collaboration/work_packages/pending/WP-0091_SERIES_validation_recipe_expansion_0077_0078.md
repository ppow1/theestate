# SERIES TASK WP-0091 — Validation Continuation #4: Add Validation Recipes for WP-0077 and WP-0078

## Codex Command

Read `collaboration/work_packages/pending/WP-0091_SERIES_validation_recipe_expansion_0077_0078.md` and do exactly what it says.

## Mode

SERIES

## Mission

Expand the Estate validation recipe registry so the validation runner can validate WP-0077 and WP-0078 instead of producing `validation_status = no_recipe` reports.

WP-0079 created the validation runner.

WP-0086 expanded recipe coverage for WP-0075, WP-0076, and WP-0086.

This work package continues the validation project by adding recipe coverage for the next merged capability work packages:

- WP-0077 — Capability Dependency Visualization and Mission Control integration
- WP-0078 — Capability Gap Report and planned-evidence handling refinement

## Background

The Steward ran the validation runner against WP-0077 and WP-0078 after WP-0086 was merged.

Both work packages generated reviewable reports, but both returned:

```text
validation_status = no_recipe
```

This means the validation runner is functioning correctly, but the recipe registry lacks coverage for those work packages.

After WP-0091, these commands must execute real validation recipes:

```powershell
.\operations\validation\scripts\validate_work_package.ps1 -WorkPackageId WP-0077
.\operations\validation\scripts\validate_work_package.ps1 -WorkPackageId WP-0078
.\operations\validation\scripts\validate_work_package.ps1 -WorkPackageId WP-0091
```

## Scope

Implement recipe expansion only.

Add or update validation recipes for:

- WP-0077
- WP-0078
- WP-0091 self-check

Do not redesign the validation runner.

Do not redesign the validation report schema.

Do not weaken the safe Git wrapper.

Do not create a new validation subsystem.

Do not change validation authority or work-package approval behavior.

## Required Recipe: WP-0077

Create a recipe for:

`WP-0077 — Capability Dependency Visualization and Mission Control integration`

The recipe should validate that capability dependency visualization can be generated and that its Mission Control / Steward Command Center integration surfaces remain reachable.

Recommended commands:

```bash
python -m estate.cli.main capability-dependency-visualization --json
python -m estate.cli.main estate-capability-registry --json
python -m estate.cli.main steward-command-center --json
python -m estate.cli.main estate-search "Capability Dependency" --json
python -m estate.cli.main global-search "Capability Dependency" --json
```

If any command name differs from the implemented CLI surface, use the actual existing command and document the substitution in the completion record.

At least one command must be required.

Recommended classification:

- `capability-dependency-visualization --json` should be required.
- `estate-capability-registry --json` should be required or observational depending on implementation dependency.
- Mission Control / Steward Command Center visibility checks may be observational if they are adjacent integration evidence.
- Search checks may be observational if search index freshness can vary.

The recipe must not return `no_recipe`.

## Required Recipe: WP-0078

Create a recipe for:

`WP-0078 — Capability Gap Report and planned-evidence handling refinement`

The recipe should validate that the Capability Gap Report can be generated and that its planned-only evidence handling is represented in generated outputs.

Recommended commands:

```bash
python -m estate.cli.main capability-gap-report --json
python -m estate.cli.main estate-capability-registry --json
python -m estate.cli.main capability-dependency-visualization --json
python -m estate.cli.main steward-command-center --json
python -m estate.cli.main global-search "Capability Gap" --json
```

If any command name differs from the implemented CLI surface, use the actual existing command and document the substitution in the completion record.

At least one command must be required.

Recommended classification:

- `capability-gap-report --json` should be required.
- `estate-capability-registry --json` should be required or observational depending on implementation dependency.
- dependency visualization, Steward Command Center, and search checks may be observational.

The recipe must not return `no_recipe`.

## Required Recipe: WP-0091 Self-Check

Create a self-check recipe for:

`WP-0091 — Validation Continuation #4: Add validation recipes for WP-0077 and WP-0078`

The self-check must confirm the new recipes are registered and executable through the validation runner.

Recommended commands:

```bash
python -m estate.cli.main validate-work-package --id WP-0077 --json
python -m estate.cli.main validate-work-package --id WP-0078 --json
```

Both commands should be required.

The self-check must not depend on manual copy/paste output.

The WP-0091 recipe must not return `no_recipe`.

## Runner Compatibility

Keep compatibility with the existing runner scripts:

```powershell
.\operations\validation\scripts\validate_work_package.ps1 -WorkPackageId WP-0077
.\operations\validation\scripts\validate_work_package.ps1 -WorkPackageId WP-0078
.\operations\validation\scripts\validate_work_package.ps1 -WorkPackageId WP-0091
```

Do not break existing recipe coverage for:

- WP-0056
- WP-0057
- WP-0058
- WP-0059
- WP-0060
- WP-0074
- WP-0075
- WP-0076
- WP-0079
- WP-0086

Unknown work packages must still produce graceful `no_recipe` reports.

## Report Expectations

After implementation, these files should be generatable locally:

- `operations/validation/reports/WP-0077_validation.md`
- `operations/validation/reports/WP-0078_validation.md`
- `operations/validation/reports/WP-0091_validation.md`
- `runtime/validation/work_packages/WP-0077_validation.json`
- `runtime/validation/work_packages/WP-0078_validation.json`
- `runtime/validation/work_packages/WP-0091_validation.json`
- `runtime/validation/work_packages/latest.json`

The JSON reports for WP-0077 and WP-0078 must include non-empty `commands_run` and non-empty `command_results`.

The JSON reports for WP-0077 and WP-0078 must not have `validation_status = no_recipe`.

## Safe Git Wrapper

Do not weaken safe Git behavior.

The existing safe commit wrapper must continue to:

- refuse unrelated local changes
- stage only validation artifacts
- avoid `git add .`
- avoid staging unrelated source or operational files when publishing validation reports
- push only when explicitly configured or invoked that way

## Tests

Add or update tests to prove:

- WP-0077 recipe exists
- WP-0078 recipe exists
- WP-0091 recipe exists
- WP-0077 validation report is not `no_recipe`
- WP-0078 validation report is not `no_recipe`
- WP-0077 commands are captured
- WP-0078 commands are captured
- WP-0091 self-check calls WP-0077 and WP-0078 validation through the runner
- existing recipes remain registered
- unknown work packages still produce graceful `no_recipe`
- safe wrapper behavior is not weakened

Existing validation tests must continue to pass.

## Demonstration Requirements

Before completion, run or document the equivalent of:

```powershell
.\operations\validation\scripts\validate_work_package.ps1 -WorkPackageId WP-0077
.\operations\validation\scripts\validate_work_package.ps1 -WorkPackageId WP-0078
.\operations\validation\scripts\validate_work_package.ps1 -WorkPackageId WP-0091
```

The completion record must identify the resulting validation statuses.

## Completion Signal

Create:

`collaboration/work_packages/completions/WP-0091_codex_done.json`

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
- validation statuses observed for WP-0077, WP-0078, and WP-0091 if generated during implementation

## Acceptance Criteria

WP-0091 is complete when:

1. WP-0077 has a registered validation recipe.
2. WP-0078 has a registered validation recipe.
3. WP-0091 has a registered self-check recipe.
4. Running the validator for WP-0077 executes commands instead of returning `no_recipe`.
5. Running the validator for WP-0078 executes commands instead of returning `no_recipe`.
6. Reports and runtime JSON are generated for WP-0077 and WP-0078.
7. Existing validation runner behavior remains intact.
8. Unknown work packages still produce graceful `no_recipe` reports.
9. The safe commit wrapper remains Git-safe.

## Merge Class

Class A.

Escalate only if implementation changes validation authority, governance authority, automatic approval behavior, or Git safety behavior.
