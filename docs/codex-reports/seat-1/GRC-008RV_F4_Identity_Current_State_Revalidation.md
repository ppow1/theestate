# GRC-008RV — F4 Identity and Current-State Repair Revalidation

Package: GRC-008RV  
Roadmap package: GRC-003-F4 — Bounded resident reasoning packet / context assembly  
Role: C1 independent repair revalidator  
Date: 2026-08-25

## Verdict

**FAIL — BLOCKING DEFECTS REMAIN**

The two original GRC-008 blocking probes are resolved at the normal assembler
boundary. Independent adversarial probing found one remaining reachable
blocking current-state defect: a mandatory `current_assignment` item with an
empty mapping value is accepted and projected. F4 requires actual current
operational-state material, not merely a typed empty mapping plus a source
reference.

## Repository verification

Implementation repository: `ppow1/Riverview`  
Implementation branch: `codex/c484-operator-persistent-service`  
Repair implementation commit: `15f6ae7734dade8400c289b799641876a1993aa1`  

The repair commit was verified after fetching the reported branch. It changes:

- `src/riverview/reasoning/context_assembler.py`;
- `tests/test_reasoning_context_assembler.py`;
- `tests/test_reasoning_context_assembler_repair.py`.

Report repository: `ppow1/theestate`  
Report branch: `codex/riverview-bounded-doorbell`  
Repair report commit: `a2356f3d315b501f4b8ed17526d81a4e4a5a8560`.

## Original blocking probe 1: wrong resident

**Resolved.**

Using the actual repaired `ResidentReasoningPacketAssembler`, I built the
valid fixture bundle for the authoritative resident and supplied a different
`request.resident_id`. Assembly raised `ReasoningContextAssemblyError` with
`identity-mismatch` before packet construction. No packet or downstream
association was produced.

The repaired source now requires both:

```text
bundle.resident_id == request.occupant_id
bundle.resident_id == request.resident_id
```

The packet resident is therefore tied to the authoritative bundle/request
correspondence. The identity anchor is separately checked against the bundle.
Transcript content, provider metadata, implementation metadata, and model-like
content do not supply packet identity.

## Original blocking probe 2: missing current state

**Resolved for absent current-state material.**

I removed the `current_assignment` item from an otherwise valid bundle while
retaining identity, office, authority, and other context. Assembly raised
`ReasoningContextAssemblyError` with `current-state-missing`. No packet was
emitted.

I repeated the probe with transcript-like prose and with provider metadata
added in another context item. Both were rejected. Transcript and provider
metadata cannot substitute for authoritative current state.

## Remaining blocking defect: empty current-state value

**Blocking — unresolved.**

I retained the mandatory `current_assignment` item but replaced its value with
an empty mapping `{}` while retaining its source reference. The repaired
assembler accepted the bundle and emitted a packet:

```text
empty-current-value ACCEPTED
operational_state_refs count: 2
```

The relevant implementation condition is:

```python
item.layer == "current_assignment"
and item.mandatory
and isinstance(item.value, Mapping)
```

followed only by a nonempty `source_ref` check. An empty mapping satisfies the
condition. The resulting reference count does not prove that current
operational-state material exists; it can be only the reference to an empty
value. This is a reachable version of the missing-current-state failure
condition in the accepted F4 definition, which requires current operational
state to be present in the bounded packet.

Minimum correction: require the mandatory current-state value to contain the
accepted current-assignment/state fields or otherwise be nonempty and
semantically valid at the F4 boundary, with a regression proving an empty
mapping fails closed. Do not infer current state from transcript, provider,
model, or resource metadata.

## Correspondence and boundary checks

The repaired resident check preserves the authoritative resident source and
does not introduce a second resident authority. Wrong occupant and stale
bundle probes remained rejected. Office and authority anchors are checked
against the bundle; implementation identity remains request data and is not
derived from provider/resource metadata. The F4 projector does not create a
session identity or replace the accepted F3 session/request boundary.

The valid current-assignment fixture assembled successfully and retained
operational-state references. An explicitly absent assignment, empty
assignment collection, transcript-only substitute, and provider-only
substitute failed closed. The empty mapping case is the exception described
above.

## Aggregate, reference, and determinism regressions

The approximately 64,000-character F1 aggregate bound remains enforced. The
repair test suite retained the over-budget constraint/reference pressure case,
and `operational_state_refs` remain part of the aggregate preflight. Context
items continue to project bounded source references rather than unrestricted
embedded values. Equivalent authoritative inputs remained deterministic.

## F1/F2/F3 and authority regressions

The relevant independently accepted suites passed:

- F1 cognition contracts, bounded context, identity, provider neutrality,
  authority, live-generation behavior;
- F2 provenance and correspondence repair, including forged-event rejection;
- F3 session identity, session/request separation, wrong-session behavior,
  persistence/serialization, and identity preservation;
- F4 assembler and targeted repair tests;
- resident context/runtime and Grace authority tests.

Result: **113 passed in 1.38s** for the integrated relevant selection.

Focused F4 tests: **17 passed**.  
`python -m compileall -q src tests`: **PASS**.

The broad unfiltered suite could not complete collection because the current
environment lacks the optional `mcp` package required by three unrelated MCP
test modules. This is an environment limitation, not an F4 implementation
finding.

Provider/model/GPU/endpoint searches and source inspection found no new F4
binding or routing behavior. Packet assembly remains non-executing and does
not widen authority. No P1/P2 behavior was implemented.

## Roadmap compliance and next package

F4 roadmap compliance: **FAIL** because the empty current-state mapping can
still cross the required current-state boundary.

The accepted dependency graph makes **GRC-003-P1** (escalation decision policy)
and **GRC-003-P2** (capability/resource request and binding adapter) separate
packages. Once F4 is repaired and accepted, both are dependency-eligible from
the graph; neither precedes the other. They must not be treated as accepted by
this report.

Grace implementation readiness: **REPAIR_REQUIRED**

