# GRC-004R — Grace F1 Contract Identity and Bounded-Context Repair

Package: GRC-004R  
Role: C3 original implementation repair writer  
Status: REPAIR_COMPLETE_READY_FOR_REVALIDATION  
Date: 2026-08-25

## Validation basis

This repair used the complete independent validation report:

`docs/codex-reports/seat-1/GRC-004V_Cognition_Contract_Validation.md`

The report validated source at GRC-004 commit
`4e4d67c10cf956160d0478bf1b513f3a69383528` and identified three related
blocking contract defects: incomplete bounded packet context, incomplete
escalation lineage, and result envelopes unable to enforce office,
implementation, or authority correspondence.

## Exact defects and root causes

### Identity preservation

`ResidentReasoningPacket` carried resident, occupant, and office IDs but no
implementation identity or source cognition event lineage. `EscalationAssessment`
also omitted office, implementation, authority, packet, and provenance
correspondence. `CognitionResult.validate_against` compared resident and
occupant identity but could not compare office, implementation, authority, or
source-event identity. The root cause was an incomplete identity model and a
correspondence loop limited to the fields that happened to exist.

The repair adds typed identity and lineage fields to the packet, escalation
assessment, capability request, and result. Result/request correspondence now
fails closed for resident, occupant, office, implementation, authority,
source-event, correlation, tier, and classification mismatches. Provider and
resource references remain separate metadata and cannot substitute for
resident identity.

### Bounded context

The original packet had bounded objective/question/reference/constraint fields
and rejected a field literally named `transcript`, but it did not expose the
required GRC-002 context components with enforceable omission and provenance
semantics. It therefore could not serve as F4's complete bounded packet. The
root cause was treating a small existing field set as equivalent to the full
GRC-002 packet rather than defining each required context path.

The repair adds typed, bounded fields for source cognition event, objective,
authoritative current state references, unresolved ambiguity, relevant prior
decisions, known deterministic results, home assessment, requested output
schema, egress policy, and max budget. Reference collections are capped at 64
entries with 500-character references; bounded text collections are capped at
32/64 entries as appropriate and 4,000 characters per value. The complete
packet context is capped at 64,000 aggregate characters. No transcript,
arbitrary mapping, generic metadata, or unbounded embedded context field was
added.

## Code and tests changed

Implementation repository: `ppow1/Riverview`  
Branch: `codex/c484-operator-persistent-service`  
Repair commit: `c7646bb`  

Changed files:

- `Riverview/src/riverview/reasoning/cognition_contracts.py`
- `Riverview/tests/test_cognition_contracts.py`

Added validation and regression coverage for:

- provider/resource replacement preserving resident, occupant, office,
  implementation, and authority identity;
- HOME → HIGH and HOME → EXTERNAL tier transitions preserving identity;
- resident, occupant, office, implementation, and authority mismatch rejection;
- complete packet and result serialization identity preservation;
- bounded task/context values, reference values, collection counts, and
  aggregate packet context;
- complete reference-based packet round trip;
- existing unknown-tier, advisory-authority, provider-neutrality, failure,
  expiry, correlation, classification, and deterministic live-generation
  safeguards.

## Verification evidence

Focused and required adjacent suites:

`81 passed in 5.55s`

The run covered:

- `test_cognition_contracts.py`
- provider-neutral contracts;
- resident context and runtime;
- Grace authority;
- Grace consultation loop;
- autonomous reason/execute loop;
- governed provider scheduler.

Python compileall for the reasoning source and focused tests also passed.

Existing independent PASS areas remain preserved:

- Provider neutrality: PASS — no model, GPU, endpoint, or provider binding was
  introduced.
- Authority boundary: PASS — results remain restricted to advisory/read/
  diagnostic scopes and execution authority remains rejected.
- Live-generation truth: PASS — failed and deterministic outcomes cannot claim
  live generation.

## F4 contract readiness

F1 now supplies F4 with stable resident, occupant, office, authority, and
implementation lineage; explicit tier semantics; packet/source correlation;
authoritative state and evidence references; ambiguity/prior-decision/
deterministic-result context; output and egress constraints; bounded aggregate
context; capability request identity; result correspondence; and truthful
generation state. F4 can assemble live context against these contracts without
inventing the missing identity or context-safety semantics.

Status: READY_FOR_REVALIDATION.

## Deferred work and scope confirmation

This repair does not implement F2 provenance emission, F3 runtime transitions,
F4 live context assembly, P1 policy execution, P2 resource scheduling, any
provider/model/GPU selection or dispatch, home/high/external generation, CME,
or live acceptance.

No migration was created. No model was selected. No GPU was assigned. No
unrelated files were staged or changed.
