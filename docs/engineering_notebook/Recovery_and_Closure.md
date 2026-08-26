# Recovery and Closure

For recovery, load the last verified JSON through the runtime loader, verify its
revision and digest, retain the Markdown rendering, handoff, and append-only
verification/rejection receipts. Re-check source digests and authorization
before issuing a new packet. If the state is conflicted, refresh it through the
authoritative refresh operation rather than editing history. If a worker is
reassigned, record the handoff and require fresh acknowledgment.

Completion requires final validation, a verified update, reconciliation against
authoritative receipts, and a terminal result. Archive through the atomic
archive helper; the archived snapshot retains revision, prior/resulting digests,
update IDs, idempotency keys, and institutional acceptance state. Interrupted
writes leave the previous snapshot intact. Do not delete failed states or
silently roll back persistent data. Institutional acceptance remains a separate
Steward decision.
