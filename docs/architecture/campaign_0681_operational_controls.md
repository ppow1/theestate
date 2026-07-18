# CAMPAIGN-0681 operational controls

WP-0699 adds a plan-only control evaluator to the existing runtime recovery seam.
It evaluates pause, resume, retry, recovery, and abandonment requests but never
mutates state or creates a Dispatch request.

## Transition and authority contract

| Control | Source states | Planned state | Required authority |
|---|---|---|---|
| Pause | queued, active, validating, blocked | paused | Operations Manager, Work Owner, or Safety Authority |
| Resume | paused | queued | Operations Manager or Work Owner |
| Retry | failed or blocked | queued | Traffic Controller or Engineering Authority |
| Recover | interrupted or recovering | paused for review | Operations Manager or Recovery Operator |
| Abandon | non-terminal execution states | abandoned | Chief Architect or Steward |

Resume and recovery require a fresh, checksum-valid, canonically referenced
checkpoint. Recovery returns to paused review, not active execution. Protected
authority, privacy, staffing, and acceptance blockers cannot be cleared by a
mechanical resume, retry, or recovery.

## Retry, rollback, and evidence

Retry requires a positive bounded budget, elapsed cooldown, and a new idempotency
key. Exhaustion and duplicates are refused. Every evaluation names the actor,
roles, reason code, timestamp, source state, evidence reference, checkpoint, retry
posture, decision, and refusal reasons in an audit-event payload.

Prior failures and checkpoint lineage are preserved. Safe rollback may restore
only from the referenced checksum-valid checkpoint; destructive rollback requires
separate authority. The evaluator always reports `creates_dispatch: false`,
`mutates_state: false`, and `authorizes_acceptance: false`.
