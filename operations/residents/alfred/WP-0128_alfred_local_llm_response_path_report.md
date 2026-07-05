# WP-0128 Alfred Local LLM Response Path Report

## Summary
WP-0128 repairs Alfred's resident chat response path so `process_chat()` uses a local-only Ollama provider when models are available and only uses deterministic fallback when discovery or generation fails.

## Current Git Commit
`fcbd48a7e5b3c19462d878e5797afc1af925359c`

## Local Model Discovery Mechanism
`LocalOllamaAdapter.discover_models()` first probes `http://127.0.0.1:11434/api/tags`; if HTTP probing fails it falls back to `ollama list`. No cloud API path is present.

## Selected Alfred Model Policy
Alfred prefers `qwen3:8b` when present. If `qwen3:8b` is absent, Alfred selects the first discovered local model.

## Provider Endpoint
Default endpoint: `http://127.0.0.1:11434`. Codex validation environment result: Ollama unavailable (`connection refused`; no `ollama` executable), so automated tests use a mocked adapter.

## Prompt Construction Summary
Alfred's prompt identifies him as Alfred, resident of the Estate, Office of Operations, speaking with Pat the Steward. It directs Alfred to answer the actual question, avoid generic status repetition, preserve non-execution/authority boundaries, and disclose local LLM/fallback mode when asked.

## Context Packet Summary
The context packet is bounded and deterministic. It includes concise availability summaries for production readiness, local operational validation, assignment queue, Alfred's surface artifact, Engineering/CueMastery handoff, up to eight pending work-package filenames, and recent active conversation history.

## Fallback Behavior
Deterministic fallback remains available. It is used only when local Ollama discovery fails, no usable model is selected, or local generation fails. Persisted metadata includes `llm.mode`, `provider`, `model`, `endpoint`, `fallback_used`, and `fallback_reason`.

## UI Mode Transparency Changes
The Operations Center Alfred chat history and live response display a source line such as `Mode: local_llm / provider: ollama / model: qwen3:8b` or a deterministic fallback reason.

## Example Role Prompt and Response
Prompt: `Good afternoon Alfred, define your role for me.`

Mocked local LLM response: `Pat, my role is Alfred of the Office of Operations: I coordinate local Estate status, recommendations, and proposed next actions without executing privileged work.`

## Example Mode Prompt and Response
Prompt: `Alfred, are you running from JSON files or an LLM right now?`

Mocked local LLM response: `Pat, this answer is being generated through local_llm with provider ollama and model qwen3:8b; JSON artifacts provide context, not the whole response.`

## Tests Run
- `PYTHONPATH=src pytest tests/test_resident_interaction.py -q`
- `PYTHONPATH=src pytest tests/test_work_package_validation.py tests/test_production_readiness_validation.py -q`
- `PYTHONPATH=src python -m pytest tests/test_resident_conversation_sessions.py tests/test_resident_authority.py tests/test_resident_interaction.py tests/test_steward_command_center.py -q`

## Validation Commands Run
- `PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0123 --json`
- `PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0126 --json`
- `PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0127 --json`
- `PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0128 --json`
- `PYTHONPATH=src python -m estate.cli.main validation-production-readiness --json`
- `PYTHONPATH=src python -m estate.cli.main resident-interaction-surface --resident alfred --json`
- `PYTHONPATH=src python -m estate.cli.main resident-chat send --resident alfred --message "Good afternoon Alfred, define your role for me." --json`
- `PYTHONPATH=src python -m estate.cli.main resident-chat send --resident alfred --message "Alfred, are you running from JSON files or an LLM right now?" --json`

## Known Limitations
Codex cannot reach local Ollama in this container. The Steward should run the two resident-chat smoke checks on the Windows machine with Ollama running to confirm true `local_llm` mode with `qwen3:8b`.

## Recommended Next Action
Run local Steward smoke validation against the Windows Ollama service and verify the Operations Center displays `Mode: local_llm / provider: ollama / model: qwen3:8b`.
