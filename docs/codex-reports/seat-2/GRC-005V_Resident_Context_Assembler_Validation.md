# GRC-005V — Resident Context Assembler Independent Validation

Package: GRC-005V  
Role: C2 independent Grace implementation validator  
Date: 2026-08-25

## Verdict

**FAIL — BLOCKING DEFECTS REMAIN**

The submitted implementation is behaviorally a strong bounded resident
reasoning-packet assembler, but it is not the authoritative GRC-003 F2
package. The accepted roadmap defines `GRC-003-F2` as cognition provenance and
River event lineage. The submitted source implements the roadmap’s
`GRC-003-F4` bounded reasoning-packet assembly instead.

Accepting this package as F2 would falsely close the provenance foundation
while the required F2 event envelope, event types, and durable lineage
validation remain unimplemented. This is a blocking roadmap/package-gate
defect. No blocking behavioral defect was found in the assembler considered as
an F4 implementation.

## Repository and commit verification

Implementation repository: `ppow1/Riverview`  
Implementation branch: `codex/c484-operator-persistent-service`  
Implementation commit:
`dab860cd8eb02b6333fbade67f6a63abb8887181`

The local implementation worktree is at the reported branch and commit. The
changed implementation files are:

* `src/riverview/reasoning/context_assembler.py`;
* `src/riverview/reasoning/__init__.py`; and
* `tests/test_reasoning_context_assembler.py`.

No Campaign Runner files were changed by this validation.

## 1. Roadmap compliance — FAIL

The accepted roadmap states at line 128 that the foundation includes:

* `GRC-003-F2`: cognition provenance and River event envelope;
* `GRC-003-F3`: identity-preserving Grace cognition session boundary; and
* `GRC-003-F4`: bounded Grace reasoning-packet assembly.

The authoritative F2 package card begins at line 228:

* objective: distinguish every cognition attempt, escalation, result,
  unavailable outcome, and continuation from deterministic work;
* expected ownership: `river/events.py`, `river/store.py`, and a bounded
  provenance/event helper;
* required envelope: actor class, resident/occupant/office, tier,
  implementation, provider/resource class, request/correlation, packet,
  policy, live-generation, result/failure status, and evidence refs;
* required event types: requested, admitted, held, started, completed,
  unavailable, rejected, timed_out, and integrated; and
* required durable event, idempotency, causation, mismatch, and truthful
  generation tests.

The bounded packet assembler card begins at line 317 and matches the submitted
source: project identity/current state/relevant evidence/task/authority into
`ResidentReasoningPacket`, using `ContextBundle`, budgets, contradiction
handling, and packet digest.

The GRC-005 report’s claim that the roadmap defines F2 as the packet projector
contradicts the accepted roadmap. The implementation therefore satisfies the
F4-shaped objective, not the authoritative F2 objective.

F2 roadmap compliance: **FAIL**

## 2. Actual assembler behavior

`ResidentReasoningPacketAssembler` projects one accepted `ContextBundle` into
the accepted F1 `ResidentReasoningPacket` through:

* mandatory identity, office, and authority anchors;
* explicit request lineage and task fields;
* bounded source-reference projection;
* stable layer/item/reference ordering;
* duplicate-reference removal preserving first occurrence;
* preflight collection, individual-value, and aggregate limits; and
* F1 construction/serialization with source bundle ID and digest.

It does not retrieve history, invoke a model/provider, select a cognition
tier/resource, emit River provenance, execute recommendations, or mutate
Estate state.

## 3. Behavioral validation of the implemented assembler

### Identity preservation — PASS

The assembler preserves explicit request resident and implementation IDs,
corresponds request occupant ID to the authoritative bundle resident ID, and
derives office and authority from mandatory authoritative bundle anchors.
Missing/mismatched occupant, identity anchor, office anchor, and authority
anchor cases fail closed.

Independent probes confirmed occupant/source correspondence, office-anchor
mismatch rejection, and occupant mismatch rejection.

Identity preservation: **PASS**

### Transcript-not-identity — PASS

Transcript-like content placed in an ordinary context item value was not
projected into packet identity or reference fields. Authoritative occupant and
explicit request resident identity remained unchanged. A forbidden
`conversation_history` layer was rejected with `unbounded-context`.

The assembler does not infer identity from text, display name, source value,
provider, model, GPU, endpoint, or implementation class.

Transcript-not-identity: **PASS**

### Bounded assembly — PASS

`_bounded_packet_preflight` checks all F1 packet context collections before F1
construction, including operational-state references, evidence references,
authoritative-state references, constraints, ambiguity, prior decisions, and
known deterministic results. It checks collection counts, individual lengths,
and the 64,000-character aggregate.

