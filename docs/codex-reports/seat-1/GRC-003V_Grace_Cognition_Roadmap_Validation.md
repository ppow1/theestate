# GRC-003V — Grace Cognition Roadmap Validation

Status: Independent architecture / implementation-roadmap validation
Validator: C1
Primary input: docs/codex-reports/seat-3/GRC-003_Grace_Cognition_Implementation_Decomposition.md
Design basis: docs/codex-reports/seat-3/GRC-002_Grace_Cognition_and_Escalation_Contract.md
Validation date: 2026-08-25

## Verdict

# PASS WITH REQUIRED NON-BLOCKING CHANGES

No blocking defect remains.

The roadmap faithfully decomposes GRC-002 into bounded implementation and
acceptance packages. It preserves identity, authority, provenance, provider
neutrality, truthful failure behavior, deterministic/cognitive separation, and
the CME boundary.

Three required non-blocking corrections should be made before or at the start
of implementation:

1. F2 must explicitly enumerate the complete GRC-002 provenance envelope,
   including model/resource IDs and validation/supersession lineage, rather
   than relying on an abbreviated field list.
2. The dependency/concurrency text must remove ambiguity between formal package
   dependencies and the claim that F1-F4 may proceed concurrently. P1, E1,
   and E4 also need their required F4/F2 dependencies stated consistently.
3. F3/E5 must choose and document the durable persistence seam before their
   implementation begins: either an existing consultation/continuity store
   with exact fields, or an additive persistence contract to be implemented
   by the owning package. "Likely additive" is insufficient as an execution
   handoff.

These findings do not invalidate the roadmap and do not require a replacement
roadmap.

## Validation scope and method

The validation compared GRC-003 against GRC-002 requirements and inspected
the repository seams named by the roadmap. This was a design validation; no
Grace cognition implementation was executed or changed.

Inspected local evidence included:

- docs/codex-reports/seat-3/GRC-003_Grace_Cognition_Implementation_Decomposition.md
- docs/codex-reports/seat-3/GRC-002_Grace_Cognition_and_Escalation_Contract.md
- Riverview/src/riverview/residents/runtime.py
- Riverview/src/riverview/residents/context.py
- Riverview/src/riverview/reasoning/contracts.py
- Riverview/src/riverview/reasoning/registry.py
- Riverview/src/riverview/river/events.py
- Riverview/src/riverview/river/store.py
- Riverview/src/riverview/grace/authority.py
- Riverview/src/riverview/autonomy/runtime.py
- Riverview/tests/test_resident_runtime.py
- Riverview/tests/test_resident_context.py
- Riverview/tests/test_provider_neutral_contracts.py
- Riverview/tests/test_grace_response_contract.py
- Riverview/tests/test_grace_authority.py
- Riverview/tests/test_grace_continuation_proof.py
- tests/test_grace_consultation_loop.py
- tests/test_governed_provider_scheduler.py
- tests/test_autonomous_reason_execute_loop.py

## Severity summary

| Severity | Count | Result |
|---|---:|---|
| Blocking defect | 0 | No implementation-stopping defect found |
| Required non-blocking | 3 | Correct before or during implementation |
| Future hardening | Several | Explicitly outside this campaign |
| Nit / preference | Not recorded | No effect on acceptance |

## A. Design-basis fidelity

Result: PASS.

GRC-003 explicitly preserves:

    Office != Occupant != Implementation != State

It also preserves:

    DESIGNED != IMPLEMENTED != TESTED != LIVE-ACCEPTED != RUNNING

The roadmap repeatedly distinguishes implementation reports from acceptance
evidence and requires independent validation of source, tests, runtime
artifacts, and boundary evidence.

The roadmap does not silently select a final model, provider, endpoint, or GPU.
Its campaign architecture states that HOME_COGNITION, HIGH_REASONING, and
EXTERNAL_ESCALATION are capability classes whose concrete bindings are supplied
later by configuration.

This matches GRC-002 sections 1, 3, 7, 9, and 13.

## B. Identity preservation

Result: PASS.

F3 is an appropriately bounded identity-preserving seam. It reuses:

- ImplementationBinding;
- RuntimeSession;
- ResidentImplementationRuntime;
- PostgresBindingCatalog;
- transition preflight;
- resident context identity anchors.

Its tests require the same occupant across provider/model/resource changes,
reject wrong occupant/binding, preserve predecessor implementation history, and
prove that a high result cannot create a second Grace.

Its acceptance criteria explicitly preserve occupant, office, authority, and
state IDs when implementation/provider/model/resource changes.

This is supported by:

- Riverview/src/riverview/residents/runtime.py;
- Riverview/src/riverview/residents/context.py;
- Riverview/tests/test_resident_runtime.py;
- Riverview/tests/test_resident_context.py.

