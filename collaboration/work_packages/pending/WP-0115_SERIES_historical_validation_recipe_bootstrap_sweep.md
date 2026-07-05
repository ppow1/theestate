# SERIES TASK WP-0115 — Historical Validation Recipe Bootstrap Sweep

## Codex Command

Read collaboration/work_packages/pending/WP-0115_SERIES_historical_validation_recipe_bootstrap_sweep.md and do exactly what it says.

## Mode

SERIES

## Mission

Reduce the remaining historical validation backlog by adding conservative validation recipes for completed historical work packages that already have sufficient repository evidence and completion receipts.

This package follows WP-0114. WP-0114 successfully reduced incomplete receipts from 54 to 5 and increased production-ready work packages from 31 to 51. The largest remaining blocker class is now missing validation recipes. WP-0115 must attack that class directly without falsely marking pending implementation work complete.

## Background

Current verified state after WP-0114 local validation:

- total_work_packages_scanned: 101
- total_production_ready: 51
- total_blocked: 50
- total_missing_recipes: 46
- total_missing_receipts: 4
- total_incomplete_receipts: 5

WP-0114 intentionally left the remaining backlog cleaner than before. The remaining blockers include:

- many completed packages with complete receipts but no validation recipe
- a small number of missing receipts
- a small number of incomplete receipts
- a few ambiguous packages requiring human review
- genuine implementation packages that must remain blocked

This package should focus on the remaining missing-recipe class.

## Scope

In scope:

1. Run current production-readiness validation and use it as the source of truth.
2. Identify all packages that are blocked only because they have no registered validation recipe.
3. For each candidate, verify that:
   - a completion receipt exists and is complete, or can be validated as complete under the current validator;
   - repository artifacts clearly correspond to the package mission;
   - a conservative local validation surface exists.
4. Add validation recipe registrations for eligible packages.
5. Use conservative template-based validation recipes.
6. Validate every package that receives a new recipe.
7. Regenerate production-readiness and coverage artifacts.
8. Create human-readable and machine-readable reports documenting what was repaired and what was skipped.
9. Add a validation recipe for WP-0115 itself.
10. Create a WP-0115 completion receipt.

Out of scope:

- Implementing missing or pending work.
- Creating completion receipts for packages without clear completion evidence.
- Repairing ambiguous architecture receipts unless only a clearly mechanical field is missing and evidence is already present.
- Changing validation policy semantics.
- Changing production-readiness meaning.
- Changing receipt schema requirements.
- Changing Steward, Resident, Chief Architect, merge, or governance authority.
- Reopening the WP-0114 receipt-normalization sweep except where required to support recipe validation.
- Touching WP-0112 except to preserve its current validated state.

## Explicit Do-Not-Promote List

Do not mark the following packages production-ready unless they already satisfy all validation and receipt requirements without fabricated evidence:

- WP-0016
- WP-0017
- WP-0018
- WP-0056
- WP-0073
- WP-0094
- WP-0106
- WP-0107
- WP-9999

These packages must remain blocked unless the evidence is unambiguous and all production-readiness requirements are met. If uncertain, report them as skipped.

## Candidate Selection Rules

A package is eligible for a generated validation recipe only if all of the following are true:

1. It appears in the production-readiness report as blocked by `no_recipe` or missing recipe.
2. It has a completion receipt that validates as complete, or the only missing metadata can be verified from existing repository evidence without judgment.
3. The implemented artifact is discoverable in repository files.
4. The recipe can be conservative and local-first.
5. The recipe does not require live external services, network calls, UI automation, or unsafe mutation.

If any condition fails, skip the package and record the reason.

## Recipe Templates

Use the smallest safe validation recipe for each eligible package.

### Artifact Presence Recipe

For document, registry, board, dashboard, or policy packages:

- assert the expected final file exists
- assert the file contains a package-specific anchor phrase or identifier
- assert the receipt is complete

### JSON Registry Recipe

For JSON registry or manifest packages:

- assert the file exists
- parse JSON successfully
- assert expected IDs or keys exist
- assert the receipt is complete

### CLI Smoke Recipe

For packages that introduced read-only CLI commands:

- run the CLI command in JSON or safe read-only mode
- assert exit code 0
- assert expected JSON keys or text markers exist
- assert the receipt is complete

### Validation Artifact Recipe

For validation/reporting packages:

- assert reports and runtime JSON exist
- parse runtime JSON
- assert relevant status fields are present
- assert the receipt is complete

### Search/Discoverability Recipe

Where useful but non-blocking:

