# GRC-008 — Existing Early F4 Bounded Packet Assembler Validation

Package: GRC-008  
Roadmap package: GRC-003-F4 — Bounded Grace reasoning-packet assembly  
Role: C2 independent implementation validator  
Date: 2026-08-25

## Verdict

**FAIL — BLOCKING DEFECTS REMAIN**

The preserved early implementation is correctly F4-shaped and technically
strong on bounds, deterministic projection, references, provider neutrality,
and F1 serialization. However, two reachable F4 acceptance failures remain:

1. `ResidentReasoningPacketAssembler` accepts a request resident identity that
   conflicts with the authoritative `ContextBundle` resident identity and
   emits the unverified request identity into the packet.
2. It accepts a bundle containing identity, office, and authority anchors but
   no current operational-state/assignment material, despite F4 requiring
   current state in the bounded packet.

These can produce a plausible packet with incorrect identity or insufficient
authoritative state, so F4 cannot be accepted yet.

## Repository and integrated commit

Implementation repository: `ppow1/Riverview`  
Implementation branch: `codex/c484-operator-persistent-service`  
Integrated implementation commit: `726b88755f8881fb283b5ac9a472290c6d33f37b`

The early F4 implementation originated in commit
`dab860cd8eb02b6333fbade67f6a63abb8887181` and remains in
`src/riverview/reasoning/context_assembler.py`. The current integrated branch
adds accepted F2 and F3 commits without modifying that assembler. No runtime
files were changed during this validation.

## 1. Authoritative F4 definition

The repaired GRC-003 roadmap defines F4 as projecting required Grace identity,
current operational state, relevant memory/evidence, task information, and
authority boundaries into the bounded F1 `ResidentReasoningPacket`.

Dependencies are F1 and existing `ContextBundle` assembly. The roadmap names
the packet projector, relevance/omission handling, authoritative-state
snapshot adapter, and packet digest as possible F4 ownership. Required tests
include identity/office/authority/current-state/task fields, relevance and
budget handling, contradiction preservation, stale-bundle rejection,
protected-data classification, omission reasons, and no full transcript dump.

Acceptance requires bounded high/external input with required authority and
current state, no unrelated history or unapproved protected content, and
reproducibility from source references and digest. Non-goals are model calls,
escalation policy, retrieval redesign, and unbounded memory.

The preserved implementation is materially the F4 projector, not the earlier
misclassified F2. GRC-005V’s historical roadmap finding remains correct and
is not rewritten here.

F4 roadmap compliance: **FAIL** because the two acceptance conditions above
are not enforced.

## 2. Dependency satisfaction — PASS

The accepted evidence establishes F1 aggregate/identity contracts, F2 durable
River provenance and exact request/result correspondence, and F3 identity-
preserving session/request boundaries. The integrated branch contains the
corresponding F1/F2/F3 implementations at the verified commit.

Dependency satisfaction: **PASS**

F3 is not a direct F4 dependency in the roadmap; its accepted session boundary
remains an upstream identity seam. F4 does not invent a second session model.

## 3. Actual bounded assembler behavior

`ResidentReasoningPacketAssembler.assemble`:

- rejects stale bundles;
- requires authoritative identity, office, and authority anchors;
- projects bounded source references rather than arbitrary item values;
- preflights per-field, collection, individual-value, and aggregate limits;
- creates the canonical F1 `ResidentReasoningPacket`;
- computes a deterministic digest; and
- performs no model/provider/resource invocation or state-changing action.

These behaviors are valid F4 foundations, but the source-to-request checks are
incomplete as described below.

## 4. Blocking defect A — resident identity correspondence

The assembler checks:

`bundle.resident_id == request.occupant_id`

and checks that the bundle’s identity anchor matches `bundle.resident_id`.
It does not check `request.resident_id` against the authoritative bundle or
identity anchor. It then copies `request.resident_id` directly into the packet.

Independent reproduction using the actual assembler and fixture bundle:

```text
wrong_resident ACCEPTED
<random request resident UUID>
<authoritative bundle resident UUID>
<occupant UUID>
```

The resulting packet therefore carries a resident identity not established by
the authoritative context source. This contradicts F4’s required identity
projection and can associate valid bounded context with the wrong resident.

Severity: **BLOCKING**  
Minimum correction: require the request/session resident identity to
correspond to the authoritative bundle identity before projection, or require
the accepted F3-bound session/turn as the authoritative source for all packet
identity fields. Add a negative test proving a wrong resident is rejected.

Identity preservation: **FAIL**

## 5. Blocking defect B — missing current operational state

F4 requires current operational state in the packet. The assembler requires
identity, office, and authority anchors but does not require a current
assignment or other current-state item. A bundle reduced to only those three
anchors was accepted:

