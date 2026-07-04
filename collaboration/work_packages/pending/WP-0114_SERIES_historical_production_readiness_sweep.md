# SERIES TASK WP-0114 — Historical Production-Readiness Sweep

## Codex Command

Read collaboration/work_packages/pending/WP-0114_SERIES_historical_production_readiness_sweep.md and do exactly what it says.

## Mode

SERIES

## Mission

Perform a broad but controlled historical production-readiness sweep to resolve the majority of remaining validation blockers through mechanical recipe generation, receipt normalization, validation execution, and production-readiness regeneration.

This package is intended to replace many small one-off validation repair loops with one auditable pass across mechanically repairable historical work packages.

The goal is to reduce the remaining blocked count substantially while preserving the distinction between:

- completed work that only needs validation/receipt closure
- genuinely pending implementation work
- packages requiring human architectural judgment

## Background

The validation framework is now operational. Recent validation work established:

- WP-0101 standardized the Codex task template.
- WP-0102 retrofitted pending backlog packages to the new task standard and is production-ready.
- WP-0103 repaired historical validation recipe coverage for selected completed packages and is production-ready.
- WP-0105 repaired validation closure defects and is production-ready.
- WP-0111 selected the first Helen-readiness burn-down batch and validated WP-0020.
- WP-0113 repaired WP-0111 self-validation and produced Helen next-batch recommendations.

The remaining backlog is now mostly historical production-readiness debt:

- missing validation recipes
- missing completion receipts
- incomplete completion receipts
- packages with registered recipes but stale or missing validation runs
- genuinely pending implementation packages that should not be marked complete

The Steward has requested a faster path that combines:

1. historical coverage sweep
2. auto-generated validation recipes
3. receipt normalization
4. enforcing the current completion pattern going forward

Parallel execution is out of scope for this package.

## Scope

In scope:

1. Run current production-readiness validation and use it as the source of truth for blockers.
2. Classify every scanned work package into clear categories:
   - already production-ready
   - missing recipe but implementation appears complete
   - incomplete receipt but implementation appears complete
   - missing receipt but implementation appears complete
   - registered recipe but stale/missing validation report
   - failing validation
   - genuinely pending or unimplemented
   - requires human architectural judgment
3. Mechanically repair completion receipts where the missing fields can be filled from existing repository evidence without fabrication.
4. Create conservative completion receipts only when repository evidence clearly proves the work was completed/merged and no receipt exists.
5. Add generated validation recipes for packages where safe local validation surfaces exist.
6. Prefer reusable recipe templates for documentation/artifact-only packages, registry/report packages, CLI-command packages, and validation/reporting packages.
7. Run validation for every package repaired in this sweep.
8. Regenerate production-readiness and coverage artifacts.
9. Produce a sweep report listing repaired packages, unresolved packages, and next recommended batches.
10. Add a validation recipe for WP-0114 itself.
11. Create a WP-0114 completion receipt.

Out of scope:

- Implementing pending packages.
- Marking pending packages complete without implementation evidence.
- Broadly changing validation policy semantics.
- Broadly changing receipt schema requirements.
- Changing governance, Steward authority, Chief Architect authority, Resident authority, merge authority, or production-readiness meaning.
- Rewriting work package missions.
- Changing WP-0112, which is reserved for Parallel Workstream Isolation and Install Handoff.
- Changing WP-0106 through WP-0110 implementation behavior unless only receipt/recipe validation closure is being documented as still pending.

## Required Safety Rules

Do not fabricate completion evidence.

Do not create a completion receipt for a package unless at least one of these is true:

- a completion artifact already exists and only needs metadata normalization
- repository implementation artifacts clearly correspond to the package mission
- a merged PR, local completion file, or generated validation artifact already documents completion
- the package is documentation-only and the expected final document exists in the repository

If evidence is ambiguous, classify the package as `requires_human_review` or `pending_implementation_evidence`.

Do not treat a pending work package as production-ready just because its pending file exists.

## Recipe Generation Strategy

Generate or register validation recipes using conservative local-first patterns.

Acceptable recipe templates include:

### Artifact Presence Recipe

For documentation-only or registry/report packages, validate that required files exist and include package-specific anchor text.

### CLI Smoke Recipe

For packages that introduced read-only CLI commands, run the command with `--json` or a read-only mode and require exit code 0.

### Registry Consistency Recipe

For packages that introduced registry entries, validate that registry JSON or Markdown exists, parses if applicable, and contains the expected identifier.

### Report Generation Recipe

For packages that introduced generated reports or dashboards, run the report generator in read-only/safe mode if available, or validate existing report artifacts if generation would be destructive.

### Validation Framework Recipe

For validation/reporting packages, run existing validation commands and ensure they do not return `no_recipe` or fail.

### Documentation-Only Not-Applicable Handling

If a work package truly has no executable validation surface, create the smallest safe recipe that validates the final artifact exists and is discoverable. Do not invent operational behavior.

## Receipt Normalization Strategy

For incomplete receipts, add only missing required metadata that can be supported by local repository evidence.

Common fields to normalize:

- `work_package_id`
- `codex_status`
- `completed_at`
- `branch`
- `summary`
- `files_changed`
- `tests_run`
- `known_limitations`
- `ready_for_ca_review`
- `merge_authority` or equivalent
- `pull_request_url` or `pull_request_url_not_applicable_reason`

If live PR metadata is unavailable and the local-first standard permits it, use a clear not-applicable reason such as:

`Live PR metadata unavailable in local-first historical validation; completion evidence derived from repository artifacts.`

Do not overwrite useful existing receipt content. Preserve existing evidence, limitations, and notes.

## Required Classification Report

Create:

`operations/validation/backlog_burn_down/WP-0114_historical_sweep_report.md`

Create machine-readable companion:

`runtime/validation/backlog_burn_down/WP-0114_historical_sweep_report.json`

The reports must include:

- production-readiness totals before sweep
- production-readiness totals after sweep
- packages already ready before the sweep
- packages repaired by recipe addition
- packages repaired by receipt normalization
- packages repaired by both recipe and receipt work
- packages validated during the sweep
- packages still blocked by missing implementation
- packages still blocked by ambiguous evidence
- packages still blocked by failing validation
- packages still blocked by policy/human review
- packages intentionally not touched and why
- recommended next work package batch after the sweep
- Helen path status after the sweep

## Target Priority

Prioritize mechanically repairable historical packages first, then Helen-path-adjacent packages only where the work is already complete.

Suggested order:

1. Packages with registered recipes and complete receipts but missing/stale validation reports.
2. Packages with registered recipes and incomplete receipts requiring only metadata normalization.
3. Packages with obvious artifact-only validation surfaces.
4. Packages with simple read-only CLI smoke checks.
5. Packages with missing receipts but strong completion evidence.
6. Ambiguous packages, which should be reported but not repaired automatically.
7. Pending implementation packages, which should be left blocked.

## Required Tests

Add or update tests for:

- any recipe-generation helper logic added
- representative generated recipes
- receipt normalization behavior
- no receipt is created for known pending packages without completion evidence
- WP-0114 recipe registration
- production-readiness report generation after the sweep

Run existing validation tests:

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
```

Run validation for every package repaired by this sweep:

```bash
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-XXXX --json
```

## Required Outputs

Update or create as applicable:

- `src/estate/core/work_package_validation.py`
- optional helper modules if needed for generated recipes or receipt normalization
- relevant tests
- repaired completion receipts under `collaboration/work_packages/completions/`
- validation reports for repaired packages under `operations/validation/reports/`
- runtime validation JSON for repaired packages under `runtime/validation/work_packages/`
- `operations/validation/production_readiness_report.md`
- `runtime/validation/production_readiness_report.json`
- `operations/validation/validation_coverage_manifest.md`
- `runtime/validation/validation_coverage_manifest.json`
- `operations/validation/backlog_burn_down/WP-0114_historical_sweep_report.md`
- `runtime/validation/backlog_burn_down/WP-0114_historical_sweep_report.json`
- `collaboration/work_packages/completions/WP-0114_codex_done.json`

Do not broad-stage unrelated generated artifacts. Include only artifacts required by this sweep.

## WP-0114 Self-Validation Recipe

Add a recipe for WP-0114 that verifies:

- the human-readable sweep report exists
- the machine-readable sweep report exists and parses as JSON
- the sweep report includes before and after production-readiness totals
- at least one package was classified or repaired, unless no eligible packages existed
- no known pending implementation package was falsely marked complete
- production-readiness validation executes successfully
- WP-0102, WP-0105, and WP-0111 remain passing
- WP-0114 completion receipt is complete

Use cross-platform Python checks only. Avoid Bash-specific loops.

## Completion Artifact

Create:

`collaboration/work_packages/completions/WP-0114_codex_done.json`

It must include:

- `work_package_id = WP-0114`
- `codex_status = done`
- `completed_at`
- `branch`
- `pull_request_url` or `pull_request_url_not_applicable_reason`
- `summary`
- packages scanned
- packages repaired
- packages validated
- packages left blocked by category
- Helen path status
- files changed
- tests run
- validation commands run
- production-readiness totals before and after
- known limitations
- `ready_for_ca_review = true`
- `merge_authority = ca_verified_auto_merge_allowed`

## Acceptance Criteria

WP-0114 is complete when:

1. The production-readiness backlog has been classified from current repository artifacts.
2. Mechanically repairable receipts have been normalized without fabricating evidence.
3. Safe validation recipes have been added for mechanically repairable packages.
4. Repaired packages have been validated.
5. Production-readiness totals are regenerated.
6. A clear residual blocker report exists.
7. WP-0102, WP-0105, and WP-0111 remain passing.
8. WP-0114 has its own validation recipe and complete receipt.
9. Pending implementation packages are not falsely marked complete.
10. The Chief Architect can use the sweep report to decide the next implementation or repair batch.

## Merge Class

Class A.

Escalate only if the work requires changing validation policy semantics, receipt schema semantics, production-readiness meaning, governance authority, Steward authority, Chief Architect authority, Resident authority, or merge authority.
