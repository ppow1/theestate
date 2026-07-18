# CAMPAIGN-0681 operational guardrails

WP-0701 evaluates existing constitutional, protected-decision, office, campaign,
work-package, and delegation rules against a proposed operational action. It does
not create policy or authority.

Each normalized rule has a stable ID, canonical authority source, policy kind,
scope, disposition, decision owner, effective start, optional expiry, and
explanation. Precedence is constitutional, protected decision, office, campaign,
work package, then delegation. Equally authoritative conflicts escalate.

The explicit outcomes are allow, deny, defer, and escalate. Allow means only that
the proposal may proceed to its existing authorization lane; it is not execution
authority. Missing, malformed, future, stale, expired, ambiguous, or conflicting
policy never implies permission. Guardrails cannot convert protected or prohibited
actions into executable actions.

Every result records proposal evidence, applicable and controlling rules,
canonical authority sources, decision owner, missing/conflicting evidence,
explanation, timestamp, and audit payload. It always reports
`authorizes_action: false` and `creates_authority: false`.