No final binding is selected by the roadmap.

## C. Bounded context and reasoning packets

Result: PASS, with the F2/F4 contract clarification recorded below.

F4 correctly uses the existing ContextBundle seam and requires:

- identity;
- office;
- authority;
- current operational state;
- task/question;
- relevant evidence;
- contradiction preservation;
- dependency fingerprints;
- exclusions and omission reasons;
- classification;
- packet digest;
- stale-bundle rejection;
- budget limits;
- no full transcript dump.

It explicitly prohibits transcript copies as the default authority and requires
reproducibility from source references and digest.

This matches GRC-002 section 6 and the actual bounded assembly behavior in
Riverview/src/riverview/residents/context.py.

Required clarification R1 below concerns the exact complete field list, not the
bounded-packet design itself.

## D. Provider-neutral contracts

Result: PASS.

F1 creates the correct contract foundation. P2 defines capability/resource
requests without physical GPU topology and keeps provider/resource binding
behind an adapter/configuration layer.

The roadmap explicitly states that:

- Grace requests HOME_COGNITION, HIGH_REASONING, or EXTERNAL_ESCALATION;
- Grace does not inspect physical GPU topology;
- provider replacement changes configuration, not orchestration code;
- no final model map or assignment is introduced.

The current repository supports this direction through:

- Riverview/src/riverview/reasoning/contracts.py;
- Riverview/src/riverview/reasoning/registry.py;
- Riverview/src/riverview/residents/runtime.py.

The roadmap correctly identifies that the existing generic reasoning envelope
is not yet sufficient and must be extended rather than falsely declared
complete.

## E. Escalation policy

Result: PASS.

P1 explicitly separates:

1. home cognition's belief that stronger reasoning may help;
2. policy permission to escalate;
3. capacity/resource eligibility.

Its proposed EscalationAssessment contains separate
home_belief, policy_permitted, and capacity_eligible outcomes. Its tests
include policy denial, capacity denial, and the negative case where capacity
is treated as policy.

E2 requires an explicit high-reasoning request after an accepted home
escalation decision. E2 also requires no silent provider switch, no silent
downgrade, truthful hold/unavailable outcomes, and no execution authority.

This directly preserves GRC-002 sections 5, 7, and 10.

## F. Home, high, and external paths

Result: PASS.

The roadmap provides bounded packages for all three paths:

- E1 — home cognition execution;
- E2 — high-reasoning escalation request;
- E3 — external advisory escalation;
- E4 — result return and Grace integration.

E2 treats high reasoning as an intentional, correlated, classified,
capacity-aware request. E3 treats external reasoning as explicitly external,
advisory, bounded, and classified. E4 returns recommendation, rationale,
uncertainty, constraints, unresolved questions, and further-escalation state
to the same Grace occupant.

High and external results cannot execute, accept, merge, or widen authority.

## G. Resource and capacity abstraction

Result: PASS.

P2 correctly requests capability/resource classes, not physical GPU topology.
P3 adds only the minimum shared-resident reservation seam rather than a
general population scheduler.

P3 covers:

- resident/occupant identity;
- tier;
- request;
- priority/fairness class;
- candidate resource;
- lease/deadline;
- hold/release;
- expiry recovery;
- no dispatch on reservation.

A3 covers two-resident contention and truthful exhaustion while leaving exact
fairness/SLO/preemption decisions open to Steward configuration, as GRC-002
permits.

The roadmap does not attempt to solve generalized resident scheduling.

## H. Provenance and truthfulness

Result: PASS WITH REQUIRED NON-BLOCKING CHANGE R1.

F2 correctly identifies the need to distinguish deterministic work, Grace home,
Grace high, external, worker, validation, and Steward activity. It includes
actor class, resident/occupant/office, tier, implementation, provider,
resource class, request/correlation, packet, policy, live_generation,
result/failure state, and evidence references.

It also requires negative tests proving deterministic events cannot serialize
as Grace cognition and that false generation claims fail.

### R1 — F2 provenance field completeness

Severity: REQUIRED NON-BLOCKING

Exact location: GRC-003-F2, "CognitionProvenance envelope"; related E1,
E2, E3, E4, and I2 acceptance criteria.

Requirement: GRC-002 section 9 requires every cognition, transition,
recommendation, handoff, execution, validation, and acceptance record to carry:

- event_id;
- event_type;
- actor_class;
- actor_id;
- resident_id;
- occupant_id;
- office_id;
- cognition_tier;
- implementation_id;
- provider_id;
- model_ref;
- resource_id;
- request_id;
- correlation_id;
- causation_id;
- packet_id;
- authoritative_state_refs;
- evidence_refs;
- policy_version;
- classification;
- live_generation;
- timestamp;
- status;
- predecessor/supersession;
- validation_refs.

