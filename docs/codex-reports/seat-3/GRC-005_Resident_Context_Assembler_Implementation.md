# GRC-005 — Grace F2 Resident Context Assembler Implementation

Package: GRC-005  
Role: C3 primary Grace implementation writer  
Implementation status: IMPLEMENTATION_COMPLETE_READY_FOR_VALIDATION  
Date: 2026-08-25

## 1. Accepted F2 roadmap definition

The accepted/repaired GRC-003 roadmap defines F2 as the bounded resident
context packet projector. Its purpose is to assemble resident identity,
office, authority, current state, relevant memory/evidence, task information,
and authority boundaries into the F1 `ResidentReasoningPacket`.

Dependencies are F1 and the existing `ContextBundle` assembly. Expected
ownership is a new packet projector under `Riverview/src/riverview/residents`
or `reasoning`, with `context.py` changed only if a missing bounded source
field requires it, plus existing resident-context tests and new packet tests.

The roadmap names these seams to reuse: `ResidentContextAssembler`,
`ContextBundle.compact_items`, policy decisions, dependency fingerprints,
contradiction handling, budgets, and renderer validation. Possible new
components are `PacketProjector`, an omission/relevance contract, an
authoritative-state snapshot adapter, and packet digest support.

Required tests are identity/office/authority/current-state/task fields,
relevance filtering, budget shedding, contradiction preservation, stale-bundle
rejection, protected-data classification, omission reasons, and no full
transcript dump. Acceptance requires bounded high/external input with required
authority/current state, no unrelated history or unapproved protected content,
and reproducibility from source references and digest. Failure conditions are
missing identity/authority/current state, stale dependency fingerprint,
policy-denied evidence, packet over budget, or unresolved classification.

Explicit non-goals are model calls, escalation decisions, retrieval redesign,
and unbounded memory. No conflict was found between this implementation and
the accepted F2 definition.

## 2. Existing seams discovered and reused

The implementation reuses the existing `Riverview/src/riverview/residents/context.py`
contracts without changing them:

- `ResidentContextAssembler` supplies the authoritative `ContextBundle`;
- `ContextBundle` supplies resident/office identity, selected bounded items,
  policy results, stale state, dependency fingerprint, and source references;
- mandatory `identity_anchor`, `office_anchor`, and `authority_anchor` items
  are checked before projection;
- existing budget/policy/contradiction handling remains owned by the resident
  context assembler;
- `ContextBundle.bundle_id` becomes the F1 `source_context_id`;
- F1 `ResidentReasoningPacket` remains the only packet contract and enforces
  its own final typed validation and aggregate limit.

No parallel resident identity store, transcript store, provider registry,
model binding, GPU binding, or runtime cognition path was introduced.

## 3. Implementation architecture

Added `reasoning.context_assembler` with:

- `ReasoningAssemblyRequest`: explicit task, lineage, identity, tier,
  classification, output, egress, and expiry inputs;
- `ResidentReasoningPacketAssembler`: deterministic projector from one
  accepted `ContextBundle` to one F1 packet;
- `ReasoningContextAssemblyError`: fail-closed F2 checkpointed failure;
- bounded preflight and deterministic packet digest helpers.

The projector derives office and authority only from mandatory authoritative
bundle anchors. It carries the caller-supplied resident/occupant/
implementation lineage explicitly and rejects occupant/bundle mismatch. It
projects source references rather than embedding arbitrary item values. State,
evidence, ambiguity, prior-decision, and constraint collections are normalized
in stable item order and checked against F1 per-field, collection, and
aggregate limits before F1 construction.

The digest uses stable JSON ordering over the fixed request lineage, bundle ID,
assembler version, and projected packet fields. Equivalent immutable inputs
produce the same packet payload and digest. No provider or model call occurs.

## 4. Files and symbols changed

Implementation repository: `ppow1/Riverview`  
Branch: `codex/c484-operator-persistent-service`

Changed files:

- `Riverview/src/riverview/reasoning/context_assembler.py`
- `Riverview/src/riverview/reasoning/__init__.py`
- `Riverview/tests/test_reasoning_context_assembler.py`

The existing F1 contract module and resident context module were not modified.

