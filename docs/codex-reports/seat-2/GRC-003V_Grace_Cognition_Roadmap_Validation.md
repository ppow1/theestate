# GRC-003V — Grace Cognition Roadmap Validation

Package: GRC-003V  
Role: C2 — independent Grace implementation-roadmap validator  
Date: 2026-08-25  
Validation basis: GRC-002 and GRC-003 seat-3 report copies  
Verdict: PASS WITH REQUIRED NON-BLOCKING CHANGES

## 1. Validation scope and method

This validation reviewed both documents in full:

- docs/codex-reports/seat-3/GRC-002_Grace_Cognition_and_Escalation_Contract.md
- docs/codex-reports/seat-3/GRC-003_Grace_Cognition_Implementation_Decomposition.md

The repository source and test seams were inspected, including:

- Riverview/src/riverview/residents/runtime.py
- Riverview/src/riverview/residents/context.py
- Riverview/src/riverview/reasoning/contracts.py
- Riverview/src/riverview/reasoning/registry.py
- Riverview/src/riverview/river/events.py
- Riverview/src/riverview/river/store.py
- src/estate/core/grace_consultation_loop.py
- src/estate/core/governed_provider_scheduler.py
- src/estate/core/provider_capacity.py
- src/estate/core/provider_health.py
- src/estate/core/provider_routing_recommendations.py

The focused existing validation set passed:

55 passed in 6.07s

The executed set covered provider-neutral contracts, resident context/runtime
identity, Grace authority, consultation continuations, autonomous
reason/execute boundaries, and governed provider scheduling.

This report validates the roadmap. It does not claim any GRC-003 package is
implemented, live-accepted, or running.

## 2. Verdict summary

GRC-003 is a safe, complete, dependency-ordered, practically implementable
roadmap for beginning GRC-004 implementation. It preserves the accepted
GRC-002 architecture and does not require a giant rewrite before Grace can
become useful.

No blocking defect was found. In particular, the roadmap does not:

- couple Grace to a final model, endpoint, provider, or physical GPU;
- collapse Office, Occupant, Implementation, and State;
- permit deterministic CME behavior to masquerade as Grace cognition;
- grant high or external reasoning execution or acceptance authority;
- replace CME or Campaign Runner;
- make the initial implementation fundamentally single-resident;
- rely on browser/provider transcript state as authoritative memory; or
- omit live proof of actual configured runtime use.

Two required non-blocking corrections should be made before package handoff:

1. Correct the F1/F4 concurrency wording so F4 is not described as
   independently assignable before its stated F1 dependency is accepted.
2. Correct the E3 concurrency/dependency wording so external escalation is
   explicitly an alternate path that may be implemented from the common
   contracts without depending on the completed high-reasoning execution
   path. E3 may still reuse E2-compatible envelope shapes.

A minor consistency correction is also required in the same documentation
repair: A2 and A3 use “Tests/scenarios required” rather than the standard
“Tests required” package field. The content is present, but the label should
be normalized so package validators can consume one field vocabulary.

These corrections do not require a new architecture, package split, runtime
change, migration, model selection, or GPU decision.

## 3. Requirement-by-requirement validation

### 3.1 Identity preservation — PASS

GRC-003-F3 explicitly binds cognition turns to the existing occupant/office/
state and reuses ImplementationBinding, RuntimeSession,
ResidentImplementationRuntime, transition preflight, and context identity
anchors. Its tests require the same occupant across home/high/provider changes,
preserve predecessor implementation history, and reject wrong bindings.

F4 supplies the identity and authority context packet. E4 requires return to
the same occupant. The acceptance suite includes replacement continuity.

This establishes implementation work, not just an invariant statement. The
roadmap correctly keeps personality/context in bounded resident context rather
than treating a provider session as identity.

### 3.2 Truthful cognition attribution — PASS

GRC-003-F2 is the critical truth boundary. It requires actor class, resident,
occupant, office, cognition tier, implementation, provider, resource class,
request/correlation, policy, live_generation, status, and evidence references.
It explicitly requires deterministic events to use live_generation=false and
prevents deterministic events from serializing as Grace cognition.

