# GRC-006V — Cognition Provenance and River Event Lineage Validation

Package: GRC-006V  
Roadmap package: GRC-003-F2 — Cognition provenance and River event lineage  
Role: C2 independent implementation validator  
Date: 2026-08-25

## Verdict

**FAIL — BLOCKING DEFECTS REMAIN**

The implementation is correctly scoped as the actual GRC-003-F2 and reuses
River/EventStore appropriately. Valid request/result lineage persists and
reloads. However, the durable writer does not enforce exact result/request
correspondence before appending a result event. A forged result with
substituted resident, occupant, office, implementation, authority, or source
event identity is accepted into the request aggregate. This is a blocking
provenance and identity-integrity defect.

## Repository and commit verification

Implementation repository: `ppow1/Riverview`  
Implementation branch: `codex/c484-operator-persistent-service`  
Implementation commit:
`2a04ce0b2977814baac4d8896467c92e1c3b9bfc`

The local implementation worktree is at the reported branch and commit.
Changed implementation files are `src/riverview/reasoning/provenance.py`,
`src/riverview/reasoning/__init__.py`, and
`tests/test_cognition_provenance.py`. The earlier bounded packet assembler
remains present and was not removed.

## 1. F2 roadmap compliance — PASS

The accepted roadmap defines `GRC-003-F2` at its package card beginning at
line 228 as cognition provenance and River event lineage. Its purpose is to
distinguish cognition attempts, escalation, results, unavailable outcomes,
and continuations from deterministic work, using River correlation,
causation, idempotency, actor, identity, tier, provider/resource observation,
request, packet, policy, live-generation, result/failure, and evidence fields.

The implementation provides `CognitionProvenance`, the F2 event vocabulary,
`CognitionProvenanceWriter`, River-event conversion, idempotency/conflict
handling, and aggregate reconstruction. It does not implement provider calls,
routing, sessions, policy, resource scheduling, or orchestration, consistent
with F2 non-goals.

F2 roadmap compliance: **PASS**

## 2. River/EventStore reuse — PASS

`CognitionProvenance.to_river_event` creates the existing immutable
`RiverEvent` with aggregate type `cognition_request`, request ID aggregate
identity, separate correlation and causation IDs, River classification, and
the bounded typed payload.

`CognitionProvenanceWriter` delegates append/read to the existing
EventStore-compatible protocol. No second event store, parallel persistence
table, migration, or duplicate provenance authority was introduced.

River/EventStore reuse: **PASS**

## 3. Source/request/result lineage

### Valid path — PASS

The implementation can durably represent and reconstruct:

`source_event_id → cognition.requested(request_id) → cognition.completed(result_id)`

The request and result share request/correlation/identity fields, and the
result can carry the request event ID as causation. The real PostgreSQL probe
persisted a request and result through `EventStore`, recreated the writer, and
reconstructed two ordered records with correct causation.

### Enforcement path — FAIL

`CognitionProvenanceWriter.record` at line 347 checks only that some previously
recorded `cognition.requested` event exists for the same `request_id`. It does
not load that request payload and compare the result’s resident, occupant,
office, implementation, authority, correlation, or source event IDs.

`validate_against_request` exists at line 255, but `record` does not invoke it
against the stored request event. `for_result` also accepts a result and
source-event ID without retrieving or validating the originating request.

Therefore valid reconstruction works, but the writer can durably reconstruct
false lineage as well.

Source/request/result lineage: **FAIL**

## 4. Exact request/result correspondence — FAIL

Independent probe sequence:

1. Record a valid request event.
2. Create a result with the same request ID but substitute each identity field
   independently.
3. Create a result with a different source event ID.
4. Call `CognitionProvenanceWriter.record`.

Every probe was accepted unexpectedly:

```text
resident ACCEPTED_UNEXPECTEDLY
occupant ACCEPTED_UNEXPECTEDLY
office ACCEPTED_UNEXPECTEDLY
implementation ACCEPTED_UNEXPECTEDLY
authority ACCEPTED_UNEXPECTEDLY
source_event ACCEPTED_UNEXPECTEDLY
```

The result was not rejected merely because it had a related request ID. This
violates the F2 requirement that unrelated or mismatched results cannot attach
to another request merely through shared resident, prompt, timestamp, or
provider context.

