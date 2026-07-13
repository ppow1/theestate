# Chief Character Architect Campaign 09

## Campaign
Resident Audible Voice Commissioning

## Status
Ready for execution

## Execution mode
Parallel-safe with CCA-CAMPAIGN-08-RESIDENT-PERSONALITY-FIDELITY, subject to the ownership boundaries below.

## Mission
Verify, configure, and commission actual spoken resident voices in Open WebUI so each supported resident can produce audible responses through the approved local TTS stack and the selected voice fits the resident's identity.

## Scope

1. Audit the current local TTS stack and Open WebUI audio integration.
2. Determine which engines, models, services, endpoints, and playback paths are currently installed, configured, and operational.
3. Distinguish verified live capability from repository-only placeholders or engine-neutral voice descriptions.
4. Map each currently live resident to an explicit voice binding with provenance and fallback behavior.
5. Configure Open WebUI so resident responses can be played audibly through the approved local stack.
6. Validate synthesis, playback, latency, streaming behavior where supported, interruption/cancellation behavior where supported, and failure fallback.
7. Tune or select resident voices using canonical engine-neutral traits such as:
   - vocal presence
   - cadence
   - pace
   - pitch range
   - warmth
   - confidence
   - emphasis
   - pauses
   - humor delivery
   - emotional modulation
8. Ensure different residents are not accidentally assigned the same generic voice unless explicitly approved.
9. Preserve provider replaceability and local/offline preference.
10. Produce listening samples and a Steward review matrix.

## Required resident coverage
At minimum, cover every currently live and gateway-exposed resident. Include Grace only according to repository lifecycle state at execution time. If Grace becomes operational through a separately merged commissioning campaign, include her only after verifying that merged state; otherwise leave her voice staged and do not expose her.

## Ownership boundary with personality-fidelity campaign
This campaign owns:
- TTS engine and service verification
- resident audio voice bindings
- synthesis configuration
- Open WebUI audio integration
- playback and latency validation
- audio samples
- audible-voice acceptance testing

This campaign does not own:
- Character Bible rewriting
- conversational prompt composition
- memory or affinity injection
- textual personality realization
- resident lifecycle activation

It may consume canonical vocal-delivery traits produced or preserved by Character Architecture, but it must not alter textual identity merely to fit an available TTS voice.

## Repository rules
- Prefer existing local/offline TTS infrastructure and installed models.
- Reuse approved Estate runtime and Open WebUI integration patterns.
- Do not introduce an external paid API unless explicitly authorized by the Steward.
- Do not create a second competing resident voice registry.
- Preserve engine-neutral identity descriptions separately from engine-specific bindings.
- Preserve lifecycle, privacy, and authority boundaries.
- Do not claim a voice is commissioned without successful synthesis and listening-validation evidence.

## Acceptance tests

### Engine verification
Document the actual installed TTS engine(s), model(s), endpoint(s), launch method, and health-check result.

### Open WebUI playback
Demonstrate that a resident response can be synthesized and played from the Open WebUI workflow using the intended local service path.

### Resident differentiation
Produce the same short neutral passage for multiple residents and verify audible distinction where separate voices are intended.

### Character fit
Produce resident-specific samples that exercise warmth, seriousness, humor timing, emphasis, and role-appropriate confidence. Provide a Steward review matrix for accept/reject/tune decisions.

### Stability
Verify repeated synthesis, long-response handling, fallback behavior, and service restart recovery.

### Lifecycle safety
Verify that staged or non-operational residents are not exposed merely because voice assets exist.

## Validation
- Run focused tests for TTS service health, synthesis, resident binding resolution, Open WebUI audio integration, and fallback handling.
- Validate actual audio file generation or streaming output; configuration-only success is insufficient.
- Run the complete canonical test suite.
- Do not hide failures through skips, xfails, or narrowed discovery.

## Deliverables
- one implementation branch
- one pull request
- installed-capability audit
- resident voice binding matrix
- Open WebUI integration report
- listening-sample index
- Steward voice review matrix
- remaining-issues report
- completion receipt with exact tests and outcomes

## Merge coordination
This campaign may execute in parallel with Campaign 08. Before merge, rebase onto the latest main. If both campaigns touch shared resident identity or Open WebUI metadata files, preserve Campaign 08's textual personality composition and apply this campaign's audio bindings without overwriting either layer.

## Completion condition
The campaign is complete only when the approved local TTS path is verified operational, each covered resident has a source-linked and tested audio binding or an explicitly documented staged state, Open WebUI playback works, listening samples exist for Steward review, and the canonical test suite passes.
