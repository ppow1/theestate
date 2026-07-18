# CAMPAIGN-0681 acceptance, graduation, and closeout

WP-0704 extends the read-only readiness projection with acceptance-readiness and
closeout-draft functions. It does not create an acceptance lane or close campaigns.

Capabilities distinguish implemented, validated, operationally ready, accepted,
graduated, and retired lifecycle concepts. A complete graduation bundle requires
validation, operating procedure, ownership, support, recovery, observability,
audit, and authority records. Every capability names its canonical accepting
authority. Running software, elapsed time, completion receipts, validation, or a
dashboard state cannot produce acceptance.

Accepted state is observed only from a protected acceptance reference issued by
the named authority after the evidence bundle is complete. Conditional exceptions
must name risk and authority evidence. Deferred scope must name successor work.
Residual risks, exceptions, deferred scope, and successor obligations stay in the
assessment and closeout draft.

The closeout draft records accepted deliverables, continuity ownership, evidence,
support/recovery obligations, residual risk, deferred scope, successors, and
pending protected acceptance. Campaign acceptance requires an existing Steward
acceptance record. Even then, the draft remains blocked for separate manual
closeout authority and reports `campaign_closed: false` and
`authorizes_action: false`.
