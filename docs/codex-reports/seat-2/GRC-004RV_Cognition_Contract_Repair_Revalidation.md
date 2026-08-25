# GRC-004RV — Grace F1 Identity and Bounded-Context Repair Revalidation

Package: GRC-004RV  
Role: C2 independent repair revalidator  
Date: 2026-08-25

## Verdict

**FAIL — BLOCKING DEFECTS REMAIN**

The identity-preservation defect is resolved. The bounded-context repair is
not complete: `ResidentReasoningPacket` still permits a packet whose actual
aggregate context exceeds the advertised 64,000-character limit. This is a
remaining instance of the original blocking bounded-context defect, not a
future-hardening observation.

## Evidence and repository verification

Implementation repository: `ppow1/Riverview`  
Implementation branch: `codex/c484-operator-persistent-service`  
Repair implementation commit:
`c7646bb41ffbde51687a06023b0003e4679c8e3d`

The local nested implementation repository is at `A:\theestate\Riverview`,
and its HEAD and origin branch both resolve to the reported repair commit.

The original validation report was read from the available local path
`docs/codex-reports/seat-1/GRC-004V_Cognition_Contract_Validation.md` (the
user-specified `docs/reports/seat-1` path is not present locally). It matches
the copy on `origin/codex/riverview-bounded-doorbell`.

The repair report was read from:
`docs/codex-reports/seat-3/GRC-004R_Cognition_Contract_Repair.md`.

## Original blocking findings mapped to revalidation

### Original identity findings — RESOLVED

The original report identified incomplete resident/occupant/office/
implementation/authority lineage and a result correspondence check that only
compared resident and occupant identity.

The repair adds typed identity and lineage to
`ResidentReasoningPacket`, `EscalationAssessment`,
`CapabilityResourceRequest`, and `CognitionResult` in
`src/riverview/reasoning/cognition_contracts.py`.

`CognitionResult.validate_against` at line 626 now checks, when present on the
request, `resident_id`, `occupant_id`, `office_id`, `implementation_id`,
`authority_ref`, `source_cognition_event_id`, correlation, tier, and
classification, plus packet ID correspondence.

Independent negative probes rejected mismatched:

* resident A / result resident B;
* occupant A / result occupant B;
* office A / result office B;
* implementation A / result implementation B;
* authority A / result authority B; and
* source-event/correlation mismatches against a packet.

Serialization/deserialization preserved resident, occupant, office,
implementation, source event, objective, and authority identity. Provider and
resource reference replacement left those identities unchanged. HOME to HIGH
and HOME to EXTERNAL transitions also preserved them. No provider/resource
value is used as resident identity.

Identity preservation: **PASS**  
Original identity defect: **RESOLVED**

### Original bounded packet/context finding — NOT RESOLVED

The repair correctly adds the previously missing typed context paths and
introduces `MAX_CONTEXT_CHARS = 64_000`, per-field/reference bounds, and a
packet aggregate helper. The new tests cover many of those paths.

However, `ResidentReasoningPacket.__post_init__` validates
`operational_state_refs` at line 227 with `_context_refs`, but the call to
`_packet_context_total` at line 238 does not include
`operational_state_refs`. The packet-wide aggregate therefore excludes one
caller-controlled context collection.

Independent reproduction:

* 64 individually valid `operational_state_refs`, each 500 characters:
  32,000 characters;
* otherwise valid context constructed to count as 60,133 characters by the
  implementation; and
* actual combined context: **92,133 characters**.

The repaired packet was accepted. Therefore the advertised aggregate limit
can be bypassed using a collection that the repair itself identifies as
context. This is equivalent in consequence to the original bounded-context
failure: a caller can supply more context than the contract says it permits.

Minimum correction: include `operational_state_refs` in the packet aggregate
calculation, and add a regression test combining a near-limit counted packet
with a large-but-individually-valid operational-state reference collection.
The aggregate check must cover every packet context collection exactly once.

Bounded context: **FAIL**  
Original bounded-context defect: **UNRESOLVED**

## Independent focused tests

Command run from the repaired implementation repository:

```text
PYTHONPATH=src python -m pytest -q \
  tests/test_cognition_contracts.py \
  tests/test_provider_neutral_contracts.py \
  tests/test_resident_context.py \
  tests/test_resident_runtime.py \
  tests/test_grace_authority.py \
  ..\tests\test_grace_consultation_loop.py \
  ..\tests\test_autonomous_reason_execute_loop.py \
  ..\tests\test_governed_provider_scheduler.py
```

Result: **81 passed in 5.59s**.

The passing count does not close the defect because the added aggregate test
does not include `operational_state_refs` in a near-limit combined payload.
The independent reproduction above is a behavior test outside the reported
suite.

The new tests genuinely cover identity mismatch rejection for resident,
occupant, office, implementation, and authority; tier transitions;
serialization; field/reference limits; some collection limits; and aggregate
limits. They do not cover the omitted operational-state collection in the
packet-wide aggregate.

## Regression verdicts

### Provider neutrality — PASS

The repaired contract remains capability/tier based. No implementation,
provider, model, endpoint, GPU, RTX 3060/4090, P100, or physical resource
binding was introduced into F1. Provider/resource references remain metadata.

### Authority boundary — PASS

`CognitionResult.authority_scope` remains closed to advisory/read/diagnostic
values. An `execute` scope is rejected. The repair adds identity/context
fields but does not grant reasoning execution or acceptance authority.

### Live-generation truth — PASS

Non-success results cannot claim live generation, deterministic substrate
cannot claim live generation, and actor/tier consistency remains enforced.
The identity/context additions did not weaken these safeguards.

## F4 contract readiness

**REPAIR_REQUIRED**

F1 now supplies the required identity and typed context surface, but F4 cannot
rely on the advertised bounded packet contract until every packet context
collection participates in the aggregate bound.

## Required repair scope

One narrow correction is required: include `operational_state_refs` in
`_packet_context_total` and add the corresponding adversarial regression test.
No redesign of identity, provider routing, authority, runtime cognition, or
later GRC packages is required.

## Final readiness

Grace implementation readiness: **REPAIR_REQUIRED**  
F4 contract readiness: **REPAIR_REQUIRED**

