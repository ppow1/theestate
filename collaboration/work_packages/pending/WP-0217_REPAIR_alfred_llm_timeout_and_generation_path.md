# REPAIR TASK WP-0217 — Alfred LLM Timeout and Generation Path Repair

## Codex Command

Read collaboration/work_packages/pending/WP-0217_REPAIR_alfred_llm_timeout_and_generation_path.md and do exactly what it says.

## Mode

REPAIR

## Mission

Repair Alfred's local LLM response path so ordinary Steward prompts do not fall back to deterministic text because the Ollama `/api/generate` call times out.

Alfred must reliably produce a real local-LLM response when Ollama is reachable and the selected model is available, or clearly report a blocked/unavailable response state when generation cannot complete. He must not present a deterministic fallback as a completed conversational answer when the intended LLM call failed.

## Problem Statement

The Steward tested Alfred after recent LLM diagnostic and chat-repair work. The Office UI showed that Alfred discovered Ollama and selected `qwen3:8b`, but the actual response failed generation and fell back to deterministic text.

Observed UI output included:

```text
Mode: local_llm_discovered_but_generation_failed
Type: direct_conversational_response
Status: completed
Adapter: available
provider: ollama
model: qwen3:8b
generation attempted: true
generation result: failed
generation endpoint: http://127.0.0.1:11434/api/generate
fallback: Local Ollama invocation failed: timed out
adapter error: TimeoutError: timed out
```

This proves that provider discovery and model detection are not sufficient. Alfred still does not reliably connect through the generation path. The fallback behavior is also misleading because the UI reports a completed response even though the requested LLM generation failed.

## Required Diagnosis

Before changing behavior, inspect:

1. `src/estate/core/resident_interaction.py`
2. Alfred local LLM adapter timeout behavior.
3. Alfred prompt construction and context size.
4. `alfred-llm-diagnostics` output and diagnostic artifact behavior.
5. Office UI display of generation status.
6. Any recent WP-0216 changes that repaired test expectations without proving real generation success.
7. Any interaction between qwen3:8b startup latency, Windows/Ollama cold-load behavior, and adapter timeout.

Determine whether the timeout is caused by:

- adapter timeout too short;
- prompt/context packet too large;
- cold model load taking longer than adapter allows;
- synchronous request design not allowing a pending/in-progress state;
- Ollama invocation parameters;
- server/process contention;
- incorrect endpoint/model selection;
- or another concrete cause.

Document the cause in the report.

## Scope

In scope:

1. Repair Alfred's local LLM generation path for normal conversational prompts.
2. Increase or configure generation timeout in a governed way rather than relying on a too-short fixed timeout.
3. Add a model warm-up or first-token readiness check if needed.
4. Bound Alfred prompt/context size so ordinary prompts do not trigger unnecessary timeouts.
5. Distinguish provider discovery success from generation success.
6. Ensure failed generation is reported as `failed`, `blocked`, or `llm_generation_failed`, not as a normal completed answer.
7. Preserve deterministic fallback only as a clearly labeled degraded fallback.
8. Ensure Office UI shows the exact generation state, provider, model, timeout, and recovery hint.
9. Add tests that simulate slow generation, timeout, success after longer timeout, and fallback labeling.
10. Add a WP-0217 validation recipe, report, runtime validation artifacts, and completion receipt.

Out of scope:

- Estate-wide model selector UI.
- Per-worker model authority.
- Vision model selection.
- AI Services Control Plane redesign.
- Cloud model providers.
- Changing Steward authority semantics.
- Giving Alfred unrestricted host command access.

## Required Behavior

### Successful generation

When Ollama is reachable, selected model is available, and generation completes, Alfred response metadata must show:

```json
{
  "mode": "local_llm",
  "provider": "ollama",
  "model": "qwen3:8b",
  "generation_attempted": true,
  "generation_result": "succeeded",
  "fallback_used": false
}
```

The UI must show that Alfred answered through the local LLM.

### Generation timeout

When Ollama is reachable but generation times out, Alfred metadata must distinguish this from provider unavailability:

```json
{
  "mode": "local_llm_discovered_but_generation_failed",
  "provider": "ollama",
  "model": "qwen3:8b",
  "generation_attempted": true,
  "generation_result": "timeout",
  "fallback_used": true,
  "fallback_reason": "Local Ollama invocation timed out after N seconds"
}
```

The UI must not imply the LLM answer succeeded. It may show a degraded fallback, but must clearly label it.

### Cold model load

If the first generation after reboot or model change takes longer because Ollama is loading the model, Alfred should either:

