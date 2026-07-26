# Validation report

Date: 2026-07-26

Focused pytest validation covers deterministic ledger creation and replay, deterministic hashes, immutable inputs and query results, append-only decision/audit chains, lineage, supersession, unresolved/expired views, duplicate and malformed inputs, unsupported versions, tamper detection, invalid lifecycle states, all seven CLI commands, and byte-for-byte CLI read-only enforcement.

Result: PASS. The same published input and explicit timestamp produce byte-equivalent ledger values. No authoritative provider artifact is written.
