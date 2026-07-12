# WP-4048 — Internal Resident Message Runtime

Status: Pending
Execution Mode: SERIES
Owner: Office of Character Architecture / Resident Runtime Integration
Execution Target: Codex
Classification: Estate Internal
Priority: Immediate

## Depends On

- WP-4047 — Resident Conversation Isolation

## Objective

Implement a canonical internal resident-message runtime so residents can create, receive, inspect, and reference real Estate messages without pretending communication occurred.

`collaboration/messages/*.json` remains the canonical message source. This package must strengthen that system rather than create a parallel bus.

## Required Work

1. Inspect the existing canonical message schema, message files, employee/resident identifiers, mailbox projections, and routing utilities.
2. Define one typed runtime interface for composing and reading canonical messages.
3. Require explicit sender, recipient, classification, subject, body, created time, message ID, and delivery state.
4. Validate sender and recipient against synchronized resident/employee state.
5. Enforce authority and disclosure boundaries before a message is written or read.
6. Persist successful sends as canonical message artifacts using existing repository conventions.
7. Return a concrete receipt containing message ID, canonical path, sender, recipients, classification, and write status.
8. Make resident inference distinguish draft intent, successful send, failed send, and unverified historical claim.
9. Integrate message facts with the grounded fact provider so residents answer from evidence rather than model memory.
10. Preserve room and conversation isolation; creating a message does not inject private chat history into the message body automatically.

## Behavioral Rules

Residents shall not say they sent, received, read, acknowledged, or routed a message unless the corresponding canonical evidence exists.

When a send fails, the resident must report failure and may offer a draft; it may not narrate success.

Message content must be authored by the resident or user within the permitted context. Hidden private continuity must not be copied into a message merely because it was available to the sender's inference context.

## Acceptance Tests

1. A valid resident-to-resident message creates exactly one canonical message artifact and returns its ID/path.
2. Invalid or inactive recipients fail visibly without creating an artifact.
3. Residents cannot claim a send succeeded when persistence failed.
4. Duplicate retries are idempotent or produce explicit duplicate diagnostics.
5. Classified content is unavailable to unauthorized residents and surfaces.
6. The conference room cannot silently send privileged messages.
7. Helen no longer invents mail history; she reports only canonical messages.
8. Tests prove canonical artifacts, source lineage, validation, classification enforcement, and safe failure.

## Deliverables

- canonical message runtime interface;
- sender/recipient and authority validation;
- canonical persistence adapter;
- message receipts and diagnostics;
- grounded-fact integration;
- resident fixtures and regression tests;
- completion receipt.

## Non-Goals

- Do not create mailbox indexes in this package beyond the minimum compatibility required for existing projections.
- Do not implement automated routing, escalation, acknowledgment policy, or external email.
- Do not create a second message store or event bus.

## Completion Standard

WP-4048 is complete only when residents can create and inspect real canonical Estate messages through one governed runtime, every claimed communication is supported by evidence, unauthorized or failed operations remain explicit, and no parallel message system is introduced.
