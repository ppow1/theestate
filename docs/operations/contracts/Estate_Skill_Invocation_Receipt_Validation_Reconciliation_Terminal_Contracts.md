# Estate Skill Contracts

Invocation preserves `invocation_id`, exact Steward request, formal Skill/version, requested mode, owner, authority evidence, scope, and cancellation/timeout policy. Discovery has `executed=false` and no invocation side effect.

Execution emits only declared artifacts. A receipt is `estate.skill.receipt.v1` and records receipt/invocation IDs, Skill/version, terminal status, artifact references, validation, reconciliation, terminal result, and `institutional_acceptance: not_granted`. Validation checks schema, bounded paths, artifact hash, and declared scope. Reconciliation confirms the artifact and receipt agree and reports attention for blocked, failed, partial, stale, or conflicting outcomes. Terminal states are completed, blocked, failed, or partial; no provider result or report grants institutional acceptance.
