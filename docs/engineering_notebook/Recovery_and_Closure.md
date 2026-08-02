# Recovery and Closure

For recovery, retain the last verified JSON, Markdown rendering, handoff, and
verification receipts. Re-check source digests and authorization before issuing
a new packet. If the state is conflicted, create a new governed reconciliation
action rather than editing history. If a worker is reassigned, record the
handoff and require fresh acknowledgment.

Completion requires final validation, a verified update, reconciliation against
authoritative receipts, and a terminal result. Archive the notebook read-only
with its source digests and rejected proposals. Do not delete failed states or
silently roll back persistent data. Institutional acceptance remains a separate
Steward decision.
