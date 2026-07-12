# WP-4049 — Resident Mailbox Processing

Status: Pending
Execution Mode: SERIES
Owner: Office of Character Architecture / Resident Runtime Integration
Execution Target: Codex
Classification: Estate Internal
Priority: Immediate

## Depends On

- WP-4048 — Internal Resident Message Runtime

## Objective

Implement deterministic resident mailbox processing from canonical Estate messages so each resident can discover, read, classify, and act on actual inbound communication without fabricated mail history or manually maintained duplicate state.

## Required Work

1. Treat `collaboration/messages/*.json` as canonical and mailbox views as derived indexes.
2. Build or strengthen a deterministic mailbox-index generator keyed by canonical resident/employee identity.
3. Represent unread, read, acknowledged, deferred, and action-required states without altering the original message body.
4. Preserve classification and disclosure rules in mailbox views.
5. Detect malformed messages, unknown recipients, duplicate message IDs, stale indexes, and source/index divergence.
6. Integrate mailbox summaries with resident identity composition and grounded facts using bounded metadata rather than loading all message bodies into every turn.
7. Provide explicit read operations that retrieve authorized canonical content and produce evidence-backed state transitions.
8. Regenerate derived mailbox artifacts from canonical sources; never require manual edits to indexes.
9. Expose diagnostics containing source counts, mailbox counts, generation time, index hash/version, and conflicts without leaking protected content.

## Behavioral Rules

- A resident may report only messages visible in the current authorized mailbox view.
- “No messages” means the current generated view contains none; it must not be guessed from prompt memory.
- Reading a message and acknowledging it are separate actions.
- Conversation history does not become mailbox content.
- Shared-room participants do not inherit each participant's private mailbox.

## Acceptance Tests

1. New canonical messages appear in the correct resident mailbox after regeneration or supported refresh.
2. Messages do not appear in unrelated mailboxes.
3. Unauthorized classified messages remain absent or redacted according to policy.
4. Duplicate or malformed canonical messages produce diagnostics rather than arbitrary mailbox state.
5. Read/unread transitions are evidence-backed and survive runtime restart.
6. Rebuilding indexes from canonical sources produces deterministic results.
7. Helen, Grace, Alfred, Ingrid, and Evelyn accurately summarize their own mailbox state.
8. Conference-room context does not expose private mailbox bodies.

## Deliverables

- deterministic mailbox-index generator or strengthened existing generator;
- typed mailbox summary and item contracts;
- authorized read and state-transition interfaces;
- identity-composer and grounded-fact integration;
- drift and conflict diagnostics;
- tests and completion receipt.

## Constraints

- Do not create a second canonical message source.
- Do not manually repair derived mailbox indexes.
- Do not implement routing policy or automatic acknowledgment in this package.
- Do not expose protected message bodies in diagnostics or shared surfaces.

## Completion Standard

WP-4049 is complete only when every active resident receives an accurate, reproducible, privacy-filtered mailbox view derived from canonical messages; mailbox state changes are evidence-backed; stale or conflicting projections are visible; and residents stop inventing inbox contents.
