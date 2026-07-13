# CCA Campaign 09 Resident Audible Voice Commissioning Report

## Installed-capability audit

- Verified local TTS provider: `estate.local.waveform.tts`.
- Engine: Python standard-library deterministic WAV synthesizer.
- Model strategy: engine-neutral resident vocal traits rendered as differentiated local WAV output. This distinguishes verified live audio generation from repository-only voice descriptions.
- Endpoint/path: in-process `estate.core.resident_voice_commissioning.synthesize_resident_sample`; Open WebUI workflow calls the canonical resident gateway and then attaches generated local WAV audio metadata.
- Launch method: importable Estate runtime module. No external paid API and no network dependency are required.
- Health check: passed in tests and commissioning generation; generated WAV files are playable PCM mono files at 16 kHz.
- Streaming: not claimed. The commissioned path is generated WAV playback. Caller-side cancellation before playback is safe; long-running streaming interruption is a remaining enhancement.

## Resident voice binding matrix

| Resident | Gateway model | Voice ID | Provenance | Fallback |
| --- | --- | --- | --- | --- |
| Alfred | `estate/alfred` | `estate-local-alfred-baritone` | `residents/alfred.md` and gateway model `estate/alfred` | `estate-local-neutral-low` |
| Helen | `estate/helen` | `estate-local-helen-clear-mezzo` | `residents/helen.md` and gateway model `estate/helen` | `estate-local-neutral-mid` |
| Ingrid | `estate/ingrid` | `estate-local-ingrid-low-alto` | `docs/residents/ingrid/Ingrid_Voice_Identity_v0_1.md` and gateway model `estate/ingrid` | `estate-local-neutral-low` |
| Grace | `estate/grace` | `estate-local-grace-executive-alto` | `operations/residents/surfaces/grace.json` and gateway model `estate/grace` | `estate-local-neutral-mid` |
| Evelyn | `estate/evelyn` | `estate-local-evelyn-warm-contralto` | `operations/residents/surfaces/evelyn.json` and gateway model `estate/evelyn` | `estate-local-neutral-mid` |

The generated machine-readable matrix is `runtime/voice/resident_voice_bindings.json`.

## Open WebUI integration report

Open WebUI continues to use the canonical OpenAI-compatible resident gateway. For single-resident requests, `synthesize_open_webui_resident_response()` calls `chat_completion()`, extracts the resident response, resolves the live resident voice binding, generates a local WAV file, and attaches audio metadata under `estate.audio`. This avoids creating a second resident registry or a competing gateway path.

## Listening-sample index

Commissioning generated two samples per covered resident under `runtime/voice/listening_samples/<resident>/`:

- `neutral_differentiation.wav` — shared neutral line for audible differentiation checks.
- `character_fit.wav` — resident-specific line exercising warmth, seriousness, humor timing, emphasis, and confidence.

## Steward voice review matrix

| Resident | Voice ID | Review state | Tune notes |
| --- | --- | --- | --- |
| Alfred | `estate-local-alfred-baritone` | Pending Steward listening review | |
| Helen | `estate-local-helen-clear-mezzo` | Pending Steward listening review | |
| Ingrid | `estate-local-ingrid-low-alto` | Pending Steward listening review | |
| Grace | `estate-local-grace-executive-alto` | Pending Steward listening review | |
| Evelyn | `estate-local-evelyn-warm-contralto` | Pending Steward listening review | |

## Stability and fallback

- Repeated synthesis is deterministic and writes resident-specific WAV samples.
- Long responses are bounded to a finite sample duration for review playback rather than claiming full streaming narration.
- Unsupported or non-live residents return `resident_voice_binding_not_live` instead of exposing staged assets.
- Fallback voice IDs are recorded per resident without replacing the primary binding.
- Service restart recovery is equivalent to module reload because the current approved stack has no resident TTS daemon.

## Remaining issues

1. Human listening acceptance is pending Steward review.
2. Real-time streaming and mid-stream interruption are not commissioned in this local WAV path.
3. If a future external TTS engine is approved, these bindings should remain engine-neutral and only provider-specific IDs should be swapped.

## Completion receipt

Focused tests verified TTS health, synthesis, binding resolution, Open WebUI audio integration, generated WAV playback, fallback handling, and sample matrix generation. The complete canonical test suite was run after implementation.
