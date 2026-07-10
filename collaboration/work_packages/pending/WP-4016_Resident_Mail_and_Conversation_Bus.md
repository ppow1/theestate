# WP-4016 — Resident Mail and Conversation Bus

Status: Pending
Owner: Resident Runtime Implementation Stream
Execution Target: Codex
Depends On: WP-4011
Classification: Estate Internal

## Objective

Implement a governed local communication bus over the Estate's existing mailbox, message, audit, and resident identity systems so residents and offices can exchange durable messages without using GitHub or the Steward as the transport layer.

## Required Implementation

- Reuse existing personnel, mailbox, message, acknowledgment, reply, and audit mechanisms.
- Add versioned message-thread, delivery, acknowledgment, reply, and routing metadata where missing.
- Support resident-to-resident, resident-to-office, office-to-resident, and Steward-directed messages.
- Preserve sender identity, recipient identity, classification, timestamps, thread linkage, delivery status, and source artifacts.
- Add inbox, sent, archive, unread, acknowledgment, reply, and thread inspection APIs and CLI commands.
- Support concise notification summaries without exposing restricted message bodies.
- Integrate with Alfred attention routing, Helen workforce notices, Grace operational directives, and existing Office mailbox views.
- Add idempotent delivery and duplicate-message protection.
- Add tests for routing, identity resolution, classification, acknowledgments, replies, unread counts, duplicate delivery, and privacy.

## Deliverables

- communication service integrated with existing mailbox/message storage;
- versioned schemas;
- CLI and Office integration;
- tests and local demonstration;
- `operations/validation/reports/WP-4016_resident_mail_conversation_bus.md`;
- `collaboration/work_packages/completions/WP-4016_codex_done.json`.

## Boundaries

Do not create a second mailbox registry, external chat service, new authority system, or cloud dependency. Messages do not grant authority merely because they were delivered.

## Acceptance Criteria

- messages route through existing identities and mailboxes;
- threads, acknowledgments, and replies persist;
- duplicate delivery is prevented;
- restricted content stays protected;
- Office summaries remain privacy-safe;
- all focused tests pass.

## Codex Handoff

```text
Read collaboration/work_packages/pending/WP-4016_Resident_Mail_and_Conversation_Bus.md and do exactly what it says.
```
