# OPENWEBUI CAMPAIGN 03 — CANONICAL RESIDENT INSTANTIATION

Status: Ready for Codex
Owner: Office of the Chief Architect
Priority: High
Classification: Estate Internal

## Mission

Complete the user-facing Open WebUI resident-instantiation path so selecting an Estate resident automatically loads the resident's authoritative identity composition, office/role context, visual state, commissioned voice state, and auditable runtime metadata without requiring the Steward to manually assemble prompts, run separate audition scripts, or think about underlying model and TTS providers.

The immediate acceptance target is not a speculative custom dashboard. It is a real, testable Open WebUI experience using the existing canonical Estate resident gateway.

## Steward Intent

The normal interaction should be equivalent to:

`Instantiate Helen.`

The visible surface should then behave as Helen, using Helen's canonical identity and approved voice configuration. The same pattern must apply to every active resident while remaining honest about provisional, unavailable, or placeholder visual and voice assets.

## Current Known State

- The canonical OpenAI-compatible resident gateway exists and exposes active Estate residents.
- Open WebUI Campaign 02 added resident-first catalog metadata, identity-composition traces, honest avatar truth state, voice-binding availability, comparison prompts, and Steward review artifacts.
- Helen and Grace have now been approved by the Steward through actual listening and conversation testing:
  - Helen: Kokoro `af_bella`, speed `0.92`, status canonical v1.
  - Grace: Kokoro `af_jessica`, speed `1.00`, status canonical v1.
- Other resident voices remain provisional or uncommissioned and must not be represented as canonical.
- Kokoro is available locally through the dedicated Python 3.11 environment at `A:\AI\TTS\kokoro_py311` on the Steward machine.
- F5-TTS is not currently the production path because its Python 3.14/TorchCodec runtime is not commissioned.
- The visual canon is manifest-controlled. Final raster portraits may be canonical, provisional, placeholder, restricted, or unavailable depending on the resident and asset slot.

## Required Outcome

When Open WebUI connects to the Estate resident gateway and the Steward selects a resident model:

1. The resident appears by resident name, not by raw foundation-model name.
2. The resident's authoritative identity composition is loaded for every turn.
3. The resident's office title and short role description are visible in model metadata.
4. The resident's visual/avatar state is displayed honestly.
5. The resident's voice state is displayed honestly.
6. For commissioned voices, the response can be synthesized through the approved Kokoro path and returned through a stable audio endpoint or attachment contract usable by Open WebUI.
7. For uncommissioned voices, the UI reports `provisional` or `unavailable`; it must not silently substitute a fake canonical voice.
8. Identity hash, schema version, source trace, voice binding, and visual provenance remain auditable in the response envelope.
9. No competing resident gateway or duplicate identity authority is created.

## Scope

### 1. Canonical resident package projection

Create or extend a single resident-package projection consumed by the Open WebUI surface. The projection should compose existing authoritative sources rather than duplicating resident truth.

Minimum projected fields:

- `resident_id`
- `display_name`
- `office_title`
- `role_summary`
- `model_id`
- `identity_schema_version`
- `identity_source_hash`
- `identity_failed_closed`
- `identity_sources`
- `visual_state`
- `avatar_uri` or explicit null
- `visual_provenance`
- `voice_state`
- `voice_engine`
- `voice_id`
- `voice_speed`
- `voice_approval_state`
- `tts_available`
- `capabilities`
- `privileged_actions_enabled`

### 2. Canonical commissioned voice registry

Create a repository-controlled canonical voice-commissioning registry. Do not treat the local runtime audition file as institutional truth.

Initial canonical entries:

```json
{
  "helen": {
    "engine": "kokoro",
    "engine_version": "0.9.4",
    "voice": "af_bella",
    "speed": 0.92,
    "status": "canonical_v1",
    "approval": "Steward",
    "validation": [
      "individual audition",
      "speed audition",
      "three-mode validation",
      "conversation chemistry test"
    ]
  },
  "grace": {
    "engine": "kokoro",
    "engine_version": "0.9.4",
    "voice": "af_jessica",
    "speed": 1.0,
    "status": "canonical_v1",
    "approval": "Steward",
    "validation": [
      "individual audition",
      "Helen comparison",
      "conversation chemistry test"
    ]
  }
}
```

All other active residents must be marked `provisional`, `uncommissioned`, or `unavailable` until the Steward approves them.

### 3. Kokoro adapter

Implement a stable Estate Kokoro adapter rather than relying on one-off PowerShell/Python audition scripts.

Requirements:

- Support explicit Kokoro executable or Python path through environment/configuration.
- Prefer the known local path when present, but do not hard-code it as the only supported installation:
  - `A:\AI\TTS\kokoro_py311\Scripts\python.exe`
  - `A:\AI\TTS\kokoro_py311\Scripts\kokoro.exe`
- Generate WAV output at 24 kHz.
- Accept resident ID, text, canonical voice, canonical speed, and requested output name.
- Use safe deterministic output paths under Estate runtime storage.
- Return structured success/failure metadata.
- Never claim success without a playable non-empty WAV.
- Do not generate sine waves, formant placeholders, or fake speech.
- Preserve local-only operation; no paid external API is required.

### 4. Audio serving contract

Provide a reliable way for Open WebUI to retrieve generated resident audio.

Acceptable implementations include:

- a local authenticated or loopback-only `GET /v1/estate/audio/...` endpoint;
- a response attachment URL contract;
- another Open WebUI-compatible local playback mechanism.

Requirements:

- Prevent arbitrary filesystem reads.
- Serve only registered/generated audio under the approved runtime directory.
- Use correct MIME type.
- Return explicit 404/unavailable states.
- Include resident ID, turn ID, voice ID, speed, and provenance metadata in the response envelope.

### 5. Open WebUI model catalog

