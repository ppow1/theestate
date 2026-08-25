# GRC-010 — Grace Cognition P2 Implementation

Package: GRC-010  
Roadmap package: GRC-003-P2 — Capability/resource request and binding adapter  
Role: C2 primary implementation writer  
Date: 2026-08-25  
Status: **IMPLEMENTATION_COMPLETE_READY_FOR_VALIDATION**

## 1. Exact P2 roadmap definition

### Title

**GRC-003-P2 — Capability/resource request and binding adapter**

### Purpose

Let Grace request `HOME_COGNITION`, `HIGH_REASONING`, or
`EXTERNAL_ESCALATION` capability without knowing physical GPU topology.

### Dependencies

- F1;
- the existing provider registry, capability, health, and capacity seams.

### Owned implementation seams

The roadmap assigns P2 a new resident cognition binding adapter; a narrow
extension to the reasoning registry only if tier/capability filtering is
missing; configuration schema/fixtures; and focused tests. It explicitly says
not to alter final model maps.

Reusable seams are `ReasoningProviderRegistry`, `ReasoningProvider`, provider
capability definitions, provider health/capacity, `CapabilityProfile`,
`ImplementationBinding`, and routing recommendation contracts. The roadmap
allows `CognitionCapabilityRequest`, `TierBinding`,
`ProviderResourceCandidate`, candidate filtering/eligibility, and a binding
configuration loader where required.

### Required tests/scenarios

- capability request independent of GPU;
- eligible/ineligible provider filtering;
- classification and health/capacity denial;
- model/provider replacement;
- no candidate;
- no physical topology access from Grace policy.

### Acceptance criteria

The caller specifies capability class and policy only; selection returns
candidates/evidence or a truthful unavailable result; there is no hardcoded
Grace-to-GPU/model logic; and provider replacement changes configuration,
not orchestration code.

### Non-goals

- final model benchmark;
- live GPU selection;
- queue implementation;
- resource ownership policy;
- provider invocation or reservation.

P2 has no P2-owned migration requirement. The roadmap says to define an
additive configuration/projection if needed but not create a migration in this
package.

## 2. Implemented behavior

Added a topology-neutral binding layer:

- `TierBinding` maps an F1 `CognitionTier` to a named capability class,
  policy reference, configuration reference, and optional abstract resource
  class reference.
- `BindingConfiguration` and `BindingConfigurationLoader` provide an
  immutable configuration projection. Physical topology keys and resident
  identity keys are rejected at load time.
- `CognitionBindingAdapter` accepts the existing F1
  `CapabilityResourceRequest`, verifies its tier/capability/policy against
  configuration, queries measured provider candidates, filters exclusions,
  classification, health, capacity, and capability, and returns either
  candidates with evidence references or a truthful `unavailable` decision.
- `ProviderResourceCandidate` is an observed candidate, not a selection,
  reservation, dispatch, or execution authority.
- `CapabilityBindingDecision.selected` is always `None`; P2 does not select or
  reserve a physical resource.

The existing `ReasoningProviderRegistry` gained `available_for`, which applies
PostgreSQL-side filtering for enabled, healthy, positive-capacity providers
with the requested capability, classification eligibility, and fresh
`observed_at` data. Ordering is deterministic by capacity and participant ID.

The existing F1 `CapabilityResourceRequest` was reused rather than creating a
competing request contract. No provider adapter, model map, GPU assignment,
queue, or runtime invocation was added.

## 3. Foundation integration/regression

### F1

**PASS.** P2 consumes the accepted `CapabilityResourceRequest` and
`CognitionTier` without modifying F1 contracts. The request retains resident,
occupant, office, implementation, authority, correlation, classification, and
policy identity. No provider/resource field becomes identity authority.

### F2

**PASS.** P2 emits no parallel provenance path and does not modify the F2
writer or event schema. Candidate evidence is bounded descriptive evidence for
the binding decision; it is not a cognition result or acceptance event.

### F3

**PASS.** No session code or session identity was changed. P2 does not derive
identity from a provider, model, endpoint, resource, or transcript.

### F4

**PASS.** P2 accepts the existing typed F1 request and does not assemble a
parallel context path. F4 remains the sole bounded packet/context boundary;
no packet, current-state, aggregate-context, or reference/value behavior was
changed.

## 4. Provider/resource behavior

