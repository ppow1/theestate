# Open WebUI Campaign 01 — Steward Local Validation Instructions

Repository validation has repaired the resident fallback conversation path and replaced the commissioned sine/formant placeholder with an honest local intelligible-TTS boundary. Codex could not locate an approved TTS engine in this container and did not have a running Open WebUI browser process, so final human listening and UI selection remain Steward-local validation items.

## Launch the resident gateway

```bash
PYTHONPATH=src python -m estate.core.resident_gateway
```

If your entry point differs, point Open WebUI at the gateway base URL reported by the Estate launch wrapper and verify `GET /v1/models` contains `estate/alfred`, `estate/helen`, `estate/ingrid`, `estate/grace`, `estate/evelyn`, `estate/eleanor`, `estate/marie`, and `estate/judy`.

## Generate local intelligible speech

Install or expose one approved local TTS engine: Kokoro, F5-TTS, espeak/espeak-ng, speech-dispatcher, macOS `say`, or set `ESTATE_TTS_COMMAND` to a local command accepting `<output-wav> <text>`.

```bash
PYTHONPATH=src python - <<'PY'
from estate.core.resident_voice_commissioning import commissioning_report
print(commissioning_report())
PY
```

Generated samples, when an approved local TTS engine is discoverable, are written under `runtime/voice/listening_samples/<resident>/`.

## End-to-end Open WebUI validation

For each resident model in Open WebUI:

1. Select the model.
2. Send: `The Estate feels noisy. What is the first useful move?`
3. Confirm the answer sounds resident-specific rather than generic assistant boilerplate.
4. Send: `Stay with me for one more turn. What should I watch next?`
5. Confirm the resident identity remains stable.
6. Generate audio through the Estate TTS path and listen for intelligible speech.
7. Record latency, failures, and voice tuning notes in the Steward review matrix.

Grace-specific check: select `estate/grace` and confirm she is visible and conversationally available as Director of Operations without claiming Steward authority.
