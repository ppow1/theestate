# Execution Result Reconciliation

Status: Implemented for WP-0505
Classification: Estate Internal

## Purpose

Execution result reconciliation closes the operational loop between an `ExecutionProviderAdapterResult` and the originating Execution Dispatch item. It records provider-result evidence, updates dispatch lifecycle state conservatively, emits Execution Activity visibility, and prepares successful provider output for validation or review.

Provider completion is not institutional acceptance. The reconciliation runtime always records `institutional_acceptance_state: not_granted`.

## Runtime Module

The runtime is implemented in:

```text
src/estate/core/execution_result_reconciliation_runtime.py
```

It uses existing canonical systems:

- Execution Dispatch queue: `runtime/execution_dispatch/queue.json`
- Execution Dispatch event log: `runtime/execution_dispatch/events.jsonl`
- Execution Activity surface: `runtime/execution_activity/events.jsonl`, `current.json`, and `report.md`
- Execution Adapter artifacts: `runtime/execution_adapters/results/`, `reconciliation/`, and `reports/`

No provider is called by this runtime.

## Lifecycle Mapping

| Adapter result status | Dispatch outcome |
| --- | --- |
| `accepted` | Leaves `Queued`, `Waiting`, `Ready`, or `Running` in place and records evidence. |
| `completed` | Moves to `Validation` when `validation_required` is true or unspecified. |
| `completed` with `validation_required: false` | Moves to `Completed` while preserving `institutional_acceptance_state: not_granted`. |
| `failed` | Moves to `Failed` and sets attention required. |
| `blocked` | Moves to `Blocked` and sets attention required. |
| `dry_run_completed` | Does not advance dispatch into running, validation, or completion; records dry-run evidence only. |

Terminal-state regression is blocked without override authority. Cancelled dispatch items are not reopened.

## Identity Checks

Reconciliation validates that:

- the dispatch item exists;
- the result dispatch ID matches the requested dispatch item;
- the adapter request ID matches dispatch provider metadata or handoff reference when available;
- the provider ID matches the dispatch provider;
- the adapter status is one of the contract statuses;
- result artifacts are present and well formed for completed, failed, blocked, and dry-run results;
- lifecycle transition is possible.

## Idempotency

The runtime computes a SHA-256 hash of the canonical adapter result payload. Replaying the same result for the same dispatch item returns `status: replayed` and does not append duplicate dispatch or activity events.

## CLI

```bash
python -m estate.cli.main execution-result-reconciliation inspect --dispatch-id <id> --json
python -m estate.cli.main execution-result-reconciliation reconcile --dispatch-id <id> --result <path> --json
python -m estate.cli.main execution-result-reconciliation report --dispatch-id <id>
```

The CLI is deterministic and local-only. It does not invoke Codex CLI, ChatGPT CLI, Ollama, GPU, network services, movement authorization, or institutional acceptance.

## Activity Events

The runtime emits existing Execution Activity records for:

- `provider_result_received`
- `provider_result_blocked`
- `provider_execution_failed`
- `provider_execution_completed`
- `provider_result_ready_for_validation`
- `provider_result_requires_attention`

Each activity record distinguishes provider result state, dispatch state, validation preparation, attention state, and institutional acceptance state.
