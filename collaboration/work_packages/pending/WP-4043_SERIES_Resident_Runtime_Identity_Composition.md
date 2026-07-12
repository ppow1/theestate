# WP-4043 — Resident Runtime Identity Composition

Status: Pending
Execution Mode: SERIES
Owner: Office of Character Architecture / Resident Runtime Integration
Execution Target: Codex
Classification: Estate Internal
Priority: Immediate

## Start Condition

Execute only after WP-4042 is merged to `main`.

## Objective

Replace ad hoc resident prompting with one canonical runtime identity-composition pipeline so every resident consistently behaves as the same institutional person on every turn.

This package must improve Alfred, Helen, Grace, Ingrid, Evelyn, the conference-room surface, and all future residents through shared runtime architecture rather than resident-specific prompt patches.

## Evidence Requiring This Work

Live testing after WP-4042 showed that:

- residents sometimes reverted to generic assistant behavior;
- Helen and Grace failed to recognize Evelyn as an active resident;
- Alfred described himself as serving the wrong office;
- Ingrid's privacy guardrail suppressed ordinary self-description;
- conference-room participants did not share one stable institutional cast;
- model switching and chat history influenced identity more than canonical Estate artifacts.

These failures indicate that resident identity is currently assembled inconsistently across prompts, model wrappers, runtime surfaces, and conversation history.

## Architectural Principle

The resident is not the model.

A resident's identity must remain stable across:

- model changes;
- provider changes;
- chat renewal;
- single-resident and conference-room surfaces;
- runtime restart;
- prompt refactoring;
- implementation-vessel replacement.

The identity-composition path shall assemble canonical context on every inference rather than trusting model recollection or accumulated transcript state.

## Required Work

1. Inspect the existing resident gateway, model-control surfaces, resident interaction runtime, multi-resident room runtime, registry artifacts, resident profiles, prompts, identity packages, and installed workstreams before adding structures.
2. Define one canonical runtime identity-composition interface used by all resident inference surfaces.
3. Compose identity from existing canonical Estate artifacts and derived read-only runtime snapshots.
4. Keep identity, authority, institutional facts, privacy rules, relationship context, conversation history, and presentation data as explicit separate layers.
5. Ensure every composed context item exposes source lineage, classification, version or timestamp where available, and inclusion reason.
6. Make missing or contradictory source data visible through diagnostics rather than silently selecting or inventing identity facts.
7. Integrate the composer with both single-resident gateway calls and the conference-room runtime.
8. Preserve provider independence: no resident identity may depend on one model's hidden memory, provider-specific system prompt, or one chat transcript.

## Canonical Composition Layers

The runtime identity object shall support, at minimum:

1. **Resident Core Identity**
   - resident ID and canonical name;
   - office, role, department, lifecycle status, and reporting relationship;
   - provider-independent identity summary;
   - stable role boundaries and prohibited role conflations.

2. **Character Context**
   - loaded through the canonical Character Bible mechanism established by WP-4044;
   - personality, voice, manner, presentation, preferences, boundaries, and relationship expression;
   - no authority elevation through character traits.

3. **Institutional Registry Context**
   - loaded through the synchronized registry snapshot established by WP-4045;
   - active residents, offices, appointments, lifecycle states, public authority facts, and available communication endpoints.

4. **Grounded Estate Facts**
   - loaded through the provider established by WP-4046;
   - current work-package, message, runtime, repository, and operational facts appropriate to the request and classification.

5. **Authority and Capability Context**
   - explicit actions the resident may advise on, request, route, or perform;
   - actions reserved to the Steward or other offices;
   - no authority inferred from model capability.

6. **Privacy and Disclosure Context**
   - Ingrid-governed classification and disclosure rules;
   - surface-specific filtering;
   - private continuity excluded from unrelated residents and shared rooms.

7. **Relationship Context**
   - only relationships authorized for the active resident, user, and surface;
   - Steward-specific or private layers must never become global resident context.

8. **Conversation Context**
   - bounded transcript context for the current resident and surface only;
   - never treated as canonical identity or institutional truth;
   - conversation isolation is implemented in a later package.

## Composition Order

The composer shall apply context in this order:

