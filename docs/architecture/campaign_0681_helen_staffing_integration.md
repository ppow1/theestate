# CAMPAIGN-0681 Helen Staffing and Capability Integration

Status: WP-0695 implementation contract

## Canonical seam

WP-0695 extends `HelenWorkforceStore` in
`src/estate/core/helen_workforce.py`. Requests, assessments, operational
dispositions, events, and status remain under the existing
`runtime/workforce_development/` seam. No personnel, provider, capability,
campaign, mailbox, or staffing registry is created.

## Blocker-to-request adapter

`create_operational_request` accepts only WP-0693
`staffing_or_capability_blocker` and `provider_or_environment_blocker`
classifications with canonical evidence. It records:

- campaign and package correlation;
- staffing, capability, provider, or environment need kind;
- required role and capabilities;
- urgency and bounded duration;
- operational constraints and protected constraints;
- evidence references; and
- explicit false authority and execution flags.

The result is a canonical `WorkforceRequest` with request type
`staffing_request`. A request is evidence of demand, not fulfillment. Missing
identity, role, capability, urgency, duration, or evidence fails closed.

Budget, privacy, protected-policy, unresolved-provider-suitability, or an upstream
protected-decision flag makes the request blocked and requires the applicable
protected lane. Helen's workforce intake cannot resolve those constraints by
assertion.

## Disposition correlation

`record_operational_disposition` records fulfilled, partially fulfilled, refused,
deferred, expired, and protected-review-required outcomes in the same workforce
store. It updates the correlated request status without assigning staff or
executing a provider.

Fulfillment and partial fulfillment require:

- `decided_by: Helen`;
- explicit authority evidence;
- evidence for the claimed capability; and
- no unresolved protected constraint.

Partial fulfillment lists the remaining capabilities. Refusal, deferral, expiry,
and protected review keep the unresolved need visible. An expired disposition
requires an explicit expiry timestamp.

## Authority boundary

Helen may assess workforce fit, availability, capability, and staffing disposition
within the accepted Human Resources lane. The adapter expressly grants no
Engineering priority, architecture, Dispatch, provider execution, merge,
deployment, Engineering acceptance, Steward, or institutional acceptance
authority. Model or provider availability alone is never staffing fulfillment.

Grace receives only operational constraint summaries and correlated disposition
evidence. Private workforce details remain governed by existing classification and
boundary-review controls.

## Progression semantics

- `fulfilled`: all required capabilities are evidenced; request becomes closed.
- `partially_fulfilled`: evidenced capabilities are recorded; remaining need stays
  visible and the request is ready for further governed action.
- `refused`: request becomes declined.
- `deferred`, `expired`, or `protected_review_required`: request remains blocked.

None of these states dispatches work, accepts deliverables, or changes campaign
priority. Later packages may observe the evidence through existing canonical
state adapters.
