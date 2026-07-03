# SERIES TASK WP-0049 — Validation and Estate Health Dashboard

## Codex Command
Read `collaboration/work_packages/pending/WP-0049_SERIES_validation_health_dashboard.md` and do exactly what it says.

## Mission
Add the Validation and Estate Health dashboard view to the Estate Operations Center so the Steward can see operational health, warnings, and validation state without reading separate reports.

## Scope
Create an Operations Center tab or panel that displays validation and health information from existing artifacts where available:

- local operational validation runner output
- capability lifecycle reports
- dependency graph reports
- mailbox synchronization reports
- recall audit reports
- worker heartbeat reports
- work package completion/review records

The view should show:

- overall Estate health
- validation pass/warning/fail state
- current warnings
- blocked subsystems
- stale or missing runtime artifacts
- last successful validation time
- recommended next action

## Behavior Requirements
- Use quiet refresh without full-page redraws where feasible.
- Clearly distinguish warnings from failures.
- Link back to source reports where possible.
- Respect the UI principles from WP-0046.
- Surface health summary into the bottom status bar where available.

## Constraints
Do not replace validation logic. Do not create new governance. Do not make generated dashboard output authoritative. Do not edit `estate_ledger/ledger.md` or `development/devlog.md`.

## Tests
Verify rendering for passing, warning, failing, stale, and missing-data states. Verify source report references are preserved where available.

## Completion Signal
Create `collaboration/work_packages/completions/WP-0049_codex_done.json` using the standard completion schema.

## Merge Class
Class A.
