# GRC-007 — Identity-Preserving Grace Cognition Session Boundary

Package: GRC-007  
Roadmap package: GRC-003-F3 — Identity-preserving Grace cognition session boundary  
Role: C3 primary implementation writer  
Status: IMPLEMENTATION_COMPLETE_READY_FOR_VALIDATION  
Date: 2026-08-25

## 1. Exact authoritative F3 definition

The accepted GRC-003 roadmap defines F3 as:

Objective: bind cognition turns to Grace’s existing occupant/office/state
while keeping implementation/provider changes replaceable.

Dependencies: F1; existing resident implementation runtime and context
identity records.

Files/symbols expected to be touched: preferably a new cognition session
module; `Riverview/src/riverview/residents/runtime.py` only through a bounded
adapter seam; resident runtime tests. Current Grace gateway behavior must not
be altered.

Existing seams to reuse: `ImplementationBinding`, `RuntimeSession`,
`ResidentImplementationRuntime.validate/open_session`, transition preflight,
`PostgresBindingCatalog`, and resident context identity anchors.

New components if required: `CognitionSession`/turn record,
occupant-preserving implementation resolver, session-to-request correlation,
and explicit distinction between occupant identity, current implementation,
and cognition tier.

Database/persistence impact: likely additive persistence for cognition session
and turn lineage, but no migration in GRC-003 planning. Use an adapter over
existing continuity records where possible.

Required tests: same occupant across home/high/provider changes; current state
read from authoritative context; predecessor implementation remains history;
wrong occupant/binding rejected; session is not identity.

Acceptance criteria: replacing provider/model/resource preserves occupant,
office, authority, and state IDs; a high result cannot create a second Grace;
invalid binding and stale context fail closed.

Failure conditions: no active occupant binding, missing office authority,
stale context, implementation/occupant mismatch, or attempted identity change
through a cognition request.

Validation evidence: source inspection, identity transition tests, persisted
record readback, and an implementation replacement fixture.

Explicit non-goals: no final binding selection, no personality redesign, no
model invocation, no resource scheduling, and no canonical identity mutation.

Downstream dependencies: E1 home cognition depends on F1/F3/P1/P2; later
execution and integration packages consume the session boundary while F4
remains separately gated.

## 2. Accepted basis and existing seams

F1 is accepted and supplies typed cognition requests/results, identity fields,
classification, expiry, and advisory authority references. F2 is accepted and
supplies durable request/result provenance, exact stored request
correspondence, source lineage, correlation/causation, restart reconstruction,
and truthful failure/live-generation semantics.

The implementation inspected and reuses the existing:

- `ImplementationBinding` and `BindingCatalog` identity relationship;
- `RuntimeSession` occupant/office runtime anchor;
- `ResidentImplementationRuntime` validation/open-session seam;
- `PostgresBindingCatalog` active-binding adapter;
- `ResidentContextAssembler`/`ContextBundle` resident and office anchors; and
- immutable `RiverEvent`/`EventStore` persistence.

No existing class was relabeled as a cognition session. The new boundary is a
bounded adapter contract over those seams.

## 3. Session identity model

`CognitionSession` carries independent typed fields for:

- `session_id`;
- `resident_id`;
- `occupant_id`;
- `office_id`;
- current `implementation_id`;
- `authority_ref`;
- bounded authoritative `state_refs`;
- opening timestamp and status; and
- a versioned schema identifier.

`session_id` is required to differ from `resident_id`. It is not a provider,
model, endpoint, GPU, process, transcript, or context-window identity.

`CognitionSessionTurn` separately carries `session_id`, `request_id`,
`correlation_id`, and the identity correspondence required to attach an F1
request. A turn cannot collapse session identity into request identity.

## 4. Session/request/result distinction and F2 integration

The boundary records `cognition.session.opened` and
`cognition.session.request_attached` River events under the
`cognition_session` aggregate. F1/F2 request IDs remain unchanged; the session
association is an additional durable relation. Multiple turns can share a
session while retaining distinct request IDs and correlations.

F2 request/result exact correspondence remains authoritative for cognition
lineage. Session membership does not authorize a result to attach to another
request and does not replace F2 source-event or stored-request validation.
The accepted F2 provenance suite remains in the regression command.

## 5. Identity, authority, and source preservation

Identity enters through explicit authoritative fields or the
`open_from_runtime` adapter, which checks runtime occupant/binding occupant
and runtime office/context office correspondence. No transcript, prompt,
result prose, provider, model, GPU, endpoint, implementation class, or office
display text is used to infer identity.

