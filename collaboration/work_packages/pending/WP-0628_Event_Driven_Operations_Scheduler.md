# WP-0628 - Event-Driven Operations Scheduler

Status: Proposed
Priority: High
Owner: Chief Architect #6
Classification: Estate Internal
Depends on: WP-0627

## Mission

Add a scheduler beneath Operations Runtime so recurring and event-triggered operational jobs run without Steward prompting while preserving bounded execution and movement constraints.

## Required Implementation

- Schedule existing runtime functions; do not create a parallel orchestrator.
- Support interval, calendar, event-triggered, debounce, retry, timeout, and dependency conditions.
- Prevent overlapping instances unless explicitly allowed.
- Persist next-run, last-run, lease, retry, and failure state outside the repository.
- Support bounded catch-up after downtime.
- Emit operational events and Office-readable status.
- Traffic Controller constraints remain authoritative for movement.

Expected files:

```text
src/estate/core/operations_scheduler.py
src/estate/core/operations_scheduler_runtime.py
tests/test_operations_scheduler.py
tests/test_operations_scheduler_runtime.py
docs/integration/event_driven_operations_scheduler.md
```

## CLI

Provide commands equivalent to:

```text
operations-scheduler list
operations-scheduler show <job>
operations-scheduler enable <job>
operations-scheduler disable <job>
operations-scheduler run-due
operations-scheduler trigger <event>
```

## Acceptance

- Merge discovery, audit processing, Ring 2 preparation, health refresh, and repository monitoring can be scheduled.
- Event triggers wake eligible jobs without polling-only dependence.
- Duplicate and overlapping runs are prevented.
- Downtime catch-up is bounded.
- No execution-provider calls bypass provider seams.
- Completion receipt: `collaboration/work_packages/completions/WP-0628_codex_done.json`.

## Codex Handoff

```text
Read collaboration/work_packages/pending/WP-0628_Event_Driven_Operations_Scheduler.md and do exactly what it says.
```
