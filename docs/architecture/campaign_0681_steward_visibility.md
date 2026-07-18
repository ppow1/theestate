# CAMPAIGN-0681 Steward operational visibility

WP-0703 extends the existing Steward dashboard with a bounded, read-only view of
caller-supplied canonical health, momentum, blocker, readiness, office,
Engineering, and audit projections. It creates no registry, queue, control plane,
or truth source.

The information architecture presents highest-priority constraints, protected
decisions, campaign momentum, health/readiness, audit/evidence, then explicitly
authorized controls. Failed, protected, blocked, indeterminate, stale, degraded,
active, and ready signals are ordered deterministically. Status is always shown as
text, never color alone.

Every item carries stable identity, state, freshness, confidence, observation
time, owner, warnings, classification, and canonical drill-through references.
Missing references or protected-decision authority/questions become visibly
indeterminate. Restricted details are redacted according to the viewer's existing
classification access while the canonical reference remains visible.

Controls appear only when both the control evidence marks them authorized and the
viewer's evidenced role is allowed. Display never grants authority. The view is
bounded to 500 items, reports truncation, and always returns
`derived_view_only: true` and `authorizes_action: false`.
