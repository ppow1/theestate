# WP-0139 Alfred Resident Chat and Action Request Repair Report

## Work Package Id

WP-0139

## Root Cause

The backend deterministic fallback treated most Alfred chat messages as Estate operations summaries because UI submissions always used action=summarize and the fallback response was not intent-gated. The browser submit handler also lacked timeout/transport error handling, so a failed POST could leave the visible status at “Alfred is reviewing local Estate context...” indefinitely.

## Changed Files

- `src/estate/core/resident_interaction.py`
- `src/estate/core/steward_command_center.py`
- `tests/test_resident_interaction.py`
- `tests/test_steward_command_center.py`
- `operations/residents/WP-0139_alfred_resident_chat_and_action_request_repair_report.md`
- `runtime/resident_interactions/WP-0139_alfred_resident_chat_and_action_request_repair_report.json`
- `collaboration/work_packages/completions/WP-0139_codex_done.json`

## Before Behavior

- Simple prompts could be replaced by the generic Estate status block in deterministic fallback.
- `The UI only showed a transient processing string and did not render safe timeout/transport failure diagnostics if fetch failed.`
- Local adapter diagnostics were not exposed as a clear response contract on each turn.

## After Behavior

- `Alfred classifies direct conversation, local summaries, recommendations/status guidance, blocked governed action requests, fallback responses, and completed/failed UI states.`
- Joke prompts get a direct fallback joke when no local LLM is available instead of the generic Estate status summary.
- `Status/triage prompts can still return Estate guidance.`
- The browser submit path renders completed or safe failed states with a 30-second timeout message and retryable endpoint diagnostics.

## Why Alfred Did Not Respond To Joke Prompt

The request path had two failure modes: a transport/timeout exception in the browser was not caught, leaving the old processing message visible; and when the backend did respond in fallback mode, fallback content was always an Estate status block rather than respecting conversational intent such as “tell me a new joke.”

## Simple Conversation Handling

Simple conversational prompts are classified as direct_conversational_response. Local LLM output is used when available; deterministic fallback now provides direct conversational text for low-risk prompts.

## Failed Offline Timeout Surface

Each turn stores diagnostics with adapter availability, selected provider/model, fallback state/reason, safe adapter error, request/response timestamps, and transport/timeout fields. The UI races POST requests against a 30-second timeout and renders “Alfred request failed safely” instead of leaving the processing message indefinitely.

## Governed Action Requests

Prompts asking to start/stop/load TextGen, SillyTavern, Ollama, models, or AI services are classified as blocked_privileged_execution. Alfred does not execute from chat, does not claim Steward authorization, and returns a governed AI Services dry-run plan or copyable Steward command/AI Services Models next step.

## Local Llm Adapter

```json
{
  "adapter_available": false,
  "available": false,
  "discovery": "Ollama unavailable locally: <urlopen error [Errno 111] Connection refused>; ollama executable not found",
  "endpoint": "http://127.0.0.1:11434",
  "fallback_active": true,
  "intended_mode": "local_llm",
  "model": null,
  "models": [],
  "provider": "ollama",
  "selected_model": null,
  "selected_provider": "ollama"
}
```

## Fallback Behavior

When local Ollama discovery or generation is unavailable, deterministic fallback remains local-only, intent-gated, and includes redacted diagnostics.

## Tests Run

- `PYTHONPATH=src pytest -q tests/test_resident_interaction.py tests/test_steward_command_center.py -q`

## Remaining Limitations

- The static UI cannot continue polling a long-running resident request after a browser timeout; it surfaces a retryable safe failure instead.
- `Governed AI Services requests from chat are dry-run/next-step only; actual execution remains in the AI Services approval/execution path.`

