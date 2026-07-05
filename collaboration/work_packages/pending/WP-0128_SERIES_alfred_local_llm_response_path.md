# SERIES TASK WP-0128 — Alfred Local LLM Response Path Repair

## Codex Command

Read collaboration/work_packages/pending/WP-0128_SERIES_alfred_local_llm_response_path.md and do exactly what it says.

## Mode

SERIES

## Mission

Repair Alfred's resident chat path so Alfred actually uses the available local Ollama LLM to answer the Steward's questions instead of returning the same deterministic fallback response for every prompt.

WP-0126 created the resident interaction framework.

WP-0127 added Alfred's Operations Center chat UI and endpoint wiring.

WP-0128 must make Alfred's response generation real.

## Problem Statement

The Steward has confirmed that Alfred's chat UI is now visible and that the API endpoints can be reached after restarting the correct server process.

However, Alfred is currently returning nearly identical responses to materially different questions. For example:

- When asked to define his role, Alfred returned the same generic Estate status / recommended next action response.
- When asked whether he was running from JSON files or an LLM, Alfred returned the same generic Estate status / recommended next action response.

This is not acceptable resident behavior.

The merged code currently detects local LLM availability with `local_llm_status()`, but `process_chat()` always generates the resident response through `_fallback_response(...)` instead of invoking the local model.

The Steward's environment has Ollama installed, reachable, and populated with local models:

- `qwen3:8b`
- `llama3:8b`
- `qwen2.5-coder:7b`
- `llama3.2:3b`

Ollama is reachable at the normal local API endpoint:

```text
http://127.0.0.1:11434
```

This work package must wire the resident interaction layer to the local LLM path when available.

## Required Design Position

Local LLM is the intended production mode for Alfred.

Deterministic fallback is only a fallback.

Do not treat the deterministic fallback response as the primary Alfred behavior.

The target behavior is:

```text
Steward message
  -> Operations Center Alfred chat UI
  -> POST /api/residents/alfred/chat
  -> process_chat("alfred", ...)
  -> resident surface + authority check + Estate context collection
  -> local Ollama model call when available
  -> model-generated Alfred response
  -> persisted resident conversation turn
  -> visible UI response and history reload
```

## Preconditions

Before work begins:

1. Confirm WP-0126 is merged.
2. Confirm WP-0127 is merged.
3. Confirm `src/estate/core/resident_interaction.py` currently detects local LLM status.
4. Confirm Alfred chat UI and endpoint wiring exists in `src/estate/core/steward_command_center.py`.
5. Confirm local deterministic fallback still exists and can be used for tests or unavailable model environments.
6. Inspect existing validation failures for WP-0126/WP-0127 caused by chained validation and repair if the failure is directly related to this work.

If a precondition fails, stop and report the exact blocker.

## Scope

In scope:

1. Add a local Ollama invocation path for resident chat.
2. Use the local LLM path when `local_llm_status()` reports a usable model.
3. Prefer `qwen3:8b` for Alfred when available unless an existing Estate config already specifies another model.
4. Preserve deterministic fallback if Ollama is unavailable, the requested model is unavailable, or model invocation fails.
5. Build a resident-aware Alfred prompt using:
   - Alfred's resident role and office;
   - Alfred's resident API/surface;
   - Alfred's authority boundaries;
   - local-first and non-execution policy;
   - relevant Estate context artifacts;
   - recent conversation history where safe and available;
   - the Steward's current message.
6. Ensure Alfred answers the actual question asked.
7. Ensure Alfred can distinguish different prompt intents.
8. Persist response metadata showing whether the answer came from `local_llm` or `deterministic_fallback`.
9. Persist provider, model, endpoint, and fallback reason if fallback was used.
10. Expose local LLM mode in the Operations Center UI response/history enough that the Steward can tell whether Alfred answered with a model or fallback.
11. Add tests that prove different prompts do not receive the same canned fallback response when local LLM mode is available or when a mocked local LLM adapter is used.
12. Add validation recipe and completion receipt for WP-0128.

Out of scope:

- Rebuilding the resident interaction framework.
- Rebuilding Alfred's UI layout.
- Adding cloud LLM/API support.
- Adding autonomous action execution.
- Granting Alfred new authority.
- Implementing tool use through Ollama.
- Implementing Character Development Engineer behavior.
- Implementing mood arcs.
- Solving all Operations Center layout/navigation issues.

