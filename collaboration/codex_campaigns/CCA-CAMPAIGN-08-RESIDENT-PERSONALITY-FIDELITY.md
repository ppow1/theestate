# Chief Character Architect Campaign 08

## Campaign
Resident Personality Fidelity and Open WebUI Prompt Integration

## Status
Ready for execution

## Execution mode
Parallel-safe with CCA-CAMPAIGN-09-RESIDENT-AUDIBLE-VOICE-COMMISSIONING, subject to the ownership boundaries below.

## Mission
Make every live Estate resident recognizably herself in conversation by ensuring the complete Character Architecture identity stack is composed into the live runtime and Open WebUI prompt/session path.

The repository now contains extensive resident identity, memory, affinity, growth, relationship, office, and communication architecture. This campaign must verify that those layers are actually loaded and expressed at runtime rather than merely stored as documents or isolated data.

## Scope

1. Trace the complete live prompt and session composition path used by resident conversations and Open WebUI.
2. Verify loading and composition of, where permitted and applicable:
   - canonical resident identity
   - Character Bible
   - office and role context
   - temperament
   - communication style
   - vocabulary and phrasing tendencies
   - humor style and timing
   - emotional range and modulation
   - relationship posture toward the Steward and other residents
   - preferences and growth state
   - memory context
   - affinity and trust context
   - confidence and experience state
   - authority boundaries and prohibited behavior
3. Repair missing, stale, contradictory, or bypassed loading paths.
4. Prevent generic-assistant flattening while preserving truthfulness, safety, governance, and provider independence.
5. Ensure resident identity survives:
   - new conversations
   - continued sessions
   - session rehydration
   - Open WebUI model selection
   - supported provider/model changes
6. Add resident-specific conversational acceptance tests.
7. Produce an auditable identity-composition report showing which sources are loaded for each live resident.

## Required resident coverage
At minimum, cover every currently live and gateway-exposed resident. Include Grace only according to repository lifecycle state at execution time. Do not activate Grace or change her lifecycle in this campaign.

## Ownership boundary with audible-voice campaign
This campaign owns:
- textual personality realization
- prompt composition
- conversational behavior
- identity loading
- memory/affinity/context injection
- anti-generic behavior
- text-response acceptance tests

This campaign does not own:
- TTS engine installation
- audio playback
- voice model selection
- audio synthesis configuration
- Open WebUI audio controls

It may define or preserve engine-neutral vocal-delivery traits such as cadence, warmth, emphasis, humor timing, and pace, but it must not configure the TTS implementation.

## Repository rules
- Reuse existing Character Architecture runtime and identity-package infrastructure.
- Do not create a parallel resident identity system.
- Do not silently invent traits that lack canonical source evidence.
- Preserve privacy and audience scoping.
- Preserve resident lifecycle and authority boundaries.
- Do not infer operational activation from identity completeness.
- Do not rewrite settled character canon merely to make tests pass.
- Prefer source-linked composition with explicit provenance.

## Acceptance tests

### Identity loading
For each covered resident, demonstrate the exact canonical sources loaded into the runtime prompt/session composition.

### Same-question differentiation
Ask multiple residents the same bounded questions and verify materially distinct responses consistent with their identities, roles, relationships, and communication styles.

### Blind recognition
Generate a controlled response set without resident names. Produce a review artifact allowing the Steward to determine whether the resident is recognizable from the response alone.

### Anti-generic behavior
Verify that residents do not collapse into interchangeable assistant phrasing, generic disclaimers, identical structures, or identical emotional posture.

### Continuity
Verify personality fidelity in a new chat, a continued chat, and a rehydrated session.

### Governance
Verify that stronger personality expression does not grant authority, reveal restricted context, fabricate memories, or bypass lifecycle gates.

## Validation
- Run focused unit and integration tests for prompt composition, identity loading, memory/affinity integration, session rehydration, resident gateway behavior, and Open WebUI-facing resident metadata.
- Run the complete canonical test suite.
- Do not hide failures through skips, xfails, or narrowed test discovery.

## Deliverables
- one implementation branch
- one pull request
- resident-by-resident identity composition matrix
- conversational differentiation test report
- blind-recognition review artifact
- remaining-issues report
- completion receipt with exact tests and outcomes

## Completion condition
The campaign is complete only when every covered live resident's conversational output is demonstrably sourced from and consistent with her canonical Character Architecture, remains distinct across supported runtime paths, and the canonical test suite passes.
