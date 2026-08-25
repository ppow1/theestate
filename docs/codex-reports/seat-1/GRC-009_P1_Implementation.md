# GRC-009 — Grace Cognition P1 Implementation

Package: GRC-009  
Roadmap package: GRC-003-P1  
Role: C1 primary implementation writer  
Status: `IMPLEMENTATION_COMPLETE_READY_FOR_VALIDATION`

## Exact authoritative P1 extraction

Title: **GRC-003-P1 — Escalation decision policy**

Purpose: separate home cognition’s belief that stronger reasoning would help,
policy permission to escalate, and capacity/resource ability to satisfy the
escalation.

Dependencies: accepted F1 and F4.

Owned seams: a new policy module under `src/riverview/reasoning`; policy
fixtures/tests; no direct provider-adapter edits. Reused F1
`EscalationAssessment`, `EscalationDecision`, bounded packet, River event, and
F2 provenance seams.

Required components/scenarios: assessment fields for
`home_belief`/`policy_permitted`/`capacity_eligible`, consequence/risk
categories, policy version, explicit outcomes, and a deterministic-versus-
cognition boundary. Required scenarios include routine home decision,
difficult decision requiring high reasoning, pointless escalation denial,
consequential ambiguity refusal, external classification denial,
Steward-required authority, and policy/capacity independence.

Acceptance: home belief alone cannot reach a provider; policy and capacity are
separately evaluated; empty eligibility is truthful; no silent downgrade.

Failure conditions: missing policy, unknown consequence class, missing
authority envelope, ambiguous decision class, or capacity treated as policy.

Non-goals: provider scheduling, model invocation, hardware choice, and changes
to Steward authority. P2 and later execution packages remain out of scope.

## Implementation

Added `src/riverview/reasoning/escalation_policy.py`:

- `ConsequenceClass` — bounded routine, difficult, consequential ambiguity,
  protected boundary, and unknown classes;
- `CapacitySnapshot` — capability-class eligibility only, not a reservation or
  scheduler;
- `EscalationPolicy.evaluate` — deterministic evaluation of separate home
  belief, policy permission, and capacity facts;
- `PolicyDecisionRecorder` — immutable River/F2 policy-decision event with
  policy version, decision, reason class, request/correlation/causation, and
  the typed assessment payload;
- `PolicyInputError` and policy constants/version.

The policy consumes the accepted bounded `ResidentReasoningPacket`. It does
not assemble parallel context, invoke cognition, select a provider, reserve a
resource, or grant execution authority.

Decision behavior:

- routine with no home escalation belief → `DETERMINISTIC`;
- difficult with home belief and high capacity →
  `HIGH_REASONING_REQUIRED`;
- difficult with home belief and no high capacity →
  `CAPACITY_UNAVAILABLE`, retaining the high target and never silently
  downgrading;
- no home belief → home/deterministic outcome with no escalation target,
  regardless of available capacity;
- consequential ambiguity, protected boundary, and unknown class →
  `STEWARD_REQUIRED`;
- external classification outside configured eligibility → `POLICY_DENIED`,
  independently of external capacity.

## F2 integration and persistence

`PolicyDecisionRecorder` writes `cognition.policy_decided` as a River event on
the `cognition_request` aggregate. The event includes the explicit policy
version (`grace-escalation-policy-p1-v1`), decision outcome, three separate
booleans, consequence class, typed assessment, correlation, and causation.

The existing F2 provenance reconstruction was minimally extended to select
only the accepted F2 provenance schema from a mixed cognition-request
aggregate. This allows P1 policy facts to coexist with canonical request
lineage without attempting to parse a policy payload as an F2 provenance
record.

No migration was required; River persistence already supports the event.

## F1–F4 preservation

- F1: policy assessments are built from the bounded packet and preserve
  resident/occupant/office/implementation/authority/current-state references;
  no alternate cognition contract or provider identity was introduced.
- F2: policy events carry request correlation/causation and policy version;
  canonical request reconstruction remains intact, including mixed-event
  readback.
- F3: no session code or session identity was changed.
- F4: policy accepts only `ResidentReasoningPacket` input, so the accepted
  resident correspondence, meaningful current state, aggregate bound,
  deterministic assembly, and reference/value boundary remain upstream
  requirements.

Provider neutrality: **PASS**. No provider, model, endpoint, GPU, or hardware
assignment is selected or named.

Authority boundary: **PASS**. All outcomes are advisory policy decisions;
Steward-required outcomes remain blocked and no decision grants execution,
acceptance, merge, or canonical mutation authority.

## Files and symbols changed

Implementation repository scoped files:

- `src/riverview/reasoning/escalation_policy.py`
- `src/riverview/reasoning/__init__.py`
- `src/riverview/reasoning/provenance.py` — mixed F2 aggregate reconstruction
  compatibility filter
- `tests/test_escalation_policy.py`

No P2-owned registry/provider/resource files were changed. No Campaign Runner,
Grace execution, model, GPU, migration, or later-package files were changed.

## Tests and evidence

P1 policy tests cover:

- routine deterministic decision;
- difficult high-reasoning decision;
- capacity-unavailable truthful block and no downgrade;
- pointless escalation denial;
- consequential/protected/unknown Steward-required paths;
- external policy denial by classification;
- missing/unknown input and authority fail-closed behavior;
- policy event version/outcome persistence;
- event readback after store recreation;
- coexistence with F2 canonical request lineage.

Focused P1 plus provenance tests: **39 passed**.  
Relevant integrated F1/F2/F3/F4, resident-context, authority, provider, and
P1 selection: **127 passed**.  
Compile/import validation: **PASS**.  
Scoped `git diff --check`: **PASS**.

A real PostgreSQL `EventStore` smoke test appended a canonical F2 request and
P1 policy event, read back two aggregate events, found one policy event, and
reconstructed one canonical F2 request record successfully.

The unfiltered repository suite remains unable to collect three unrelated MCP
test modules because the environment lacks the optional `mcp` package. This
does not affect the clean relevant suite or P1 implementation evidence.

## P2 collision assessment

**NONE.** P1 owns the new policy module and policy tests. P2’s provider/capacity
binding seams were not modified. The only shared change is the narrowly
required F2 mixed-event reconstruction filter needed to persist policy facts on
the existing cognition-request River aggregate.

## Remaining roadmap packages

GRC-003-P2 remains independently eligible and was not implemented. The later
execution, integration, and acceptance packages remain gated on their stated
dependencies.

This implementation is ready for independent validation; C1 does not accept
GRC-009.

