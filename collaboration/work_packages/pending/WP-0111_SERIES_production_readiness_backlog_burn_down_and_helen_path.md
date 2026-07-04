# SERIES TASK WP-0111 — Production-Readiness Backlog Burn-Down and Helen Online Path

## Codex Command

Read collaboration/work_packages/pending/WP-0111_SERIES_production_readiness_backlog_burn_down_and_helen_path.md and do exactly what it says.

## Mode

SERIES

## Mission

Begin the production-readiness backlog burn-down so the Estate can move through the remaining work-package queue toward bringing Helen online for onboarding Chief Architect #5, the replacement for Chief Architect #3.

This package must not attempt to repair the entire historical backlog in one uncontrolled pass. It must establish the first focused burn-down batch, prioritize packages that affect Helen-online readiness and Chief Architect onboarding continuity, and leave a clear machine-readable report for the next batch.

## Background

The validation system is now operational after the WP-0101, WP-0102, WP-0103, and WP-0105 closure sequence.

Current validated state from Chief Architect verification after PR #103:

- WP-0102 validates and is production-ready.
- WP-0105 validates and is production-ready.
- WP-0101 and WP-0103 remain production-ready.
- The production-readiness validator works and reports remaining blockers.
- The remaining backlog is not primarily a validation-engine defect. It is production-readiness coverage debt: missing recipes, missing receipts, and incomplete receipts.

The Steward's operational goal is to burn through the remaining work-package queue so Helen can come online and perform onboarding for Chief Architect #5.

Known relevant pending/near-term packages include resident runtime presence and online duty runner work for Alfred and Helen. These should be treated as priority path packages if present in the repository:

- WP-0106 — Resident Runtime Presence Model
- WP-0107 — Alfred Online Duty Runner
- WP-0108 — Helen Online Duty Runner
- WP-0109 — Resident Conversation Session and Audit Trail
- WP-0110 — Resident Action Authority Boundary

If exact file names differ, discover the current pending files by work-package ID.

## Scope

In scope:

1. Run the current production-readiness validator and identify blocked packages.
2. Classify blockers into at least these groups:
   - missing validation recipe
   - missing completion receipt
   - incomplete completion receipt
   - failing validation
   - genuinely pending/unimplemented work
3. Identify a first burn-down batch that advances the Helen-online path without broadening the Estate architecture.
4. Add or repair validation recipes for the first batch where implementation already exists and safe local validation commands are available.
5. Repair completion receipt metadata for the first batch only when the underlying work was already completed or merged.
6. Do not invent implementation completion for packages that are still genuinely pending.
7. Run validation for each selected batch package.
8. Run production-readiness validation after the batch.
9. Produce a clear next-batch report for the Chief Architect and Steward.

Out of scope:

- Implementing Helen online runtime behavior unless the selected existing package already contains the implementation and only validation/receipt closure is missing.
- Creating new departments, registries, governance structures, or doctrine.
- Changing validation policy semantics.
- Changing Steward authority, Resident authority, Chief Architect authority, or merge authority.
- Marking unimplemented packages as complete.
- Repairing the entire backlog in a single uncontrolled PR.
- Editing generated artifacts unrelated to the selected batch unless required by validation commands.

## Priority Rules

Select the first batch using this order:

1. Packages directly needed to get Helen online and able to be validated from existing code/artifacts.
2. Packages that are already implemented/merged but blocked only by missing recipe or incomplete receipt.
3. Packages with registered recipes but stale/missing validation reports.
4. Older historical packages with simple artifact-only validation.

Do not select packages whose implementation is absent or whose required behavior is still pending. For those, report them as implementation backlog, not validation backlog.

## Required Diagnosis

Before modifying files, inspect:

```bash
PYTHONPATH=src python -m estate.cli.main validation-production-readiness --json
find collaboration/work_packages/pending -maxdepth 1 -type f | sort
find collaboration/work_packages/completions -maxdepth 1 -type f | sort
rg "WP-0106|WP-0107|WP-0108|WP-0109|WP-0110|Helen Online|Helen" collaboration src tests operations docs
```

Use PowerShell equivalents where necessary.

## Required Batch Report

Create:

`operations/validation/backlog_burn_down/WP-0111_first_batch_report.md`

Create machine-readable companion:

`runtime/validation/backlog_burn_down/WP-0111_first_batch_report.json`

The report must include:

- current production-readiness totals before the batch
- selected batch package IDs
- reason each selected package was chosen
- blocker type before repair
- files changed per package
- validation result per package
- production-readiness result per package after repair
- packages discovered as genuinely pending/unimplemented
- explicit Helen-online path status
- recommended next batch

## Required Implementation Work

For each selected batch package:

1. If the package has implementation artifacts and only lacks a recipe, add the smallest safe validation recipe in `src/estate/core/work_package_validation.py`.
2. If the package has a completion receipt with missing metadata and the work is already completed, repair only the missing metadata fields.
3. If the package has no completion receipt but is demonstrably completed/merged, create a conservative completion receipt with documented evidence.
4. If completion cannot be proven, do not create a completion receipt. Report it as pending implementation or pending evidence.
5. Add tests covering any new recipe registrations or receipt validation behavior.

## Required Validation Commands

Run or document equivalent:

```bash
PYTHONPATH=src pytest tests/test_work_package_validation.py tests/test_production_readiness_validation.py -q
PYTHONPATH=src python -m estate.cli.main validation-production-readiness --json
```

Run validation for every selected batch package:

```bash
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-XXXX --json
```

Also revalidate the closure baseline:

```bash
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0102 --json
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0105 --json
```

## Required Outputs

Update or create as applicable:

- `src/estate/core/work_package_validation.py`
- relevant tests
- selected completion receipts under `collaboration/work_packages/completions/`
- selected validation reports under `operations/validation/reports/`
- selected runtime validation JSON under `runtime/validation/work_packages/`
- `operations/validation/production_readiness_report.md`
- `runtime/validation/production_readiness_report.json`
- `operations/validation/validation_coverage_manifest.md`
- `runtime/validation/validation_coverage_manifest.json`
- `operations/validation/backlog_burn_down/WP-0111_first_batch_report.md`
- `runtime/validation/backlog_burn_down/WP-0111_first_batch_report.json`
- `collaboration/work_packages/completions/WP-0111_codex_done.json`

## Completion Artifact

Create:

`collaboration/work_packages/completions/WP-0111_codex_done.json`

It must include:

- `work_package_id = WP-0111`
- `codex_status = done`
- `completed_at`
- `branch`
- `pull_request_url` or `pull_request_url_not_applicable_reason`
- selected batch package IDs
- summary of blocker classes repaired
- Helen-online path findings
- files changed
- tests run
- validation commands run
- production-readiness totals before and after
- packages intentionally left pending and why
- known limitations
- `ready_for_ca_review = true`
- `merge_authority = ca_verified_auto_merge_allowed`

## Acceptance Criteria

This package is complete when:

1. A first production-readiness burn-down batch has been selected using the priority rules.
2. No unimplemented package is falsely marked complete.
3. Every selected package has a validation result.
4. WP-0102 and WP-0105 remain passing and production-ready.
5. Production-readiness totals are regenerated.
6. The batch report clearly identifies the next work needed to get Helen online.
7. The Chief Architect can decide the next batch from the generated report without redoing the diagnosis.

## Merge Class

Class A.

Escalate only if the work requires changing validation policy semantics, governance authority, Resident authority, Steward authority, Chief Architect authority, or the meaning of production readiness.
