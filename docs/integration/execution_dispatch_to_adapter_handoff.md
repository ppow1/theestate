# Execution Dispatch to Adapter Handoff Runtime

Status: Implemented for WP-0503  
Classification: Estate Internal

## Purpose

The dispatch-to-adapter handoff runtime prepares governed provider-neutral handoff evidence from an existing Execution Dispatch Queue item. It bridges the canonical dispatch queue to the existing Execution Provider Adapter Contract without invoking live providers.

## Boundary

Preparing and validating an adapter handoff is not provider execution, authorization, scheduling, worker assignment, or institutional acceptance.

The runtime preserves the institutional stack:

```text
Runtime computes.
Operations conducts.
Traffic Controller constrains.
Execution Providers implement.
Steward governs.
```

## Eligibility

A dispatch item is eligible only when it already exists and satisfies the deterministic checks in `src/estate/core/execution_adapter_handoff_runtime.py`:

- state is explicitly handoff-eligible (`Ready`);
- provider is present;
- classification is present;
- prompt or work-package source is present;
- read scope is present;
- write scope is present for `workspace-write` dispatches;
- authorization or decision reference is present in provider metadata;
- provider is not forbidden;
- provider matches `allowed_providers` when restrictions exist.

The runtime does not infer authorization from the absence of blockers.

## CLI

```bash
python -m estate.cli.main execution-adapter-handoff inspect --dispatch-id <id> --json
python -m estate.cli.main execution-adapter-handoff validate --dispatch-id <id> --json
python -m estate.cli.main execution-adapter-handoff prepare --dispatch-id <id> --json
python -m estate.cli.main execution-adapter-handoff dry-run --dispatch-id <id> --json
```

All commands are deterministic and local. The `dry-run` command uses `DeterministicDryRunExecutionProviderAdapter` and records `live_provider_called: false`.

## Runtime Artifacts

The runtime uses the existing execution-adapter artifact tree:

```text
runtime/execution_adapters/requests/<adapter_request_id>.json
runtime/execution_adapters/results/<adapter_request_id>.json
runtime/execution_adapters/status/latest.json
runtime/execution_adapters/status/summary.json
runtime/execution_adapters/reports/<adapter_request_id>.md
```

The dispatch queue item records the request artifact path in `handoff_reference`. The dispatch state is not automatically changed to `Running` or `Completed`.

## Evidence States

The runtime reports these handoff evidence states:

- `not_ready`
- `blocked`
- `authorized_for_handoff`
- `handoff_prepared`
- `handoff_validated`
- `dry_run_completed`
- `accepted_for_provider_submission`

These are evidence states only, not institutional acceptance states.