```text
MISSING_CURRENT_STATE_ACCEPTED 0 2
```

The resulting packet had zero `operational_state_refs`; its two
`authoritative_current_state_refs` were anchor references, not proof that a
current operational-state snapshot or assignment was present.

This is a truthful-failure violation: when required current state is absent,
the assembler should reject rather than produce a plausible but incomplete
packet.

Severity: **BLOCKING**  
Minimum correction: define and enforce the authoritative current-state
requirement at the F4 boundary, including the accepted current assignment or
state snapshot/reference and its freshness/correspondence checks. Add a
missing-current-state negative test.

Bounded packet assembly: **FAIL**

## 6. Aggregate context and F1 bound — PASS

The assembler counts `operational_state_refs` and all other packet context
collections in its preflight, then relies on the F1 constructor’s independent
aggregate validation. An independent pressure probe using approximately
60 legal near-limit references plus approximately 60,000 characters of
distinct bounded constraints was rejected with the F1 aggregate-bound error.

The prior approximately 92,133-character F1 bypass was not reintroduced.
Operational-state reference collection overflow was also rejected.

Aggregate context: **PASS**

## 7. Identity, transcript, references, and failure behavior

Wrong occupant identity is rejected. Wrong office/authority anchors, stale
bundles, missing anchors, malformed source references, forbidden transcript
layers, and over-limit collections fail closed. A transcript claiming another
resident remains bounded context and does not enter typed packet identity.

Reference-as-payload pressure was safe: a context item containing a very large
embedded mapping projected only its bounded source reference; the large value
did not enter the packet.

The resident mismatch defect is the exception: the explicit resident field is
caller-supplied and not checked against the authoritative bundle.

Transcript-not-identity: **PASS**  
Reference/value semantics: **PASS**  
Failure semantics: **FAIL** due to missing-current-state and resident mismatch
acceptance paths

## 8. Determinism and F2/F3 compatibility

Equivalent immutable bundle/request inputs produced identical typed payloads
and packet digests. Ordering is based on stable layer/item/source-reference
sorting and duplicate removal.

The packet retains source cognition event, correlation, causation, packet,
identity, and bounded context fields. An independent compatibility probe built
a matching F2 result provenance record and passed
`CognitionProvenance.validate_against_request(packet)` with matching packet,
source-event, and correlation identifiers. The accepted F2 durable writer and
F3 session boundary were not modified.

F3 does not require F4 to create a second session field; F3’s `bind_request`
and `validate_turn` remain the upstream session-A/session-B correspondence
boundary. F4’s lack of direct session coupling is therefore not itself a new
requirement. However, the resident mismatch above must still be closed before
an F3-bound request is projected into a packet.

Deterministic assembly: **PASS**  
F2 provenance integration: **PASS**  
F3 session integration: **PASS as an upstream boundary; F4 resident
correspondence remains blocking**

## 9. Provider, model, and authority boundaries — PASS

The assembler contains no provider, model, GPU, endpoint, Ollama, OpenAI,
ChatGPT, RTX 3060/4090, or P100 selection. It performs no model invocation,
resource scheduling, escalation decision, or execution. Authority is carried
from the authoritative anchor and no execution capability is manufactured.

Provider neutrality: **PASS**  
Authority boundary: **PASS**

## 10. Regression tests

Focused F4/F1/F2/F3/context/runtime/provider/authority selection:

`130 passed in 6.04s`

This included the early assembler tests, F1 cognition contracts, F2
provenance and correspondence repair, F3 session tests, provider-neutral
tests, resident context/runtime tests, Grace authority, consultation loop,
autonomous reason/execute loop, and governed provider scheduler tests.

The submitted tests cover wrong occupant, stale bundle, transcript spoof,
reference bounds, operational-state reference count, deterministic output,
and F1 serialization. They do not cover wrong resident against the bundle or
missing current-state material; the independent probes exposed both.

F1 regression: **PASS**  
F2 regression: **PASS**  
F3 regression: **PASS**

## 11. Next roadmap package

F4 requires targeted repair and independent revalidation before downstream
packages may rely on it. After F4 acceptance, the repaired roadmap makes the
next eligible policy/capability work:

- **GRC-003-P1 — Escalation decision policy**, dependent on F1 and F4; and
- **GRC-003-P2 — Capability/resource request and binding adapter**, eligible
  from F1 and existing provider/capability seams.

P1 and P2 are separate eligible packages and may proceed as the roadmap
permits; neither is accepted by this report.

Next roadmap package: **GRC-003-P1 and GRC-003-P2 after F4 repair/acceptance**  
Grace implementation readiness: **REPAIR_REQUIRED**