GRC-003-I2 adds the no-generation/deterministic masquerade guard, external
claim guard, authority widening checks, and worker/validation/external actor
class regression tests. A1 includes the explicit no-masquerade acceptance case.

The roadmap also correctly distinguishes Grace home/high actor classes from
external advisory, worker execution, validation, and Steward decision classes.
This is consistent with GRC-002 and is sufficient to determine whether “Grace
decided” is truthful.

### 3.3 Bounded context — PASS

GRC-003-F4 reuses ResidentContextAssembler and ContextBundle and creates a
PacketProjector with relevance/omission reasons and a packet digest. Required
identity, office, authority, current state, task, evidence, constraints,
classification, contradictions, and source references are covered by F1/F4.

F4 explicitly rejects stale dependencies, policy-denied evidence, over-budget
packets, unresolved classification, and full transcript dumping. E2/E3 use the
packet rather than browser or provider history. E5 makes continuation state
durable and bounded.

The roadmap therefore meets the requirement without inventing an unbounded
memory or transcript architecture.

### 3.4 Provider neutrality — PASS

GRC-003-P2 is correctly capability/resource oriented. It defines
CognitionCapabilityRequest, TierBinding, ProviderResourceCandidate, filtering,
and configuration loading. Its acceptance criteria explicitly prohibit
hardcoded Grace-to-GPU/model logic.

E1, E2, and A2 keep model selection/configuration outside the cognition
orchestration path. The roadmap records the current closed GPU adapter as a
gap rather than treating it as the target architecture.

### 3.5 Escalation decision separation — PASS

GRC-003-P1 directly separates home_belief, policy_permitted, and
capacity_eligible. Its tests cover routine home decisions, difficult high
decisions, pointless escalation denial, ambiguity, classification denial,
Steward cases, and policy/capacity independence.

P2 and P3 own capability/resource eligibility and reservation separately.
E2 requires both an accepted home escalation and resource eligibility. The
roadmap does not treat Grace’s belief as permission or capacity as policy.

### 3.6 Home cognition — PASS

GRC-003-E1 provides a bounded HomeCognitionService, routine request
classification, home result validation, and latency/capacity observations.
It covers routine operation, monitoring/consultation, unavailable provider,
malformed output, deterministic non-generation, and identity preservation.

It does not select a final home model or GPU. The path is practical because it
can begin with deterministic fixture providers before live configuration.

### 3.7 High reasoning — PASS

GRC-003-E2 provides an explicit high request lifecycle, correlation, policy and
capacity separation, classification checks, timeout/deadline handling, and
no-silent-fallback behavior. E4 returns typed results to the same Grace
occupant and preserves advisory authority.

A1/A2 require routine non-escalation, intentional high escalation, result
return, busy/timeout behavior, and no execution authority. This meets the
high-reasoning requirement without selecting a 4090 model or resource.

### 3.8 External escalation — PASS

GRC-003-E3 reuses the provider-neutral advisory contract, classification
eligibility, GraceConsultationLoop, external provenance, continuation lineage,
and claim guards. It explicitly requires approval reference, egress validation,
unavailable outcome, and no fabricated external claim.

Its acceptance criteria preserve external/advisory attribution and normal
execution/acceptance paths. The package explicitly excludes automatic fallback,
credential provisioning, and provider approval decisions.

The dependency ordering correction noted in section 6 is required to make this
alternate path operationally clear, but the architecture itself is sound.

### 3.9 Resource/capacity abstraction — PASS

GRC-003-P2 prevents Grace from knowing physical topology. GRC-003-P3 reuses
ProviderCapacityRecord, health/capacity projections, reservation, lease expiry,
recovery, priority, and no-dispatch-on-reserve behavior.

P3 includes resident, occupant, tier, request, priority, fairness, resource
candidate, lease, queue, and release fields. It explicitly prohibits a full
future scheduler and permanent Grace ownership.

### 3.10 Other residents — PASS