GRC-003-F2's abbreviated list does not explicitly enumerate actor_id,
model_ref, resource_id, authoritative_state_refs, validation_refs, or
predecessor/supersession lineage. A2 mentions provider/model/resource metadata,
but the contract owner should not rely on a later acceptance harness to define
the canonical envelope.

Why it matters: incomplete provenance can cause false attribution, inability
to distinguish configuration from live generation, or loss of result and
supersession lineage. This is a truth-boundary risk, but the correction is
local and does not invalidate the package graph.

Minimum correction: add the complete GRC-002 field list to F2's contract and
require every applicable event/result package to populate or explicitly mark
each field as not-applicable. Add negative fixtures for missing model/resource
identity and missing predecessor/validation lineage.

## I. Authority boundary

Result: PASS.

The roadmap preserves GRC-002's authority matrix:

- deterministic substrate performs mechanics;
- Grace home/high recommends within policy;
- external reasoning provides advice;
- CME orchestrates;
- workers execute authorized bounded action;
- validation provides validation evidence;
- Steward retains material authority and acceptance.

E4 explicitly prohibits direct dispatch and acceptance. I1 requires CME to
remain owner of mechanics. I2 requires execution to use the normal structured
execution/dispatch path and prevents advice from becoming execution authority.

The roadmap does not grant cognition authority merely because a result exists.

## J. CME integration

Result: PASS WITH REQUIRED NON-BLOCKING CHANGE R2.

I1 is a bounded adapter, not a CME rewrite. It maps cognition requests/results
to existing CME wait, blocked, escalated, lease, idempotency, and evidence
behavior. It explicitly prohibits cognition from mutating dependencies or
campaign state outside the accepted operation.

The existing seam is real:

- Riverview/src/riverview/autonomy/runtime.py;
- CME status and River cursor;
- existing objective/stage and reconciliation behavior.

I1 does not make CME responsible for Campaign Runner mechanics and does not
replace CME.

## K. Failure and unavailable behavior

Result: PASS.

The roadmap covers:

- home unavailable;
- high busy/unavailable/timeout;
- external unavailable;
- malformed result;
- correlation mismatch;
- classification denial;
- stale context;
- capacity exhaustion;
- identity/binding mismatch;
- authority widening;
- no-silent-downgrade behavior.

Failures are truthful and fail closed. E2/E3 explicitly require no fabricated
result and no silent fallback. E4 rejects stale or mismatched results. I2
consolidates truth guards.

This matches GRC-002 section 10.

## L. Continuations

Result: PASS WITH REQUIRED NON-BLOCKING CHANGE R3.

E5 correctly requires bounded durable continuations with root/child lineage,
packet-bounded context, prior result/evidence references, duplicate
suppression, no-progress limits, capacity-hold recovery, and Steward
checkpoint boundaries.

It correctly rejects browser/chat transcript state as authoritative memory.

### R3 — Durable persistence seam must be selected

Severity: REQUIRED NON-BLOCKING

Exact location: GRC-003-F3 and GRC-003-E5 persistence-impact statements.

Requirement: GRC-002 requires durable bounded reasoning/continuation lineage
and authoritative event/provenance records.

F3 says cognition session/turn persistence is "likely additive" and may use an
adapter over existing continuity records. E5 says to use existing consultation
persistence "where it fits" and otherwise define additive continuity records.
Those alternatives are reasonable design space, but they leave the
implementation package without a fixed durable contract.

Why it matters: independent implementation and crash/restart validation cannot
be deterministic if package owners may choose different persistence authorities
or treat a conversation/session file as authoritative.

Minimum correction: before implementation, F3/E5 must name the authoritative
store and exact fields for session/turn/continuation lineage. If existing
consultation persistence is sufficient, specify the adapter symbols and
readback contract. If it is insufficient, specify one additive persistence
contract and assign it to an owning package. Do not create a second parallel
conversation memory system.

## M. Package quality

Result: PASS WITH REQUIRED NON-BLOCKING CHANGE R2.

Each F, P, E, I, and A package contains:

- objective;
- dependencies;
- expected files/symbols;
- reusable seams;
- new components;
- persistence impact;
- tests;
- acceptance criteria;
- failure conditions;
- validation evidence;
- explicit non-goals.

The package boundaries are practical:

- F1 contracts;
- F2 provenance;
- F3 identity session;
- F4 bounded packet;
- P1 policy;
- P2 binding;
- P3 minimum capacity;
- E1/E2/E3/E4/E5 execution and return paths;
- I1/I2 CME and guards;
- A1/A2/A3 acceptance.

F2 and F4 are foundational but remain independently reviewable. E4 is broader
than a single function but is a coherent result-return boundary. A3 is
appropriately a live operational proof rather than a production feature.

No package is inherently too broad or too small for the stated campaign.

