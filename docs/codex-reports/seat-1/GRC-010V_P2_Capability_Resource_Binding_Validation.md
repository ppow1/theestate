# GRC-010V — P2 Capability/Resource Binding Adapter Validation

Package: GRC-010V  
Roadmap package: GRC-003-P2 — Capability/resource request and binding adapter  
Role: C1 independent implementation validator  
Implementation commit: `5fbb36625e564fab7a9a53650a7005f30c08d500`

## Verdict

**PASS**

The implementation satisfies the authoritative P2 contract: Grace supplies a
capability class and policy, the adapter returns eligible observed candidates
or a truthful unavailable result, and no physical resource is selected,
reserved, dispatched, or made authoritative.

## Repository and scope verification

The implementation commit was independently verified in
`ppow1/Riverview`, branch `codex/c484-operator-persistent-service`.
The report was independently read from `ppow1/theestate` branch
`codex/riverview-bounded-doorbell`.

Scoped implementation files are:

- `src/riverview/reasoning/binding.py`;
- `src/riverview/reasoning/registry.py`;
- `src/riverview/reasoning/__init__.py`; and
- `tests/test_cognition_binding.py`.

No migration, Campaign Runner file, P1 policy file, model map, provider
invocation, queue, reservation, or scheduler implementation was added.

## Authoritative P2 compliance

The roadmap defines P2 as a capability/resource request and binding adapter.
Its objective is to let Grace request `HOME_COGNITION`, `HIGH_REASONING`, or
`EXTERNAL_ESCALATION` without knowing physical GPU topology. P2 depends on F1
and existing provider registry/capability/health/capacity seams. It explicitly
excludes final model choice, live GPU selection, queue implementation, and
resource ownership policy.

The implementation consumes the existing F1 `CapabilityResourceRequest` and
maps its `CognitionTier` through immutable `TierBinding` configuration. It
filters measured provider candidates through the existing registry and returns
`CapabilityBindingDecision` with candidates/evidence or `unavailable`.

P2 roadmap compliance: **PASS**

## Independent probe results

I independently exercised the actual adapter and contracts, beyond rerunning
the reported tests:

- valid typed request plus eligible candidate: **PASS**;
- capability mismatch: **REJECTED / unavailable**;
- policy/binding mismatch: **REJECTED / unavailable**;
- request identity/correlation preserved in the decision: **PASS**;
- malformed request object: **FAIL CLOSED**;
- unhealthy and zero-capacity candidate construction: **FAIL CLOSED**;
- duplicate tier binding: **FAIL CLOSED**;
- physical topology configuration key: **FAIL CLOSED**;
- resident identity configuration key: **FAIL CLOSED**;
- candidate data containing forged authority/transcript-like fields: ignored
  and unable to change structured request identity: **PASS**.

The adapter has no input path for arbitrary request A plus binding B beyond
the tier/capability/policy correspondence checks. A binding for another tier,
capability, or policy produces unavailable rather than fallback.

## Capability request and resource binding

`TierBinding` requires a supported cognition tier, capability name, policy
reference, and configuration reference. `BindingConfiguration` requires
nonempty unique tier bindings. The adapter requires the request to be the
typed F1 request, validates freshness-bound input, and requires request
capability and policy to match the configured tier binding.

`ProviderResourceCandidate` validates provider/participant metadata, healthy
status, positive measured capacity, and bounded fields. The registry’s
`available_for` query additionally requires enabled providers, healthy state,
positive capacity, eligible classification, requested capability, and fresh
observations. Ordering is deterministic by capacity descending and participant
ID.

Resource binding: **PASS**  
Request/binding correspondence: **PASS**

## Identity and authority boundaries

The P2 decision retains only request ID, correlation ID, cognition tier, policy
reference, status, reason, and observed candidates. It does not replace or
derive resident, occupant, office, implementation, session, or authority
identity. The configuration loader explicitly rejects resident/occupant/office
identity keys, and candidate/provider metadata is not treated as identity.

The adapter exposes `selected` as permanently `None`. It has no reservation,
lease, dispatch, execution, acceptance, or authority-granting operation.
Caller-supplied candidate metadata cannot create execution or resident
authority.

