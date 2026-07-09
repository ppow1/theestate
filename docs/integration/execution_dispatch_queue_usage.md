# Execution Dispatch Queue Usage

Status: Initial local integration  
Classification: Estate Internal  
Work package: WP-EXECUTION-DISPATCH-QUEUE-001

## Purpose

The execution dispatch queue stores local provider-neutral execution intent
between work packages and execution providers. It does not schedule work,
auto-select providers, or invoke live providers by default.

## Runtime Artifacts

The queue writes local runtime artifacts under:

```text
runtime/execution_dispatch/queue.json
runtime/execution_dispatch/events.jsonl
runtime/execution_dispatch/current.json
runtime/execution_dispatch/report.md
runtime/execution_dispatch/handoffs/
```

These files are local runtime state and are ignored by Git by default.

## Dispatch Request

Minimal request JSON:

```json
{
  "dispatch_id": "dispatch-example-001",
  "work_package_id": "WP-EXAMPLE",
  "title": "Review and implement a bounded package",
  "requested_by": "Steward",
  "assigned_worker": "Codex Worker",
  "provider": "codex-cli-openai",
  "profile_label": "A2C3",
  "classification": "Estate Internal",
  "priority": "High",
  "state": "Queued",
  "prompt_source": "docs/governance/workers/WP-EXAMPLE.md",
  "sandbox": "read-only",
  "allowed_read_paths": ["docs/governance/workers"],
  "allowed_write_paths": [],
  "allowed_providers": ["codex-cli-openai"],
  "forbidden_providers": [],
  "dependencies": [],
  "validation_commands": ["pytest -q tests/test_example.py"],
  "attention_required": false
}
```

`classification` is required. Provider/profile labels such as `A2C3`,
`A2C2`, `local-ollama`, `codex-cli-openai`, and `codex-cli-ollama` are stored
as labels and are not treated as authority to bypass Ingrid/security
boundaries.

## CLI

Enqueue a request:

```powershell
python -m estate.cli.main execution-dispatch enqueue --file runtime/execution_dispatch/example_request.json --json
```

List queue state:

```powershell
python -m estate.cli.main execution-dispatch list --json
python -m estate.cli.main execution-dispatch list --state Ready --json
```

Inspect and update items:

```powershell
python -m estate.cli.main execution-dispatch inspect dispatch-example-001 --json
python -m estate.cli.main execution-dispatch update-state dispatch-example-001 --state Running --json
python -m estate.cli.main execution-dispatch block dispatch-example-001 --reason "Waiting for Steward approval" --json
python -m estate.cli.main execution-dispatch attention dispatch-example-001 --reason "Boundary approval needed" --json
python -m estate.cli.main execution-dispatch cancel dispatch-example-001 --json
python -m estate.cli.main execution-dispatch complete dispatch-example-001 --result-reference runtime/codex_bridge/example/audit.json --json
```

Generate Office-visible artifacts:

```powershell
python -m estate.cli.main execution-dispatch snapshot --json
python -m estate.cli.main execution-dispatch-report
```

## Codex Bridge Dry-Run Handoff

For items targeting `codex-cli-openai` or `codex-cli-ollama`, the queue can
write a Codex Bridge request shape:

```powershell
python -m estate.cli.main execution-dispatch prepare-handoff dispatch-example-001 --json
```

The handoff preserves:

- `dispatch_id`
- `work_package_id`
- `prompt_source`
- `provider`
- `profile_label`
- `sandbox`
- `classification`
- `allowed_read_paths`
- `allowed_write_paths`
- `validation_commands`

The handoff file includes `dry_run: true` and
`handoff_mode: dry_run_only_no_live_provider_invocation`. Creating the handoff
does not call Codex, OpenAI, Ollama, ChatGPT, GitHub, or any browser provider.

## Office of the Steward Hook

The Office command center reads:

```text
runtime/execution_dispatch/current.json
```

When present, the command center exposes dispatch counts in its status payload
and activity console. The Operator Activity Stream also treats the dispatch
snapshot as a local source. The Office remains a consumer of local queue state;
it does not become the dispatch authority.

## Events

Queue events are appended to:

```text
runtime/execution_dispatch/events.jsonl
```

Implemented event types include:

- `dispatch_enqueued`
- `dispatch_ready`
- `dispatch_started`
- `dispatch_blocked`
- `dispatch_awaiting_approval`
- `dispatch_cancelled`
- `dispatch_completed`
- `dispatch_failed`
- `dispatch_handoff_prepared`

## Validation

Local validation commands:

```powershell
pytest -q tests/test_execution_dispatch.py
python -m estate.cli.main execution-dispatch list --json
python -m estate.cli.main validation-production-readiness --json
```

No live Codex, OpenAI, ChatGPT, Ollama, GitHub, browser, or network access is
required.

## Known Limitations

- This is not the full Orchestrator.
- This does not decide final scheduling policy.
- This does not perform live provider execution by default.
- Provider saturation and quota data may remain unknown.
- ChatGPT CLI dispatch shape is not finalized.
- Final Operations Office authority remains an architectural question for Steward review.