## Required Implementation Details

### 1. Local Ollama adapter

Create or add a small local Ollama adapter in the appropriate Estate module, preferably near `resident_interaction.py` unless a better local-provider registry already exists.

Minimum behavior:

- discover usable model names from `ollama list` and/or `http://127.0.0.1:11434/api/tags`;
- select `qwen3:8b` for Alfred when present;
- otherwise select the first available local model;
- call Ollama locally using its HTTP API or CLI;
- timeout safely;
- return structured result metadata.

The adapter must never call cloud APIs.

Suggested response metadata shape:

```json
{
  "mode": "local_llm",
  "provider": "ollama",
  "model": "qwen3:8b",
  "endpoint": "http://127.0.0.1:11434",
  "fallback_used": false,
  "fallback_reason": null
}
```

Fallback metadata should include `fallback_used = true` and a clear reason.

### 2. Alfred prompt construction

Build a prompt that makes Alfred answer as Alfred, not as a generic artifact summarizer.

The prompt must include at least:

```text
You are Alfred, resident of the Estate, Office of Operations.
You are speaking with Pat, the Steward.
Answer the actual question asked.
Do not repeat the same generic status summary unless the Steward asked for status.
Use local Estate context when relevant.
Do not claim to have executed privileged actions.
If asked about your mode, explain whether this response is local_llm or deterministic_fallback based on metadata available to you.
If you do not know something, say what you can verify from local artifacts and what remains unknown.
```

Also include relevant resident metadata:

- resident id;
- resident display name;
- office;
- role;
- API standard version;
- resident implementation version;
- allowed capabilities;
- authority status for the requested action.

### 3. Estate context collection

Do not dump unlimited files into the model prompt.

Collect a concise context packet from existing local artifacts, such as:

- production-readiness status;
- latest work-package validation status;
- pending work-package queue;
- Alfred surface artifact;
- recent resident conversation history;
- Engineering/CueMastery handoff if present.

The context packet must be small, deterministic, and safe.

If an artifact cannot be read, report that as unavailable rather than crashing.

### 4. Mode transparency

The Steward must be able to tell whether Alfred answered through a local LLM or fallback.

Minimum acceptable implementation:

- the persisted turn records `llm.mode`, `provider`, `model`, and fallback reason if any;
- the API response includes the same metadata;
- the UI displays a small source/mode line, for example:

```text
Mode: local_llm / provider: ollama / model: qwen3:8b
```

or

```text
Mode: deterministic_fallback / reason: Ollama unavailable
```

### 5. Behavior test cases

Add tests proving Alfred's responses are no longer one canned answer.

Minimum test prompts:

```text
Good afternoon Alfred, define your role for me.
```

```text
Alfred, are you running from JSON files or an LLM right now?
```

Expected behavior:

- the role question must answer Alfred's role;
- the mode question must answer mode/model/fallback status;
- the two answers must not be identical canned status summaries;
- neither answer claims unauthorized execution.

Because CI/Codex may not have Ollama installed, implement tests with a mocked local LLM adapter or injectable provider boundary. Also keep a deterministic fallback test.

## Required Files / Artifacts

Create:

`operations/residents/alfred/WP-0128_alfred_local_llm_response_path_report.md`

Create machine-readable companion:

`runtime/residents/alfred/WP-0128_alfred_local_llm_response_path_report.json`

The report must include:

- current git commit;
- local model discovery mechanism;
- selected Alfred model policy;
- actual Ollama endpoint or provider path used;
- prompt construction summary;
- context packet summary;
- fallback behavior;
- UI mode transparency changes;
- example role prompt and response;
- example mode prompt and response;
- tests run;
- validation commands run;
- known limitations;
- recommended next action.

## Required Tests

Add or update tests for:

