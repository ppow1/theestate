# WP-0143 Alfred Local LLM Adapter Truthfulness and Generation Report

## Root Cause
Alfred had two separate concepts collapsed into the same label: Ollama model discovery and local model generation. `process_chat` built provisional metadata with `mode: local_llm` as soon as the adapter discovered local models, before the final visible response was proven to come from a generation endpoint. When generation failed or was bypassed by deterministic fallback, that provisional label could still be exposed by the turn metadata/UI.

## Root-Cause Questions
1. **Did Alfred actually call a local LLM generation endpoint for the observed joke response?** The inspected code shows Alfred only attempted generation when `local_llm_status()` reported models available. If generation failed or availability was false, deterministic fallback produced the visible joke. The repeated canned joke is therefore evidence of deterministic fallback, not proven local generation.
2. **If yes, which endpoint, provider, and model were used?** The real generation path is provider `ollama`, endpoint `POST http://127.0.0.1:11434/api/generate`, selected model from `ESTATE_ALFRED_OLLAMA_MODEL` (`qwen3:8b`) when present, otherwise the first discovered model.
3. **If yes, what prompt was sent and what response came back, after safe redaction?** Diagnostics now store only a safe prompt summary, not the full prompt. The prompt includes Alfred role instructions, authority status, bounded Estate context, and the Steward message. The generated response is the final visible response only when mode is `local_llm_generated`.
4. **If no, why did the UI report `Mode: local_llm`?** Because metadata was initialized as `local_llm` based on adapter/discovery intent before final generation success was known.
5. **Why does the response metadata mention fallback while also reporting local LLM mode?** The older metadata allowed `mode: local_llm` and `fallback_used: true` to coexist. That mixed state has been replaced with explicit final modes.
6. **Is Alfred discovering Ollama models but failing to generate from them?** That state is now represented as `local_llm_discovered_but_generation_failed`, with generation attempted/result diagnostics.
7. **Is Alfred selecting a model but never calling generation?** Discovery-only no longer marks a response generated. If models are available, ordinary conversational prompts attempt generation via `/api/generate` before fallback.
8. **Is Alfred using deterministic fallback while labeling it as local LLM?** That was the repair target; deterministic fallback is now labeled `deterministic_fallback` unless a governed action is refused as `blocked_privileged_execution`.
9. **Is the repeated skeleton joke hard-coded in the fallback path?** The skeleton joke was not present in the inspected current fallback path, but fallback had only one local joke. It now rotates through a small deterministic fallback set and states fallback novelty is limited.

## Changed Files
- `src/estate/core/resident_interaction.py`
- `src/estate/core/steward_command_center.py`
- `tests/test_resident_interaction.py`

## Before Behavior
- Model discovery could result in UI text equivalent to `Mode: local_llm` even if deterministic fallback produced the response.
- Fallback metadata could mention fallback while the mode still looked like local LLM.
- Joke fallback returned one canned joke.
- Diagnostics did not explicitly expose generation attempted/result state.

## After Behavior
- Final modes are explicit: `local_llm_generated`, `local_llm_discovered_but_generation_failed`, `deterministic_fallback`, and `blocked_privileged_execution`.
- Ollama discovery alone is not treated as generation.
- Ollama generation success is the only path that sets `local_llm_generated`.
- Generation failure after model discovery is reported separately from deterministic no-model fallback.
- UI source lines include mode, generation attempted, generation result, generation endpoint, discovered model count, fallback reason, and sanitized error.

## Generation Endpoint Behavior
- Provider: `ollama`.
- Discovery endpoint: `GET /api/tags`.
- Generation endpoint: `POST /api/generate` with `stream: false`.
- The adapter records `generation_attempted`, `generation_endpoint`, `generation_result_state`, and `discovered_models_count`.

## Fallback Behavior
- Deterministic fallback is labeled `deterministic_fallback` when no generation endpoint produced the response.
- If models were discovered but generation failed, the response falls back but the mode is `local_llm_discovered_but_generation_failed`.
- Governed action requests remain refused from resident chat and are labeled `blocked_privileged_execution`.

## Repeated Joke Behavior
Fallback joke responses rotate across a small local set and include a statement that deterministic fallback has limited novelty. Local LLM joke novelty comes from the model when `local_llm_generated` is active.

## Diagnostics Added
Per turn diagnostics now include provider, endpoint, discovered model count, selected model, generation attempted, generation endpoint, generation result state, fallback active, fallback reason, sanitized error, safe prompt summary, request timestamp, and response timestamp.

## Tests Run
- `PYTHONPATH=src python -m pytest tests/test_resident_interaction.py tests/test_steward_command_center.py -q` — passed, 65 tests.

## Remaining Limitations
- The adapter remains local-only and uses Ollama `/api/generate`; it does not add a cloud fallback.
- Diagnostics intentionally store only a prompt summary to avoid leaking sensitive prompt content.
- Deterministic fallback novelty is limited by design and clearly labeled.
