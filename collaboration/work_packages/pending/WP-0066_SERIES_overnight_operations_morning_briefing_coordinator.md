# SERIES TASK WP-0066 — Overnight Operations and Morning Briefing Coordinator

## Codex Command
Read `collaboration/work_packages/pending/WP-0066_SERIES_overnight_operations_morning_briefing_coordinator.md` and do exactly what it says.

## Mission
Coordinate unattended overnight Estate operations and produce a consolidated Morning Briefing from existing institutional artifacts.

## Scope
Aggregate overnight activity from work package completions, validation, notifications, recalls, worker runtime, and mission status into a single briefing artifact.

## Behavior Requirements
- Local-first.
- Produce summary, accomplishments, warnings, failures, pending decisions, and recommended next actions.
- Link back to authoritative artifacts.
- Do not fabricate events.

## Constraints
Do not execute work automatically. Do not notify external services. Do not edit `estate_ledger/ledger.md` or `development/devlog.md`.

## Tests
Verify empty overnight activity, successful overnight run, failures, recalls, validation issues, and missing artifact handling.

## Completion Signal
Create `collaboration/work_packages/completions/WP-0066_codex_done.json` using the standard completion schema.

## Merge Class
Class A.
