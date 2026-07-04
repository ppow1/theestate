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


## WP-0102 Template Retrofit Notice

This section was added by WP-0102 as a mechanical template retrofit. It preserves the original mission and scope above. This pending package remains authored and queued; it is not implemented, validated, operationally validated, approved, or institutionalized by this retrofit.

## Out of Scope

- Do not change the original mission or core scope of WP-0091.
- Do not treat this pending package as already implemented or validated.
- Do not modify `estate_ledger/ledger.md` or `development/devlog.md` unless a future package explicitly authorizes it.
- Do not change governance authority, validation authority, merge authority, or automatic approval behavior.

## Required Behavior

- Execute the original package behavior described above when this package is later implemented.
- Preserve local-first operation unless the Steward explicitly authorizes networked behavior.
- Leave auditable evidence for every check, limitation, and generated artifact.
- Report known limitations explicitly instead of implying production readiness.

## Safety and Authority Constraints

- Do not change governance authority.
- Do not change validation authority.
- Do not automatically approve work packages.
- Do not modify `estate_ledger/ledger.md`.
- Do not modify `development/devlog.md`.
- Do not weaken Git safety behavior.
- Do not stage broad paths.
- Preserve local-first operation unless explicitly authorized.

## Required CLI / Command Surface

Use and preserve the validation command surfaces already named in this package. Do not change validation authority or reserved validation-stream semantics.

## Required Artifacts

- Implement the artifacts already specified by this pending package.
- Create `collaboration/work_packages/completions/WP-0091_codex_done.json`.
- Add or update the registered validation recipe for `WP-0091` unless this file explicitly states that the recipe is not applicable.

## Validation Recipe Requirement

Add or update the validation recipe for WP-0091. The recipe must be registered in the existing validation framework and must not return `no_recipe`. Classify checks as required or observational, use local-first non-destructive commands, and ensure future validation can evaluate this package with:

```bash
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0091 --json
PYTHONPATH=src python -m estate.cli.main validation-production-readiness --json
```

## Codex Completion Receipt Requirement

Create `collaboration/work_packages/completions/WP-0091_codex_done.json` with at least:

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
- validation recipe status or not-applicable rationale
- production readiness command status if run
- final command surfaces or Steward commands when applicable

Missing receipt metadata blocks production-readiness status under the WP-0095 validation standard.

## Production Readiness Requirement

This package must remain compatible with the production-readiness validation loop. When practical, run or document the equivalent of:

```bash
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0091 --json
PYTHONPATH=src python -m estate.cli.main validation-production-readiness --json
```

If readiness remains blocked by intentionally pending work, missing external dependencies, or a documented recipe exception, record that limitation in the completion receipt rather than claiming readiness.

## Merge Class

Class A.

Escalate only if implementation changes validation authority, governance authority, automatic approval behavior, or Git safety behavior.