The design remains resident-general. F3 uses occupant identity rather than
Grace-specific identity; P3 requires a Grace and another-resident simultaneous
demand fixture; A3 validates independent addressability, isolation, fairness,
and no permanent ownership.

The roadmap does not attempt full resident migration or population scheduling.

### 3.11 Continuations — PASS

GRC-003-E5 reuses logical root/child consultation IDs, bounded proposition
context, same-turn transport recovery, capacity holds, no-progress boundaries,
and Steward checkpoints. It explicitly rejects transcript-only context, new
roots for the same decision, duplicate physical attempts, and unbounded loops.

This is consistent with the existing consultation tests and does not make
browser/provider history authoritative memory.

### 3.12 Failure behavior — PASS

The package cards and A1/A2 cover home unavailable, high busy/unavailable/
timeout, external unavailable, capacity exhaustion, policy/classification
denial, malformed output, correlation mismatch, stale packet/context, and
identity mismatch.

The required outcomes are held, rejected, failed, unavailable, reassembled, or
Steward-escalated as appropriate. No package authorizes fabricated success or
silent downgrade. Existing focused tests independently prove related
capacity, correlation, continuation, and no-fabricated-completion seams.

### 3.13 Authority boundary — PASS

GRC-003-E4 explicitly prevents high/external results from silently executing or
accepting work. I2 reuses GraceAuthority, response validators, external claim
guards, execution classification, and provider failure states. Its tests cover
merge, acceptance, appointment, override, and prose bypass.

The roadmap correctly keeps reasoning advisory and uses normal structured
execution/dispatch paths.

### 3.14 CME integration — PASS

GRC-003-I1 is a bounded CognitionActivationAdapter. It maps cognition states
into CME waiting/blocked/escalated states, preserves leases/idempotency, and
requires unrelated-lane progress and deterministic transitions to remain
deterministic.

It explicitly leaves CME and Campaign Runner ownership intact and prohibits
blind continuation, a new scheduler, and provider bypass.

### 3.15 Package decomposition — PASS

The roadmap contains the requested package families:

- F1-F4 foundation;
- P1-P3 policy/resource;
- E1-E5 execution/return/continuity;
- I1-I2 operational/authority integration;
- A1-A3 acceptance/live proof.

Each package provides objective, dependencies, expected files/symbols, seams,
new components, persistence impact, tests, acceptance criteria, failure
conditions, validation evidence, and explicit non-goals. The package boundaries
are useful implementation units rather than artificial micro-packages.

The package count and scope are appropriate for independent Codex assignment.
No circular dependency was found in the dependency graph.

### 3.16 Concurrent implementation — PASS WITH REQUIRED CORRECTION

The report correctly states that concurrent seats require separate file/
contract ownership and forbids simultaneous edits to shared runtime modules,
migrations, provider registries, event schemas, or fixtures without an owner.
It correctly identifies P1/P2 and later E3/P3 work as separable by ownership.

Required non-blocking correction: section 4.2 lists “F1, F2, F3, and F4”
as concurrently assignable, while section 4.1 says F4 depends on F1. F4 may
be scaffolded or prepared concurrently, but implementation acceptance and
dependent work must wait for the accepted F1 contract. Change the wording to
state that F1 is a predecessor of F4, with only non-dependent preparation
allowed concurrently.

### 3.17 Acceptance and live proof — PASS

The roadmap clearly distinguishes Designed, Implemented, Tested,
Live-Accepted, and Running. A1 requires actual resulting code and negative
tests. A2 requires an actual configured provider call, request/response IDs,
resource evidence, event timeline, latency breakdown, packet digest, and
truthful failure behavior. A3 requires concurrent Grace/other-resident live
proof with identity-specific packets, capacity snapshots, leases, latency,
and cleanup.

The acceptance plan therefore does not mistake source presence or unit tests
for live operational use.

### 3.18 Practicality — PASS WITH REQUIRED CORRECTION

The staged path is practical: contracts/context/provenance first, policy and
capability next, deterministic fixture execution before live hardware, then
CME and live proof. It does not require a rewrite before the first useful home
path.

