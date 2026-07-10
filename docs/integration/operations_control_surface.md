# Operations Control Surface

The Operations Control Surface extends the existing Office of the Steward; it is not a separate dashboard. It appears on the Operational Activity tab and combines live host/runtime status, scheduled jobs, operational watches, audit admission state, latest verdicts, faults, and evidence links.

## Canonical controls

All available buttons dispatch through `estate.core.office_command_surface.execute_office_action` to existing runtime handlers:

- Host lifecycle: `OperationsRuntimeHost.start`, `stop`, `restart`, and `status`.
- Scheduler state: `OperationsSchedulerRuntime.enable`, `disable`, and `trigger`.
- Watch state: `OperationalWatchRuntime.set_enabled`, `pause`, and `evaluate`.
- Bounded cycle: `OperationsRuntimeService.run_once`.
- Holds: `MergeDiscoveryRuntime.hold` and `release`.
- Evidence inspection: reads existing files under the Estate root only.

## Boundaries

The surface does not grant final acceptance, does not execute providers directly, and does not bypass Traffic Controller constraints. Failures are recorded in the Office action result log with the failed handler and diagnostics path when an exception occurs.

## Persistence

Scheduler state persists in `runtime/operations_scheduler/state.json`; watch state persists in `runtime/background_operations/watch_state.json`; runtime cycles and status persist under `runtime/operations_runtime/`.