Ensure `/v1/models` exposes a resident-first catalog with readable metadata for at least:

- Alfred
- Helen
- Ingrid
- Grace
- Evelyn
- Eleanor
- Marie
- Judy
- Estate conference room

For each resident, expose:

- display name;
- office/role;
- avatar truth state;
- voice truth state;
- canonical/provisional status;
- resident-gateway capability;
- whether audible playback is currently available.

Do not show a provisional voice as canonical.

### 6. Single-resident turn integration

For every single-resident Open WebUI request:

- compose the resident identity before response generation;
- include office and role context;
- retain session continuity;
- return identity trace metadata;
- synthesize audio only when requested/enabled and a commissioned binding plus working engine are available;
- expose explicit unavailable state otherwise;
- do not execute privileged actions merely because the resident is instantiated.

### 7. Visual projection

Resolve each resident's avatar from the canonical visual registry or existing resident surface metadata.

Truth states must include at least:

- `canonical`
- `provisional`
- `placeholder`
- `restricted`
- `unavailable`

Never promote placeholder art merely to fill the UI. When a canonical raster does not exist, return the correct state and a neutral Estate placeholder only if the existing visual governance permits it.

### 8. Human-visible resident-ready state

Add a small status payload or report that allows the Steward to see what loaded for the selected resident, for example:

```text
Helen ready
Identity: canonical
Office: loaded
Visual: provisional/canonical
Voice: canonical — Kokoro af_bella @ 0.92
TTS engine: available
Memory/session: connected
Privileged actions: disabled
```

This may be metadata consumed by Open WebUI, a local status endpoint, or both. Do not add a large new custom frontend unless required for minimum functionality.

### 9. Validation harness

Create a repeatable local validation script that:

- audits the resident catalog;
- validates identity composition for every resident;
- validates Helen and Grace canonical voice bindings;
- checks Kokoro discovery;
- synthesizes one short Helen and one short Grace sample when Kokoro is available;
- checks that the audio files are playable and non-empty;
- validates the audio-serving endpoint or contract;
- verifies uncommissioned residents remain honestly labeled;
- verifies no raw foundation-model name is required in the normal resident selection path;
- creates JSON and Markdown reports for Steward review.

The validation script must produce useful output when Kokoro is absent and must not fail by pretending unavailable services are present.

### 10. Tests

Add focused tests covering:

- canonical Helen binding;
- canonical Grace binding;
- uncommissioned resident truth state;
- resident package projection;
- resident-first model catalog;
- identity trace propagation;
- visual truth-state behavior;
- Kokoro command construction;
- synthesis success and failure paths;
- generated-file validation;
- audio path traversal prevention;
- audio endpoint/attachment behavior;
- Open WebUI response envelope metadata;
- no privileged action execution.

## Out of Scope

- Commissioning the remaining resident voices.
- Repairing F5-TTS/TorchCodec.
- Motion/video avatars.
- FaceTime-style live resident performance.
- Executive Council orchestration beyond preserving the existing conference-room model.
- A new Office of Estate Presentation.
- Replacing Open WebUI.
- Creating final visual raster assets that do not already exist.
- Cloud TTS or paid APIs.

## Repository Guidance

Inspect and extend the existing canonical paths before creating new modules, especially:

- `src/estate/core/resident_gateway.py`
- `src/estate/core/openwebui_resident_surface.py`
- `src/estate/core/open_webui_multi_resident_gateway.py`
- `src/estate/core/resident_identity_composition.py`
- `src/estate/core/resident_voice_commissioning.py`
- `data/visuals/canonical_visual_registry.json`
- `runtime/voice/resident_voice_bindings.json`
- Campaign 02 reports and tests

Place repository-controlled voice truth under an appropriate `data/`, `config/`, or resident-canon path. Runtime-generated WAV files and machine-specific discovery state must remain runtime artifacts.

## Acceptance Criteria

Campaign 03 is complete only when all of the following are true:

1. Open WebUI can list and select active Estate residents by resident name.
2. Selecting Helen loads Helen's authoritative identity composition and reports her canonical Kokoro binding `af_bella @ 0.92`.
3. Selecting Grace loads Grace's authoritative identity composition and reports her canonical Kokoro binding `af_jessica @ 1.00`.
4. A requested Helen or Grace response can produce a playable WAV on a machine with the approved Kokoro environment.
5. Open WebUI can retrieve/play that WAV through the documented local contract.
6. Residents without approved voices are not mislabeled as canonical.
7. Visual/avatar states are honest and provenance-aware.
8. Identity and voice trace metadata are returned for every resident turn.
9. Existing single-resident and conference-room gateway behavior remains compatible.
10. Automated tests pass.
11. A Steward commissioning report clearly states what is operational, provisional, unavailable, and still pending.

## Required Reports

Produce at minimum:

- `collaboration/reports/openwebui_campaign_03/validation_report.json`
- `collaboration/reports/openwebui_campaign_03/VALIDATION_REPORT.md`
- `collaboration/reports/openwebui_campaign_03/STEWARD_RESIDENT_INSTANTIATION_REVIEW.md`
- local startup/configuration instructions using the Estate PowerShell style, beginning command blocks with `CLS`;
- an explicit list of remaining manual Open WebUI configuration steps, if any.

## Codex Execution Instruction

Read this file completely and do exactly what it says.

Work against the current `main` branch state. Reuse the canonical resident gateway and existing identity-composition authority. Implement the smallest complete resident-instantiation path that the Steward can actually test in Open WebUI.

Do not claim that portraits, voices, TTS playback, or Open WebUI integration are operational unless validated by code, tests, and generated reports. Preserve explicit unavailable and provisional states.

At completion, open a pull request with a clear summary, tests run, local-machine dependencies, and exact Steward validation steps.