The only package-quality issue is the dependency/concurrency ambiguity recorded
as R2.

## N. Dependency graph and concurrency

Result: PASS WITH REQUIRED NON-BLOCKING CHANGE R2.

The formal dependency graph is otherwise coherent:

- F1-F4 provide contract, provenance, identity, and packet foundation;
- P1/P2/P3 provide policy, binding, and minimum capacity;
- E1-E5 provide home, high, external, return, and continuation paths;
- I1/I2 integrate CME and authority/failure guards;
- A1-A3 provide deterministic, live-local, and shared-resident proof.

### R2 — Dependency and concurrency wording is inconsistent

Severity: REQUIRED NON-BLOCKING

Exact location: section 4.1 package graph, section 4.2 safe concurrency, and
E1/E4 dependency declarations.

Observed inconsistencies:

1. F4 formally depends on F1 and F1/F4 context contracts, but section 4.2
   says F1, F2, F3, and F4 can be assigned concurrently.
2. P1 formally depends on F1 and F4, but section 4.2 says P1/P2 may proceed
   after F1.
3. E1 says F2 event emission should be available, but F2 is absent from
   E1's formal dependency list.
4. E4 requires provenance/event integration but omits F2 from its formal
   dependency list.

Why it matters: a literal scheduler could start implementation against a
moving contract or create event/result seams before the provenance contract is
frozen. This is an implementation-order safety issue, but it is readily
correctable.

Minimum correction:

- distinguish parallel package preparation from implementation/acceptance;
- require F1 accepted before F4/P1/P2 implementation;
- require F2 accepted before packages that emit or consume canonical cognition
  provenance events, including E1 and E4;
- make the formal dependency graph authoritative over the prose concurrency
  paragraph;
- state that concurrent work may begin only in separate files with frozen
  predecessor contracts.

No long-lived branches are required; the ownership rule is sufficient.

## O. Acceptance strategy

Result: PASS.

The roadmap does more than require source presence.

A1 proves contract, packet, policy, provenance, identity, continuation, CME,
failure, and masquerade behavior with negative tests and actual resulting code.

A2 proves real local/provider reasoning through an approved configured
boundary, with request/response IDs, provider/model/resource metadata, event
timeline, packet digest, latency, and truthful unavailable behavior.

A3 proves multi-resident addressability, identity isolation, resource
contention, queue/lease evidence, stale recovery, latency, capacity
exhaustion, and deterministic/cognitive separation.

The handoff protocol requires validators to inspect actual changed files,
allowed paths, tests, runtime/persistence evidence, negative cases, identity/
provider/resource separation, and the five distinct status claims.

The campaign gates order design, contracts, policy/provider readiness, local
cognition, continuity/CME, and live proof.

## P. Scope discipline

Result: PASS.

GRC-003 explicitly excludes:

- final Grace model selection;
- final high-reasoning model selection;
- final GPU assignment;
- generalized GPU scheduling;
- Campaign Runner implementation;
- entire resident migration;
- new security framework;
- global provider-routing redesign;
- CME redesign;
- external credential provisioning;
- generalized population scheduling;
- UI/dashboard work.

The roadmap's P3/A3 shared-capacity work is the minimum required by GRC-002,
not a generalized scheduler.

Open Steward decisions are correctly recorded as deferred configuration rather
than invented implementation answers.

## Required corrections before implementation

### R1 — Complete F2 provenance field checklist

Add all GRC-002 section 9 fields, including model/resource IDs,
authoritative-state refs, validation refs, actor ID, and supersession lineage.

### R2 — Make dependency order authoritative

Resolve F1-F4/P1/E1/E4 dependency wording. Parallel preparation is acceptable;
implementation and acceptance must wait for frozen predecessor contracts.

### R3 — Name the durable F3/E5 persistence authority

Choose existing consultation/continuity persistence or one additive contract,
with exact fields and readback behavior. Do not leave the source of truth as a
package-owner choice during implementation.

## Future hardening

These are valid but not acceptance defects for GRC-003:

- final latency SLOs and fairness weights;
- full population scheduling;
- model benchmarking;
- preemption policy;
- production rollout;
- broader resident cognition migration;
- generalized provider-routing redesign;
- UI/dashboard improvements;
- complete external provider/credential governance;
- future artifact retention and redaction refinements beyond GRC-002's
  required bounded packet/provenance controls.

## Final validation conclusion

GRC-003 is a faithful and practical implementation decomposition of GRC-002.
It preserves the identity boundary, provider/resource neutrality, cognition
tiers, explicit escalation policy, bounded reasoning packets, durable
provenance intent, advisory authority, truthful failure behavior, bounded
continuations, CME ownership, and live acceptance strategy.

The roadmap is ready for implementation after the three localized required
non-blocking corrections above.

Implementation readiness: READY_FOR_GRC-004

