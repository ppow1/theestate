# CAMPAIGN-0681 Engineering operational integration

WP-0697 extends the existing campaign momentum observer with a read-only
Engineering projection. It does not create a workflow, state store, scheduler,
dispatcher, validator, review system, acceptance mechanism, dashboard, or office.

## Canonical signal inventory

Adapters may supply only traceable records from existing Engineering seams:

| Source kind | Canonical source | Meaning | Precedence |
|---|---|---|---:|
| `protected_acceptance` | Protected acceptance record | Work is accepted | 100 |
| `protected_abandonment` | Authorized abandonment/closure record | Work is abandoned | 100 |
| `review_record` | Existing review or protected-gate evidence | Review, pause, or block posture | 90 |
| `validation_record` | Existing validation report/evidence | Validation posture | 80 |
| `dispatch_record` | Existing execution-dispatch record | Queued or active execution | 70 |
| `work_package_record` | Authoritative work-package/campaign artifact | Declared/blocked work state | 60 |
| `runtime_claim` | Existing runtime observation | Low-confidence runtime posture | 30 |

Every signal must name a canonical `work_id`, repository `reference`, state,
source kind, and effective timestamp. Optional owner and lane values remain
observations; they neither assign work nor establish capacity limits.

## State mapping

The minimum vocabulary is `queued`, `active`, `blocked`, `validating`, `accepted`,
`paused`, `abandoned`, and `indeterminate`. Existing ready/eligible signals map to
queued; running/in-progress maps to active; validation or completion pending
acceptance maps to validating. Only protected acceptance maps to accepted.

## Provenance, freshness, confidence, and conflicts

The projection retains the complete normalized evidence lineage and reference
set. Protected, review, and validation records are high confidence; dispatch and
work-package records are medium confidence; runtime claims are low confidence.
The default freshness window is 24 hours and may be explicitly bounded per
signal. Missing, undated, expired, future-dated, unknown-source, or unreferenced
evidence fails closed. Equally authoritative contradictory signals resolve to
`indeterminate`; lower-precedence evidence never silently overrides a canonical
record. Stale evidence is surfaced in warnings even when current evidence exists.

The capacity summary reports observed active, queued, and blocked counts and
named active lanes. It explicitly leaves the capacity limit unknown because a
projection must not infer staffing or assignment authority.

Every projection carries `derived_view_only: true` and
`authorizes_action: false`. Engineering governance and canonical records remain
authoritative. Grace and other authorized operational surfaces may display this
view, but cannot use it to dispatch, validate, accept, merge, close, pause, or
abandon work.
