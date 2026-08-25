# GRC-009R — P1 Provenance Correspondence Repair

Package: GRC-009R  
Roadmap package: GRC-003-P1 — Escalation decision policy  
Role: C1 original P1 implementation writer / targeted repair writer  
Status: `REPAIR_COMPLETE_READY_FOR_REVALIDATION`

## Defect repaired

GRC-009V identified that `PolicyDecisionRecorder.record()` accepted an
arbitrary `request_id` and appended `cognition.policy_decided` without proving
that the `EscalationAssessment` came from that canonical cognition request.
This permitted a valid assessment from request A to be persisted under request
B, creating false F2 lineage.

## Root cause and repair

Before append, the recorder only checked that `request_id` was a UUID. The
repair adds an authoritative durable gate in
`src/riverview/reasoning/escalation_policy.py`:

1. `_canonical_request()` reads the target `cognition_request` aggregate.
2. It requires exactly one stored `cognition.requested` event.
3. It reconstructs the canonical request through the accepted
   `CognitionProvenance.from_typed_payload()` path.
4. It rejects missing, ambiguous, malformed, or aggregate-mismatched lineage.
5. `_validate_correspondence()` compares the assessment against canonical
   resident, occupant, office, implementation, authority, source-event, and
   correlation identity.
6. If the canonical F2 request contains a packet identity, that packet is
   compared as well.
7. Caller-supplied causation is rejected unless it equals the assessment's
   authoritative source cognition event.
8. Only then is the River policy event appended.

The repair reuses F2's canonical provenance schema and reconstruction seam; it
does not create a second provenance authority. A missing canonical request
cannot be manufactured from the policy assessment.

## Correspondence results

- Original arbitrary-request defect: **RESOLVED**.
- Canonical request lookup: **PASS**.
- Packet/request correspondence: **PASS**. Assessment source-event and all
  request-bound identity/correlation fields are checked; an existing durable
  canonical packet identity is checked when present.
- Identity correspondence: **PASS** for resident, occupant, office,
  implementation, and authority.
- Correlation/source lineage: **PASS**. Source cognition event and correlation
  are checked; unrelated caller causation is rejected.
- Forged policy-event prevention: **PASS**. Rejections occur before append and
  leave the aggregate unchanged.

## Valid paths

An exact assessment and canonical request persist successfully as a
`cognition.policy_decided` event. The routine non-escalation path uses the same
gate and remains valid; the gate is not conditional on `escalation=true`.

The existing deterministic policy behavior is unchanged, including separate
home belief, policy permission, and capacity eligibility; truthful capacity
unavailability; Steward-required outcomes; and external classification denial.
The repair does not grant execution authority, select providers/resources, or
implement P2.

## Adversarial tests

Added to `tests/test_escalation_policy.py`:

- unrelated `request_id` rejected before persistence;
- resident, occupant, office, implementation, authority, source-event, and
  correlation substitutions rejected;
- unrelated causation rejected;
- missing canonical request rejected;
- exact escalation and exact non-escalation persistence retained;
- policy event reload/coexistence with the canonical F2 request retained.

## Persistence/restart evidence

A real PostgreSQL probe appended a canonical request and matching policy event,
recreated `EventStore`/`PolicyDecisionRecorder`, and reloaded the aggregate:

```text
POSTGRES_POLICY_RELOAD 2 cognition.policy_decided True
```

The final `True` is the unrelated-request rejection. The aggregate remained at
two events and the forged event was not persisted.

No migration or new persistence table was required; existing River JSONB event
storage remains authoritative.

## Regression evidence

Focused P1 suite:

```text
tests/test_escalation_policy.py — 22 passed
```

Relevant accepted regression command passed across:

- F1 cognition contracts;
- F2 provenance and correspondence repair;
- F3 cognition session;
- F4 bounded packet assembler and current-state repair;
- provider-neutral contracts; and
- Grace authority.

Compile/import validation: **PASS**.  
`git diff --check`: **PASS**.

Regression classification:

- F1 regression: **PASS**.
- F2 regression: **PASS**; the recorder now follows the accepted durable
  canonical-request correspondence pattern.
- F3 regression: **PASS**; no session implementation changed.
- F4 regression: **PASS**; no packet assembler implementation changed.
- Provider neutrality regression: **PASS**.
- Authority-boundary regression: **PASS**.
- P1/P2 separation: **PASS**.

## Files and commits

Implementation repository: `ppow1/Riverview`  
Implementation branch: `codex/c484-operator-persistent-service`  
Implementation repair commit: `f0ffa4ec78fc81b821b4f7948cc69066729dc147`

Scoped implementation/test files:

- `src/riverview/reasoning/escalation_policy.py`
- `tests/test_escalation_policy.py`

Report repository: `ppow1/theestate`  
Report branch: `codex/riverview-bounded-doorbell`

No F1–F4 runtime redesign, P2 implementation, provider/resource routing,
Campaign Runner change, migration, or unrelated cleanup was made.

## Readiness

The original arbitrary-request provenance defect is closed in the scoped
implementation and ready for independent revalidation. C1 does not accept its
own repair.

`READY_FOR_INDEPENDENT_REVALIDATION`
