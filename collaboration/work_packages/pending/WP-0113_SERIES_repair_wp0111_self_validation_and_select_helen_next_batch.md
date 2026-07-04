# SERIES TASK WP-0113 — Repair WP-0111 Self-Validation and Select Helen Next Batch

## Codex Command

Read collaboration/work_packages/pending/WP-0113_SERIES_repair_wp0111_self_validation_and_select_helen_next_batch.md and do exactly what it says.

## Mode

SERIES

## Mission

Repair the narrow production-readiness closure gap left by WP-0111, then select and prepare the next Helen-online implementation batch without falsely marking pending work complete.

WP-0111 successfully advanced the Helen path by validating WP-0020. However Chief Architect local verification showed WP-0111 itself is blocked because it has no validation recipe and its completion receipt is missing required `summary` metadata.

This package must close WP-0111's self-validation gap and then produce the next actionable Helen-online batch recommendation from the WP-0111 report.

## Numbering Correction

WP-0112 is already assigned to Parallel Workstream Isolation and Install Handoff. Do not use WP-0112 for this validation repair. This package is WP-0113.

## Confirmed Local Verification Evidence

After PR #105 was merged and pulled locally:

- Current commit: `3894fd7 Merge pull request #105 from ppow1/codex/follow-instructions-in-wp-0111`
- `WP-0020` validation passed and is production-ready.
- `WP-0102` validation passed and is production-ready.
- `WP-0105` validation passed and is production-ready.
- `WP-0111` validation status was `no_recipe`.
- `WP-0111` production-ready was `False`.
- `WP-0111` receipt status was `incomplete` due to missing `summary`.
- Production-readiness totals after local verification: scanned 98, production-ready 29, blocked 69, missing recipes 57, missing receipts 15, incomplete receipts 51.

WP-0111's burn-down report identified the next Helen-online implementation path:

1. `WP-0106` — Resident Runtime Presence Model
2. `WP-0110` — Resident Action Authority Boundary
3. `WP-0107` — Alfred Online Duty Runner
4. `WP-0108` — Helen Online Duty Runner
5. `WP-0109` — Resident Conversation Session and Audit Trail

The report explicitly classified WP-0106 through WP-0110 as pending implementation, not validation-only repair.

## Scope

In scope:

1. Add a validation recipe for `WP-0111`.
2. Repair `collaboration/work_packages/completions/WP-0111_codex_done.json` to include required `summary` metadata and any other required metadata gaps found by the validator.
3. Validate that WP-0111's required report artifacts exist:
   - `operations/validation/backlog_burn_down/WP-0111_first_batch_report.md`
   - `runtime/validation/backlog_burn_down/WP-0111_first_batch_report.json`
4. Validate that WP-0111 selected `WP-0020` as the first batch and did not mark WP-0106 through WP-0110 complete.
5. Revalidate baseline packages:
   - `WP-0020`
   - `WP-0102`
   - `WP-0105`
   - `WP-0111`
6. Run production-readiness validation.
7. Produce a short next-batch recommendation artifact for Helen online implementation sequencing.
8. Create a completion receipt for WP-0113.

Out of scope:

- Implementing WP-0106, WP-0107, WP-0108, WP-0109, or WP-0110 in this package.
- Marking WP-0106 through WP-0110 complete.
- Creating completion receipts for pending implementation packages.
- Changing validation policy semantics.
- Adding new governance structures.
- Editing Steward, Resident, Chief Architect, or merge authority semantics.
- Using or modifying WP-0112.

## Required WP-0111 Validation Recipe

Register a recipe for `WP-0111` in `src/estate/core/work_package_validation.py`.

The recipe should verify at minimum:

1. The human-readable first-batch report exists.
2. The machine-readable first-batch report exists and parses as JSON.
3. The report selected `WP-0020` as the first batch package.
4. The report identifies WP-0106 through WP-0110 as pending/unimplemented or next implementation path, not as completed validation-only repairs.
5. `WP-0020` validates successfully.
6. The WP-0111 completion receipt is complete according to the production-readiness receipt validator.

Use local Python checks for portability. Do not use Bash-only loops or shell-specific syntax.

## Required Next-Batch Artifact

Create:

`operations/validation/backlog_burn_down/WP-0113_helen_next_batch_recommendation.md`

Create machine-readable companion:

`runtime/validation/backlog_burn_down/WP-0113_helen_next_batch_recommendation.json`

The artifact must include:

- current production-readiness totals after WP-0111 repair
- Helen path status after WP-0020 readiness
- why WP-0106 should come before WP-0108
- whether WP-0110 should be implemented before or alongside WP-0106
- explicit statement that WP-0107, WP-0108, and WP-0109 remain implementation packages, not validation-only repairs
- recommended next work-package command for Codex or Chief Architect review

## Required Tests

Add tests covering:

- WP-0111 recipe is registered.
- WP-0111 recipe uses cross-platform Python checks or otherwise avoids Bash-only syntax.
- WP-0111 completion receipt validates as complete.
- WP-0111 report artifacts are present and identify WP-0020 as selected first batch.

Use existing test files where appropriate.

## Required Validation Commands

Run or document equivalent:

```bash
PYTHONPATH=src pytest tests/test_work_package_validation.py tests/test_production_readiness_validation.py -q
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0020 --json
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0102 --json
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0105 --json
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0111 --json
PYTHONPATH=src python -m estate.cli.main validation-production-readiness --json
```

## Required Outputs

Update or create as applicable:

- `src/estate/core/work_package_validation.py`
- relevant tests
- `collaboration/work_packages/completions/WP-0111_codex_done.json`
- `operations/validation/reports/WP-0111_validation.md`
- `runtime/validation/work_packages/WP-0111_validation.json`
- `operations/validation/backlog_burn_down/WP-0113_helen_next_batch_recommendation.md`
- `runtime/validation/backlog_burn_down/WP-0113_helen_next_batch_recommendation.json`
- `collaboration/work_packages/completions/WP-0113_codex_done.json`
- regenerated production-readiness and coverage artifacts

## Completion Artifact

Create:

`collaboration/work_packages/completions/WP-0113_codex_done.json`

It must include:

- `work_package_id = WP-0113`
- `codex_status = done`
- `completed_at`
- `branch`
- `pull_request_url` or `pull_request_url_not_applicable_reason`
- `summary`
- files changed
- tests run
- validation commands run
- WP-0111 repair summary
- Helen next-batch recommendation
- production-readiness totals before and after
- known limitations
- `ready_for_ca_review = true`
- `merge_authority = ca_verified_auto_merge_allowed`

## Acceptance Criteria

This package is complete when:

1. WP-0111 has a registered validation recipe.
2. WP-0111 completion receipt is complete.
3. WP-0111 validates successfully.
4. WP-0020, WP-0102, and WP-0105 remain production-ready.
5. Production-readiness validation has been regenerated.
6. The next Helen-online implementation batch is clearly recommended without falsely completing pending packages.
7. No WP-0112 artifacts are overwritten, repurposed, or renamed by this repair.

## Merge Class

Class A.

Escalate only if the repair requires changing validation policy semantics, authority boundaries, or the meaning of production readiness.
