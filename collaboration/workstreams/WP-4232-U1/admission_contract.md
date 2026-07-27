# Provider admission and readiness contract

Admission is an authenticated Engineering command and persists
`provider_admission.json` with adapter identity/version, capability, authority,
objective/directive, readiness reference, locality, no-egress/no-spend and
determinism assertions, schemas, effect identity policy, and stop/rollback
capability.

The public readiness projection is true for governed local execution only when
the runtime is in `governed_local_test`, the admission is durable and admitted,
the emergency stop is healthy and inactive, persistence/replay/idempotency are
healthy, and local-only, egress-disabled, and spend-disabled assertions hold.
Configuration alone cannot make the gate ready.
