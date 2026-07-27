# Provider adapter contract

Registered adapter: `estate.local.sha256` version `1.0.0`.

The descriptor declares capability `deterministic.sha256`, effect type
`local_hash`, `in_process` locality, UTF-8 string input capped at 4096 bytes,
SHA-256 output, deterministic behavior, no egress, no spend, no machine-state
mutation, stop support, and rollback support.

Unknown adapters, identity/version mismatches, malformed schemas, network or
egress capability, spend capability, non-determinism, and missing stop/rollback
capability fail closed. No arbitrary shell or file execution path exists.
