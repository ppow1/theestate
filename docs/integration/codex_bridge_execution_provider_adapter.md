# Codex Bridge Execution Provider Adapter

Status: Implemented for WP-0504  
Classification: Estate Internal

## Purpose

The Codex Bridge Execution Provider Adapter makes the existing Codex Bridge available behind the provider-neutral `ExecutionProviderAdapter` contract. Dispatch and handoff remain canonical; the adapter only translates an already-authorized adapter request into a `CodexBridgeRequest` and maps the bridge result back into an `ExecutionProviderAdapterResult`.

## Supported provider identities

The adapter supports existing local Codex Bridge identities without introducing a new provider registry:

- `provider_id: codex-cli-openai`
- `provider_id: codex-cli-ollama`
- `provider_type: codex-cli` or legacy-compatible `codex_bridge`

Provider profiles are validated by the existing Codex Bridge profile policy. Unsupported provider IDs, invalid profiles, missing decision references, prohibited sandboxes, cloud dispatch/apply requests, and invalid paths are blocked before submit.

## Request translation

`ExecutionProviderAdapterRequest` fields are preserved as follows:

| Adapter request | Codex Bridge request |
| --- | --- |
| `adapter_request_id` | `request_id` as `cbr-<adapter_request_id>` |
| `work_package_id` | `work_package_id` |
| `prompt_source` / `work_package_path` | `prompt_source` |
| `classification` | `classification` |
| `provider_id` | `provider` |
| `profile_label` or `metadata.codex_home_profile` | `codex_home_profile` |
| `read_scope_paths` | `allowed_read_paths` |
| `write_scope_paths` | `allowed_write_paths` |
| `expected_outputs` | `expected_outputs` |
| `metadata.validation_commands` | `validation_commands` |

The adapter preserves `approval_policy: never` by default and relies on Codex Bridge validation to block danger-full-access, cloud execution, cloud apply, bypass flags, denied paths, and invalid profiles.

## Dry-run behavior

Dry run validates the adapter request, translates it to a Codex Bridge request, validates the bridge request, and invokes the bridge only in `dry_run=True` mode. It records `live_provider_called: false` and writes standard execution-adapter artifacts:

```text
runtime/execution_adapters/requests/<adapter_request_id>.json
runtime/execution_adapters/results/<adapter_request_id>.json
runtime/execution_adapters/status/latest.json
runtime/execution_adapters/reports/<adapter_request_id>.md
```

No subprocess, network, GPU, local model, ChatGPT, Ollama, or live Codex CLI call is required for deterministic validation.

## Submit behavior

Submit requires an injected bridge runner. This explicit seam allows deterministic tests to exercise submit behavior with a fake runner while preventing accidental live Codex execution from the adapter itself. Submit does not mark dispatch items completed and does not accept institutional truth.

## CLI

Deterministic commands are available:

```bash
python -m estate.cli.main codex-bridge-adapter validate --request <path> --json
python -m estate.cli.main codex-bridge-adapter dry-run --request <path> --json
```

A live submit command is intentionally not exposed by WP-0504.