Implementation replacement creates a new immutable session value with the
same session, resident, occupant, office, authority, and state identities. It
records `previous_implementation_id` in an append-only River event. It does
not mutate canonical resident identity or make a provider choice.

Authority is carried only as the existing reference. The session module has no
execution-authority field, action dispatcher, or authority-widening behavior.

## 6. Provider/resource neutrality and bounded state

The session and turn payloads contain no provider, model, endpoint, GPU, or
resource ownership field. Home/high tier changes are represented by the F1
request bound to a stable session; provider/resource selection remains later
work.

State references are bounded to 64 entries and 512 characters per reference.
The session contract has no transcript field and no arbitrary content map.
Serialized payloads therefore cannot become an ever-growing transcript
identity or session store.

## 7. Persistence, restart, and serialization

The module uses the existing immutable `RiverEvent` and `EventStore` seam;
no migration or new table was created. Session opening, implementation
replacement, and request attachment are append-only events. Reconstruction
reads the durable `cognition_session` aggregate, restores the current
implementation, and returns the attached turns. It does not depend on Python
object identity, terminal history, provider conversation IDs, or transcript
similarity.

Real PostgreSQL probe:

`POSTGRES_SESSION_RELOAD_OK 497a301e-ebf5-4cf9-8d1d-f423fd0447ed 4cb69482-a3a6-4911-9c53-7f3588292863 1`

The session and attached request were persisted, a new EventStore/boundary
was created, and the session/turn reconstructed successfully.

## 8. Failure semantics

The boundary fails closed for malformed UUIDs/schema/timestamps, session IDs
equal to resident IDs, unbounded state references, invalid authority refs,
runtime/binding/context mismatch, wrong-session turns, request identity
mismatch, malformed durable opening/turn payloads, missing opening lineage,
and changed resident/occupant/office/authority identity during
implementation reconstruction.

It does not manufacture a session from transcript content or partial prose.
Stale context remains owned by the existing runtime/context validation seam;
this package does not bypass that validation.

## 9. Files and symbols changed

Implementation repository: `ppow1/Riverview`  
Branch: `codex/c484-operator-persistent-service`

- `src/riverview/reasoning/session.py` — `CognitionSession`,
  `CognitionSessionTurn`, `CognitionSessionBoundary`, durable session/turn
  events, runtime adapter, replacement and reconstruction validation.
- `src/riverview/reasoning/__init__.py` — bounded public exports.
- `tests/test_cognition_session.py` — focused F3 identity, continuity,
  wrong-binding, serialization, persistence seam, and non-provider tests.

No existing runtime/gateway module, F1 contract, F2 provenance module, early
F4 assembler, Campaign Runner file, schema, migration, model, or GPU
assignment was changed.

## 10. Test evidence

Focused F3 suite: **8 passed**.

Combined regression suite covering F3, accepted F2 provenance and repair,
River/EventStore, F1 cognition contracts, provider-neutral contracts, resident
context/runtime, Grace authority, and adjacent Grace/provider tests:

**121 passed in 5.32s**.

Compileall and package import validation: **PASS**.

PostgreSQL session persistence/reconstruction probe: **PASS**.

The tests cover valid session creation, stable identity, session/request
distinction, wrong resident/office/authority/session rejection, transcript and
provider non-identity, implementation replacement with predecessor history,
home/high turns sharing a session, serialization, runtime adapter
correspondence, F1 regressions, and F2 exact correspondence/forged-event/
persistence regressions.

## 11. Early F4 preservation and explicit non-goals

The technically sound GRC-005 bounded packet assembler remains preserved as
early F4 implementation. It was not modified, relabeled, or accepted here.

This package does not implement provider execution, model invocation, home or
high routing, external escalation, final resource binding, scheduling/GPU
arbitration, personality redesign, F4 acceptance, F2 changes, CME
integration, Campaign Runner work, or canonical identity mutation.

## 12. Next roadmap dependency and readiness

F3 is implemented against accepted F1/F2 identity and provenance contracts.
The next execution dependencies remain P1/P2 and E1 according to the
accepted graph; F4 remains a separate prerequisite for E2/E3. Independent
validation must inspect the scoped source, River payloads, identity
transition/reconstruction behavior, tests, and runtime evidence while keeping
DESIGNED, IMPLEMENTED, TESTED, LIVE-ACCEPTED, and RUNNING distinct.

`IMPLEMENTATION_COMPLETE_READY_FOR_VALIDATION`