Required non-blocking correction: the dependency graph makes E3 depend on E2.
External escalation is an alternate path specifically needed when high
reasoning is unavailable. E3 may reuse the common F1/F2/F4/P1/P2 envelopes,
but its implementation should not require completed E2 execution. Change the
dependency to the common contracts and make E2/E3 parallel alternate
execution paths after those contracts are accepted. E4 should then depend on
both result shapes, not require E2 to be operational before E3 can proceed.

This is a sequencing correction, not an architectural defect.

## 4. Required non-blocking changes

### RNC-001 — Correct F4 concurrency statement

Severity: REQUIRED NON-BLOCKING  
Location: GRC-003 section 4.2, first concurrency bullet  
Requirement: dependency-correct concurrent assignment  
Issue: F4 is listed as concurrently assignable with F1 although F4 depends
on F1 in section 4.1.  
Why it matters: a Codex seat could begin against an unfrozen packet contract,
creating avoidable contract drift or write/reconciliation conflict.  
Minimum correction: state that F1 must be accepted before F4 implementation is
accepted; allow only non-dependent preparation/scaffolding in parallel.

### RNC-002 — Decouple E3 implementation readiness from E2 completion

Severity: REQUIRED NON-BLOCKING  
Location: GRC-003 sections 4.1 and 4.2  
Requirement: external escalation remains available when high reasoning is
unavailable.  
Issue: E3 depends on E2 even though E3 is an alternate advisory path.  
Why it matters: the campaign could unnecessarily delay the external path and
make the high path appear to be a prerequisite for the fallback/alternate
path, contrary to the explicit no-silent-fallback and high-unavailable
requirements.  
Minimum correction: make E3 depend on F1, F2, F4, P1, and P2/common result
contracts; permit E2 and E3 to proceed in parallel after shared contracts;
retain E4’s dependency on both result forms.

### RNC-003 — Normalize acceptance field label

Severity: REQUIRED NON-BLOCKING  
Location: GRC-003-A2 and GRC-003-A3 package cards  
Requirement: independently machine-checkable package template.  
Issue: these cards use “Tests/scenarios required” while all other cards use
“Tests required.”  
Why it matters: a package validator using the stated field vocabulary may
report a false omission.  
Minimum correction: rename the label to “Tests required” and retain the
scenario content.

## 5. Blocking-defect analysis

No blocking defect remains.

The following were specifically checked and passed:

- identity cannot be changed by provider/tier replacement;
- deterministic work has a non-generation actor/provenance path;
- home/high/external attribution is distinguishable;
- bounded packet contents and transcript exclusion are specified;
- capability/resource requests do not expose GPU topology to Grace;
- escalation belief, policy permission, and capacity are separate;
- no silent external fallback or protected-data transfer is authorized;
- high/external results remain advisory;
- malformed, stale, unavailable, denied, timed-out, and mismatched outcomes
  fail closed;
- CME mechanics remain CME-owned;
- package ownership/dependencies do not form a circular implementation plan;
- live acceptance includes actual configured provider/resource evidence.

## 6. Future hardening, not acceptance objections

These are legitimate later improvements and are not defects in GRC-003:

- exact home/high latency SLO values;
- detailed fairness weights and preemption policy;
- full resident-population scheduler;
- final model benchmark and model/resource configuration;
- broader protected-data retention policy;
- expanded live acceptance across more residents and resource classes.

GRC-003 correctly leaves these to later configuration, Steward decision, or
future resident infrastructure rather than blocking the first Grace campaign.

## 7. Validation conclusion

GRC-003 is safe to use as the implementation planning basis for GRC-004.
Its package boundaries are independently assignable and its acceptance plan is
strong enough to detect false attribution, identity corruption, authority
widening, silent fallback, and merely-present source code.

After the three documentation corrections in section 4, the roadmap is
READY_FOR_GRC-004. The current verdict is therefore:

PASS WITH REQUIRED NON-BLOCKING CHANGES

This validation does not claim GRC-004 implementation exists or that any Grace
cognition path is currently live.
