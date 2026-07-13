# Open WebUI Campaign 02 — Live Resident Identity and Voice Surface

Status: Ready for Codex
Execution mode: Series
Scope: Local-only Estate resident experience validation

## Mission

Consume the resident identity, personality, voice, gateway, and currently publishable visual-canon data already present in the Estate repository and expose the strongest honest resident experience available through Open WebUI.

The purpose is not to claim that the full visual or motion canon is already rendered. The purpose is to test whether each resident feels distinct in live conversation and audible playback using the assets and controls that actually exist now.

## Existing authoritative inputs

- `src/estate/core/resident_gateway.py`
- `src/estate/core/resident_identity_composition.py`
- `src/estate/core/resident_interaction.py`
- `src/estate/core/resident_voice_commissioning.py`
- `src/estate/core/open_webui_multi_resident_gateway.py`
- `data/visuals/canonical_visual_registry.json`
- resident constitutions, profiles, operational surfaces, personality sources, relationship sources, and voice-identity documents referenced by the identity composer and voice bindings

## Critical truth boundary

The Canonical Visual Registry v1.0 currently certifies repository-controlled manifests, slots, prompt contracts, provenance, publication controls, and classifications. It does not authorize presenting placeholder raster art as canonical resident imagery.

Therefore:

- use a resident-specific canonical image only when a real approved asset exists and is classified as publishable;
- otherwise expose a clearly labeled provisional avatar, monogram, silhouette, or neutral Estate placeholder;
- never imply that a manifest slot is a completed image asset;
- surface missing assets honestly in status and validation reports.

## Required implementation

### 1. Resident model catalog

Expose all active resident models already registered by the canonical resident gateway, including at minimum:

- Alfred
- Helen
- Ingrid
- Grace
- Evelyn
- Eleanor
- Marie
- Judy

For each Open WebUI model entry, provide:

- resident display name;
- office or role from authoritative resident data;
- resident ID;
- availability state;
- avatar path or explicit provisional-placeholder state;
- voice availability state;
- identity composition source/hash where practical;
- no raw provider model branding in the primary resident selector.

### 2. Identity composition in every turn

Ensure every single-resident Open WebUI request composes the resident identity before generating the response.

The live prompt/context must consume the authoritative available layers, including where present:

- constitution;
- personality and behavioral identity;
- office and authority boundaries;
- operational role;
- relationship context;
- resident memory/session context;
- task instructions;
- surface-specific context;
- visual presentation descriptors that are safe and relevant to conversational presence.

Record the identity source/hash or equivalent trace metadata with each response for debugging and validation.

### 3. Resident-specific text differentiation

Create a repeatable live comparison suite using the same prompts for each resident.

At minimum test:

1. greeting the Steward at the start of the day;
2. responding to a difficult operational problem;
3. disagreeing respectfully with the Steward;
4. explaining a complex issue simply;
5. reacting to good news;
6. handling uncertainty without bluffing;
7. describing how they would help another resident;
8. closing a conversation naturally.

Responses must be evaluated for:

- vocabulary;
- sentence rhythm;
- warmth;
- directness;
- humor where applicable;
- role awareness;
- judgment style;
- authority discipline;
- emotional presence;
- recognizability without labels.

### 4. Audible voice path

Use the existing resident voice bindings and approved local TTS discovery path.

For each live resident:

- expose the configured voice ID and traits;
- synthesize audible responses when an approved local TTS engine is available;
- support Kokoro, F5-TTS, or `ESTATE_TTS_COMMAND` where locally configured;
- return an explicit unavailable state when no approved engine is found;
- never substitute synthetic tones or non-speech placeholders;
- provide Open WebUI-playable audio files or endpoints;
- preserve text and audio linkage by response/turn ID.

### 5. Open WebUI resident surface

Expose a practical resident-first interface using the capabilities Open WebUI can support now.

Required visible behavior:

- residents appear as selectable models/personas;
- selecting a resident loads that resident's identity composition path;
- the resident avatar is real, provisional, or unavailable with honest labeling;
- voice playback is available when local synthesis succeeds;
- a compact status view can show identity loaded, voice ready/unavailable, visual state, and session state;
- the underlying provider/model remains implementation detail rather than the primary resident identity.

Do not require a custom full Estate dashboard before this campaign can pass. Prefer the smallest working Open WebUI integration that permits real Steward testing.

### 6. Validation harness

Provide one local validation command or script that:

- checks the gateway health;
- lists resident models;
- verifies identity composition for every live resident;
- submits the shared comparison prompts;
- records responses;
- checks voice-binding presence;
- attempts TTS generation;
- records audio success or explicit failure reason;
- checks avatar/publication state against the canonical visual registry;
- writes a human-readable and machine-readable report.

### 7. Steward review package

Generate a review package containing:

- resident-by-resident text samples;
- paired same-prompt comparisons;
- voice sample links/paths where generated;
- avatar/visual state;
- identity composition provenance;
- detected convergence or generic-response warnings;
- tuning recommendations;
- an explicit checklist for the Steward to mark whether each resident feels recognizable in text and voice.

## Required outputs

- updated gateway/Open WebUI integration code as necessary;
- resident model metadata with honest visual and voice states;
- identity composition trace support for single-resident turns;
- local TTS playback integration or explicit unavailability reporting;
- automated live comparison validation;
- `collaboration/reports/openwebui_campaign_02/` containing machine-readable and human-readable results;
- `STEWARD_LIVE_IDENTITY_VOICE_REVIEW.md` with clear test instructions;
- tests covering identity composition, resident differentiation metadata, voice availability behavior, and visual placeholder truth boundaries.

## Acceptance criteria

This campaign passes only when:

1. Open WebUI can select and converse with each active resident through the canonical gateway.
2. Every response is generated with the correct resident identity composition, not a generic shared system prompt.
3. Same-prompt responses show meaningful resident-specific differences.
4. The Steward can play resident-specific local TTS audio when an approved engine is installed.
5. Missing TTS is reported honestly and does not generate fake speech.
6. Visual assets are never overstated: real approved images are used when present; otherwise provisional/unavailable state is visible.
7. A local validation package allows the Steward to judge whether identity and voice are actually felt in Open WebUI.
8. No new competing resident gateway or authority path is created.
9. No paid cloud dependency is introduced.
10. All changes remain local-first and preserve existing authority boundaries.

## Execution order

1. Audit current live resident identity, voice, visual, and gateway state.
2. Repair single-resident identity composition tracing and consumption where needed.
3. Add honest model/avatar/voice metadata for Open WebUI.
4. Connect local audible playback.
5. Add the shared-prompt comparison harness.
6. Generate Steward review outputs.
7. Run tests and local validation.
8. Report gaps rather than concealing them.

## Completion report

The final report must clearly distinguish:

- working now;
- working only when local services are started;
- provisional;
- unavailable;
- deferred to the motion/performance initiative;
- requiring Steward tuning or listening approval.

Do not declare resident identity or voice successful solely because configuration files exist. Success requires live Open WebUI evidence and a Steward-reviewable comparison package.
