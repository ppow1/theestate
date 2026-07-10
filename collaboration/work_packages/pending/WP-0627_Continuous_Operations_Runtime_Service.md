# WP-0627 - Continuous Operations Runtime Service

Status: Proposed  
Priority: Critical  
Owner: Chief Architect #6  
Classification: Estate Internal  
Created: 2026-07-10

## Mission

Turn the current bounded one-shot Operations Runtime into a persistent local service that wakes, performs a bounded cycle, sleeps, and repeats without Steward prompting.

## Required Behavior

- start, stop, restart, status, pause, resume
- configurable wake interval and jitter
- event-triggered wakeups for merge, mailbox, audit, validation, and target changes
- durable heartbeat, last-cycle, next-cycle, and service-state artifacts
- lock/lease protection against duplicate instances
- crash recovery and stale-lock repair
- bounded work per cycle
- graceful shutdown after current bounded unit of work
- no provider execution outside provider adapter seams

## Office Contract

Expose stable callable functions and status artifacts for CA5 WP-0516 and WP-0521:

- service state
- heartbeat age
- current cycle
- next wake
- pause reason
- latest error
- start/stop/restart/pause/resume result contracts

## Expected Artifacts

- `src/estate/core/operations_runtime_daemon.py`
- `src/estate/core/operations_runtime_daemon_state.py`
- `tests/test_operations_runtime_daemon.py`
- `docs/integration/continuous_operations_runtime_service.md`

Integrate with existing Operations Runtime, Background Operations, Operational Targets, cleanroom audit service, CLI, and Steward command center.

## Test Requirements

Prove repeated cycles, event wake, interval wake, pause/resume, graceful stop, crash recovery, stale-lock handling, bounded work, and truthful Office status.

## Validation

```powershell
Clear-Host
cd A:\theestate
python -m py_compile src\estate\core\operations_runtime_daemon.py src\estate\core\operations_runtime_daemon_state.py
python -c "from pathlib import Path; Path('Temp').mkdir(exist_ok=True)"
pytest -q tests/test_operations_runtime_daemon.py tests/test_operations_runtime.py tests/test_operations_runtime_service.py --basetemp Temp/pytest-operations-daemon
python -m estate.cli.main validate-work-package --id WP-0627 --json
```

## Promotion Criteria

Ready when the runtime can remain active across multiple bounded cycles, recover after interruption, and expose real controls and truthful health without requiring the Steward to rerun commands.
