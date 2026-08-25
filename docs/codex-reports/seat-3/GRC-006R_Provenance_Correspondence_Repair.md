# GRC-006R — Enforce Exact Stored Request/Result Provenance Correspondence

Package: GRC-006R  
Roadmap package: GRC-003-F2 — Cognition provenance and River event lineage  
Role: C3 repair writer  
Status: REPAIR_COMPLETE_READY_FOR_REVALIDATION  
Date: 2026-08-25

## 1. Exact C2 defect

GRC-006V identified that `CognitionProvenanceWriter.record` only checked for
the existence of a `cognition.requested` event with the same `request_id`.
It did not parse the stored request payload or invoke the typed
correspondence validator. Consequently, a downstream event could substitute
resident, occupant, office, implementation, authority, or source-event
identity and still be appended to the request aggregate.

The defect was at the durable writer boundary. Caller-side
`validate_against_request(...)` was optional and therefore insufficient to
protect persisted lineage.

## 2. Root cause

The writer treated request existence as equivalent to request correspondence.
The existing typed validator compared a candidate with an in-memory F1 request
or packet, but `record` never reconstructed the canonical request from River
storage before appending a non-request event.

## 3. Durable-writer repair

`CognitionProvenanceWriter.record` now, for every non-`cognition.requested`
event:

1. reads the request aggregate from the injected `CognitionEventStore`;
2. identifies the stored `cognition.requested` River row;
3. rejects missing or ambiguous request lineage;
4. reconstructs the typed `CognitionProvenance` request payload;
5. rejects malformed or invalid stored request payloads; and
6. invokes the authoritative typed correspondence validator before
   `EventStore.append`.

No candidate downstream event reaches persistence when correspondence fails.
The request event itself retains its original creation/idempotency behavior.

The repair reuses `CognitionProvenance.validate_against_request` by extending
it to accept the canonical stored provenance request. It does not create a
second competing correspondence implementation.

## 4. Exact fields enforced

Against the stored request, downstream events must preserve:

- `request_id`;
- `correlation_id`;
- `resident_id`;
- `occupant_id`;
- `office_id`;
- `implementation_id`;
- `authority_ref`;
- `source_event_id`;
- `cognition_tier`; and
- `classification`.

If the canonical request contains a `packet_id`, it must also match. Result
facts such as result ID, status, failure code, provider/resource observation,
and live-generation state remain result-specific and are not incorrectly
frozen to request values. Policy decision references remain result/request
facts according to their existing F1 contract and are not overconstrained by
this repair.

Correlation and causation remain separate River fields. This repair enforces
the required source and identity correspondence without collapsing those
semantics.

## 5. Downstream event types covered

The writer gate applies to every non-request provenance event, including:

- `cognition.admitted`;
- `cognition.held`;
- `cognition.started`;
- `cognition.completed`;
- `cognition.unavailable`;
- `cognition.rejected`;
- `cognition.timed_out`; and
- `cognition.integrated`.

Thus failure and unavailable outcomes cannot use a shared request ID to
substitute authoritative identity.

## 6. Idempotency and valid lineage

Existing River idempotency behavior remains in place. An identical repeat
event continues to return the existing acknowledgement. A conflicting payload
with the same event identity remains rejected. Correspondence validation runs
before append and therefore does not weaken conflict handling.

A matching request/result pair still appends successfully and reconstructs as
an ordered source → request → result lineage. Existing request creation and
duplicate behavior were preserved.

## 7. Regression evidence

The new direct durable-writer tests record a valid request and independently
attempt downstream events with substituted:

- resident ID;
- occupant ID;
- office ID;
- implementation ID;
- authority reference; and
- source-event ID.

Each attempt is rejected with the specific correspondence error, and the
stored event history remains unchanged. Additional tests cover:

- successful matching result append and reload;
- unavailable, rejected, and timed-out events using the same canonical
  correspondence gate;
- rejection of a forged failure event;
- malformed stored request payload rejection before append; and
- ambiguity/missing-lineage fail-closed behavior through the writer path.

## 8. PostgreSQL persistence/restart evidence

The actual PostgreSQL `EventStore` was exercised with a fresh request and
matching result. The writer and EventStore were recreated before reload.
The aggregate reconstructed two ordered records with the original request and
result IDs, matching source event, and request-event causation.

Probe result:

`POSTGRES_RELOAD_OK d00777a6-d38d-4974-a389-5833f8c555e6 True True 2`

No migration, schema change, or new persistence table was required. The
canonical request is read from durable River state rather than an in-memory
cache.

## 9. Preserved regression areas

The repair does not change provider selection, model selection, resource
binding, authority execution, or live-generation rules.

- Failure provenance regression: PASS.
- Provider neutrality regression: PASS; no provider/model/endpoint/GPU was
  introduced.
- Authority-boundary regression: PASS; `authority_ref` remains a reference,
  not execution authorization.
- Live-generation regression: PASS; deterministic/no-generation and actor/tier
  truth rules remain unchanged.
- F1 identity, bounded context, operational-state aggregate inclusion, and
  provider-neutral contract behavior remain passing.

## 10. Early F4 preservation

The technically sound early F4 bounded packet assembler from GRC-005 was not
modified, deleted, relabeled, or accepted by this repair. Its final F4
acceptance remains separately gated by the roadmap prerequisites and F4
validation.

## 11. Files changed

Implementation repository `ppow1/Riverview`, branch
`codex/c484-operator-persistent-service`:

- `src/riverview/reasoning/provenance.py` — canonical stored-request lookup,
  typed reconstruction, and durable correspondence gate.
- `tests/test_cognition_provenance.py` — corrected valid restart fixture to
  use the same authoritative source event as its request.
- `tests/test_cognition_provenance_repair.py` — focused mismatch, failure,
  malformed-payload, history-integrity, and valid-lineage regressions.

No River foundation replacement, provider routing, authority semantics, F3
session work, F4 assembler work, Campaign Runner work, migration, model
selection, or GPU assignment was made.

## 12. Tests and validation

Focused provenance and repair tests: **27 passed**.

Required combined regression suite, including provenance, repair, River,
accepted F1 contracts, provider-neutral contracts, resident context/runtime,
Grace authority, and adjacent Grace/provider tests: **113 passed in 6.72s**.

Compile/import validation: **PASS** (`compileall` and package imports).

PostgreSQL durable reload probe: **PASS**.

## 13. Readiness

The durable request/result correspondence gate is repaired and ready for
independent C2 revalidation. C3 does not self-accept the repair.

`REPAIR_COMPLETE_READY_FOR_REVALIDATION`