## 5. Identity-preservation evidence

Identity is never read from transcript text, provider/resource metadata, model
names, GPU identifiers, endpoints, implementation classes, display names, or
arbitrary context values. The request carries resident, occupant, and
implementation IDs explicitly. Occupant identity must match the authoritative
bundle resident ID. Office identity must be present in the bundle and is
projected from its office anchor. Authority is projected from the mandatory
authority anchor rather than inferred from task text.

Tests cover resident/occupant/office preservation, transcript content that
mentions another resident, provider/resource fields being absent from the
packet, occupant mismatch, missing identity/office/authority anchors, and
serialization round-trip preservation.

## 6. Bounded assembly and reference/value semantics

The assembler preflights the exact F1 packet context fields before constructing
the packet. It counts operational-state references, evidence references,
authoritative-state references, constraints, ambiguity, prior decisions,
known deterministic results, objective/question, home assessment, output
schema, and egress policy. It enforces F1's 64,000-character aggregate and
collection/value limits before F1 construction.

Only source references are projected from `ContextItem` values. Arbitrary
embedded item mappings are not copied into the packet. Empty, malformed, or
overlong source references fail closed. Transcript-like layers are rejected;
historical or contradiction material can only cross through bounded references
and explicit bounded ambiguity values.

Stale bundles, missing anchors, invalid references, excessive embedded text,
excessive reference collections, identity mismatch, and impossible aggregate
assembly produce truthful `ReasoningContextAssemblyError` outcomes. The
assembler does not silently truncate meaning-bearing context; it fails closed
when the accepted packet cannot fit.

## 7. Determinism

Projection ordering is explicitly sorted by layer, item ID, and source
reference. Duplicate references are removed deterministically while preserving
first occurrence. Digest serialization uses sorted JSON keys and fixed
contract/assembler versions. No filesystem, database retrieval order, provider
health, model, GPU, or endpoint state participates in packet construction.

## 8. Authority and provider boundaries

The packet carries the existing authoritative reference but adds no execution
authority. The tests assert that no `execute` authority field is created.
Assembly does not select or invoke a cognition provider, model, endpoint, GPU,
or resource class. Packet tier is a capability request field supplied by the
caller; F2 does not choose escalation or resource topology.

## 9. Tests and evidence

Focused F2 tests cover:

- valid F1-compatible assembly;
- resident, occupant, office, and authority preservation;
- transcript/provider/resource identity substitution rejection;
- deterministic repeated projection;
- stale, missing-anchor, and identity mismatch failure;
- embedded-context, reference-count, and operational-state bounds;
- malformed source-reference failure;
- reference-only projection semantics;
- F1 serialization preservation;
- no execution authority and no provider/model/GPU binding.

Required F1 and adjacent regression suites were also run:

`95 passed in 7.42s`

The run included the F2 tests, all accepted F1 cognition-contract tests,
provider-neutral contracts, resident context/runtime, Grace authority,
consultation loop, autonomous reason/execute loop, and governed provider
scheduler tests. Python compileall and package import validation passed.

The accepted F1 aggregate bound, `operational_state_refs` inclusion, identity
correspondence, provider neutrality, advisory authority, and live-generation
truth tests remain passing.

## 10. Explicit non-goals and deferred work

This package does not implement:

- F2 River provenance event emission or persistence;
- cognition sessions or runtime identity transitions;
- escalation policy or capacity/resource selection;
- provider dispatch or model invocation;
- home/high/external generation;
- continuation management;
- CME or Campaign Runner changes;
- migrations, model selection, GPU assignment, or live acceptance.

F2 prepares the bounded packet required by later F3/F4/P1/P2/E packages. It
does not claim that Grace is running or that a live model consumed the packet.

## 11. Readiness

Implementation is complete and tested for this bounded F2 slice. Independent
validation must inspect the actual changed symbols, verify the allowed-file
scope, rerun the tests, exercise negative identity/boundary cases, and keep
DESIGNED, IMPLEMENTED, TESTED, LIVE-ACCEPTED, and RUNNING as separate claims.

`IMPLEMENTATION_COMPLETE_READY_FOR_VALIDATION`
