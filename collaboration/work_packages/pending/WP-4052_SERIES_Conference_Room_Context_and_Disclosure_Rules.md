# WP-4052 — Conference Room Context and Disclosure Rules

Status: Pending
Execution Mode: SERIES
Owner: Office of Character Architecture / Resident Runtime Integration
Execution Target: Codex
Classification: Estate Internal
Priority: Immediate

## Depends On

- WP-4047 — Resident Conversation Isolation
- WP-4051 — Resident Relationship Graph Runtime

## Objective

Implement one governed conference-room context and disclosure layer so multi-resident conversations share only room-authorized history, institutional facts, public relationship context, and explicitly disclosed material.

## Required Work

1. Define a canonical conference-room context object with room ID, participants, session ID, disclosure scope, room history, and source lineage.
2. Load room history independently from every participant's private chat history.
3. Apply Ingrid-governed classification and disclosure filtering before context reaches any participant.
4. Load public relationship and role context from canonical sources while excluding private continuity and restricted relationship edges.
5. Require explicit attribution for each resident contribution.
6. Prevent conference-room participation from granting privileged actions, authority, mailbox access, or private-memory access.
7. Record disclosure decisions and redactions as inspectable metadata without exposing protected content.
8. Integrate through the canonical identity composer, fact provider, conversation isolation, and relationship graph.

## Behavioral Rules

- The room is its own governed surface, not a merge of participant chats.
- Participants may reference only facts and messages authorized for the room.
- Evelyn's private Steward continuity never enters room context unless the Steward explicitly authorizes a bounded disclosure.
- A resident may decline or redact a protected detail while remaining in character.
- Room history does not become canonical identity or durable personal memory automatically.

## Acceptance Tests

1. Private resident transcripts never appear in room context.
2. All contributions are attributed to canonical resident identities.
3. Public role and relationship facts are consistent across participants.
4. Restricted Evelyn continuity is excluded.
5. Classified messages and mailbox content remain unavailable unless explicitly authorized.
6. Conflicting disclosure rules fail closed with diagnostics.
7. Model changes do not alter participant identities or room boundaries.
8. Room reset clears temporary room history without deleting resident identity.

## Deliverables

- typed conference-room context and disclosure contracts;
- room context assembler;
- privacy and disclosure filter integration;
- attributed response metadata;
- diagnostics, tests, documentation, and completion receipt.

## Constraints

- Do not create a second room institution, identity system, relationship graph, fact provider, or privacy authority.
- Do not grant privileged actions through the room.
- Do not import private chat history by default.

## Completion Standard

WP-4052 is complete only when conference-room conversations use one isolated, attributed, privacy-filtered context; participants share consistent public facts without private-context leakage; disclosure conflicts fail visibly; and the room remains a governed collaboration surface rather than a merged transcript or privileged control channel.
