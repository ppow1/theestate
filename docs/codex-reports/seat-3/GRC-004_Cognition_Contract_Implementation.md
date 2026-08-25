# GRC-004 — Cognition Contract Implementation

Package: GRC-004  
Role: C3 primary implementation writer  
Implementation status: IMPLEMENTATION_COMPLETE_READY_FOR_VALIDATION  
Date: 2026-08-25  
Basis: GRC-002, repaired GRC-003, and GRC-003V

## 1. Result

Implemented GRC-003-F1 as an additive, provider-neutral cognition contract
layer. The implementation defines machine-validatable contracts for cognition
tiers, bounded resident reasoning packets, separate escalation assessment,
capability/resource requests, advisory reasoning results, truthful failure
outcomes, and provenance references.

No provider was invoked by the new contracts. No home/high/external runtime,
resource scheduler, CME integration, context assembly, River event emission,
or live acceptance path was implemented.

## 2. Files changed

Implementation:

- Riverview/src/riverview/reasoning/cognition_contracts.py
- Riverview/src/riverview/reasoning/__init__.py

Tests:

- Riverview/tests/test_cognition_contracts.py

Report:

- docs/codex-reports/seat-3/GRC-004_Cognition_Contract_Implementation.md

Existing provider-neutral positional contracts in
Riverview/src/riverview/reasoning/contracts.py were preserved. Existing
ReasoningRequest, ReasoningResponse, adapters, gateway consumers, and runtime
consumers remain compatible.

## 3. Contracts and symbols introduced

The new bounded module introduces:

- CognitionTier: HOME_COGNITION, HIGH_REASONING, EXTERNAL_ESCALATION;
- EscalationDecision;
- CognitionResultStatus;
- CognitionActorClass;
- CognitionFailureCode;
- ResidentReasoningPacket;
- EscalationAssessment;
- CapabilityResourceRequest;
- CognitionResult;
- ReasoningResult compatibility alias.

Each typed contract exposes as_typed_payload and from_typed_payload. Payload
deserialization requires the versioned cognition contract identifier
riverview-cognition-f1-v1 and reconstructs typed UUID, enum, datetime, tuple,
classification, bound, and authority values through the same fail-closed
validation.

## 4. Validation behavior

ResidentReasoningPacket validates:

- packet, resident, occupant, office, correlation, source-context, and
  causation identity references;
- authority reference, request class, objective, and exact question bounds;
- bounded operational-state/evidence references and constraints;
- accepted classification;
- SHA-256-shaped packet digest;
- future expiry;
- contract version;
- absence of any unrestricted transcript field.

EscalationAssessment validates separately:

- home belief and reason;
- policy permission and reason;
- capacity eligibility and reason;
- target cognition tier;
- decision/reason class;
- policy reference;
- classification, correlation, creation, and expiry.

Policy denial cannot be serialized as an executable escalation decision.
Stronger cognition cannot be targeted when home cognition did not express the
belief that it is needed.

CapabilityResourceRequest validates:

- resident/occupant/correlation identity;
- requested cognition tier and capability class;
- classification, policy, and authorization references;
- bounded optional priority, deadline, latency requirement, exclusions, and
  constraints.

Its payload contains no GPU ID, model name, endpoint, provider hostname, or
physical device ownership field. Resource binding remains a later package.

CognitionResult validates:

- request/correlation/resident/occupant identity;
- cognition tier, actor class, and status;
- bounded recommendation, rationale, uncertainty, constraints, and unresolved
  questions;
- confidence range and further-escalation indicator;
- provider/resource-class, packet, policy-decision, and provenance references;
- live_generation truth;
- accepted classification;
- timestamps and optional expiry;
- advisory-only authority scope;
- failure code/reason for every non-success status.

Completed results require recommendation and rationale. Non-success results
cannot claim live generation and require a truthful failure code and reason.
Deterministic substrate results cannot claim live generation. Home/high/external
actor classes must match their corresponding cognition tiers. The
validate_against method rejects request/result correlation, tier, resident,
occupant, packet, or classification mismatches.

No reasoning result can carry execution authority: authority_scope is closed
to read:bounded, return:advisory, and return:diagnostic.

## 5. Compatibility decisions

The existing ReasoningProvider, ReasoningRequest, and ReasoningResponse classes
are used by current adapters and consumers through positional construction.
They were not casually reshaped. The new resident-facing F1 contracts are
additive and exported from riverview.reasoning.

ReasoningResult is an alias for CognitionResult to provide a stable semantic
name for later packages without duplicating result behavior.

