# SERIES TASK WP-0103 — Historical Validation Recipe Coverage Through WP-0085

## Codex Command

Read `collaboration/work_packages/pending/WP-0103_SERIES_historical_validation_recipe_coverage_through_0085.md` and do exactly what it says.

## Mode

SERIES

## Mission

Close the historical validation recipe gap for completed and merged work packages through WP-0085.

This package uses the WP-0095 production-readiness validation loop and coverage manifest to add missing validation recipes for historical completed work packages. It does not redesign the validation system.

WP-0101 defines the future Codex task template standard.

WP-0102 retrofits pending backlog work packages WP-0086 through WP-0100 to that template.

WP-0103 covers the separate historical gap: completed/merged work packages up through WP-0085 that predate the new template and therefore often lack reusable validation recipes.

## Background

The WP-0095 production-readiness report established that the validation mechanism is operational, but many historical work packages are blocked by missing validation recipes, incomplete receipts, or missing receipts.

The Steward has clarified the boundary for this package:

- WP-0085 is the last completed/merged historical work package in scope.
- WP-0086 and later are pending/backlog standardization territory and are not part of this package.
- WP-0102 is responsible for pending work packages WP-0086 through WP-0100.

Therefore WP-0103 must focus on historical completed/merged work packages through WP-0085.

## Scope

Use repository artifacts, not chat memory, to identify work packages through WP-0085 that need validation recipe coverage.

At minimum, inspect:

- `runtime/validation/production_readiness_report.json`
- `runtime/validation/validation_coverage_manifest.json`
- `operations/validation/production_readiness_report.md`
- `operations/validation/validation_coverage_manifest.md`
- `collaboration/work_packages/completions/`
- `collaboration/work_packages/pending/`
- existing validation recipes in `src/estate/core/work_package_validation.py`

For work packages through WP-0085 that are completed/merged and have `recipe_status = missing`, add validation recipes where safe, local, and non-destructive validation is possible.

Prioritize:

1. completed work packages with complete receipts and missing recipes
2. completed work packages with incomplete receipts but obvious local validation surfaces
3. documentation-only or architecture-only packages where explicit recipe-not-applicable handling is appropriate
4. packages requiring receipt repair but not recipe work, which should be reported rather than silently altered unless safe and mechanical

## Explicit Boundary

In scope:

- WP-0001 through WP-0085, where repository artifacts show the work package is completed/merged or has a completion artifact.
- Missing validation recipes for historical completed work.
- Safe, local, non-destructive validation checks.
- Updated production-readiness artifacts after recipe additions.

Out of scope:

- WP-0086 and later pending backlog packages.
- Any implementation changes to the historical work packages themselves.
- Redesigning the validation framework.
- Rewriting the Codex task template standard.
- Retrofitting pending backlog files; WP-0102 owns that.
- Changing governance, validation authority, merge authority, or approval authority.
- Broad receipt rewriting unless explicitly safe and mechanical.

## Required Approach

Work from the WP-0095 manifest.

Do not guess the backlog from memory.

Create a clear list of in-scope historical work packages with missing recipes.

For each candidate, classify it as one of:

- `recipe_added`
- `already_has_recipe`
- `not_applicable_documentation_only`
- `requires_receipt_repair_before_recipe`
- `unsafe_or_destructive_to_validate_locally`
- `deferred_with_reason`

Add recipes in controlled batches rather than broad speculative coverage.

If there are many missing recipes, prioritize enough to materially improve production readiness while keeping the change reviewable. The completion artifact must clearly list any remaining historical gaps.

## Validation Recipe Requirements

Every added recipe must:

- be registered in the existing validation framework
- not return `no_recipe`
- use local-first commands
- avoid destructive commands
- classify checks as required or observational
- capture stdout/stderr through the existing runner
- produce normal Markdown and JSON validation artifacts
- integrate with the WP-0095 production-readiness report

Prefer CLI checks already exposed by the Estate.

Examples of acceptable validation surfaces include:

- `python -m estate.cli.main <command> --json`
- `python -m estate.cli.main estate-search "<term>" --json`
- `python -m estate.cli.main global-search "<term>" --json`
- `python -m estate.cli.main validate-work-package --id <WP-ID> --json`
- read-only report generators
- read-only dashboard generators

Do not use validation commands that create real people, alter operational state, send messages, start long-running services, or commit changes unless the work package explicitly authorizes it and the command is safe in dry-run mode.