- use `estate-search` as observational, not required, unless discoverability was the actual package mission and the search command is stable locally.

## Required Report Artifacts

Create:

`operations/validation/backlog_burn_down/WP-0115_recipe_bootstrap_report.md`

Create machine-readable companion:

`runtime/validation/backlog_burn_down/WP-0115_recipe_bootstrap_report.json`

The report must include:

- production-readiness totals before the sweep
- production-readiness totals after the sweep
- packages considered
- packages selected for recipe generation
- packages skipped and why
- recipes added by template class
- packages successfully validated
- packages still blocked by missing recipes
- packages still blocked by missing receipts
- packages still blocked by incomplete receipts
- packages still blocked by implementation or human review
- Helen path status after the sweep
- recommended next batch

## Required Implementation Work

1. Inspect the current `src/estate/core/work_package_validation.py` recipe structure.
2. Add generated recipes in the existing style.
3. Prefer simple explicit recipe registrations over a complex generator if that is safer for maintainability.
4. If helper functions are added, keep them small and well-tested.
5. Avoid Bash-only syntax; use Python one-liners or cross-platform commands.
6. Preserve all existing passing recipes.
7. Do not remove or weaken existing validation checks.

## Required Tests

Add or update tests covering:

- representative newly added recipes are registered
- generated recipes use cross-platform checks
- no recipe is added for packages explicitly skipped for implementation/human-review reasons
- WP-0115 recipe is registered
- WP-0115 report artifacts exist and parse
- production-readiness generation still works

Run:

```bash
PYTHONPATH=src pytest tests/test_work_package_validation.py tests/test_production_readiness_validation.py -q
```

Add targeted tests if new helper modules are introduced.

## Required Validation Commands

Run or document equivalent:

```bash
PYTHONPATH=src python -m estate.cli.main validation-production-readiness --json
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0102 --json
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0105 --json
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0111 --json
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0114 --json
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0115 --json
```

Run validation for every package that receives a new recipe:

```bash
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-XXXX --json
```

## Required Outputs

Update or create as applicable:

- `src/estate/core/work_package_validation.py`
- relevant tests
- validation reports for newly repaired packages under `operations/validation/reports/`
- runtime validation JSON for newly repaired packages under `runtime/validation/work_packages/`
- `operations/validation/production_readiness_report.md`
- `runtime/validation/production_readiness_report.json`
- `operations/validation/validation_coverage_manifest.md`
- `runtime/validation/validation_coverage_manifest.json`
- `operations/validation/backlog_burn_down/WP-0115_recipe_bootstrap_report.md`
- `runtime/validation/backlog_burn_down/WP-0115_recipe_bootstrap_report.json`
- `collaboration/work_packages/completions/WP-0115_codex_done.json`

## WP-0115 Self-Validation Recipe

Add a recipe for WP-0115 that verifies:

- the human-readable recipe bootstrap report exists
- the machine-readable recipe bootstrap report exists and parses as JSON
- the report includes before and after production-readiness totals
- at least one package was considered
- skipped packages include explicit reasons
- no package from the explicit do-not-promote list was falsely marked complete by WP-0115
- WP-0102, WP-0105, WP-0111, and WP-0114 remain passing
- production-readiness validation executes successfully
- WP-0115 completion receipt is complete

Use cross-platform Python checks only.

## Completion Artifact

Create:

`collaboration/work_packages/completions/WP-0115_codex_done.json`

It must include:

- `work_package_id = WP-0115`
- `codex_status = done`
- `completed_at`
- `branch`
- `pull_request_url` or `pull_request_url_not_applicable_reason`
- `summary`
- packages considered
- packages selected
- packages skipped with reasons
- recipes added
- packages validated
- production-readiness totals before and after
- Helen path status
- files changed
- tests run
- validation commands run
- known limitations
- `ready_for_ca_review = true`
- `merge_authority = ca_verified_auto_merge_allowed`

## Acceptance Criteria

WP-0115 is complete when:

1. Eligible historical packages blocked only by missing recipes have conservative validation recipes.
2. Every newly registered recipe has been run.
3. Production-readiness totals are regenerated.
4. Missing recipe count is reduced unless no safe eligible candidates exist.
5. Existing production-ready packages remain production-ready.
6. Do-not-promote packages are not falsely marked complete.
7. Residual blockers are clearly reported.
8. WP-0115 validates itself and has a complete receipt.

## Merge Class

Class A.

Escalate only if the work requires changing validation policy semantics, receipt schema semantics, production-readiness meaning, governance authority, Steward authority, Chief Architect authority, Resident authority, or merge authority.
