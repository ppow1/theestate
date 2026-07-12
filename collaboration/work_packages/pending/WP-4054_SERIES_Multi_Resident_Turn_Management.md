# WP-4054 — Multi-Resident Turn Management

Status: Pending
Execution Mode: SERIES
Owner: Office of Character Architecture / Resident Runtime Integration
Execution Target: Codex
Classification: Estate Internal
Priority: Immediate

## Depends On

- WP-4052 — Conference Room Context and Disclosure Rules

## Objective

Implement deterministic multi-resident turn management so conference-room exchanges preserve attribution, ordering, participation boundaries, interruption handling, and bounded context without collapsing residents into one voice.

## Required Work

1. Define a canonical room-turn record containing room ID, turn ID, speaker, addressee, sequence, reply target, timestamps, and disclosure metadata.
2. Add a turn coordinator that selects eligible speakers through explicit room rules rather than arbitrary model order.
3. Support directed questions, open-floor prompts, moderator sequencing, bounded follow-ups, abstention, and interruption requests.
4. Preserve each resident's independent identity composition and context window.
5. Prevent one resident's draft cognition or hidden prompt from entering another resident's context.
6. Limit repetition, pile-on behavior, and unbounded response fan-out.
7. Record skipped, denied, timed-out, and failed turns with diagnostics.
8. Keep privileged actions disabled unless routed through separately governed action systems.

## Behavioral Rules

- Each contribution belongs to exactly one canonical speaker.
- Silence or abstention is valid and must not be filled with fabricated speech.
- Turn coordination does not make the coordinator an authority over resident identity or institutional decisions.
- Residents may disagree without having their distinct positions merged into a synthetic consensus.

## Acceptance Tests

1. Directed prompts reach only eligible addressees unless the room explicitly opens discussion.
2. Every response is correctly attributed and ordered.
3. Residents retain distinct voice and role across long room sessions.
4. Private context and hidden cognition never cross participant boundaries.
5. Timeouts and failures remain visible without invented responses.
6. The coordinator prevents duplicate and runaway turns.
7. Disagreement remains represented accurately.
8. Concurrent room requests preserve deterministic sequencing.

## Deliverables

- typed room-turn schema;
- turn coordinator and participation policy;
- speaker-selection and reply-target handling;
- bounded fan-out and timeout controls;
- diagnostics, tests, documentation, and completion receipt.

## Constraints

- Do not create a second conference-room institution.
- Do not merge resident identities or prompts.
- Do not infer authority from speaking order.
- Do not add privileged action execution.

## Completion Standard

WP-4054 is complete only when multi-resident conversations produce deterministic, attributed, bounded turns; residents remain distinct; private context and hidden cognition remain isolated; failures and abstentions are represented honestly; and room sequencing cannot silently create authority or consensus.
