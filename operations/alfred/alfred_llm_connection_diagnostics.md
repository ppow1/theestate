# Alfred LLM Connection Diagnostics

Generated for WP-2026-07-07 Alfred LLM Connection Diagnostics.

## Findings

- Alfred chat uses the local-first resident interaction adapter in `src/estate/core/resident_interaction.py`.
- The expected provider is Ollama.
- The endpoint is loaded from `ESTATE_OLLAMA_ENDPOINT`, defaulting to `http://127.0.0.1:11434`.
- Alfred's preferred model is loaded from `ESTATE_ALFRED_OLLAMA_MODEL`, defaulting to `qwen3:8b`.
- Runtime provider discovery is performed against Ollama `/api/tags`, with `ollama list` as a local fallback when the HTTP endpoint is unavailable.
- `data/registry/providers.json` and Discovery observations contain AI Services / Models inventory context, but Alfred chat selection currently depends on live runtime Ollama discovery rather than a persisted provider registry setting.
- After a Windows restart/update, the Office web server can be available while the separate Ollama service is stopped, PATH is not restored for `ollama`, or the preferred model is not installed. Previously this degraded into deterministic fallback without a visible startup diagnostic.

## Implemented Diagnostic Path

Alfred now exposes and writes a local diagnostic artifact at:

- `runtime/residents/alfred/llm_diagnostics.json`

The diagnostic answers:

- Alfred expected provider.
- Configuration source.
- Provider reachable: yes/no/unknown.
- Selected model and discovered models.
- Failure reason, distinguishing missing configuration, unreachable service, missing executable, and unavailable model where practical.
- Recovery hint for Pat.

The Office of the Steward Alfred panel now displays the same diagnostic fields before a chat message is sent, so Office/server readiness is not confused with AI-service readiness.

## Verification

Run:

```bash
PYTHONPATH=src python -m estate.cli.main alfred-llm-diagnostics --json
```

Then start or stop the local Ollama service and refresh the Office. The Alfred panel should update `Provider reachable`, `LLM failure reason`, and `Recovery hint`. No internet access or cloud provider is required.
