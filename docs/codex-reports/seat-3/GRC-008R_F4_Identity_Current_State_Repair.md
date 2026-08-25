# GRC-008R — F4 Identity Correspondence and Current-State Repair

Package: GRC-008R  
Roadmap package: GRC-003-F4 — Bounded resident reasoning packet/context assembly  
Role: C3 targeted repair writer  
Status: REPAIR_COMPLETE_READY_FOR_REVALIDATION  
Date: 2026-08-25

## 1. Blocking findings repaired

C2's GRC-008 validation identified two reachable blocking defects in the
preserved early F4 `ResidentReasoningPacketAssembler`:

1. a caller-supplied `ReasoningAssemblyRequest.resident_id` could disagree
   with the authoritative `ContextBundle.resident_id`, yet the assembler
   copied the caller value into the packet; and
2. a bundle containing identity, office, and authority anchors but no current
   operational-state material was accepted and projected with no meaningful
   current state.

No other GRC-008 passing area was redesigned.

## 2. Resident mismatch root cause and repair

The existing projector checked `bundle.resident_id` against
`request.occupant_id`, but omitted the independent `request.resident_id`
correspondence check. The packet constructor then used `request.resident_id`.

The authoritative resident source is the existing `ContextBundle.resident_id`,
validated by its mandatory `identity_anchor` and its resident ID value. The
assembler now rejects unless both:

`bundle.resident_id == request.occupant_id`

and:

`bundle.resident_id == request.resident_id`

The packet continues to receive resident identity from the now-corresponding
request/bundle path, and a mismatch fails before packet construction. No
second resident identity source was created.

Matching resident identity is serialized and round-tripped unchanged. A
rejected mismatch emits no packet.

The existing analogous occupant, office, authority-anchor, stale-bundle, and
implementation lineage behavior was inspected and preserved; no additional
defect was found or invented.

## 3. Current-state root cause and repair

The accepted F4 definition requires current operational state in the bounded
packet. The existing projector required mandatory identity, office, and
authority anchors, but did not require a current assignment/state item.

In the accepted `ContextBundle` vocabulary, the authoritative current-state
material available to F4 is the mandatory `current_assignment` item produced
by the existing context assembler for the relevant profile. Its bounded value
and non-empty `source_ref` provide current task/state material; anchor-only
references are not treated as current operational state.

The projector now requires exactly one mandatory `current_assignment` item
with mapping-shaped bounded value and a non-empty source reference. If absent,
empty, or replaced only by transcript/provider metadata, assembly fails with
`ReasoningContextAssemblyError("current-state-missing", ...)`.

The repair does not invent state, infer state from prose, substitute stale
history, or silently create an empty packet.

## 4. Aggregate and reference safety

The accepted F1 aggregate context bound remains unchanged at 64,000
characters. Existing F4 preflight continues to count operational-state
references and all other packet context collections before F1 construction.
The prior approximately 92,133-character operational-state bypass remains
covered by the F1 regression suite.

Reference/value semantics remain unchanged: context item values are not
embedded as unrestricted packet content; bounded source references are
projected. Provider/model/resource metadata cannot satisfy the current-state
requirement.

## 5. Tests added and changed

Added `tests/test_reasoning_context_assembler_repair.py` covering:

- matching authoritative resident identity and packet serialization;
- wrong resident rejection before packet emission;
- missing current assignment/state rejection;
- transcript/provider metadata unable to substitute current state;
- valid bounded current-state projection; and
- continued aggregate-bound rejection under pressure.

Updated the existing F4 fixture expectations so its valid request explicitly
corresponds to the authoritative bundle resident identity. The transcript
test now asserts that authoritative resident identity remains unchanged.

## 6. Regression evidence

Focused F4 assembler and repair tests: **17 passed**.

Integrated suite covering F4, F1 cognition contracts and aggregate bounds, F2
provenance/correspondence, F3 session identity, River events, resident
context/runtime, provider neutrality, Grace authority, and adjacent Grace
provider tests:

**138 passed in 7.55s**.

Compile/import validation: **PASS**.

Preserved regression areas:

- F1 regression: PASS, including aggregate context and
  `operational_state_refs` inclusion.
- F2 regression: PASS, including exact stored request/result correspondence,
  forged-event rejection, failure provenance, and restart lineage tests.
- F3 regression: PASS, including session identity, session/request
  distinction, stale context, and provider-neutral identity behavior.
- Provider neutrality: PASS; no model, provider, endpoint, GPU, or resource
  selection was added.
- Authority boundary: PASS; no execution authority was created or widened.
- Deterministic assembly: PASS.
- Reference/value semantics: PASS.
- Transcript-not-identity and transcript-not-current-state: PASS.

No PostgreSQL change was required by this F4 repair. Existing F2/F3 durable
River/EventStore behavior was not modified.

## 7. Files and scope

Implementation repository: `ppow1/Riverview`  
Branch: `codex/c484-operator-persistent-service`

Changed implementation/test files:

- `src/riverview/reasoning/context_assembler.py` — resident correspondence
  and mandatory current-state gate.
- `tests/test_reasoning_context_assembler.py` — corrected valid authoritative
  identity expectations.
- `tests/test_reasoning_context_assembler_repair.py` — targeted repair
  regressions.

The early F4 assembler remains preserved and is not claimed accepted here.
No F1, F2, F3, P1, P2, provider, model, GPU, migration, CME, Campaign Runner,
or unrelated runtime work was changed.

## 8. Readiness

Both C2 blocking findings are repaired at the authoritative F4 projector
boundary. The implementation is ready for independent revalidation; C3 does
not self-accept F4.

`REPAIR_COMPLETE_READY_FOR_REVALIDATION`