Identity preservation: **PASS**  
Authority boundary: **PASS**

## Provider/resource behavior and P3 boundary

Provider neutrality does not mean inability to represent concrete observed
providers. P2 accepts provider/resource observations from the registry and
returns them as candidates, while Grace-facing configuration names capability
and abstract resource classes rather than GPU/model/endpoint topology.

The source contains no hardcoded OpenAI, ChatGPT, Codex, Ollama, model,
endpoint, host, GPU, or physical assignment. Physical topology keys are
rejected in binding configuration. Provider replacement changes configuration
and candidate data, not adapter orchestration.

P2 does not reserve capacity: it neither mutates provider capacity nor creates
leases, queue entries, ownership, fairness, or release state. This is the
correct P3 boundary. P3 owns the minimum shared-resident reservation seam.

Provider/resource behavior: **PASS**  
P3 boundary: **PASS**

## Determinism, idempotency, malformed input, and transcript boundary

Equivalent immutable configuration, request, and catalog snapshots produce the
same tier binding and deterministic candidate ordering. The adapter is
read-only and repeated calls cannot create duplicate bindings or reservation
state. Equivalent exclusion and replacement cases behaved deterministically.

Missing configuration, unsupported tier, malformed tier data, invalid health
or capacity, missing capability, stale observations, classification denial,
and conflicting request/configuration fields fail closed or return truthful
`unavailable`.

No transcript or model-output field participates in request identity,
capability identity, resource binding, or authority. Unknown extra data cannot
become a binding decision through the adapter.

Determinism/idempotency: **PASS**  
Malformed/ambiguous input: **PASS**  
Transcript/model-output boundary: **PASS**

## P1/P2 separation

P1 remains the escalation decision policy. P2 consumes a capability request and
its policy reference; it does not evaluate whether escalation is permitted,
rewrite a policy decision, select a provider, or invoke cognition. P1 does not
need to perform P2 binding. The implementation diff owns binding/resource files
and the additive registry filter only.

P1/P2 separation: **PASS**

## Persistence/restart

Persistence/restart for new P2-owned state is **NOT APPLICABLE**. The adapter
and `BindingConfiguration` are immutable/stateless projections; P2 creates no
authoritative binding record, migration, reservation, or in-memory state that
must survive restart. Existing durable provider health/capacity is read by the
registry’s `available_for` query. Restart therefore reconstructs the same P2
projection from configuration plus the existing provider registry rather than
from a new P2 persistence mechanism.

## F1–F4 regression

The relevant accepted regression command passed across:

- P2 binding tests;
- F1 cognition contracts;
- F2 provenance and correspondence repair;
- F3 cognition session;
- F4 bounded packet and current-state repair;
- provider-neutral contracts; and
- Grace authority tests.

F1 regression: **PASS**  
F2 regression: **PASS**  
F3 regression: **PASS**  
F4 regression: **PASS**

Compile/import validation: **PASS**.  
`git diff --check`: **PASS**.

## Test evidence

Focused P2 suite:

```text
tests/test_cognition_binding.py — 6 passed
```

The integrated relevant F1–F4/provider/authority command completed with all
tests passing. Independent adversarial probes also passed for valid binding,
mismatch rejection, malformed input, duplicate binding, forbidden topology or
resident keys, identity preservation, authority isolation, and no-selection/
no-reservation behavior.

## Next roadmap packages

The authoritative dependency graph states:

- P3 depends on accepted P2 and existing provider capacity/bounded scheduler
  behavior;
- E1 depends on F1, F3, P1, and P2;
- E2 depends on F1, F2, F4, P1, and P2;
- E3 depends on F1, F2, F4, P1, and P2, and is parallel with E2.

Therefore the directly next capacity package is:

**GRC-003-P3 — Minimum shared-resident capacity reservation seam**.

The dependency graph also makes **GRC-003-E1, GRC-003-E2, and GRC-003-E3**
eligible once their stated accepted prerequisites are confirmed; E2 and E3
are parallel alternate execution paths. This validation does not implement
any of them.

P2 acceptance: **ACCEPTED**  
Grace implementation readiness: **READY_FOR_NEXT_GRC_PACKAGE**
