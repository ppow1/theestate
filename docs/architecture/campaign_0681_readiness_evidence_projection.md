# CAMPAIGN-0681 readiness and evidence projection

WP-0698 provides a read-only adapter over existing validation, test, review,
approval, completion, and protected acceptance evidence. It creates no validator,
review lane, evidence store, approval workflow, or acceptance authority.

## Vocabulary and canonical sources

The shared states are unverified, partially evidenced, validating, ready,
accepted, rejected, stale, and indeterminate. Source precedence is protected
acceptance/rejection, approval, review, validation, test, completion receipt, then
implementation claim. Implementation activity and receipts cannot prove readiness
or acceptance. Only current `protected_acceptance` evidence naming its issuing
authority can project accepted state.

Each adapter record names a subject, stable evidence identity, repository
reference, source kind, state, issuing authority where applicable, issue time,
freshness window, optional expiry, and optional superseded identity. The complete
lineage remains in the projection, making the derived result reversible.

## Freshness, confidence, and supersession

The default freshness window is 24 hours. Undated, expired, future-dated, stale,
inaccessible, unidentified, unreferenced, unknown-source, or conflicting evidence
fails closed. A newer record may explicitly supersede an evidence identity; the
old record remains visible but cannot determine current readiness. Conflicting
content under one evidence identity or equally authoritative current results is
indeterminate. Confidence follows source authority and is never authority itself.

## Aggregation

A subject with declared dependencies cannot be ready or accepted unless every
dependency has its own protected accepted state. Otherwise it is partially
evidenced. An aggregate is accepted only when every subject is accepted, and ready
only when every subject is ready or accepted. Rejection, staleness, inaccessible
evidence, and contradictions remain visible and cannot be averaged away.

Every output is marked `derived_view_only: true` and `authorizes_action: false`.
Grace and authorized observers may display it, but canonical validation, review,
approval, and acceptance owners retain all authority.