1. Local LLM adapter discovery parses available Ollama models or mocked provider data.
2. Alfred selects `qwen3:8b` when available.
3. Alfred falls back safely when Ollama is unavailable.
4. `process_chat()` uses the local LLM adapter when available.
5. `process_chat()` does not always call `_fallback_response` when local LLM is available.
6. Role prompt produces a role-relevant response.
7. Mode prompt produces mode/model/fallback-relevant response.
8. Role and mode prompt responses are not identical canned responses.
9. Persisted turn includes `llm.mode`, `provider`, `model`, and fallback metadata.
10. Alfred UI or API response exposes mode/model metadata.
11. Existing WP-0126 and WP-0127 resident interaction tests remain passing.
12. Existing production-readiness validation remains passing or documents unrelated existing blockers.

Run:

```bash
PYTHONPATH=src pytest tests/test_work_package_validation.py tests/test_production_readiness_validation.py -q
PYTHONPATH=src python -m pytest tests/test_resident_conversation_sessions.py tests/test_resident_authority.py tests/test_resident_interaction.py tests/test_steward_command_center.py -q
```

Use closest existing test files if names differ, and document substitutions.

## Required Validation Commands

Run or document equivalent:

```bash
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0126 --json
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0127 --json
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0128 --json
PYTHONPATH=src python -m estate.cli.main validation-production-readiness --json
```

Also run or document equivalent local smoke checks:

```bash
PYTHONPATH=src python -m estate.cli.main resident-interaction-surface --resident alfred --json
PYTHONPATH=src python -m estate.cli.main resident-chat send --resident alfred --message "Good afternoon Alfred, define your role for me." --json
PYTHONPATH=src python -m estate.cli.main resident-chat send --resident alfred --message "Alfred, are you running from JSON files or an LLM right now?" --json
```

If local Ollama is available in the execution environment, record the detected model and confirm the response mode is `local_llm`.

If local Ollama is unavailable in Codex, mock the adapter for tests and document that local smoke validation must be run by the Steward on the Windows machine.

## Required Outputs

Update or create as applicable:

- local Ollama adapter or equivalent local model provider boundary;
- Alfred model selection policy;
- resident prompt construction function;
- bounded Estate context packet function;
- process_chat local LLM invocation path;
- deterministic fallback only on unavailable/failing local model;
- persisted LLM metadata and fallback reason;
- UI/API mode transparency;
- WP-0128 report Markdown and JSON;
- validation recipe registration for WP-0128;
- validation reports/runtime JSON for WP-0128;
- regenerated production-readiness and coverage artifacts;
- `collaboration/work_packages/completions/WP-0128_codex_done.json`.

## WP-0128 Self-Validation Recipe

Add a recipe for WP-0128 that verifies:

- WP-0128 report exists;
- JSON companion parses;
- local model discovery or mock adapter path exists;
- Alfred model selection policy exists;
- process_chat local LLM invocation path exists;
- deterministic fallback remains available;
- role prompt test exists;
- mode prompt test exists;
- role and mode responses are not identical canned responses under mocked local LLM mode;
- persisted turn includes LLM metadata;
- UI/API mode transparency exists;
- WP-0126 and WP-0127 remain passing or unrelated blockers are explicitly reported;
- production-readiness validation executes;
- WP-0128 receipt is complete.

Use cross-platform Python checks only.

## Completion Artifact

Create:

`collaboration/work_packages/completions/WP-0128_codex_done.json`

It must include:

- `work_package_id = WP-0128`;
- `codex_status = done`;
- `completed_at`;
- `branch`;
- `summary`;
- local LLM adapter/provider changes;
- selected Alfred model policy;
- prompt construction summary;
- Estate context packet summary;
- fallback behavior;
- UI/API mode transparency;
- example role prompt and response;
- example mode prompt and response;
- tests run;
- validation commands run;
- known limitations;
- Steward local smoke-test instructions if Codex cannot reach Ollama;
- recommended next action;
- `ready_for_ca_review = true`;
- `merge_authority = ca_verified_auto_merge_allowed`.

## Acceptance Criteria

WP-0128 is complete when Alfred no longer answers materially different Steward questions with the same deterministic fallback text, uses the local Ollama LLM when available, transparently reports the response mode/model, preserves authority boundaries and conversation memory, and falls back deterministically only when the local model path is unavailable or fails.

## Merge Class

Class A. Escalate only if implementation requires changing Steward authority, Alfred authority, resident API governance, server exposure/security policy, memory/redaction policy, adding cloud model dependencies, or production-readiness semantics.
