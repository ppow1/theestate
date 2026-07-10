# Background Operations Extension Framework

Background Operations extensions are explicit, committed JSON declarations at `config/background_operations/extensions.json`. The runtime never imports or executes arbitrary files discovered on disk.

## Contracts

The framework validates extension identity, semantic version, classification, enabled state, dependencies, and declared capabilities. Supported capabilities are watch providers, scheduled jobs, operational targets, evidence processors, status contributors, lifecycle hooks, and Office summaries.

## Runtime controls

`BackgroundOperationsExtensionRuntime` supports:

- `inspect` for Office-visible state;
- `validate` for schema, identity, dependency, and boundary checks;
- `dry_run` for deterministic registration previews without writing requests or executing providers;
- `enable` and `disable` for persisted local state.

Failures are isolated: invalid declarations or broken extension watch payloads are reported as quarantined/failure evidence instead of stopping the Background Operations runtime.

## Boundaries

Extensions are declarative. They cannot bypass Traffic Controller, Dispatch, provider adapters, validation, or institutional acceptance. Extension output feeds the existing Background Operations watches and status surfaces only.

## Built-ins

The default committed configuration expresses Estate built-in monitoring and Cue Mastery monitoring through the same contracts used by future departments.

## Validation recipe

Run:

```bash
pytest tests/test_background_operations_extensions.py tests/test_background_operations_extension_runtime.py
```
