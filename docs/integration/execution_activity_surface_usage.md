# Execution Activity Surface Usage

Status: Initial local integration  
Classification: Estate Internal  
Work package: WP-EXECUTION-ACTIVITY-SURFACE-001

## Purpose

The execution activity surface aggregates local execution-provider lifecycle
events into a shared current-status artifact for Office of the Steward
visibility. It does not dispatch work, schedule workers, call live providers,
or replace the existing Office command center.

## Runtime Artifacts

The surface writes local runtime artifacts under:

```text
runtime/execution_activity/events.jsonl
runtime/execution_activity/current.json
runtime/execution_activity/report.md
```

These files are local runtime state and are ignored by Git by default.

## Inputs

The generator reads these local sources when available:

```text
runtime/execution_activity/events.jsonl
runtime/codex_bridge/events.jsonl
runtime/codex_bridge/*/events.jsonl
runtime/codex_bridge/current.json
runtime/codex_bridge/current_status.json
```

Missing sources produce warnings in `current.json` and `report.md`; they do not
fail generation.

## CLI

Generate and print the current machine-readable snapshot:

```powershell
python -m estate.cli.main execution-activity --json
```

Generate and print the human-readable report:

```powershell
python -m estate.cli.main execution-activity-report
```

Both commands refresh the local runtime artifacts.

## Python Entry Point

```python
from estate.core.execution_activity import generate_execution_activity_surface

snapshot = generate_execution_activity_surface()
```

## Office of the Steward Hook

The existing Office command center reads the generated artifact at:

```text
runtime/execution_activity/current.json
```

The command center exposes execution activity counts in its status payload and
activity console. The Office remains a consumer of the local JSON artifact; it
does not become the source of execution-provider truth.

## Codex Bridge Feed

Codex Bridge lifecycle events feed this surface through local runtime files:

```text
runtime/codex_bridge/<request_id>/events.jsonl
runtime/codex_bridge/current_status.json
```

The activity surface accepts the bridge aliases already emitted today,
including `current_state`, `security_classification`, `worker`, and
`human_attention_required`.

## Validation

Local validation commands:

```powershell
pytest tests/test_execution_activity.py
python -m estate.cli.main validation-production-readiness --json
```

No live Codex, OpenAI, ChatGPT, Ollama, GitHub, or network access is required.

## Known Limitations

- Provider saturation remains unknown until provider-specific quota reporting exists.
- Codex `/status` remains interactive unless separately automated.
- ChatGPT CLI status is not defined yet.
- Final Office UI presentation may require a separate Office work package.
- This package does not decide whether an Operations Office is required.
