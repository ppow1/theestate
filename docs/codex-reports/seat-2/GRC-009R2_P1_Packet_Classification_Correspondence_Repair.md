# GRC-009R2 — P1 Packet / Classification Correspondence Repair

Package: GRC-009R2  
Roadmap package: GRC-003-P1 — Escalation decision policy  
Role: C2 targeted repair writer  
Status: `REPAIR_COMPLETE_READY_FOR_REVALIDATION`

## 1. GRC-009RV blocker

GRC-009RV confirmed the arbitrary-request defect was repaired, but
`PolicyDecisionRecorder.record()` still accepted caller-supplied `packet_id`
and `classification` when the canonical stored request did not establish the
corresponding value. The resulting policy event could therefore contain forged
P1/F2 provenance.

## 2. Root cause

The recorder compared packet identity only conditionally:

```python
if canonical.packet_id is not None:
    compare assessment.packet_id
```

It did not compare `assessment.classification` with the canonical request at
all. In addition, `CapabilityResourceRequest` carried no packet reference and
`CognitionProvenance.for_request()` always discarded packet identity.

## 3. Repair and authoritative absence semantics

The minimal contract-preserving repair adds an optional `packet_id` to
`CapabilityResourceRequest`, including typed serialization/deserialization.
`CognitionProvenance.for_request()` now preserves that reference in the
canonical stored request provenance.

`PolicyDecisionRecorder._validate_correspondence()` now requires exact packet
equality, including `None` equality. Therefore a canonical request with no
packet reference cannot be combined with a caller-supplied packet. A canonical
packet `P` accepts only `P`; `Q` is rejected.

Classification is required to exactly equal the canonical request
classification. It is not treated as a caller-authorized replacement.

The gate remains in `PolicyDecisionRecorder.record()` after durable canonical
request lookup and before `EventStore.append`; direct low-level calls cannot
bypass it.

## 4. Forged-event prevention and valid paths

Focused tests prove:

- canonical packet absent plus supplied packet: rejected, aggregate unchanged;
- canonical packet `P` plus supplied packet `Q`: rejected, aggregate unchanged;
- canonical packet `P` plus `P`: accepted when otherwise valid;
- canonical classification `X` plus `Y`: rejected, aggregate unchanged;
- exact classification and packet correspondence: accepted;
- valid escalation and valid non-escalation remain accepted.

The existing unrelated-request rejection remains in force. The recorder still
loads exactly one canonical `cognition.requested` event and rejects missing,
ambiguous, malformed, or unrelated request lineage before persistence.

## 5. Persistence / restart evidence

A real PostgreSQL probe persisted a unique canonical request and matching policy
decision, recreated `EventStore`/`PolicyDecisionRecorder`, and reloaded the
aggregate:

```text
POSTGRES_P1_RELOAD 2 cognition.policy_decided True 2 True
```

The two events were the canonical request and valid policy decision. After
reload, forged packet and forged classification attempts were rejected, and
the aggregate remained at two events. No forged policy event was persisted.

## 6. Preserved regressions

- Original arbitrary-request defect: **RESOLVED**.
- Canonical request lookup: **PASS**.
- Identity correspondence for resident, occupant, office, implementation,
  authority, source, and correlation: **PASS**.
- Correlation/source lineage: **PASS**.
- Valid escalation and non-escalation: **PASS**.
- F1: **PASS**.
- F2: **PASS**, including request/result correspondence, canonical lookup,
  forged-event prevention, correlation/causation, and persistence coverage.
- F3: **PASS**.
- F4: **PASS**.
- Provider neutrality: **PASS**.
- Authority boundary: **PASS**.
- P1/P2 separation: **PASS**; no provider/resource binding or P2 runtime was
  added.

The packet field extension is optional and backward-compatible for requests
that do not have a packet reference; P1 persistence now fails closed when an
assessment attempts to assert packet provenance not established by that
request.

## 7. Exact files and symbols changed

Implementation repository: `ppow1/Riverview`  
Implementation branch: `codex/c484-operator-persistent-service`  
Repair commit: `82b515b63031b69fb790203e60da3b7a2ec823ed`

- `src/riverview/reasoning/cognition_contracts.py`: optional canonical
  `CapabilityResourceRequest.packet_id` and typed payload handling.
- `src/riverview/reasoning/provenance.py`: preserve request packet identity in
  canonical provenance and retain prior generic request compatibility.
- `src/riverview/reasoning/escalation_policy.py`:
  `PolicyDecisionRecorder._validate_correspondence` exact packet and
  classification checks.
- `tests/test_escalation_policy.py`: absence, substitution, classification,
  durable aggregate, and valid-path regressions.

No P2, provider, Campaign Runner, Grace execution, or unrelated functionality
was changed.

## 8. Tests

Passed independently:

- focused P1 escalation policy suite;
- F1 cognition contract suite;
- F2 provenance and repair suites;
- F3 cognition session suite;
- F4 resident-context/packet suite;
- provider-neutral and Grace-authority suites;
- compile/import validation;
- `git diff --check`;
- real PostgreSQL persistence/reload and forged-event absence probe.

## 9. Readiness

Both GRC-009RV forged-provenance variants are closed at the durable recorder
boundary without regressing the original arbitrary-request repair or accepted
F1–F4 behavior. C2 does not accept its own repair.

`READY_FOR_INDEPENDENT_REVALIDATION`