## Receipt Handling

WP-0103 may identify incomplete or missing receipts, but it should not perform broad historical receipt rewriting unless the fix is narrow, factual, and directly supported by repository artifacts.

If receipt repair is needed, report it in the completion artifact as a remaining blocker.

If a completion artifact is complete enough for WP-0095, do not change it.

If a completion artifact is missing only a local-first not-applicable explanation for live PR metadata and the correct value is evident from local artifacts, Codex may add a narrow repair only if safe and documented.

## Documentation-Only / Architecture-Only Handling

Some historical work packages may not have an executable validation surface.

For these, do not invent artificial recipes.

Instead, add explicit not-applicable handling only if the validation framework supports it, or document the reason in the completion artifact for this package.

If the validation framework does not support recipe-not-applicable status, do not redesign it here unless the change is small and consistent with WP-0095. Otherwise, list those packages as deferred with reason.

## Required Outputs

At completion, update or create as applicable:

- validation recipe registrations in `src/estate/core/work_package_validation.py`
- relevant tests for recipe registration and execution behavior
- updated validation reports for newly covered historical work packages
- updated `runtime/validation/work_packages/*.json` for newly validated packages
- updated `operations/validation/validation_coverage_manifest.md`
- updated `runtime/validation/validation_coverage_manifest.json`
- updated `operations/validation/production_readiness_report.md`
- updated `runtime/validation/production_readiness_report.json`
- completion artifact `collaboration/work_packages/completions/WP-0103_codex_done.json`

Do not broad-stage unrelated generated artifacts.

## WP-0103 Self-Check Recipe

Add a validation recipe for WP-0103 itself.

Recommended required checks:

```bash
python -m estate.cli.main validation-production-readiness --json
python -m estate.cli.main validate-work-package --id WP-0103 --json
```

If self-recursion is not appropriate in the current runner design, use a non-recursive check proving the WP-0103 recipe exists and that selected newly covered historical recipes no longer return `no_recipe`.

The WP-0103 recipe must not return `no_recipe`.

## Required Tests

Add or update tests for:

- recipe registration for each newly covered WP
- recipe execution for representative newly covered WPs
- preservation of existing recipes
- WP-0103 recipe registration
- production-readiness manifest reflects improved recipe coverage
- no regression to WP-0095 production-readiness command

Run the existing validation tests that cover the recipe registry.

Recommended:

```bash
PYTHONPATH=src pytest tests/test_work_package_validation.py tests/test_production_readiness_validation.py -q
```

Run broader tests if practical.

## Demonstration Requirements

Before completion, run or document equivalent commands:

```bash
PYTHONPATH=src python -m estate.cli.main validation-production-readiness --json
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0103 --json
```

Also run representative validations for newly covered historical packages.

The completion artifact must record:

- historical work packages scanned
- work packages already covered
- recipes added
- packages marked not applicable or deferred
- packages still blocked by receipt gaps
- tests run
- production-readiness status before/after if available
- known limitations

## Completion Signal

Create:

`collaboration/work_packages/completions/WP-0103_codex_done.json`

using the standard completion schema from WP-0101.

Include at least:

- `work_package_id`
- `codex_status = done`
- `completed_at`
- `branch`
- `pull_request_url` or `pull_request_url_not_applicable_reason`
- `summary`
- `files_changed`
- `tests_run`
- `known_limitations`
- `ready_for_ca_review = true`
- `merge_authority = ca_verified_auto_merge_allowed`
- list of recipes added
- list of packages deferred with reasons
- production-readiness command status
- WP-0103 validation status

## Acceptance Criteria

WP-0103 is complete when:

1. Historical completed/merged work packages through WP-0085 have been assessed from repository artifacts.
2. Safe validation recipes have been added for in-scope historical WPs where practical.
3. Existing validation recipes are preserved.
4. WP-0086 and later are not modified by this package.
5. WP-0102's pending backlog retrofit scope is not duplicated.
6. The production-readiness report and coverage manifest can be regenerated.
7. WP-0103 has its own validation recipe or a justified non-recursive self-check equivalent.
8. Remaining historical gaps are explicitly listed with reasons.
9. No implementation behavior is changed for historical work packages.
10. The completion artifact provides a clear audit trail.

## Merge Class

Class A.

Escalate only if implementation would alter governance authority, validation authority, approval authority, merge authority, historical implementation behavior, or Git safety behavior.
