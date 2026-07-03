# SERIES TASK WP-0064 — Worker Runtime Monitor

## Codex Command
Read `collaboration/work_packages/pending/WP-0064_SERIES_worker_runtime_monitor.md` and do exactly what it says.

## Mission
Implement the Worker Runtime Monitor so Alfred and the Operations Center can observe worker state, stale activity, blocked work, and operational availability without requiring the Steward to manually inspect runtime files.

## Scope
Create or extend a bounded runtime monitor that consumes existing worker/runtime artifacts where available:

- worker heartbeat reports
- assignment queue outputs
- work package completion records
- validation outputs
- mailbox synchronization reports
- activity console event providers

The monitor should produce:

- current worker status summary
- stale worker warnings
- blocked worker entries
- active worker entries
- worker last activity
- worker current assignment where available
- recommended next action where available

Possible outputs:

- `runtime/workers/worker_runtime_monitor.json`
- `operations/workers/worker_runtime_monitor.md`
- Operations Center data provider integration where appropriate

## Behavior Requirements
- Do not infer worker state without evidence.
- Missing optional artifacts should warn, not fail.
- Stale thresholds should be configurable or clearly documented.
- Surface worker health to the Operations Center status bar or Mission Control where feasible.
- Respect UI and verbosity principles from WP-0046.

## Constraints
Do not implement a scheduler in this package. Do not launch work automatically. Do not create remote monitoring. Do not create new governance. Do not edit `estate_ledger/ledger.md` or `development/devlog.md`.

## Tests
Verify active, idle, blocked, stale, offline, missing-artifact, and empty-worker states. Verify JSON and Markdown outputs if both are created.

## Completion Signal
Create `collaboration/work_packages/completions/WP-0064_codex_done.json` using the standard completion schema.

## Merge Class
Class A.