Independent probes covered normal assembly, 65-reference overflow, malformed
source reference, excessive embedded constraints, and aggregate pressure.
The assembler rejects impossible assembly rather than silently truncating
meaning-bearing content.

Bounded assembly: **PASS**

### F1 aggregate regression — PASS

The former F1 `operational_state_refs` omission is not reintroduced. The
assembler counts those references in `_context_total`, and the final F1
constructor independently enforces the same aggregate limit.

F1 aggregate regression: **PASS**

### Determinism — PASS

Source items are sorted by layer, item ID, and source reference. Duplicate
references are removed deterministically. Digest JSON uses sorted keys and
fixed assembler/contract versions. Repeated projection from equivalent
immutable bundle/request inputs produced identical typed payloads and digest.

Deterministic assembly: **PASS**

### Reference/value semantics — PASS

The assembler projects `ContextItem.source_ref`, not arbitrary item value
mappings, into F1 reference collections. Source references are nonempty,
bounded, and collection-limited. Embedded constraint/ambiguity/result values
remain individually and aggregate bounded. Reference-pressure probes failed
closed.

Reference/value semantics: **PASS**

### Source correspondence — PASS

The assembler rejects stale bundles, missing identity/office/authority anchors,
identity-anchor mismatch, office-anchor mismatch, and occupant/bundle
mismatch. It preserves the supplied source bundle ID as F1 `source_context_id`
and carries explicit request lineage into the packet.

Source correspondence: **PASS**

## 4. Provider, model, and authority boundaries

Provider neutrality: **PASS**. The implementation contains no fixed GPU,
Ollama/OpenAI route, endpoint, or model selection. Provider/resource terms in
tests are negative assertions or metadata exclusion checks.

No model invocation: **PASS**. The assembler performs no provider call, model
selection, tier escalation decision, scheduling, GPU work, or reasoning.

Authority boundary: **PASS**. Authority is projected from the existing
authoritative anchor; the assembler does not manufacture authority, add an
`execute` capability, perform state-changing actions, or accept recommendations.

## 5. Serialization and F1 integration

The actual integration path is:

`ContextBundle → ResidentReasoningPacketAssembler → ResidentReasoningPacket →
as_typed_payload/from_typed_payload`.

Independent serialization round-trip preserved identity, office, authority,
source bundle reference, context references, values, digest, and tier. The
accepted F1 contract continued to enforce final typed and aggregate bounds.

F1 regression: **PASS**

## 6. History and bounded source use

The assembler consumes the already-selected `ContextBundle`; it does not
retrieve or flatten all resident history. Historical/episodic material crosses
only through bounded source references and explicit bounded ambiguity/context
fields. Forbidden transcript/history layers are rejected.

## 7. Independent tests and probes

Focused command:

```text
PYTHONPATH=src;tests python -m pytest -q \
  tests/test_reasoning_context_assembler.py \
  tests/test_cognition_contracts.py \
  tests/test_provider_neutral_contracts.py \
  tests/test_resident_context.py \
  tests/test_resident_runtime.py \
  tests/test_grace_authority.py \
  ..\tests\test_grace_consultation_loop.py \
  ..\tests\test_autonomous_reason_execute_loop.py \
  ..\tests\test_governed_provider_scheduler.py
```

Result: **95 passed in 5.85s**.

Compileall and package import validation also passed.

Independent adversarial probes:

* transcript identity spoof: authoritative identity preserved and transcript
  value not projected;
* forbidden transcript layer: rejected;
* aggregate/reference pressure: rejected at assembler preflight;
* office-anchor mismatch: rejected;
* occupant/source mismatch: rejected;
* operational-state reference collection overflow: rejected; and
* F1 serialization round trip: preserved semantics.

## 8. Required correction and next package

This is not a request to redesign the assembler. The package identity and
roadmap mapping must be corrected before acceptance:

* either publish/accept this implementation as the roadmap’s
  `GRC-003-F4 — Bounded Grace reasoning-packet assembly`, or
* provide the actual `GRC-003-F2 — Cognition provenance and River event
  lineage` implementation against its stated event/provenance acceptance
  criteria.

The authoritative next outstanding Grace package is:

**GRC-003-F2 — Cognition provenance and River event lineage**

Its implementation remains required; the current F2 claim cannot satisfy that
gate. F4-shaped behavior can be reused later, but it does not substitute for
F2 durable provenance/event lineage.

Grace implementation readiness: **REPAIR_REQUIRED**

