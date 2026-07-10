# Event-Driven Operations Scheduler

The event-driven operations scheduler sits beneath Operations Runtime and schedules the existing runtime modes rather than introducing another execution orchestrator.

## Jobs

Default jobs cover merge discovery, audit processing, Ring 2 preparation, health refresh, and repository monitoring. Each job can define interval timing, a daily UTC calendar time, event triggers, debounce, retry delay, timeout/lease duration, dependencies, bounded catch-up, and overlap policy.

## State and status

Scheduler state is persisted under `runtime/operations_scheduler/` and Office-readable status is written to `operations/operations_scheduler/status.md`. State includes next-run, last-run, lease, retry, and failure data.

## CLI

```text
operations-scheduler list
operations-scheduler show <job>
operations-scheduler enable <job>
operations-scheduler disable <job>
operations-scheduler run-due
operations-scheduler trigger <event>
```

## Boundaries

The scheduler calls `OperationsRuntimeService.run_once()` with existing runtime modes only. Provider execution, dispatch, movement, and Traffic Controller constraints remain authoritative outside the scheduler.
