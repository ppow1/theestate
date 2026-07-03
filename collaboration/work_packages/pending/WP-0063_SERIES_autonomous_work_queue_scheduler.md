# SERIES TASK WP-0063 — Autonomous Work Queue Scheduler

## Codex Command
Read `collaboration/work_packages/pending/WP-0063_SERIES_autonomous_work_queue_scheduler.md` and do exactly what it says.

## Mission
Implement the Estate's first autonomous work queue scheduler so Alfred can coordinate and prioritize eligible work packages without requiring continuous Steward supervision.

## Scope
Consume existing work package, dependency, validation, worker, and mission artifacts to produce Ready, Waiting, Blocked, Running, and Review queues plus a recommended next work package.

## Behavior Requirements
- Respect dependency ordering.
- Never bypass Steward approvals.
- Surface scheduler state to the Operations Center.
- Integrate with the Activity Console where available.
- Local-first only.

## Constraints
Do not launch Codex automatically. Do not modify work packages. Do not invent priorities. Do not edit `estate_ledger/ledger.md` or `development/devlog.md`.

## Tests
Verify dependency handling, blocked work, empty queue, unavailable workers, multiple ready items, and graceful handling of missing artifacts.

## Completion Signal
Create `collaboration/work_packages/completions/WP-0063_codex_done.json` using the standard completion schema.

## Merge Class
Class A.
