# Alfred Routing Engine and Worker Inbox Watcher v1

Status: Implemented  
Classification: Estate Internal  
Owner: Alfred / Chief of Staff  
Boundary Authority: Privacy and Boundary Office

## Purpose

The Alfred Routing Engine and Worker Inbox Watcher automate the first operational coordination loop in the Collaboration Layer without changing Estate governance.

The implementation preserves the approved architecture:

- Alfred owns operational routing.
- The Privacy and Boundary Office retains boundary authority.
- GitHub remains a transport adapter, not the runtime.
- Local filesystem state remains the worker execution surface.
- Message envelopes remain JSON under `collaboration/messages/`.

## Source Files

- `src/estate/core/collaboration_ops.py` implements routing, envelope validation, and inbox summaries.
- `collaboration/routing_rules.json` contains the versioned routing configuration.
- `collaboration/messages/example_alfred_routing_engine_v1.json` provides example promoted message data.

## Routing Behavior

The routing engine scans open JSON envelopes in `collaboration/messages/`, validates required envelope fields, and assigns each valid message to a worker queue.

Routing priority is:

1. Explicit destination, when the destination is not a generic queue.
2. Configured rule score from `collaboration/routing_rules.json`.
3. `alfred.review` as the default queue.

Invalid envelopes are routed to `alfred.review` with an `invalid_envelope` reason so Alfred can inspect them instead of silently dropping work.

## Inbox Watcher Behavior

The inbox watcher groups routing decisions by worker and writes durable summaries:

- `runtime/collaboration/routing/latest.json`
- `runtime/collaboration/worker_inboxes/*.json`
- `collaboration/status/worker_inbox_summary.json`

Runtime inbox files are local execution state. The status summary is safe repository-visible operational status and contains routing metadata rather than private task artifacts.

## Operational Validation

This capability is implemented. Operational validation requires using the watcher during real worker coordination and confirming that workers can claim routed messages without Steward-mediated copying.

## Architectural Questions

No architectural change was required for this implementation. Future transport adapters should consume the same message envelope and routing summary shape rather than replacing the Collaboration Layer.
