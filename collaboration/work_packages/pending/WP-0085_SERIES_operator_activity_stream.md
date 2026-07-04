# SERIES TASK WP-0085 — Operator Activity Stream

## Codex Command
Read `collaboration/work_packages/pending/WP-0085_SERIES_operator_activity_stream.md` and do exactly what it says.

## Mission
Implement an Operator Activity Stream that provides the real-time, filterable event feed envisioned for the Operations Center, allowing the Steward to monitor Estate activity without interrupting ongoing work.

## Scope
Aggregate existing operational events from Mission Control, workers, validation, notifications, mailbox activity, and service health into a unified read-only event stream.

## Behavior Requirements
- Quiet live updates.
- Configurable verbosity levels.
- Per-source filtering.
- Error-only and warning-only views.
- Designed for future dockable bottom status panel integration.
- Read-only with links to authoritative artifacts.

## Constraints
Do not become an event source. Do not duplicate logging systems. Do not edit `estate_ledger/ledger.md` or `development/devlog.md`.

## Tests
Verify filtering, verbosity changes, live updates, empty-state handling, and source-link integrity.

## Completion Signal
Create `collaboration/work_packages/completions/WP-0085_codex_done.json` using the standard completion schema.

## Merge Class
Class A.
