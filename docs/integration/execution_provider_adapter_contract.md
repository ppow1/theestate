# Execution Provider Adapter Contract

Status: Implemented for WP-0613  
Classification: Estate Internal

## Purpose

The Execution Provider Adapter Contract is the provider-neutral seam between Orchestrator dispatch records and concrete execution providers. The Orchestrator and dispatch queues produce governed records; adapters translate those records into provider-specific handoffs without making Orchestrator code depend on Codex Bridge, ChatGPT CLI, Ollama, or future providers.

## Runtime Contract

The contract is implemented in `src/estate/core/execution_provider_adapter.py` and includes:

- `ExecutionProviderAdapterRequest` for provider-neutral handoff requests.
- `ExecutionProviderAdapterResult` for provider-neutral adapter outcomes.
- `AdapterValidationStatus` for compatibility and boundary validation.
- `ExecutionProviderAdapter` as the abstract adapter interface.
- `DeterministicDryRunExecutionProviderAdapter` for local validation without provider execution.

Allowed result statuses are `accepted`, `dry_run_completed`, `blocked`, `failed`, and `completed`.

## Runtime Artifacts

Runtime helpers in `src/estate/core/execution_provider_adapter_runtime.py` write and load local artifacts under:

```text
runtime/execution_adapters/requests/<request_id>.json
runtime/execution_adapters/results/<request_id>.json
runtime/execution_adapters/status/latest.json
runtime/execution_adapters/status/summary.json
```

These paths are runtime evidence paths and should not be treated as committed live execution logs unless a work package explicitly requires evidence.

## CLI Validation

The CLI surface is deterministic and does not call live providers:

```bash
python -m estate.cli.main execution-provider-adapter validate --request runtime/execution_adapters/requests/example.json --json
python -m estate.cli.main execution-provider-adapter dry-run --request runtime/execution_adapters/requests/example.json --json
```

The dry-run command validates the request, writes request/result/status artifacts, and records `live_provider_called: false` in result metadata.

## Dispatch Compatibility

`ExecutionProviderAdapterRequest.from_dispatch_record()` accepts an Orchestrator `DispatchRecord` or compatible dictionary. It maps provider-neutral fields as follows:

| Dispatch field | Adapter request field |
| --- | --- |
| `dispatch_id` | `dispatch_id` |
| `provider_id` | `provider_id` |
| `provider_type` | `provider_type` |
| `work_package_id` | `work_package_id` |
| `work_package_path` | `work_package_path` and default `prompt_source` |
| `classification` | `classification` |
| `allowed_paths` | `read_scope_paths` |
| `forbidden_paths` | `blocked_scope_paths` |
| `expected_outputs` | `expected_outputs` |
| `validation_required` | `validation_required` |
| `boundary_review_reference` | `boundary_review_reference` |
| `decision_reference` | `decision_reference` |

This preserves the accepted stack: Traffic Controller / Operations Manager decides movement, Orchestrator creates dispatch records, and execution provider adapters perform provider handoff.

## Codex Bridge Compatibility Without Coupling

Codex Bridge can be represented as an adapter behind this contract by setting provider-neutral fields such as:

```json
{
  "provider_id": "codex-cli-openai",
  "provider_type": "codex_bridge",
  "profile_label": "A2C1",
  "metadata": {
    "codex_home_profile": "business-seat-1",
    "sandbox": "read-only"
  }
}
```

The adapter contract stores Codex-related values only as provider metadata. Orchestrator code does not need to import or call Codex Bridge internals directly.

## Boundary Notes

The deterministic dry-run adapter never invokes Codex CLI, ChatGPT CLI, Ollama, GPUs, network services, or provider work. It exists only to validate request shape, classification, required IDs, and read/write/blocked path compatibility.
