# GRC-009RV — P1 Provenance Correspondence Repair Revalidation

Package: GRC-009RV
Roadmap package: GRC-003-P1 — Escalation decision policy
Role: C3 independent repair revalidator
Repair commit: `f0ffa4ec78fc81b821b4f7948cc69066729dc147`

## Verdict

**FAIL — BLOCKING DEFECTS REMAIN**

The original arbitrary-`request_id` defect is resolved at the recorder
boundary. A second provenance correspondence gap remains: a valid canonical
request can receive and persist an assessment with a substituted `classification`
or `packet_id` when those request fields are absent or not checked by the
canonical record. Therefore P1 cannot yet be accepted as exact request/context
provenance.

## Original attack: resolved

I independently repeated the original attack against
`PolicyDecisionRecorder.record()`:

```text
valid assessment + unrelated request_id
```

The repaired recorder loads the target `cognition_request` aggregate, requires
exactly one canonical `cognition.requested` record, reconstructs it through
`CognitionProvenance.from_typed_payload()`, and validates correspondence before
calling `append`. The unrelated request was rejected with
`PolicyInputError`; the event-store aggregate remained unchanged.

Original arbitrary-request defect: **RESOLVED**
Canonical request lookup: **PASS**

## Repair source inspection

The repair adds `_canonical_request()` and `_validate_correspondence()` in
`PolicyDecisionRecorder`. It checks resident, occupant, office, implementation,
authority, source cognition event, correlation, and packet identity when the
canonical F2 request contains a packet reference. Caller-supplied causation is
also rejected unless it equals the assessment source event. The repair uses the
accepted F2 provenance reader and does not create a parallel event authority.

## Independent adversarial probes

### Identity and lineage substitutions

The repaired recorder rejected substitutions for resident, occupant, office,
implementation, authority, source event, correlation, unrelated request ID,
and unrelated causation. These rejections occurred before append and left the
aggregate unchanged.

Identity correspondence: **PASS** for the checked F2 identity fields
Correlation/source lineage: **PASS** for the checked fields

### Remaining packet/classification correspondence defect

Using a valid canonical request and a valid assessment, I independently
replaced:

- `assessment.classification` with another valid classification;
- `assessment.packet_id` with another valid UUID.

Both calls were accepted and appended under the valid request aggregate when
the canonical request did not contain a corresponding packet reference. This
is not an unsupported synthetic field: both values are part of the typed F1/P1
assessment and the F2 provenance schema. The policy event can therefore claim
to be a decision for a different classification or packet context than the
one represented by the canonical request.

Packet/request correspondence: **FAIL**
Forged policy-event prevention: **FAIL**

Minimum correction: enforce the applicable classification and packet/context
correspondence at the durable recorder boundary. If a required canonical
reference is absent, fail closed rather than allowing a caller-supplied
assessment identity to fill the gap. Add aggregate-unchanged tests for both
substitutions.

## Valid paths

The exact difficult/high-reasoning path persisted successfully after a
canonical request was recorded. The routine non-escalation policy path remains
covered by the focused suite and uses the same recorder gate; the repair is not
conditional on `escalation=true`.

Valid escalation path: **PASS**
Valid non-escalation path: **PASS**

## PostgreSQL persistence/restart

Independent real PostgreSQL probe:

```text
POSTGRES_POLICY_RELOAD 2 cognition.policy_decided REJECTED 2
```

This proves a canonical request plus matching policy decision survives
EventStore recreation, and the original unrelated-request attempt is rejected
without changing the aggregate. Because the substituted packet/classification
variant remains appendable, full P1 persistence/provenance acceptance is still
blocked.

Persistence/restart: **FAIL** for complete provenance correctness

## Policy and regression results

The repair did not alter policy semantics. Focused P1 tests passed:

```text
tests/test_escalation_policy.py — 22 passed
```

Relevant accepted regression suite passed:

```text
118 passed
```

This included F1 cognition contracts, F2 provenance and repair tests, F3
session tests, F4 assembler/current-state tests, provider-neutral contracts,
and Grace authority tests. Compileall and import validation passed.

Results:

- Deterministic policy regression: **PASS**
- Transcript-not-authority regression: **PASS**
- Provider neutrality regression: **PASS**
- Authority boundary regression: **PASS**
- P1/P2 separation regression: **PASS**
- F1 regression: **PASS**
- F2 regression: **FAIL** due remaining policy-event context forgery path
- F3 regression: **PASS**
- F4 regression: **PASS**

## Acceptance disposition

P1 remains **REPAIR_REQUIRED**. The original arbitrary-request defect is closed,
but the durable recorder still permits a valid request aggregate to receive a
policy decision carrying a substituted packet/classification context. C1 must
repair that exact boundary before another independent revalidation.

Next roadmap packages: P2 is implemented separately as GRC-010 but still
requires independent validation. P1 acceptance does not unlock downstream
execution packages.
