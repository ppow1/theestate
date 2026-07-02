# SERIES TASK WP-0024 — Daily Board and Parking Lot Integration

## Codex Command
Read `collaboration/work_packages/pending/WP-0024_SERIES_daily_board_parking_lot_integration.md` and do exactly what it says.

## Mode
SERIES. Depends on WP-0019 Alfred Operational Activation and current Operations Board / Parking Lot artifacts.

## Mission
Integrate the Daily/Operations Board and Parking Lot into a single operational planning view so active work, deferred ideas, promotion conditions, and next actions can be reviewed without manual cross-reading.

## Why This Is Next
The Estate now has active work packages, Alfred operational briefing, parking lot capture, and operations board artifacts. The Steward needs a concise operational surface that distinguishes active work from parked ideas and identifies when a parked item is ready for promotion.

## Scope
Use existing artifacts where present:

- `operations/boards/parking_lot.md`
- Operations Board runtime/status files
- Alfred operational briefing outputs
- pending work packages under `collaboration/work_packages/pending/`
- completion/review artifacts under `collaboration/work_packages/`

Create a lightweight integration report that includes:

- active work package summary
- pending Codex queue summary
- completed work awaiting review/validation
- blocked work
- parking lot items with promotion conditions
- parking lot items that appear ready for review
- recommended next actions

## Expected Outputs
- Runtime report such as `runtime/operations/daily_board_integration.json`.
- Human-readable report such as `operations/boards/daily_board_integration.md`.
- Optional CLI if consistent with existing patterns, for example:

```bash
PYTHONPATH=src python -m estate.cli.main daily-board --json
```

If a similar Operations Board command already exists, extend it rather than creating a duplicate command.

## Constraints
Do not turn the Parking Lot into a backlog. Do not automatically promote Parking Lot items. Do not create new governance. Do not redesign the Operations Board. Missing artifacts should produce warnings, not fatal errors. Do not edit `estate_ledger/ledger.md` or `development/devlog.md`.

## Tests
Add tests for:

- parsing Parking Lot items
- identifying promotion conditions without promoting items
- listing active/pending/completed work packages
- missing artifact warnings
- Markdown and JSON report generation

## Completion Signal
Before finishing, create `collaboration/work_packages/completions/WP-0024_codex_done.json` with work_package_id, codex_status=done, completed_at, branch, pull_request_url, summary, files_changed, tests_run, known_limitations, ready_for_ca_review=true, merge_authority=ca_verified_auto_merge_allowed.

## Merge Class
Class A — bounded operational reporting after CA verification. Escalate to Class B only if implementation changes Parking Lot authority or Operations Board governance.
