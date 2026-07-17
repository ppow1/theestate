# WP-0699 — Operational Pause, Resume, Retry, and Recovery Controls

## Campaign
CAMPAIGN-0681 — Estate Operationalization

## Purpose
Define bounded operational controls for pausing, resuming, retrying, and recovering campaign and work-package activity without bypassing canonical authority, losing evidence, or obscuring the reason for intervention.

## Objectives
- Establish explicit operational semantics for pause, resume, retry, recovery, and abandonment.
- Preserve state history, causality, ownership, and evidence across interruptions.
- Distinguish operator-requested pauses from dependency blocks, safety stops, infrastructure failures, and authority holds.
- Prevent automated recovery from becoming unauthorized redispatch or acceptance.

## Required Work
1. Define allowed pause, resume, retry, recovery, and abandonment transitions using the WP-0689 state contract.
2. Define the authority required for each transition under the WP-0690 action taxonomy.
3. Define retry budgets, cooldowns, idempotency expectations, and duplicate-work prevention.
4. Define recovery checkpoints, required evidence, and safe rollback behavior.
5. Define how blockers and escalation signals from WP-0693 affect available controls.
6. Define user-visible reason codes, timestamps, actor identity, and provenance for every intervention.
7. Define tests for interrupted execution, repeated failure, stale recovery state, and contested authority.

## Constraints
- A resume or retry must not silently create a new dispatch.
- Recovery must not overwrite or conceal failed evidence.
- Automated controls must remain bounded by explicit authority and retry limits.
- No action may infer acceptance, completion, or readiness.
- Canonical campaign and work-package records remain authoritative.

## Deliverables
- Operational control vocabulary and transition matrix.
- Authority matrix for pause, resume, retry, recovery, and abandonment.
- Retry and cooldown policy.
- Recovery checkpoint and rollback contract.
- Reason-code and audit-event schema.
- Representative transition and failure-mode tests.

## Acceptance Criteria
- Every operational intervention is attributable, explainable, and reversible where appropriate.
- Repeated failure cannot produce an unbounded retry loop.
- Resume and recovery preserve prior evidence and state history.
- Unauthorized actors cannot change execution state.
- Recovery behavior does not create parallel dispatch or acceptance workflows.

## Dependencies
- WP-0689
- WP-0690
- WP-0691
- WP-0692
- WP-0693
- WP-0698

## Constitutional Precedence
Existing constitutional authority, campaign governance, office authority, Engineering execution rules, and accepted records remain authoritative. This work package defines operational controls only within those bounds.
