# SERIES TASK WP-0048 — Work Package Pipeline View

## Codex Command
Read `collaboration/work_packages/pending/WP-0048_SERIES_work_package_pipeline_view.md` and do exactly what it says.

## Mission
Add the Work Package Pipeline view to the Estate Operations Center so the Steward can see pending, active, completed, blocked, and review-ready work in one place.

## Scope
Create an Operations Center tab or panel for work package pipeline status using existing artifacts where available:

- pending work packages
- completion records
- review records
- assignment queue
- launch queue documents
- local validation output

The view should show:

- work package ID
- title
- state
- mode: series, parallel, or architecture-first
- dependency notes
- assigned owner if available
- next action
- completion/review status

## Behavior Requirements
- Preserve simple Steward copy/paste launch workflow.
- Link or display the Codex command for ready packages.
- Clearly separate pending, active, blocked, completed, and review-ready work.
- Respect UI principles from WP-0046.
- Use quiet refresh without full-page redraws where feasible.

## Constraints
Do not automate Codex submission. Do not change work package contents. Do not create new governance. Do not edit `estate_ledger/ledger.md` or `development/devlog.md`.

## Tests
Verify the pipeline renders representative pending, completed, blocked, and missing-data states. Verify ready Codex commands remain copyable.

## Completion Signal
Create `collaboration/work_packages/completions/WP-0048_codex_done.json` using the standard completion schema.

## Merge Class
Class A.
