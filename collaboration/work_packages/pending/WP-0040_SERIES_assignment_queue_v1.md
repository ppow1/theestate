# SERIES TASK WP-0040 — Assignment Queue v1

## Codex Command
Read `collaboration/work_packages/pending/WP-0040_SERIES_assignment_queue_v1.md` and do exactly what it says.

## Mode
SERIES.

## Mission
Create Assignment Queue v1 so Estate work packages can be listed with owner, state, dependencies, blockers, and next action.

## Scope
Generate an assignment queue from existing work package files and completion or review records.

Produce:

- `runtime/work_packages/assignment_queue.json`
- `operations/work_packages/assignment_queue.md`

## Queue Fields
Track:

- work_package_id
- path
- mode
- owner
- state
- dependencies
- next_action
- blockers
- last_updated

## Constraints
Do not replace the pending folder. Do not automate Codex submission. Do not create new governance. Do not edit `estate_ledger/ledger.md` or `development/devlog.md`.

## Tests
Add tests for queue generation, dependency listing, blocked entries, missing owner warnings, and JSON/Markdown output.

## Completion Signal
Create `collaboration/work_packages/completions/WP-0040_codex_done.json` using the standard completion schema.

## Merge Class
Class A.
