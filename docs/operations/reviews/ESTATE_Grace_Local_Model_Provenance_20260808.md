# Grace Local Model Provenance — 2026-08-08

Status: diagnostic complete; no model assignment was changed.

## Finding

The canonical Open WebUI model remains `estate/grace`, resolving through
`resident_gateway.py` to `process_chat("grace", ...)` in
`resident_interaction.py`, then to the Estate Model Control selection hook and
`LocalOllamaAdapter`.

The Model Control default map now treats Grace as a resident assignment target
with text capability authority. The repair is classification-only: the live
runtime has no Grace-specific model ID and no Estate text default in
`runtime/model_control`, so the current selection is still an explicitly
labeled bootstrap fallback.

| Field | Authoritative finding |
|---|---|
| resident / capability | `grace` / `text` |
| assignment source | `estate_defaults` (no resident-specific model entry is active) |
| assigned Estate model ID | none |
| adapter model name | `qwen3-coder:30b-qwencode-20k` in the observed Grace turn; selected from installed Ollama models by fallback discovery |
| provider / endpoint | `ollama` / `http://127.0.0.1:11434` |
| selection source | configured path: `bootstrap_fallback`; observed turn metadata: `bootstrap_fallback` |
| policy result | `denied` for an absent Model Control assignment; generation remained available through labeled local adapter fallback |
| fallback / bootstrap | active for Grace model selection; no Estate model assignment is active |
| resident-specific assignment support | yes after the classification repair; `grace` is in the resident map and future assignment can be resolved without provider-specific Grace logic |

## Runtime proof

`runtime/resident_interactions/sessions/grace-live-diagnostic.json` records one
ordinary generated Grace turn with `model=qwen3-coder:30b-qwencode-20k`,
`provider=ollama`, endpoint `http://127.0.0.1:11434`,
`generation_attempted=true`, `generation_result_state=succeeded`, and
`selection_source=bootstrap_fallback`. This distinguishes the observed model
from the absent configured Estate assignment and proves the turn reached
Ollama rather than a deterministic fallback.

At diagnostic time Ollama reported nine installed models through `/api/tags`.
`/api/ps` reported `qwen3:8b` resident with approximately 9.97 GB VRAM and a
32,768-token context; that loaded model is not evidence of the observed Grace
turn's model, which is bound by the Grace turn metadata above.

## Validation

- `tests/test_model_control.py`: 3 passed.
- Python compilation passed for the repaired Model Control and interaction
  modules.
- The broader `tests/test_resident_interaction.py` run remains historically
  dirty: 41 passed and 4 unrelated pre-existing assertions failed in vision
  and path/fallback cases. No live model or assignment was changed here.

