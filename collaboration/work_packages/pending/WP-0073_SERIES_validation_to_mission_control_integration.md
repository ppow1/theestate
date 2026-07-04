# SERIES TASK WP-0073 — Validation to Mission Control Integration

## Codex Command
Read `collaboration/work_packages/pending/WP-0073_SERIES_validation_to_mission_control_integration.md` and do exactly what it says.

## Mission
Integrate validation summary information into Mission Control so the Steward can see validation health without leaving the primary operational workspace.

## Scope
Use existing validation artifacts and metrics outputs where available, including:

- Validation Metrics Dashboard outputs
- Validation Observation Log outputs
- validation result artifacts
- work package completion and review records
- Mission Control workspace data providers

Mission Control should be able to display:

- overall validation status
- open observations count
- confirmed defects count
- conditional pass count
- most recent validation activity
- links to validation artifacts
- recommended next validation action where available

## Behavior Requirements
- Mission Control must remain an aggregator, not the source of truth.
- Missing validation metrics should display as unavailable, not fail.
- Keep validation observations distinct from confirmed defects.
- Respect UI principles from WP-0046.

## Constraints
Do not alter validation results. Do not auto-convert observations into work packages. Do not create new governance. Do not edit `estate_ledger/ledger.md` or `development/devlog.md`.

## Tests
Verify Mission Control renders validation data when available, handles missing metrics, preserves source links, and distinguishes observations from confirmed defects.

## Completion Signal
Create `collaboration/work_packages/completions/WP-0073_codex_done.json` using the standard completion schema.

## Merge Class
Class A.