1. wait within a configurable timeout long enough for normal local model startup; or
2. return a clear `generation_pending_or_timed_out` message with a recovery hint to retry after the model is warm.

Do not silently collapse this into a generic deterministic response.

## Timeout Policy

Implement a configurable timeout policy.

Possible configuration sources, in preferred order:

1. environment variable such as `ESTATE_ALFRED_OLLAMA_TIMEOUT_SECONDS`;
2. local runtime configuration artifact if one already exists;
3. safe default in code.

The default must be realistic for a local 8B model on Windows/Ollama cold start. A 12-second fixed timeout is likely too short.

Document the chosen default and rationale.

## Prompt/Context Size Requirement

Inspect the prompt sent to Ollama. If Alfred's prompt includes excessive context or repeated history, reduce it to a bounded context packet.

Add diagnostics that record approximate prompt size or character count so future failures can distinguish timeout due to prompt bloat from provider issues.

## Required UI / Diagnostic Changes

The Alfred panel and diagnostic command must show:

- provider reachability;
- selected model;
- generation attempted;
- generation result;
- timeout seconds used;
- prompt size summary;
- fallback used;
- fallback reason;
- recovery hint.

The UI must not show `Status: completed` without qualification when the LLM generation failed.

## Required Tests

Add or update tests for:

1. Ollama provider reachable and generation success.
2. Ollama provider reachable but generation timeout.
3. Timeout uses configured value.
4. Cold-start/slow adapter mock succeeds when timeout is sufficient.
5. Failed generation metadata is not labeled as normal `local_llm` success.
6. Deterministic fallback is clearly degraded and includes fallback reason.
7. Office UI renders generation failure distinctly.
8. Alfred diagnostics include timeout seconds and generation result.
9. Prompt/context packet remains bounded.
10. Existing Alfred chat tests remain passing.

Use mocks for timing-sensitive tests. Do not require real Ollama in CI/Codex.

## Required Local Smoke Test Instructions

Document Steward-local smoke test commands equivalent to:

```powershell
CLS
Set-Location A:\theestate
$env:PYTHONPATH="A:\theestate\src"
$env:ESTATE_ALFRED_OLLAMA_TIMEOUT_SECONDS="60"
python -m estate.cli.main alfred-llm-diagnostics --json
python -m estate.cli.main resident-chat send --resident alfred --message "Alfred, give me a short operational greeting and say whether this came from the local LLM." --json
```

The expected result is a real local LLM response, not deterministic fallback.

## Required Artifacts

Create:

```text
operations/alfred/WP-0217_alfred_llm_timeout_and_generation_path_repair_report.md
runtime/residents/alfred/WP-0217_alfred_llm_timeout_and_generation_path_repair_report.json
collaboration/work_packages/completions/WP-0217_codex_done.json
```

The report must include:

- root cause;
- files changed;
- timeout policy;
- prompt/context size findings;
- diagnostic changes;
- UI changes;
- tests run;
- validation commands run;
- local smoke test instructions;
- known limitations;
- recommended next action.

## Required Validation

Run or document equivalent:

```bash
PYTHONPATH=src pytest tests/test_resident_interaction.py tests/test_steward_command_center.py -q
PYTHONPATH=src pytest tests/test_work_package_validation.py tests/test_production_readiness_validation.py -q
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0217 --json
PYTHONPATH=src python -m estate.cli.main validation-production-readiness --json
```

If the repository does not yet have a WP-0217 recipe, add one.

## Completion Artifact Requirements

`collaboration/work_packages/completions/WP-0217_codex_done.json` must include:

```json
{
  "work_package_id": "WP-0217",
  "codex_status": "done",
  "completed_at": "...",
  "branch": "...",
  "summary": "...",
  "root_cause": "...",
  "files_changed": [],
  "timeout_policy": "...",
  "tests_run": [],
  "validation_commands_run": [],
  "known_limitations": [],
  "ready_for_ca_review": true,
  "merge_authority": "ca_verified_auto_merge_allowed"
}
```

Include `pull_request_url_or_not_applicable_reason` if no PR URL is available at completion time.

## Acceptance Criteria

WP-0217 is complete when Alfred can produce a real local Ollama LLM response for a normal conversational prompt under realistic Windows/Ollama timing, failed generation is clearly labeled as failed/degraded rather than normal completion, the timeout policy is configurable, diagnostics explain the generation path, and validation artifacts are complete.

## Merge Class

Class A. Escalate only if repair requires changing Steward authority, resident authority semantics, cloud provider policy, AI Services Control Plane architecture, or model-selection governance beyond the narrow Alfred generation-timeout repair.
