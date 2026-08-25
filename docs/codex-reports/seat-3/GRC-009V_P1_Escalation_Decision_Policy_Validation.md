# GRC-009V — P1 Escalation Decision Policy Validation

Package: GRC-009V  
Roadmap package: GRC-003-P1 — Escalation decision policy  
Role: C3 independent implementation validator  
Implementation commit: `62b6ce0c5b51ff22e7ac2adf46d822b5fda03619`

## Verdict

**FAIL — BLOCKING DEFECTS REMAIN**

The deterministic policy behavior itself is substantially correct, but the
durable P1 event writer permits a policy decision to be attached to an
arbitrary cognition request. This creates false P1/F2 provenance and violates
the roadmap requirement that the decision remain correlated to the originating
bounded cognition context.

## Authoritative P1 contract

GRC-003-P1 separates three facts: home cognition’s belief that stronger
reasoning would help, policy permission, and capacity/resource eligibility. It
depends on accepted F1 and F4; it owns a new reasoning policy module and
fixtures/tests, persists policy version and decision outcome through F2 events,
and creates no migration. Required scenarios include routine home handling,
difficult high reasoning, pointless escalation denial, consequential ambiguity
and Steward-required cases, external classification denial, and policy/capacity
independence. P1 must not select providers/resources, invoke models, schedule
capacity, or grant execution authority.

## Source and implementation inspected

The implementation commit adds `reasoning/escalation_policy.py`, exports it
through `reasoning/__init__.py`, minimally extends `reasoning/provenance.py`
for mixed-event reconstruction, and adds `tests/test_escalation_policy.py`.
No P2-owned provider/resource files were changed. The policy consumes a typed
F1 `ResidentReasoningPacket`, creates typed `EscalationAssessment`, and records
`cognition.policy_decided` through the existing River event shape.

## Independent results

Focused P1, F1 cognition-contract, F2 provenance, and provider-neutral suites:
**65 passed** on the exact implementation commit. Compile/import validation:
**PASS**. The writer-reported integrated suite and PostgreSQL EventStore smoke
were consistent with the inspected code, but the provenance correspondence
probe below exposed a missing negative boundary not covered by those tests.

### Determinism and required decisions

**PASS for decision semantics.** Repeated equivalent evaluations produce the
same decision class. The policy truth table correctly distinguishes:

- routine with no home belief → `DETERMINISTIC`;
- difficult with home belief and eligible high capacity →
  `HIGH_REASONING_REQUIRED`;
- difficult with home belief and unavailable high capacity →
  `CAPACITY_UNAVAILABLE`, without downgrade;
- no home belief → no escalation despite available capacity;
- consequential ambiguity, protected boundary, or unknown class →
  `STEWARD_REQUIRED`;
- external classification outside the configured set → `POLICY_DENIED`.

The envelope contains generated IDs and timestamps, so the full object is not
byte-deterministic without supplied `now` and `assessment_id`; this did not
alter the decision result in the exercised cases.

### Fail-closed input handling

**PASS.** Unknown consequence/tier, empty home-belief reason, missing
authority through the F1 constructor, naive timestamps, expired packets, and
invalid capacity booleans are rejected or fail closed. Capacity is not treated
as policy permission.

### Identity and authority

**PASS for policy evaluation.** The assessment copies resident, occupant,
office, implementation, authority, packet, source-event, objective, and
correlation fields from the typed packet. Transcript/prose is not an input
authority seam. Policy outcomes are advisory and do not contain execution
authorization. No identity or authority mutation was found.

### Provider neutrality and P2 separation

**PASS.** No provider, model, endpoint, GPU, or hardware identity is selected
or hardcoded. `CapacitySnapshot` reports capability-class eligibility only; it
does not reserve or allocate a physical resource. No P2 adapter ownership was
modified.

## Blocking defect: durable request correspondence

### Exact location

`src/riverview/reasoning/escalation_policy.py`,
`PolicyDecisionRecorder.record()`.

### Reproduction

An independently evaluated assessment was recorded with a fresh unrelated
`request_id`:

```text
assessment packet/source/correlation: valid packet P
record(request_id=unrelated UUID)
observed: one cognition.policy_decided event persisted under unrelated UUID
expected: rejection before persistence, or verified correspondence to the
canonical cognition request
```

The probe output was:

```text
UNRELATED_REQUEST_ACCEPTED 1 True <assessment packet id>
```

### Root cause

`record()` validates only that its separately supplied `request_id` is a UUID.
`EscalationAssessment` carries packet/source/correlation and resident identity,
but the writer does not load the canonical F2 request or otherwise prove that
the supplied aggregate request identity corresponds to those fields. The
event is then constructed with `aggregate_id=request_id`, arbitrary caller
`request_id` payload, and caller-overridable `causation_id`.

### Why this blocks acceptance

P1 is required to persist its policy decision through F2/River lineage. A
caller can therefore create a plausible policy event under request B from an
assessment derived from request A. This makes source → request/context →
policy-decision lineage false and prevents trustworthy reconstruction. The
defect is at the durable writer boundary; caller-side discipline or the happy
path test is insufficient.

### Minimum correction

Make the recorder enforce exact correspondence before `EventStore.append`:
load and validate the canonical F2 request for the target request identity,
verify the assessment’s resident/occupant/office/implementation/authority,
packet/source-event, correlation, classification, and tier fields against the
stored request as applicable, and reject missing, malformed, stale, or
mismatched lineage. Causation must retain its correlation/causation distinction
and must not become an unchecked alternate lineage. Add a negative durable
test asserting the aggregate remains unchanged after the mismatch.

## Persistence/restart and F2 integration

**FAIL for P1 as a whole because of the blocking correspondence defect.** The
existing River/EventStore path is reused and the mixed-event reconstruction
filter is compatible with canonical F2 records. The tested event survives the
in-memory recreation and the writer report includes a PostgreSQL smoke test,
but persistence of a falsely attached event is not acceptable persistence
proof. A clean PostgreSQL revalidation must include the mismatch rejection and
restart lineage checks after repair.

## Regression assessment

- F1 regression: **PASS** — focused F1 contract suite passed; policy consumes
  the bounded packet and does not create a parallel context path.
- F2 regression: **FAIL** — canonical F2 mechanics remain present, but P1’s
  durable event writer bypasses exact request correspondence.
- F3 regression: **PASS** by source/suite scope; no session code changed.
- F4 regression: **PASS** by source/suite scope; P1 requires the typed bounded
  packet and does not bypass assembly.
- Transcript-not-authority: **PASS**.
- Provider neutrality: **PASS**.
- Authority boundary: **PASS**.
- P1/P2 separation: **PASS**.

## Acceptance disposition

P1 remains **REPAIR_REQUIRED**. The defect is narrow and does not require a new
architecture, P2 changes, or F1–F4 redesign. Independent revalidation should
repeat the exact unrelated-request probe, identity/source mismatch variants,
aggregate-unchanged assertions, valid request persistence/reload, and the
existing 65-test focused suite.

Next roadmap packages: P2 exists as a separate implementation and requires its
own independent validation. P1 acceptance is not granted and does not unlock
downstream execution packages.
