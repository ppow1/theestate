# WP-4050 — Resident Message Routing and Acknowledgment

Status: Pending
Execution Mode: SERIES
Owner: Office of Character Architecture / Resident Runtime Integration
Execution Target: Codex
Classification: Estate Internal
Priority: Immediate

## Depends On

- WP-4048 — Internal Resident Message Runtime
- WP-4049 — Resident Mailbox Processing

## Objective

Implement governed message routing, delivery-state transitions, and acknowledgments so canonical Estate messages move through existing institutional channels with visible evidence and without granting residents new authority.

## Required Work

1. Inspect existing message-routing, mailbox, employee, office, delegation, and operational-sequencing artifacts before adding code.
2. Define deterministic routing rules for direct residents, offices, employee IDs, and explicitly authorized distribution targets.
3. Resolve recipients through synchronized canonical registries and fail closed on ambiguity.
4. Record delivery, read, acknowledgment, rejection, deferral, and routing-failure states as linked evidence without rewriting the original canonical message body.
5. Support explicit human or resident acknowledgment with actor, timestamp, status, and optional bounded note.
6. Prevent acknowledgment from implying approval, acceptance, completion, authority transfer, or task execution.
7. Provide idempotent retry behavior and duplicate-delivery protection.
8. Integrate route and acknowledgment facts with mailbox summaries and the grounded fact provider.
9. Expose machine-readable diagnostics for unresolved recipients, classification conflicts, stale routes, duplicate attempts, and failed delivery.

## Institutional Boundaries

- Grace may coordinate operational sequencing but routing mechanics do not transfer her authority to another resident.
- Alfred may protect the Steward's attention but may not silently suppress, approve, or accept messages outside granted authority.
- Helen may receive workforce and continuity messages but may not invent employee actions.
- Ingrid's privacy and classification controls remain authoritative for disclosure decisions.
- Acknowledgment proves receipt or stated disposition only.

## Acceptance Tests

1. A direct message reaches exactly the resolved canonical recipient mailbox.
2. Ambiguous, inactive, or unauthorized targets fail without partial delivery.
3. Retry of the same route does not produce duplicate delivery.
4. Read and acknowledgment states remain separate.
5. Acknowledgment never changes package, appointment, approval, or activation state.
6. Classified messages route only to authorized recipients.
7. Routing and acknowledgment evidence survives restart and can be inspected without exposing unrelated protected content.
8. Residents accurately answer whether a message was delivered, read, or acknowledged from canonical evidence.

## Deliverables

- governed routing resolver;
- delivery and acknowledgment evidence schema;
- idempotent route execution and retry handling;
- mailbox and grounded-fact integration;
- diagnostics and regression tests;
- completion receipt.

## Constraints

- Do not create a second message bus, scheduler, registry, or authority system.
- Do not treat delivery or acknowledgment as approval or completed work.
- Do not add external email or notification providers.
- Do not allow resident inference to route privileged messages without governed action validation.

## Completion Standard

WP-4050 is complete only when canonical messages are routed deterministically through existing Estate identities and offices; delivery and acknowledgment states are durable, inspectable, and semantically precise; retries are safe; and no routing event silently grants authority or changes institutional state.