**PASS — roadmap-defined behavior only.** Provider/resource behavior is
limited to configuration-driven capability binding and measured candidate
filtering. No OpenAI, ChatGPT, Codex, Ollama, fixed model, GPU, endpoint, or
physical-host assignment was introduced. Provider replacement is represented
by changing `BindingConfiguration`; adapter logic is unchanged.

The adapter never invokes a provider, selects a candidate, reserves
capacity, dispatches work, or grants execution authority.

## 5. Authority boundary

**PASS.** `CapabilityBindingDecision` is an advisory availability/candidate
projection. It contains no execution or acceptance authority and cannot turn a
candidate into a reservation or dispatch. Existing F1 authority references
are carried as request data only.

## 6. Persistence/restart

**NOT APPLICABLE for P2-owned state.** The adapter and configuration
projection are immutable/stateless and introduce no new authoritative record
or migration. Provider health/capacity remains supplied by the existing
durable `reasoning_providers` registry; `available_for` reads that existing
PostgreSQL state with freshness filtering. P2 does not claim a new persistence
system or in-memory state that must survive restart.

## 7. Determinism/idempotency

**PASS.** Equivalent requests and registry snapshots produce the same tier
binding and candidate projection. PostgreSQL candidate order is deterministic
by capacity descending and participant ID. The adapter performs no mutation,
reservation, or duplicate-producing operation, so repeated identical calls do
not create conflicting authoritative state.

## 8. Adversarial probes

The focused tests exercise:

- request and candidate projection without topology fields;
- disabled/unhealthy providers;
- zero capacity;
- capability mismatch;
- classification denial;
- provider exclusion;
- provider replacement through configuration only;
- no candidate and missing tier binding;
- GPU/model/endpoint/host configuration-key rejection;
- resident/occupant/office identity-key rejection;
- capability/policy mismatch without silent fallback.

No model or provider was invoked by these probes.

## 9. Tests

P2 focused tests: **6 passed**  
Integrated relevant F1/F2/F3/F4, resident context/runtime, provider-neutral,
authority, consultation, autonomous-loop, scheduler, and P2 tests:

```text
143 passed in 7.47s
```

`python -m compileall -q src tests`: **PASS**  
`git diff --check`: **PASS**

The broad unfiltered suite was not used as an acceptance claim; the known
environment lacks the optional `mcp` dependency for unrelated MCP test
collection.

## 10. Exact files/symbols changed

Implementation repository: `ppow1/Riverview`  
Branch: `codex/c484-operator-persistent-service`  
Implementation commit: `5fbb36625e564fab7a9a53650a7005f30c08d500`

Scoped files:

- `src/riverview/reasoning/binding.py`
  - `TierBinding`;
  - `BindingConfiguration`;
  - `BindingConfigurationLoader`;
  - `ProviderResourceCandidate`;
  - `CapabilityBindingDecision`;
  - `CognitionBindingAdapter`.
- `src/riverview/reasoning/registry.py`
  - `ReasoningProviderRegistry.available_for`.
- `src/riverview/reasoning/__init__.py`
  - public exports for the P2 adapter contracts.
- `tests/test_cognition_binding.py`
  - focused P2 contract and adversarial tests.

No migration was created. No Campaign Runner files were changed.

## 11. P1 collision assessment

**NONE after safe branch integration.** C1’s P1 commit advanced the shared
implementation branch while P2 was being developed. The P1 changes were
fetched and the P2 commit was rebased on top of them without conflict. P1’s
`escalation_policy.py`, policy tests, and F2 mixed-event reconstruction change
were preserved. P2 owns `binding.py`, the capability-filtering registry seam,
and its tests. The shared `reasoning/__init__.py` export file contains
additive imports for both packages; no incompatible symbol was overwritten.

## 12. RUN-004B collision assessment

**NONE.** No Campaign Runner or RUN-004B file, symbol, migration, fencing,
reconciliation, or lifecycle boundary was changed.

## 13. Remaining Grace roadmap packages

The next directly enabled package is:

- **GRC-003-P3 — Minimum shared-resident capacity reservation seam**, which
  depends on accepted P2 and existing provider capacity/bounded scheduler
  behavior.

The execution packages E1/E2/E3 remain gated by their stated accepted
dependencies, including P1/P2 and, where specified, F2/F4. P2 does not claim
P3, execution, integration, or live acceptance.

## 14. Readiness

The exact roadmap P2 implementation is complete, scoped tests and relevant
foundation regressions pass, and the implementation commit is published to the
shared implementation branch. C2 does not self-accept P2.

**READY_FOR_INDEPENDENT_VALIDATION**
