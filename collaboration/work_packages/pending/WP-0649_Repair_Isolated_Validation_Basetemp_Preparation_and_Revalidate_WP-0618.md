# WP-0649 — Repair Isolated Validation Basetemp Preparation and Revalidate WP-0618

## Status

Authorized for implementation by the Steward on 2026-07-12.

## Objective

Repair the confirmed WP-0618 autonomous validation failure caused by a missing repository-local `Temp` parent directory in clean isolated validation worktrees.

The repair must remain bounded to validation temporary-directory preparation and WP-0618 revalidation. It must not redesign Validation, Post-Merge Audit, Operations Runtime, governance, provider routing, or institutional acceptance.

## Confirmed failure

Audit `pma-eabe27f409904777b736d323840bf78a` validated revision `1bafdc0686eabd6e23ac51d36c5292e7ae7dcb01` and failed while running:

```text
pytest -q tests/test_operational_targets.py tests/test_operational_targets_runtime.py tests/test_post_merge_audit.py tests/test_post_merge_audit_runtime.py --basetemp Temp/pytest-operational-targets-post-merge-audit
```

Five tests errored during fixture setup because the clean isolated worktree did not contain the parent directory `Temp`.

The traceback was:

```text
FileNotFoundError: [WinError 3] The system cannot find the path specified
```

The tests did not fail assertions. Pytest could not create the configured base-temp directory because its parent was absent.

## Required implementation

1. Ensure every clean Estate checkout and isolated validation worktree contains a repository-local `Temp` directory before the WP-0618 pytest recipe executes.
2. Keep the correction repository-local and non-authoritative.
3. Do not place validation evidence in the development checkout beyond existing governed runtime behavior.
4. Add a focused regression test proving the tracked temporary-directory prerequisite exists and that the WP-0618 recipe continues to use the intended repository-local base-temp path.
5. Add a completion receipt for WP-0649.
6. Re-run the focused WP-0618 validation recipe from a clean worktree.

## Implementation choice

Track `Temp/.gitkeep` so Git materializes the required parent directory in every normal clone and worktree before pytest fixture setup.

This is the smallest safe corrective action. It does not alter the validation engine, runtime host, audit lifecycle, authority boundaries, or unrelated recipes.

## Required files

- `Temp/.gitkeep`
- `tests/test_wp0649_validation_basetemp.py`
- `collaboration/work_packages/completions/WP-0649_codex_done.json`

## Required validation

Run:

```text
python -m py_compile src/estate/core/work_package_validation.py
pytest -q tests/test_wp0649_validation_basetemp.py
pytest -q tests/test_operational_targets.py tests/test_operational_targets_runtime.py tests/test_post_merge_audit.py tests/test_post_merge_audit_runtime.py --basetemp Temp/pytest-operational-targets-post-merge-audit
python -m estate.cli.main validate-work-package --id WP-0618 --json
```

## Success criteria

- A clean checkout contains `Temp` without manual preparation.
- The focused regression test passes.
- All eight WP-0618 focused tests execute without missing-directory setup errors.
- WP-0618 validation no longer fails because `Temp` is absent.
- No governance, provider, dispatch, acceptance, or runtime-host behavior is changed.
- The completion receipt truthfully records validation results and any remaining limitations.

## Explicit exclusions

Do not:

- redesign the validation engine;
- change governance or institutional acceptance;
- modify runtime synchronization behavior;
- repair the separate stale-runtime-checkout issue;
- change provider or dispatch execution;
- broaden the work package beyond the confirmed base-temp defect.

## Work package filename

`WP-0649_Repair_Isolated_Validation_Basetemp_Preparation_and_Revalidate_WP-0618.md`

## Repository path

`A:\theestate\collaboration\work_packages\pending\WP-0649_Repair_Isolated_Validation_Basetemp_Preparation_and_Revalidate_WP-0618.md`

## Codex handoff command

```text
Implement the instructions in A:\theestate\collaboration\work_packages\pending\WP-0649_Repair_Isolated_Validation_Basetemp_Preparation_and_Revalidate_WP-0618.md. Keep the change bounded to isolated validation temporary-directory preparation and WP-0618 revalidation. Do not redesign the validation architecture, change governance, or include unrelated runtime synchronization work. Run every required validation, create the completion receipt, and report the exact files changed, tests run, and resulting WP-0618 verdict.
```