Minimum correction: when recording any non-request event, load and validate
the canonical requested event before append. Require exact request/result
correspondence for all fields present in the request contract, and require
the result source event to match the stored request source event. Reject the
append before River persistence on mismatch. A caller-side optional
`validate_against_request` call is insufficient as the durable writer gate.

Exact request/result correspondence: **FAIL**

## 5. Identity preservation — FAIL at durable writer boundary

The typed envelope contains resident, occupant, office, implementation, and
authority fields, and direct validation can compare many of them. The River
payload also serializes them. However, the writer accepts an event stream in
which those fields change between the request and result for one request ID.

That permits durable provenance to claim a result for the wrong resident,
occupant, office, implementation, or authority. Direct typed identity
substitution was enough; no transcript or provider spoof was needed.

Identity preservation: **FAIL**

## 6. Correlation and causation — PARTIALLY PASSING

The implementation keeps correlation and causation as distinct River fields.
Serialization preserves both, and valid reconstruction preserves causal
request-to-result ancestry. River aggregate ordering remains append-oriented;
later events do not rewrite earlier request payloads.

The structural distinction passes, but correlation and causation do not replace
the missing semantic request/result correspondence gate. A result with a
forged identity or source event can still be appended under the request ID.

Correlation/causation: **PASS structurally; lineage enforcement incomplete**

## 7. Persistence/restart — PASS for valid lineage

The existing PostgreSQL `EventStore` was exercised independently. A request
and result were appended, a new `EventStore`/writer was created, and the
aggregate reloaded with two ordered records and preserved causation/timestamp
data.

Persistence/restart: **PASS for valid events**

The same durable path also accepts forged mismatched result events, which is
covered by the blocking correspondence finding.

## 8. Failure provenance — PASS

Unavailable, rejected, and timed-out outcomes carry failure codes and
`live_generation=false`; they do not become completed success. Missing
request lineage is rejected, malformed source IDs fail closed, and failure
records preserve result/status identity.

Failure provenance: **PASS**

## 9. Live-generation truth — PASS

Deterministic events cannot claim live generation. Grace home/high/external
live results require matching actor/tier and observed provider/resource
references. Non-Grace worker, validation, and Steward actors remain distinct.
Stored/replayed provenance does not itself manufacture a new live result.

Live-generation truth: **PASS**

## 10. Provider neutrality — PASS

Provider/resource fields are observations copied from an F1 result. The F2
module does not select or invoke Ollama, OpenAI, ChatGPT, a model, GPU, or
endpoint. No inappropriate fixed hardware/provider binding was introduced.

Provider neutrality: **PASS**

## 11. Authority boundary — PASS

The provenance envelope carries an authority reference but no execution
authority field. An executable-looking recommendation remains provenance/
advisory evidence and is not dispatched or executed by this package.

Authority boundary: **PASS**

## 12. Serialization integrity — PASS for individual records

Round-trip tests preserve event ID, source event ID, request/result IDs,
resident/occupant/office/implementation identity, authority, correlation,
causation, timestamp, status/failure, provider/resource observations, and
lineage references. Unsupported schema, malformed UUIDs, and invalid typed
fields fail closed.

Serialization preserves a forged record too; the missing cross-record writer
validation is the separate blocking defect.

## 13. Early F4 preservation — PASS

The early bounded packet assembler from GRC-005 remains present and its files
were not modified by GRC-006. This validation does not claim final F4
acceptance.

Early F4 implementation preserved: **PASS**

## 14. Independent tests and probes

The focused command included the new provenance suite, accepted F1 contracts,
provider-neutral contracts, resident context/runtime, Grace authority,
adjacent Grace/provider suites, and River events.

Result: **102 passed in 5.98s**.

Compileall and package import validation passed.

The tests cover valid lineage, River event shape, idempotency, conflicting
duplicates, failure outcomes, live-generation truth, identity serialization,
and missing request lineage. They do not cover a result with an existing
request ID but mismatched stored-request identity/source event. The independent
probe exposed that gap.

## 15. Next roadmap package

The submitted package must first be repaired and independently revalidated.
After F2 is accepted, the next eligible foundation package is:

**GRC-003-F3 — Identity-preserving Grace cognition session boundary**

F3 depends on accepted F1 and existing resident identity/context seams and is
not replaced by the early F4 implementation. The early F4 code remains
available, but final F4 acceptance is separate and downstream E2/E3/I1
packages remain gated on accepted F2.

Grace implementation readiness: **REPAIR_REQUIRED**

