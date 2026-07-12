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
- Evelyn could state her assignment without consistently inhabiting her distinct identity;
- model switching and shared chat history allowed identity and context contamination;
- institutional facts, private continuity, authority, personality, and conversation history were not consistently separated.

## Architectural Requirement

Implement one canonical `ResidentIdentityContext` composition path used by every resident inference and by every attributed conference-room turn.

The composer must assemble bounded, source-traceable layers in a deterministic order while preserving the authority boundary of each layer.

At minimum, the composed context shall distinguish:

1. resident identity and office;
2. character-bible context;
3. current resident, employee, office, appointment, and lifecycle facts;
4. authority and delegation limits;
5. privacy, classification, and disclosure constraints;
6. relationship-layer context authorized for the active surface;
7. grounded Estate facts relevant to the request;
8. active conversation context;
9. temporary runtime and provider metadata.

## Composition Precedence

The runtime shall apply the following precedence:

1. Steward-ratified governance and authority artifacts;
2. current canonical registry and appointment state;
3. Ingrid-governed privacy and disclosure decisions;
4. canonical resident identity and Character Bible artifacts;
5. authorized relationship-layer context;
6. grounded Estate facts;
7. current conversation context;
8. provider or model defaults.

Lower layers must not override higher layers. Conversation history, model recollection, and provider defaults must never rewrite canonical identity, authority, appointment state, or privacy classification.

## Required Work

1. Inspect the existing resident gateway, model-control, onboarding, resident-surface, room, identity-package, relationship, and preference implementations before adding new structures.
2. Define a typed, read-only `ResidentIdentityContext` with explicit source lineage, classification, freshness, and version metadata.
3. Implement one composer service consumed by all resident gateway and conference-room inference paths.
4. Integrate existing canonical identity packages and resident surfaces without creating a parallel resident registry or prompt store.
5. Establish bounded layer budgets suitable for local-model operation.
6. Make missing, stale, contradictory, or unauthorized inputs visible through diagnostics rather than silently filling gaps from model memory.
7. Ensure provider changes do not alter the resident's institutional identity.
8. Preserve separate conversation histories for separate resident surfaces; do not treat an Open WebUI model switch as identity isolation.
9. Keep the composer read-only. Resident inference must not write canonical identity, authority, registry, mailbox, or relationship state.

## Surface Rules

### Single-Resident Surface

A resident receives only their own canonical identity, authorized relationship context, safe current institutional facts, and the history of that resident conversation.

### Conference Room

Each attributed resident turn receives that resident's shareable identity context plus the room's own history and disclosure envelope. The room must not inherit private resident-chat history or Evelyn's Steward-only continuity.

### Unknown or Contradictory State

If a required canonical layer is missing or contradictory, the runtime shall fail closed for the affected claim, state what is unknown, and expose a diagnostic. It shall not invent a convenient answer.

## Diagnostics

Provide a machine-readable diagnostic surface containing:

- resident ID and active surface;
- composer version and context hash;
- layer order;
- sources consulted;
- source classifications and freshness;
- omitted or redacted layers;
- missing or contradictory inputs;
- token or character budget by layer;
- provider/model selected;
- conversation-isolation identifier.

Diagnostics must not reproduce protected source content, private message bodies, secrets, or Steward-only continuity.

## Validation

Add deterministic tests proving at least:

1. Alfred, Helen, Grace, Ingrid, and Evelyn receive distinct resident identities through the same composer.
2. Alfred remains Chief of Staff and does not become Operations.
3. Grace remains Director of Operations and does not inherit Alfred's office.
4. Ingrid can describe ordinary safe identity facts without a false privacy refusal.
5. Evelyn's private relationship context is available only on authorized Steward surfaces.
6. Conference-room context does not contain private resident-chat history.
7. Registry and authority facts outrank stale conversation claims.
8. Unknown data remains unknown rather than becoming a durable invented fact.
9. Changing the underlying model preserves resident identity.
10. Every composed layer exposes lineage and remains within the configured context budget.
11. Resident inference cannot mutate canonical state.
12. All existing resident gateway and room tests continue to pass.

## Deliverables

- typed `ResidentIdentityContext` schema or model;
- canonical identity-composition service;
- resident gateway integration;
- conference-room integration;
- source-lineage and context-budget diagnostics;
- conversation-surface isolation identifiers;
- fixtures for Alfred, Helen, Grace, Ingrid, and Evelyn;
- automated tests and regression coverage;
- implementation documentation;
- completion receipt with files changed, tests, limitations, and follow-on dependencies.

## Constraints

- Strengthen existing resident runtime architecture; do not create a new institution, gateway, registry, message bus, or authority system.
- Do not embed all Estate state in one giant static prompt.
- Do not use accumulated chat history as canonical memory.
- Do not grant tools, authority, access, appointments, or privacy exceptions through character context.
- Do not implement final portrait generation or live TTS in this package.
- Keep resident-specific patches out of the shared composer unless required as explicit compatibility adapters.

## Completion Standard

WP-4043 is complete only when every active resident and every attributed conference-room turn uses the same canonical, bounded, source-traceable identity-composition path; identity remains stable across providers and conversations; private context remains isolated; contradictory state fails visibly; and no parallel source of institutional truth is introduced.
