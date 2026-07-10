# Operational Watch Catalog and Control

The Operational Watch catalog extends the existing Background Operations runtime. It does not create a second monitoring system, execute providers, approve institutional acceptance, or control dispatch queues directly.

## Descriptor model

Committed defaults are defined in `estate.core.operational_watch_catalog` as descriptors with:

- identity (`watch_id`, `name`)
- target and category (`repository`, `validation`, `runtime-health`, `queue`, `service`, `artifact-freshness`)
- trigger and cadence
- severity and action class
- dependencies and source paths
- default enabled state
- owner and classification

Existing Background Operations watches are migrated into descriptors and converted back into `BackgroundOperationWatch` objects for evaluation, preserving the runtime behavior.

## Runtime state

Mutable watch control state is written outside committed defaults at:

```text
runtime/background_operations/watch_state.json
```

The runtime state records enable/disable, pause, and override data. The synchronized Background Operations watch file remains runtime state:

```text
runtime/background_operations/watches.json
```

## CLI

```text
python -m estate.cli.main operations-watch list --json
python -m estate.cli.main operations-watch show <watch> --json
python -m estate.cli.main operations-watch enable <watch> --json
python -m estate.cli.main operations-watch disable <watch> --json
python -m estate.cli.main operations-watch pause <watch> --json
python -m estate.cli.main operations-watch evaluate <watch> --json
```

`evaluate` is a dry-run operation. It reports whether the watch would trigger without writing requests, calling providers, performing dispatch execution, or recording institutional acceptance.

## Events and Office summaries

Watch control operations emit local operational events through the existing operational event artifact mechanism. Background Operations cycles continue to emit their existing events, governed requests, status summaries, and markdown reports.

## Boundary

Operational watches only produce evidence and governed requests. No watch directly performs provider execution, dispatch execution, or institutional acceptance.
