# Estate Operational State, Event, and Transition Contract

Status: WP-0689 implementation contract
Schema version: `estate.operational.v1`
Campaign: CAMPAIGN-0681 — Estate Operationalization

## Boundary and canonical seam

This contract extends the existing `operational_events.py` and derived
`operational_status.py` seam with a normalized language and a pure replay validator.
Domain campaign, work-package, PTM, Dispatch, resident, service, office, workforce,
validation, evidence, message, readiness, decision and acceptance records remain
authoritative in their existing locations. The projection returned by
`operational_transition_contract.py` is explicitly rebuildable and
non-authoritative; this package adds no event store, registry, queue, scheduler,
validator service, dispatcher, authority model, dashboard, or acceptance lane.

## Normalized entity reference

Every event carries a `subject` with `subject_type`, literal canonical `subject_id`,
and repository-relative `canonical_path`. Supported types are campaign, work
package, resident, service, office, worker, provider, validation run, evidence
package, staffing request, message, escalation, and protected decision. Projection
paths and external URLs cannot masquerade as canonical sources.

## State vocabulary

The bounded vocabulary is: `observed`, `pending`, `not_ready`, `ready`, `eligible`,
`coordinating`, `executing`, `waiting_for_evidence`, `waiting_for_authority`,
`blocked`, `degraded`, `failed`, `paused`, `recovering`, `review_required`,
`complete`, `accepted`, `cancelled`, and `superseded`.

`complete` is technical/package completion, `review_required` is a decision wait,
and `accepted` requires a distinct canonical acceptance record and authorized
acceptance event. No execution result or validation verdict implies either review
or acceptance.

## Event envelope

The JSON schema is `schemas/operations/estate_operational_event_v1.schema.json`.
Each event records event identity/type, source system and record, canonical subject,
observed/effective time, prior/proposed state, emitter, authority classification,
evidence, correlation/causation, severity, idempotency key, and schema version.
Authority classifications keep observation, recommendation, coordination,
execution request, delegated mechanical action, office decision, protected
decision, and acceptance distinct. Emitting an event never grants authority.

## Transition and prerequisite rules

`TRANSITIONS` in the implementation is the machine-checkable adjacency table.
`validate_transition` additionally enforces:

- the event prior state matches the derived projection;
- recommendations and execution requests cannot mutate state;
- readiness, dependency, staffing and health prerequisites precede operational
  advancement, and stale/unknown/unavailable health fails closed;
- eligibility and completion require evidence;
- execution requires an authorized action class and explicit authority references;
- protected decisions require explicit protected-approval evidence;
- acceptance requires its own classification, canonical acceptance record, and
  authority evidence;
- missing, stale, future-dated, or conflicting prerequisite evidence stops replay.

Blocked, degraded, failed, paused and recovery routes remain explicit. Terminal
accepted, cancelled and superseded projections cannot silently restart.

## Replay, duplicates, and ordering

`replay_projection` consumes normalized events in canonical source order. An exact
duplicate event/idempotency key is recorded and ignored. Conflicting reuse of an ID
or key is rejected. Effective time may not move backwards, prior state must match,
all events must name the same canonical subject, and each event needs an explicit
transition context. The result carries applied/duplicate event IDs and unioned
evidence references so it can be discarded and rebuilt deterministically.

Out-of-order or contradictory facts are not rewritten. Their canonical source must
be reconciled or a later linked event supplied before the projection can advance.

## Compatibility notes

- CAMPAIGN-0670 Engineering artifacts may be referenced only under the explicit
  bounded-reuse authorization. Their integrated or completion-submitted state is
  not protected acceptance.
- CAMPAIGN-0680 decision-support surfaces remain read-only consumers; they cannot
  promote recommendations into decisions or become operational truth.
- WP-0678 campaign checkpoints and transition history may emit normalized source
  references, but its executor retains its own canonical state and protected-gate
  stops. A bounded commit never implies acceptance.
- Existing legacy `OperationalEvent` callers continue unchanged. Narrow adapters in
  later packages may normalize those records without rewriting their event files.

## Fixtures and integration

Valid readiness and invalid inferred-acceptance fixtures live in
`tests/fixtures/campaign_0681/`. Later CAMPAIGN-0681 packages should construct
normalized events at their read adapters, evaluate them with repository-grounded
contexts, and retain canonical source references in every derived view. They must
not write a projection back into a source domain as authoritative state.
