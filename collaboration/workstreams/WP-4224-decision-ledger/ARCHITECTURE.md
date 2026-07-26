# Architecture notes

The ledger is a content-addressed value object. Canonical JSON (sorted keys, compact separators, UTF-8, trailing newline) is SHA-256 hashed. Recommendation records preserve WP-4223 explanation, scoring evidence, snapshot/queue references, provenance, and a hash of the exact source entry. Decisions form a previous-hash chain; immutable audit records independently chain decision hashes. The ledger root hash covers all children.

Append-only behavior is structural: append returns a deep-copied new ledger after validating the old root and every child. Queries also deep-copy results. Supersession and expiry are decisions layered over immutable recommendation facts. Lineage connects each captured source hash to its ordered decisions. Trends aggregate current advisory states and never infer execution state.

Trust boundary: WP-4223 output is consumed as published. This component checks its schema version and required identity/hash fields but does not regenerate or rescore it. External JSON Schema validation is optional; runtime validation uses only the Python standard library.
