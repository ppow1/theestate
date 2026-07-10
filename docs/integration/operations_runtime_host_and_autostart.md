# Operations Runtime Host and Autostart

The Operations Runtime host is a local process wrapper around the existing `OperationsRuntimeService` loop. It does not create another runtime and does not execute providers directly; all cycles still pass through the governed Operations Runtime service loop.

## Commands

```bash
python -m estate.cli.main operations-runtime host install
python -m estate.cli.main operations-runtime host uninstall
python -m estate.cli.main operations-runtime host start
python -m estate.cli.main operations-runtime host stop
python -m estate.cli.main operations-runtime host restart
python -m estate.cli.main operations-runtime host status
python -m estate.cli.main operations-runtime host run-foreground
```

`run-foreground` is intended for debugging. It accepts the same observation-mode flags used by the service loop, including `--discover-merges`, `--process-audits`, `--process-audits-and-ring2`, `--auto-admit`, `--max-audit-requests`, `--dry-run`, plus host loop controls `--max-cycles` and `--interval-seconds`.

## Durable host evidence

Host process evidence is written outside the repository by default under:

```text
~/.estate/operations_runtime_host/
```

Set `ESTATE_OPERATIONS_RUNTIME_HOST_DIR` to use another external state directory. The host writes:

- `host.pid.json` for process identity.
- `host.lock.json` for the duplicate-host lease.
- `heartbeat.json` for liveness.
- `last_cycle.json` for the latest delegated runtime cycle.
- `startup.json` and `shutdown.json` for lifecycle evidence.
- `crash.json` when foreground hosting exits through an exception.
- `autostart.json` for install/uninstall state.

The host points at the Estate checkout through `ESTATE_OPERATIONS_RUNTIME_ROOT` when launched as a detached process. Active checkout dirtiness does not block hosting because all host evidence stays outside the repository.

## Duplicate-host and stale-lock behavior

Before a host starts, it acquires an external lease in `host.lock.json`. A second start is rejected while the lock belongs to a live process. If the recorded process no longer exists, or the heartbeat is older than the stale-lock threshold, the stale lock is removed and hosting can recover cleanly.

## Autostart behavior

On Windows, `install` records the scheduled-task command that can launch the host at user logon without requiring new Estate infrastructure. In non-Windows environments, `install` writes the same launch manifest so operators and tests can validate the intended autostart command deterministically.

## Status fields

`operations-runtime host status` reports host liveness together with the underlying service status, including:

- `heartbeat_age_seconds`
- `cycle_state`
- `last_verdict`
- `blocking_fault`
- `runtime_status`

These fields are derived from host heartbeat evidence and the existing Operations Runtime status files.
