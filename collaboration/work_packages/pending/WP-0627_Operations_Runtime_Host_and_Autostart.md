# WP-0627 - Operations Runtime Host and Autostart

Status: Proposed
Priority: Critical
Owner: Chief Architect #6
Classification: Estate Internal

## Mission

Turn the existing Operations Runtime service loop into a durable local host that starts with the Estate workstation, runs without an open terminal, survives user logoff where supported, and exposes truthful service health.

## Required Implementation

- Add a Windows-compatible host wrapper for the existing runtime service loop.
- Support install, uninstall, start, stop, restart, status, and foreground-debug modes.
- Prefer a scheduled-task or service-wrapper implementation that does not require new infrastructure.
- Load configuration from the existing runtime/operational-target configuration surfaces.
- Write PID, heartbeat, last-cycle, startup, shutdown, and crash evidence outside the repository.
- Refuse duplicate hosts through a lease/lock.
- Recover cleanly from stale locks.
- Do not run provider execution directly.

Expected touchpoints:

```text
src/estate/core/operations_runtime_host.py
src/estate/core/operations_runtime_service.py
src/estate/cli/main.py
tests/test_operations_runtime_host.py
docs/integration/operations_runtime_host_and_autostart.md
```

## CLI

Provide commands equivalent to:

```text
operations-runtime host install
operations-runtime host uninstall
operations-runtime host start
operations-runtime host stop
operations-runtime host restart
operations-runtime host status
operations-runtime host run-foreground
```

## Acceptance

- Host runs the existing service loop; it does not create a second runtime.
- Restart resumes from durable runtime state.
- Duplicate start is rejected safely.
- Active checkout dirtiness does not prevent hosting.
- Status reports heartbeat age, cycle state, last verdict, and blocking fault.
- Deterministic tests and WP validation pass.
- Completion receipt: `collaboration/work_packages/completions/WP-0627_codex_done.json`.

## Codex Handoff

```text
Read collaboration/work_packages/pending/WP-0627_Operations_Runtime_Host_and_Autostart.md and do exactly what it says.
```
