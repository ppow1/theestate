# Resident Memory and Relationship Runtime

The resident memory runtime is a single governed JSON-backed service for durable resident, episodic, institutional, and relationship-adjacent memory. It extends the existing identity composer and relationship graph rather than replacing them.

## Guarantees

- Temporary conversation context remains in resident interaction sessions and is not returned as durable memory until a governed proposal is approved.
- Every durable memory carries subject, class, content, source lineage, evidence, classification, confidence, timestamps, retention, review state, disclosure scope, status, and audit lineage.
- Provider/model memory, hidden reasoning, and raw transcript accumulation are excluded from canonical memory.
- Private scopes are filtered from conference-room and shared surfaces.
- Corrections and repairs preserve original records through supersession, lineage, audit logs, and repair receipts.
- Relationship trust, familiarity, conflict, affection-expression, rituals, and milestones are handled as source-lined proposals or relationship-class memories; durable graph changes remain governed by the existing relationship graph authority.

## Persistence and migrations

The store lives at `runtime/resident_memory/memory_store.json`. Older record lists are migrated into `resident_memory_runtime.v1` by `ResidentMemoryRuntime.migrate`, preserving record IDs where present and writing an audit event. The service is deterministic for identical store state and query parameters.

## Inspection and repair

`ResidentMemoryRuntime.inspect()` returns privacy-filtered records and diagnostics for duplicates, unsupported claims, contradictions, orphaned subjects, and privacy conflicts. `repair()` supports quarantine, retirement, and patch operations with actor, reason, before/after hashes, and rollback instructions.
