# SERIES TASK WP-0039 — Worker Runtime Heartbeat

## Codex Command
Read `collaboration/work_packages/pending/WP-0039_SERIES_worker_runtime_heartbeat.md` and do exactly what it says.

## Mode
SERIES. Depends on Alfred operational coordination and Morning Briefing.

## Mission
Implement a Worker Runtime Heartbeat service that records the operational health and last-known state of Estate workers.

## Scope
Track for each worker: identity, last heartbeat, current activity, last completed work package, status (idle, active, blocked, offline), and optional blocking reason.

Produce runtime outputs under `runtime/workers/` and an operational summary under `operations/workers/`.

## Constraints
No scheduling engine. No remote monitoring. Do not infer worker state without evidence. Do not edit ledger or devlog.

## Tests
Cover heartbeat creation, stale worker detection, blocked state, and summary generation.

## Completion Signal
Create `collaboration/work_packages/completions/WP-0039_codex_done.json` using the standard completion schema.

## Merge Class
Class A.
