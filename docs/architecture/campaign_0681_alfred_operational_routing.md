# CAMPAIGN-0681 Alfred Operational Routing Integration

Status: WP-0696 implementation contract

## Purpose and canonical reuse

WP-0696 extends `estate.core.alfred_runtime` to evaluate and record operational
messages through the existing repository-message and mailbox-index mechanisms.
The authoritative message remains `collaboration/messages/<message-id>.json`;
`collaboration/mailboxes/index.json` remains a generated discovery aid.

The implementation uses the canonical personnel and mailbox registries and
`mailbox_index.resolve_destination`. It creates no mailbox, notification system,
message bus, escalation queue, status registry, executor, or acceptance path.

## Supported operational message types

- notification;
- coordination request;
- staffing request;
- execution request;
- blocker escalation;
- acceptance request; and
- protected decision request.

These labels describe transport purpose. A routed execution, acceptance, or
protected-decision request is still only a request.

## Route evaluation

`evaluate_operational_route` requires:

- unique message identity;
- source, classification, payload title, and supported message type;
- explicit employee or mailbox destination IDs;
- registry-consistent destination resolution;
- current ISO-8601 evidence; and
- `operational_context.authorizes_action: false`.

The evaluation detects unresolved or guessed destinations, employee/mailbox
mismatch, stale or future timestamps, missing payloads, unsupported message types,
exact duplicates, conflicting duplicates, and unreadable existing evidence.
Uncertainty fails closed.

## Recording and discovery

`route_operational_message` writes a routable envelope to the canonical message
directory and rebuilds the existing mailbox index. It verifies that the generated
index resolves the expected destination without warning. Exact duplicates are
idempotent; a duplicate ID with changed content is refused.

The route result always states:

- routing is not execution;
- underlying work is not complete;
- acceptance was not granted; and
- no action was authorized.

## Acknowledgement and response correlation

`correlate_operational_response` recognizes canonical `reply_to`, `acknowledges`,
and `thread_id` relationships. It reports acknowledgement evidence but never turns
an acknowledgement or reply into campaign state, completion, execution, office
decision, or acceptance.

Existing `collaboration_messages.acknowledge_message` and `create_reply` remain the
write mechanisms for acknowledgements and replies.

## Alfred authority boundary

Alfred may summarize, route, brief, correlate communication evidence, and recommend
escalation. Alfred may not execute events, assign or dispatch work, decide staffing,
approve architecture, validate or accept work, merge, deploy, spend, make a
protected decision, or bypass the destination office. The destination office's
canonical decision lane remains controlling after delivery.
