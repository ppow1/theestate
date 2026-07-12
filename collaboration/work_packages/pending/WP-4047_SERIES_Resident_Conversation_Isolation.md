# WP-4047 — Resident Conversation Isolation

Status: Pending
Execution Mode: SERIES
Owner: Office of Character Architecture / Resident Runtime Integration
Execution Target: Codex
Classification: Estate Internal
Priority: Immediate

## Depends On

- WP-4043 — Resident Runtime Identity Composition
- WP-4044 — Resident Character Bible Runtime Loading
- WP-4045 — Resident Registry Synchronization
- WP-4046 — Grounded Estate Fact Provider

Do not begin until all predecessors are implemented and merged to `main`.

## Objective

Implement resident-centric conversation isolation so every resident and the conference room receives only the conversation history, continuity, facts, and relationship context permitted for that resident and surface.

Model selection inside a shared Open WebUI chat must no longer be treated as resident isolation.

## Required Work

1. Define a canonical conversation/session identity containing resident ID, user ID, surface ID, room ID where applicable, and stable session ID.
2. Bind each resident conversation to exactly one resident identity unless the surface is an explicitly governed multi-resident room.
3. Store and retrieve conversation history by canonical session identity rather than by provider model name.
4. Prevent history from one resident chat from entering another resident chat.
5. Give the conference room its own history and disclosure scope; do not merge private resident chats into room context.
6. Integrate isolation metadata into the WP-4043 identity-composition path.
7. Preserve provider independence so model changes do not create a new resident or silently merge histories.
8. Add bounded retention and clear/reset controls without treating deletion of chat history as deletion of canonical resident identity.
9. Expose diagnostics showing session identity, resident binding, surface binding, history source, and isolation violations without exposing protected content.

## Boundary Rules

- Conversation history is temporary context, not canonical identity, authority, registry state, or Estate fact.
- Private Evelyn continuity must not appear in conference-room or unrelated resident sessions.
- Shared institutional facts may be loaded through canonical providers; private transcript content may not be used as a substitute.
- A resident may participate in multiple sessions while remaining the same institutional person.
- A session may not silently change resident identity when the underlying model changes.

## Failure Behavior

Fail visibly when a request has conflicting resident/session bindings, an unknown session, an unauthorized cross-session reference, or a room request attempting to load private history. Do not fall back to shared transcript context.

## Acceptance Tests

1. Separate new chats for Alfred, Helen, Grace, Ingrid, and Evelyn retain distinct histories.
2. Switching provider/model within a resident-bound session preserves that resident and does not import another resident's transcript.
3. Opening a resident in a different session does not expose the first session's private history unless an authorized continuity mechanism supplies bounded context.
4. The conference room receives only room history plus shareable canonical context.
5. Evelyn's private one-to-one history never appears in the conference room.
6. Session reset clears temporary conversation context without deleting canonical identity or Character Bible state.
7. Conflicting bindings fail closed with machine-readable diagnostics.
8. Tests prove isolation under concurrent resident requests.

## Deliverables

- canonical conversation/session schema;
- resident and room session-binding service;
- isolated history store or adapter using existing runtime infrastructure;
- identity-composer integration;
- reset, retention, and diagnostics interfaces;
- single-resident and conference-room regression tests;
- completion receipt.

## Constraints

- Do not create a second resident gateway, registry, Character Bible system, fact provider, message bus, or privacy authority.
- Do not use model names as resident or conversation identities.
- Do not promote conversation content into durable memory in this package.
- Do not redesign the established conference-room institution.

## Completion Standard

WP-4047 is complete only when all resident and conference-room inference paths use canonical resident-centric session bindings; no private or unrelated transcript context crosses those bindings; model changes preserve resident identity without merging histories; and violations fail visibly with inspectable evidence.