1. resident identity and lifecycle;
2. authority and role boundaries;
3. safe current institutional facts;
4. character and presentation;
5. privacy and disclosure constraints;
6. authorized relationship context;
7. bounded current conversation context;
8. task-specific instructions.

Privacy controls shall filter context without erasing the resident's ordinary identity. Character data shall enrich expression without overriding authority or facts.

## Runtime Contract

The composer shall return a typed, inspectable object containing at least:

- resident ID;
- surface ID;
- composition timestamp;
- identity version or source hash;
- included context layers;
- excluded context layers with reasons;
- source artifact paths or identifiers;
- classification summary;
- detected contradictions or missing sources;
- bounded provider-ready context;
- diagnostic metadata not exposed to ordinary conversation output.

The provider-ready context may be rendered to the format required by a local or remote model adapter, but the canonical composed object must remain provider neutral.

## Failure Behavior

1. Unknown durable identity facts remain unknown.
2. Conflicting canonical identity records fail closed with a visible diagnostic.
3. Missing optional character details do not prevent basic resident operation.
4. Missing required identity, lifecycle, or authority records prevent the resident from claiming an unverified role.
5. Privacy filtering removes restricted context but does not replace the resident with a generic refusal persona.
6. Provider or model fallback must reuse the same composed identity object.

## Initial Resident Coverage

Validate at minimum:

- Alfred remains Chief of Staff and does not become Operations or Engineering;
- Helen remains Workforce Development/HR and does not invent mail or appointments;
- Grace remains Director of Operations and does not absorb Traffic Controller, Steward, or Engineering authority;
- Ingrid remains privacy and classification authority while retaining ordinary personality and self-description;
- Evelyn remains the Steward's Confidant and does not become HR, Operations, Chief of Staff, therapist, or generic romantic assistant;
- the conference room receives shareable resident identity without inheriting private resident chats.

## Acceptance Tests

1. Every active resident request passes through the same canonical composer.
2. The same resident retains role, identity, and boundaries when the underlying model changes.
3. A new chat does not create a new resident identity.
4. Conversation transcript content cannot silently rewrite canonical identity.
5. Alfred, Helen, Grace, Ingrid, and Evelyn remain distinguishable and correctly describe their offices.
6. Authority context does not grant privileged actions to resident inference.
7. Private Evelyn continuity is absent from conference-room and unrelated resident composition.
8. Contradictory required identity sources produce a machine-readable failure rather than an improvised answer.
9. Source lineage and context-layer inclusion can be inspected for every composed request.
10. Context remains bounded enough for supported local models and does not load the entire Estate indiscriminately.
11. Automated tests cover single-resident, conference-room, provider-switch, missing-source, conflict, privacy-filtering, and restart scenarios.

## Deliverables

- provider-independent resident identity-composition schema;
- canonical composition service integrated with existing resident runtime paths;
- adapters for single-resident and conference-room inference;
- source-lineage and contradiction diagnostics;
- fixtures for Alfred, Helen, Grace, Ingrid, and Evelyn;
- automated unit, integration, and behavioral regression tests;
- documentation of composition order and source precedence;
- completion receipt identifying installed files, tests, limitations, and follow-on dependencies.

## Constraints

- Strengthen the existing resident gateway and runtime; do not create a parallel resident system.
- Do not create a second registry, message bus, relationship store, privacy authority, or preference engine.
- Do not embed one enormous static prompt as the canonical identity source.
- Do not treat model memory or conversation history as durable Estate truth.
- Do not redesign settled resident offices or appointments.
- Do not implement final portraits, live TTS, conversation isolation, messaging, mailboxes, or relationship-graph runtime in this package.

## Dependency and Sequencing

- WP-4043 depends on the installed resident gateway and WP-4042 activation wave.
- WP-4044, WP-4045, and WP-4046 are SERIES successors and shall integrate through this canonical composition path.
- Later conversation-isolation, messaging, relationship, continuity, diagnostics, and monitoring packages must consume this composer rather than bypass it.

## Completion Standard

WP-4043 is complete only when all active resident and conference-room inference paths use one provider-independent, inspectable identity-composition pipeline; residents retain their correct personhood and office boundaries across model and chat changes; canonical sources outrank conversation memory; and privacy, authority, facts, character, relationships, and conversation context remain explicitly separated.