The new module reuses the existing classification vocabulary, reference bound,
bounded-text validation, and provider-neutral package conventions. It does not
call a provider, inspect hardware, or alter existing provider registration.

## 6. Tests added and tests run

Added:

- Riverview/tests/test_cognition_contracts.py

The focused suite covers:

1. valid home, high, and external tiers;
2. unknown tier rejection;
3. required resident/correlation identity;
4. packet bounds and transcript-surface rejection;
5. provider/resource replacement preserving resident identity;
6. separate home-belief, policy, and capacity decisions;
7. topology-neutral capability request;
8. valid home/high/external advisory results;
9. missing rationale and authority widening;
10. unavailable, timeout, policy-refused, and capacity-unavailable outcomes;
11. correlation, tier, classification, and resident mismatch;
12. expired packet/request;
13. deterministic live-generation rejection;
14. contract version and identity-preserving serialization/deserialization.

Command executed:

PYTHONPATH=Riverview/src;src python -m pytest -q Riverview/tests/test_cognition_contracts.py Riverview/tests/test_provider_neutral_contracts.py Riverview/tests/test_resident_context.py Riverview/tests/test_resident_runtime.py Riverview/tests/test_grace_authority.py tests/test_grace_consultation_loop.py tests/test_autonomous_reason_execute_loop.py tests/test_governed_provider_scheduler.py

Result:

73 passed in 4.77s

Python compileall also passed for the Riverview reasoning source and new
focused test. Ruff was not installed in the environment and therefore was not
claimed as run.

## 7. Provider neutrality evidence

Status: PASS for GRC-004 scope.

The cognition tier vocabulary contains only capability classes. The capability
request contains required_capability, tier, policy, classification, priority,
deadline/latency, exclusions, and constraints. It has no physical GPU,
model-name, endpoint, provider-hostname, or device-ownership field.

The new module contains no final model assignment, GPU binding, endpoint, or
Grace-specific provider route. Concrete provider/resource binding is deferred
to GRC-003-P2 and later implementation packages.

## 8. Identity preservation evidence

Status: PASS for GRC-004 scope.

All resident-facing packet/request/result contracts carry resident_id and
occupant_id separately from cognition_tier, provider_ref, resource_class_ref,
implementation-independent packet identity, and provenance references.

The tests construct replacement results with changed provider/resource-class
references and assert unchanged resident and occupant IDs. Tier/provider
changes do not mutate office or occupant fields. No contract treats provider,
model, endpoint, resource, or session as resident identity.

## 9. Authority boundary evidence

Status: PASS for GRC-004 scope.

CognitionResult authority_scope is closed to advisory/read/diagnostic values.
Execution is not an accepted authority value. Completed high and external
results carry advisory scope and actor attribution. Authority-widening values
are rejected. This package does not add execution authorization fields and
does not connect results to dispatch, acceptance, merge, or Steward authority.

## 10. Deferred work

Deferred to GRC-003-F2:

- full River event emission, durable event persistence, event lifecycle, and
  provenance event reconciliation.

Deferred to GRC-003-F3:

- cognition sessions and runtime implementation transitions.

Deferred to GRC-003-F4:

- assembly of packets from live resident context sources.

Deferred to GRC-003-P1:

- execution of escalation policy and home-belief/policy/capacity orchestration.

Deferred to GRC-003-P2:

- provider/resource candidate binding and configuration.

Deferred to E1/E2/E3:

- home generation, high-reasoning execution, and external advisory runtime.

Deferred to E4/E5:

- result integration and bounded consultation continuations.

Deferred to I1/I2:

- CME activation and cross-system authority/provenance guards.

Deferred to A1/A2/A3:

- fixture integration, live provider/resource proof, shared-resident live
  acceptance, and final live/running status.

## 11. Known limitations

This package validates typed envelopes and their local serialization boundary.
It does not prove a provider call, model residency, resource capacity,
runtime routing, live generation, River persistence, or running Grace
cognition. Those statuses remain DESIGNED/IMPLEMENTED/TESTED only for the
contract layer until later packages and independent validation establish the
corresponding evidence.

## 12. Scope confirmation

- No provider execution implemented.
- No home cognition runtime implemented.
- No high-reasoning execution implemented.
- No external escalation runtime implemented.
- No resource scheduling implemented.
- No CME integration implemented.
- No migration created.
- No model selected.
- No GPU assigned.
- No endpoint/provider hardcoded for Grace.
- No unrelated runtime behavior changed.

IMPLEMENTATION_COMPLETE_READY_FOR_VALIDATION
