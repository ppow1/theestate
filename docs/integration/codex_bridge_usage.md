# Codex Bridge Usage

Status: Implemented for review  
Classification: Estate Internal  
Work package: WP-CODEX-BRIDGE-IMPLEMENTATION  
Runtime artifact root: `runtime/codex_bridge/`

## Purpose

The Codex Bridge is a conservative local adapter around `codex exec`. It reads an approved prompt or work package, validates the boundary request, constructs a bounded CLI command, captures output, normalizes/parses the result, emits lifecycle events and a current-status snapshot, and writes a local audit record.

The bridge does not implement Codex Cloud apply, unrestricted cloud dispatch, `danger-full-access`, approval/sandbox bypass flags, or arbitrary Codex CLI passthrough.

## Python Entry Point

```python
from estate.core.codex_bridge import CodexBridgeRequest, run_codex_bridge_request

request = CodexBridgeRequest(
    request_id="cbr-example-001",
    prompt_source="docs/governance/workers/WP-CODEX-BRIDGE-IMPLEMENTATION.md",
    classification="Estate Internal",
    work_package_id="WP-CODEX-BRIDGE-IMPLEMENTATION",
    provider="codex-cli-openai",
    codex_home_profile="default",
    sandbox="read-only",
    allowed_read_paths=["docs/governance/workers"],
    cwd=".",
)

result = run_codex_bridge_request(request, dry_run=True)
```

## CLI Entry Point

Create a request JSON:

```json
{
  "request_id": "cbr-example-001",
  "prompt_source": "docs/governance/workers/WP-CODEX-BRIDGE-IMPLEMENTATION.md",
  "classification": "Estate Internal",
  "work_package_id": "WP-CODEX-BRIDGE-IMPLEMENTATION",
  "provider": "codex-cli-openai",
  "codex_home_profile": "default",
  "sandbox": "read-only",
  "allowed_read_paths": ["docs/governance/workers"],
  "cwd": "."
}
```

Dry-run request validation example:

```powershell
python -m estate.cli.main codex-bridge --request runtime/codex_bridge/example_request.json --dry-run --json
```

Dry-run mode validates policy and writes lifecycle/status/audit artifacts without invoking Codex.

## Command Shapes

Default read-only command:

```powershell
codex --ask-for-approval never exec --sandbox read-only --color never --ephemeral --json -
```

Local Ollama mechanics command when requested:

```powershell
codex --ask-for-approval never exec --oss --local-provider ollama -m qwen2.5-coder:7b --sandbox read-only --color never --ephemeral --json -
```

Workspace-write requests use `--sandbox workspace-write` only after explicit allowed write paths pass bridge validation. `danger-full-access`, bypass flags, cloud dispatch, and cloud apply are rejected by code.

## Parser-Only JSONL Fixture

```python
from estate.core.codex_bridge import parse_jsonl_output

fixture = "\n".join([
    '{"type":"thread.started","thread_id":"thread-1"}',
    '{"type":"turn.started"}',
    '{"type":"item.completed","item":{"type":"agent_message","text":"done"}}',
    '{"type":"turn.completed","usage":{"input_tokens":10,"cached_input_tokens":0,"output_tokens":2,"reasoning_output_tokens":0}}',
])

parsed = parse_jsonl_output(fixture)
assert parsed.final_message == "done"
assert parsed.usage["input_tokens"] == 10
```

## Runtime Visibility Artifacts

Each bridge request writes local artifacts under:

```text
runtime/codex_bridge/<request_id>/
```

Key files:

- `events.jsonl`: structured lifecycle events such as `job_accepted`, `execution_started`, `result_returned`, `execution_complete`, `execution_failed`, and `policy_denied`.
- `status.json`: per-request current-status snapshot for Office consumption.
- `audit.json`: local audit record with request metadata, command, prompt hash, output hashes, usage, event references, status reference, changed files, tests run, limitations, and promotion recommendation.
- `runtime/codex_bridge/current_status.json`: latest bridge status snapshot.

Terminal output is not the operational visibility source. The lifecycle event stream and status snapshot are the reviewable operational surface for the Office of the Steward.

## Smoke Tests

Local-provider smoke test, only if both `codex` and `ollama` are available:

```powershell
python -m estate.cli.main codex-bridge --request runtime/codex_bridge/ollama_smoke_request.json --json
```

The request should use:

```json
{
  "provider": "codex-cli-ollama",
  "model": "qwen2.5-coder:7b",
  "codex_home_profile": "local-ollama",
  "sandbox": "read-only",
  "allowed_read_paths": ["docs/integration"],
  "prompt_source": "docs/integration/codex_bridge_usage.md",
  "classification": "Estate Internal"
}
```

OpenAI-backed smoke test should run only when credentials, network access, and Ingrid-approved prompt classification are available. Use the same CLI entry point with `provider` set to `codex-cli-openai`.

Live Codex execution was skipped during this implementation unless separately reported in the completion receipt. Unit tests and validation recipes use mocked process results and dry-run execution only.

## Validation

Local-first validation commands:

```powershell
pytest tests/test_codex_bridge.py
python -m estate.cli.main validate-work-package --id WP-CODEX-BRIDGE-IMPLEMENTATION --json
python -m estate.cli.main validation-production-readiness --json
```

These commands must not call OpenAI or Codex Cloud.

## Preserved Limitations

- Non-interactive `/status` automation is unknown.
- Authenticated multi-seat concurrency is unknown.
- Codex Cloud task lifecycle is unknown.
- Codex Cloud apply is unapproved and blocked by this bridge.
- OpenAI-backed JSONL usage shape needs authenticated verification.
- Provider-level saturation and quota reporting may require a later capacity-monitoring package.
- Office of the Steward UI consumption may require a later integration package.

