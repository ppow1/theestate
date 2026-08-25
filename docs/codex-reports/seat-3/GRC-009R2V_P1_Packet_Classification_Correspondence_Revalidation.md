# GRC-009R2V — P1 Packet / Classification Correspondence Revalidation

Package: GRC-009R2V
Roadmap package: GRC-003-P1 — Escalation decision policy
Role: C3 independent targeted repair revalidator
Implementation commit: `82b515b63031b69fb790203e60da3b7a2ec823ed`

## Verdict

**PASS**

The second repair closes the packet/classification correspondence defect at
the direct `PolicyDecisionRecorder.record()` boundary. The original arbitrary
request defect remains closed, forged policy events were rejected before
append, and accepted F1–F4 and P1 behavior remained passing.

## Primary acceptance gate

I constructed a valid canonical cognition request whose stored F2 provenance
had no packet reference, then supplied a caller-selected `packet_id` to
`PolicyDecisionRecorder.record()`. The recorder rejected the operation before
persistence. The aggregate remained unchanged.

This confirms authoritative absence is not caller authority.

GRC-009RV defect: **RESOLVED**
Original arbitrary-request defect: **RESOLVED, NOT REGRESSED**
Canonical request lookup: **PASS**

## Packet correspondence

The repaired contract adds optional packet identity to the capability request,
preserves it in canonical F2 request provenance, and requires exact equality in
the recorder. Independent probes produced:

- canonical packet absent + caller packet supplied → **REJECTED**, no append;
- canonical packet P + caller packet Q → **REJECTED**, no append;
- canonical packet P + caller packet P → **ACCEPTED** when all other fields
  matched.

Packet/request correspondence: **PASS**
Forged packet prevention: **PASS**

## Classification correspondence

Classification is inherited from the canonical request/context, not an
independent caller authority. Independent probes produced:

- canonical classification X + caller classification Y → **REJECTED**, no
  append;
- canonical classification X + caller classification X → **ACCEPTED** when
  otherwise valid.

Classification correspondence: **PASS**

## Durable recorder boundary

The direct `PolicyDecisionRecorder.record()` call performs canonical request
lookup and correspondence validation before invoking the EventStore append.
No higher-level helper is required. Missing, ambiguous, malformed, unrelated,
or mismatched canonical lineage fails closed.

After every rejected packet/classification/request probe, durable aggregate
history was inspected and contained no forged policy event.

Forged policy-event prevention: **PASS**

## Identity, correlation, and source lineage

Resident, occupant, office, implementation, authority, source cognition event,
correlation, and unrelated causation substitutions were independently rejected.
The repair preserved the distinction between correlation and causation.

Identity correspondence: **PASS**
Correlation/source lineage: **PASS**

## Valid paths

An exact difficult/high-reasoning assessment persisted successfully. The exact
routine non-escalation assessment also remained valid through the same durable
gate. The recorder is not limited to `ESCALATE` outcomes.

Valid escalation path: **PASS**
Valid non-escalation path: **PASS**

## PostgreSQL persistence/restart

Independent real PostgreSQL probe:

```text
POSTGRES_P1_RELOAD 2 2 ['packet:REJECTED', 'classification:REJECTED'] REJECTED
```

The matching canonical request and policy decision survived EventStore
recreation. Packet and classification substitutions were rejected after
reload, and the aggregate remained at two events. An unrelated request ID was
also rejected.

Persistence/restart: **PASS**

## Regression results

Focused P1 suite:

```text
tests/test_escalation_policy.py — 25 passed
```

Relevant accepted F1–F4, provenance, session, provider, and authority suite:

```text
121 passed
```

Compileall and import validation: **PASS**.

Regression results:

- Deterministic policy regression: **PASS**
- Transcript-not-authority: **PASS**
- Provider neutrality: **PASS**
- Authority boundary: **PASS**
- P1/P2 separation: **PASS**
- F1 regression: **PASS**
- F2 regression: **PASS**
- F3 regression: **PASS**
- F4 regression: **PASS**

No provider, model, endpoint, GPU, resource-binding, P2, Campaign Runner, or
later-package changes were introduced by the repair.

## Acceptance and next package

GRC-003-P1 is **ACCEPTED**. The repair is narrow, preserves the accepted
F1–F4 foundation, and establishes trustworthy P1 policy-event provenance.

P1 acceptance unlocks the roadmap packages whose dependencies include P1:
E1 home cognition, E2 high-reasoning request path, and E3 external advisory
path, subject to their remaining F1/F2/F4/P2 dependencies. E4 remains gated by
E2/E3 result contracts. GRC-010/P2 is separately implemented and still
requires independent validation; P1 acceptance does not accept P2.
