# WP-4085 — Passive Resident Interaction Engine

Status: Pending
Execution Mode: SERIES
Owner: Office of Character Architecture / Resident Social Runtime Integration
Execution Target: Codex
Classification: Estate Internal
Priority: Immediate

## Depends On

- WP-4050 — Resident Message Routing and Acknowledgment
- WP-4051 — Resident Relationship Graph Runtime
- WP-4063 — Resident Memory Runtime
- WP-4083 — Ambient Resident Activity Runtime
- WP-4084 — Dynamic Estate Occupancy Runtime

## Objective

Implement bounded passive resident interactions that create believable social texture when residents share a space or activity, without fabricating consequential conversations, messages, commitments, or private relationship events.

## Required Work

1. Define a typed passive-interaction record with participants, location, trigger, interaction class, visibility, relationship context, generated content, source state, and persistence policy.
2. Support greetings, acknowledgments, brief check-ins, offers of assistance, shared-break moments, passing observations, and lightweight banter.
3. Select interactions from occupancy, relationship, role, activity, memory, and character-presentation context.
4. Require explicit canonical messaging for any communication that creates a task, commitment, approval, decision, or durable institutional fact.
5. Prevent passive interactions from creating romance, conflict, consent, private disclosure, or relationship-state changes without appropriate evidence and scope.
6. Preserve each resident's distinct voice, boundaries, humor, warmth, and professional mode.
7. Apply repetition limits, cooldowns, participation consent, availability, and privacy filters.
8. Allow no interaction, silence, or simple acknowledgment as valid outcomes.

## Acceptance Tests

1. Co-located residents may produce brief character-consistent interactions.
2. Interaction frequency remains bounded and does not become chatter spam.
3. No task, approval, decision, or message is fabricated.
4. Private or restricted relationship context does not leak.
5. Residents remain recognizably distinct.
6. Silence and abstention are represented honestly.
7. Restart does not replay transient interactions as new events.
8. Durable interactions persist only when an existing memory or message policy authorizes them.

## Deliverables

- passive-interaction schema and policy;
- trigger and participant selector;
- character-consistent utterance adapter;
- privacy, cooldown, and persistence controls;
- tests, diagnostics, documentation, and completion receipt.

## Constraints

- Do not create a second messaging, relationship, memory, or conference system.
- Do not manufacture consequential events through ambient narration.
- Do not force residents to speak or socialize.

## Completion Standard

WP-4085 is complete only when residents can exchange bounded, optional, character-consistent social moments based on real presence and relationship context; consequential communication remains canonical and explicit; private context stays protected; and social texture increases without producing fabricated institutional history.
