# SERIES TASK WP-0105 — Validation Continuation #6: Template Path Repair

## Codex Command

Read `collaboration/work_packages/pending/WP-0105_SERIES_validation_continuation_6_template_path_repair.md` and do exactly what it says.

## Mode

SERIES

## Mission

Repair the remaining validation failure in WP-0102 and WP-0105 after the WP-0105 closure merge.

This is Chief Architect #4 validation continuation work. The prior WP-0105 merge successfully registered recipes and repaired receipts, but the post-merge validation run on main exposed a narrow recipe defect: the WP-0102 validation recipe checks for a Codex task template path that is not present at that exact location in the repository.

## Background

After pulling main to commit `7031e7f97cadfa792d6fc60e176091a1e3d3da94`, Chief Architect validation showed:

- WP-0101 validates and is production-ready.
- WP-0102 now has a registered recipe and complete receipt, but validation fails.
- WP-0103 validates and is production-ready.
- WP-0105 now has a registered recipe and complete receipt, but validation fails because it depends on WP-0102 validation.
- WP-0080, WP-0081, and WP-0085 still validate and remain production-ready.

The WP-0102 failure is the command:

```bash
test -f docs/operations/Codex_Task_Template_Standard_v1.md && test -f collaboration/work_packages/pending/WP-0101_SERIES_codex_task_template_standard.md
```

The command exits with status 1, which means at least one expected path is wrong or missing.

This package must repair that exact issue without broadening scope.

## Scope

In scope:

1. Determine the canonical repository path for the WP-0101 Codex task template standard.
2. Determine whether `docs/operations/Codex_Task_Template_Standard_v1.md` is intended to exist.
3. Determine whether `collaboration/work_packages/pending/WP-0101_SERIES_codex_task_template_standard.md` is intended to remain the correct pending package path.
4. Repair the WP-0102 validation recipe so it checks the actual canonical template artifact and WP-0101 source artifact.
5. If the expected docs path is supposed to be canonical but was accidentally omitted, restore or create the missing document from existing repository-supported WP-0101 content.
6. Re-run WP-0102 validation.
7. Re-run WP-0105 validation.
8. Confirm WP-0101, WP-0103, WP-0080, WP-0081, and WP-0085 remain valid.
9. Regenerate validation and production-readiness artifacts.
10. Update the WP-0105 completion artifact to record this validation continuation repair.

Out of scope:

- Adding broad historical validation recipes.
- Repairing unrelated historical receipts.
- Changing the WP-0101 standard itself except to restore a missing canonical document if the repo proves it should exist.
- Changing validation policy semantics.
- Changing governance, Steward authority, merge authority, approval authority, or production-readiness rules.
- Implementing pending backlog package missions.
- Broad generated-artifact staging.

## Required Diagnosis

Before changing code, inspect the repository for:

```bash
find docs -iname '*Codex*Template*' -o -iname '*Task*Template*'
find collaboration/work_packages/pending -iname 'WP-0101*.md'
rg "Codex Task Template" .
rg "WP-0102 Template Retrofit Notice" collaboration/work_packages/pending
```

Use actual available shell equivalents if running on Windows.

Identify whether the problem is:

- wrong file path in the recipe
- missing canonical docs artifact
- renamed WP-0101 pending file
- duplicate WP-0101 artifacts requiring a more precise check
- shell portability issue in the recipe command

## Repair Requirements

The repair must result in:

- WP-0102 validation status `passed` or `passed_with_findings`
- WP-0102 production readiness `true` unless there is a real unrelated blocker
- WP-0105 validation status `passed` or `passed_with_findings`
- WP-0105 production readiness `true` unless there is a real unrelated blocker
- WP-0103 remains production-ready
- WP-0101 remains production-ready
- WP-0080, WP-0081, and WP-0085 remain production-ready

Prefer the smallest correction:

- If the recipe path is wrong, update only the recipe command and tests.
- If the canonical document is missing but required, restore it from WP-0101-supported content.
- If shell syntax is the problem, replace the check with a local Python check that works consistently under the Estate validation runner.

## Recommended Implementation

In `src/estate/core/work_package_validation.py`, replace the brittle WP-0102 file existence check with a robust local-first check.

Acceptable example:

```bash
python -c "from pathlib import Path; candidates=[Path('docs/operations/Codex_Task_Template_Standard_v1.md'), Path('docs/operations/Codex_Task_Template_Standard.md'), Path('collaboration/work_packages/pending/WP-0101_SERIES_codex_task_template_standard.md')]; assert any(p.exists() for p in candidates[:2]), candidates; assert candidates[2].exists(), candidates[2]"
```

Use the actual canonical paths discovered in the repository. Do not preserve wrong candidates if the repo clearly uses a different path.

## Required Tests

Add or update tests for:

- WP-0102 recipe command uses the correct canonical template path
- WP-0102 recipe validates on current main checkout
- WP-0105 recipe validates when WP-0102 validates
- WP-0103 historical coverage is preserved
- production-readiness generation still succeeds

Run relevant tests:

```bash
PYTHONPATH=src pytest tests/test_work_package_validation.py tests/test_production_readiness_validation.py -q
```

Use the actual available test paths if they differ.

## Required Validation Commands

Run or document equivalent:

```bash
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0101 --json
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0102 --json
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0103 --json
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0105 --json
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0080 --json
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0081 --json
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0085 --json
PYTHONPATH=src python -m estate.cli.main validation-production-readiness --json
```

## Required Outputs

Update or create as applicable:

- `src/estate/core/work_package_validation.py`
- relevant tests
- `operations/validation/reports/WP-0102_validation.md`
- `operations/validation/reports/WP-0105_validation.md`
- `runtime/validation/work_packages/WP-0102_validation.json`
- `runtime/validation/work_packages/WP-0105_validation.json`
- `operations/validation/production_readiness_report.md`
- `runtime/validation/production_readiness_report.json`
- `operations/validation/validation_coverage_manifest.md`
- `runtime/validation/validation_coverage_manifest.json`
- `collaboration/work_packages/completions/WP-0105_codex_done.json`

If restoring a missing canonical template document is required, also update the relevant document registry artifacts only if existing Estate practice requires it.

## Completion Artifact

Update or create:

`collaboration/work_packages/completions/WP-0105_codex_done.json`

It must include:

- `work_package_id = WP-0105`
- `codex_status = done`
- `completed_at`
- `branch`
- `pull_request_url` or `pull_request_url_not_applicable_reason`
- summary of the path/recipe repair
- files changed
- tests run
- validation commands run
- WP-0102 validation status
- WP-0105 validation status
- production-readiness totals after repair
- known limitations
- `ready_for_ca_review = true`
- `merge_authority = ca_verified_auto_merge_allowed`

## Acceptance Criteria

This package is complete when:

1. WP-0102 no longer fails because of the Codex template path check.
2. WP-0102 validation passes or passes with findings.
3. WP-0105 validation passes or passes with findings.
4. WP-0102 and WP-0105 receipts remain complete.
5. WP-0101 and WP-0103 remain production-ready.
6. WP-0080, WP-0081, and WP-0085 remain production-ready.
7. Production-readiness report regenerates successfully.
8. No unrelated historical recipe or receipt repair is performed.
9. Remaining unrelated blockers remain visible in the production-readiness report.

## Merge Class

Class A.

Escalate only if the repair requires changing validation policy semantics, governance authority, merge authority, approval authority, or the meaning of the WP-0101 Codex task template standard.
