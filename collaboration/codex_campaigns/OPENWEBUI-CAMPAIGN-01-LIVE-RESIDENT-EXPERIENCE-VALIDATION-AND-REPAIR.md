# Open WebUI Campaign 01 — Live Resident Experience Validation and Repair

## Status
Ready for Codex execution.

## Mission
Validate and repair the actual running Open WebUI resident experience after Grace commissioning, personality-fidelity integration, and audible-voice commissioning.

This campaign is not satisfied by repository-only tests, generated reports, metadata presence, or playable non-speech audio. It must verify the live user-facing experience.

## Current verified concerns

1. The commissioned audible-voice path currently generates deterministic sine-formant WAV files. Those files are technically playable audio but are not intelligible text-to-speech and do not satisfy the requirement that residents speak their responses aloud.
2. Personality-fidelity tests prove resident-specific identity metadata and fallback text exist, but several fallback responses remain formal self-identification and authority disclaimers rather than natural resident conversation.
3. The actual running Open WebUI instance still requires end-to-end validation after the recent merges.

## Required outcomes

### 1. Live Open WebUI model exposure

Verify the running Open WebUI-compatible gateway exposes every intended live resident model, including at minimum:

- estate/alfred
- estate/helen
- estate/ingrid
- estate/grace
- estate/evelyn
- estate/eleanor
- estate/marie
- estate/judy

Confirm the models are selectable through the actual Open WebUI workflow, not only present in a unit-test payload.

### 2. Natural personality expression

For each resident, verify the live prompt composition includes the intended identity stack, Character Bible, office role, authority boundaries, relationship posture, memory/affinity context where allowed, and resident-specific language guidance.

Repair the runtime so normal answers sound like the resident rather than like a generic assistant reciting identity and authority boilerplate.

Do not remove governance boundaries. Integrate them naturally and only surface explicit boundary disclaimers when the user request actually makes them relevant.

Acceptance standard: the Steward should be able to distinguish residents from their wording, judgment, rhythm, warmth, humor, and priorities without relying on the displayed name.

### 3. Real local text-to-speech

Replace or supplement the deterministic waveform placeholder with an intelligible local TTS engine already installed or approved for the Estate.

Preferred existing local capabilities should be audited first, including Kokoro TTS and F5-TTS if available in the local Estate environment. Do not introduce a paid external API.

Requirements:

- synthesize the actual resident response text into intelligible speech;
- preserve resident-specific voice bindings and engine-neutral vocal traits;
- produce playable audio for Open WebUI;
- provide a clear fallback when the preferred engine is unavailable;
- never represent tones or placeholder waveforms as commissioned speech;
- retain deterministic testability where practical without substituting fake speech for human listening validation.

### 4. End-to-end conversation validation

Exercise the actual live path for each resident:

1. select the resident model;
2. send a conversational prompt;
3. verify resident-specific text output;
4. verify session continuation preserves identity;
5. verify a second prompt does not collapse into generic assistant behavior;
6. generate and play intelligible spoken audio for the response;
7. record latency, failures, and fallback behavior.

Include Grace-specific validation confirming she is visible and conversationally available as Director of Operations after Steward activation.

### 5. Steward review package

Produce:

- a live Open WebUI model-exposure report;
- a resident-by-resident personality fidelity report;
- a blind-recognition sample set using natural conversational prompts;
- intelligible listening samples for each commissioned resident;
- a voice-binding review matrix for Steward approval/tuning;
- exact launch and validation instructions for the Steward's local machine;
- a remaining-issues report with no hidden failures.

## Repository and authority rules

- Preserve existing Estate governance and resident authority boundaries.
- Do not create a competing gateway, resident registry, or personality system.
- Reuse the canonical resident gateway and identity-composition path.
- Do not regress Grace's commissioned operational status.
- Do not invent approval for external services.
- Do not mark human listening or personality acceptance complete without actual Steward review; machine validation may establish readiness for that review.
- Do not hide failures through skipped tests or by narrowing canonical discovery.

## Validation

Run focused tests for:

- resident gateway model exposure;
- identity composition;
- session continuity;
- resident differentiation;
- Grace operational exposure;
- local TTS health and intelligible synthesis;
- Open WebUI audio metadata/playback integration.

Then run the complete canonical test suite.

Where the local Open WebUI process or installed TTS environment cannot be launched inside Codex, create exact executable local validation commands and distinguish clearly between:

- repository verified;
- Codex environment verified;
- local Steward machine validation still required.

## Deliverables

- one coherent implementation branch;
- one pull request;
- changed code and configuration;
- focused and full-suite test evidence;
- live-experience validation report;
- personality review artifacts;
- intelligible resident listening samples or an exact local generation workflow;
- remaining-issues report;
- completion receipt.

## Stop conditions

Stop and report rather than guessing if:

- the approved local TTS installation cannot be located;
- Open WebUI integration requires credentials or machine access unavailable to Codex;
- a proposed repair would create a parallel gateway or bypass governance;
- resident identity sources contradict one another materially.

## Completion condition

This campaign is complete only when the repository contains an honest, test-backed path for natural resident conversation and intelligible resident speech through the Open WebUI workflow, with any machine-local validation still required explicitly identified for the Steward.