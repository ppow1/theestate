# GRC-004V — Grace Cognition Foundation F1 Contract Validation

## Verdict

**FAIL — BLOCKING DEFECTS REMAIN**

GRC-004 is provider-neutral and has useful fail-closed/advisory safeguards, but
the implemented F1 contract does not expose the complete stable contract
required by GRC-002 and GRC-003. In particular, the resident reasoning packet,
escalation assessment, and result envelope omit required identity, provenance,
state, and bounded-context fields. F4 would therefore have to invent or
redefine core F1 semantics. That makes the implementation unsafe to accept as
the foundation for dependent packages.

This verdict is based on the actual source and tests at Riverview commit
`4e4d67c10cf956160d0478bf1b513f3a69383528`, not on the implementation report's
claims.

## Evidence inspected

- Design contract: `docs/codex-reports/seat-3/GRC-002_Grace_Cognition_and_Escalation_Contract.md`
- Repaired roadmap: `docs/codex-reports/seat-3/GRC-003_Grace_Cognition_Implementation_Decomposition.md`
- Roadmap validation: `docs/codex-reports/seat-2/GRC-003V_Grace_Cognition_Roadmap_Validation.md`
- Roadmap repair: `docs/codex-reports/seat-3/GRC-003R_Grace_Cognition_Roadmap_Repair.md`
- Implementation report: `docs/codex-reports/seat-3/GRC-004_Cognition_Contract_Implementation.md`
- Implementation: `Riverview/src/riverview/reasoning/cognition_contracts.py`
- Implementation tests: `Riverview/tests/test_cognition_contracts.py`
- Existing adjacent tests: provider-neutral contracts, resident context/runtime,
  Grace authority, CME recovery, autonomy control, consultation loop,
  autonomous reason/execute loop, and governed provider scheduler.

The implementation repository and report repository are separate but have
clear ownership boundaries: contract source/tests are in the nested Riverview
repository, while the implementation report is in the Estate repository and
identifies the exact source paths, branch, and commit. This split is
structurally coherent and is not itself a validation defect.

## Repository and commit verification

### Implementation repository

- Repository: `ppow1/Riverview`
- Branch: `codex/c484-operator-persistent-service`
- Local HEAD: `4e4d67c10cf956160d0478bf1b513f3a69383528`
- `origin/codex/c484-operator-persistent-service`:
  `4e4d67c10cf956160d0478bf1b513f3a69383528`
- Commit subject: `Implement Grace cognition foundation contracts`

The reported implementation source and tests exist in that commit.

### Report repository

- Repository: `ppow1/theestate`
- Branch: `codex/riverview-bounded-doorbell`
- HEAD: `93217f6f3effd7ac5b8b1f218d9a73ee1707127b`
- `origin/codex/riverview-bounded-doorbell`:
  `93217f6f3effd7ac5b8b1f218d9a73ee1707127b`

## Blocking findings

### B1 — ResidentReasoningPacket is not the complete GRC-002 bounded packet

- **Severity:** BLOCKING DEFECT
- **Location:** `Riverview/src/riverview/reasoning/cognition_contracts.py`,
  `ResidentReasoningPacket` (around lines 156–240); GRC-003 F1 and F4
  acceptance requirements.
- **Requirement violated:** GRC-002 Section 6 requires a typed packet carrying
  resident/occupant/office identity, source cognition event, objective and
  correlation, exact question, authoritative current state, constraints,
  relevant evidence, unresolved ambiguity, relevant prior decisions, known
  deterministic results, home assessment, requested output schema,
  classification, egress policy, expiry, and max budget. GRC-003 F4 depends on
  F1 to project this bounded context without redefining it.
- **Evidence:** The actual packet fields are `packet_id`, `resident_id`,
  `occupant_id`, `office_id`, `authority_ref`, `cognition_tier`,
  `request_class`, `objective`, `question`, `operational_state_refs`,
  `evidence_refs`, `constraints`, `classification`, `correlation_id`,
  `packet_digest`, `expires_at`, `source_context_id`, `causation_id`, and
  `contract_version`. It has no explicit `source_cognition_event_id`,
  `objective_id`, authoritative current-state payload/reference with the
  required semantics, unresolved ambiguity, relevant prior decisions, known
  deterministic results, home assessment, requested output schema, egress
  policy, or max budget. It also has no `implementation_id`.
- **Why it matters:** A packet can validate while omitting the information
  needed to preserve Office/Occupant/Implementation/State separation and to
  make later cognition attribution and bounded context truthful. F4 cannot
  implement the required context assembly against a complete, stable F1
  surface.
- **Minimum correction:** Extend the F1 packet with typed, bounded fields (or
  explicit durable references) for every required GRC-002 packet element,
  including implementation identity and provenance/correlation lineage. Keep
  the existing bounded limits and reject unbounded transcript/history fields.
  Add validation and serialization tests for required fields, omission
  semantics, bounds, and identity preservation. Do not bind these fields to a
  model, provider, endpoint, or physical resource.

### B2 — EscalationAssessment cannot carry the required escalation basis

- **Severity:** BLOCKING DEFECT
- **Location:** `EscalationAssessment` (around lines 248–339).
- **Requirement violated:** GRC-002 Section 5 requires the escalation record
  to preserve decision identity, resident/occupant/office identity, current
  implementation identity, objective/correlation, decision class/reason,
  question, authoritative state/evidence references, constraints,
  classification, policy version/reference, timestamps/expiry, target tier,
  and provenance.
- **Evidence:** The implemented assessment contains resident, occupant,
  correlation, home belief/reason, policy permission/reason, capacity
  eligibility/reason, decision, reason class, policy reference,
  classification, timestamps, target tier, and contract version. It omits
  `office_id`, `implementation_id`, objective/question, authoritative
  state/evidence references, constraints, and provenance references.
- **Why it matters:** The three decisions—Grace assessment, policy, and
  capacity—are usefully separated, but the resulting record cannot prove
  which office/implementation/state and evidence authorized the escalation.
  This is an unsafe and incomplete F1 basis for F4/P1 escalation consumers.
- **Minimum correction:** Add the missing typed identity, task/context,
  evidence/state, constraints, policy-version, and provenance fields and bind
  them to the packet/request lineage. Preserve the existing separation of
  cognition belief, policy permission, and capacity outcome.

### B3 — CognitionResult omits Office and Implementation identity

- **Severity:** BLOCKING DEFECT
- **Location:** `CognitionResult` (around lines 421–583), especially
  `validate_against` around line 505.
- **Requirement violated:** GRC-002's result envelope requires resident,
  occupant, office, implementation, provider, and resource identity. The core
  invariant is `Office != Occupant != Implementation != State`.
- **Evidence:** The actual result has `resident_id` and `occupant_id`, but no
  `office_id` or `implementation_id`. `validate_against` can therefore compare
  request/result request ID, correlation, resident, occupant, tier,
  classification, and packet ID, but cannot compare office or implementation
  identity. The existing tests' provider/resource replacement check likewise
  checks resident/occupant only, not office/authority/implementation/state.
- **Why it matters:** A result may pass the implemented correspondence checks
  while losing or changing the office/implementation identity that must remain
  stable when provider, model, endpoint, or resource changes. This permits a
  false or incomplete attribution path even though the advisory authority
  scope is constrained.
- **Minimum correction:** Add typed office and implementation identity to the
  result and request/packet lineage as required, require correspondence in
  `validate_against`, preserve them through serialization, and add tests that
  provider/resource changes do not alter them and mismatches fail closed.

## Areas that pass current F1 evidence

### Provider/resource neutrality — PASS

`CognitionTier` contains only `HOME_COGNITION`, `HIGH_REASONING`, and
`EXTERNAL_ESCALATION`. `CapabilityResourceRequest` requests a capability class
and contains no GPU ID, model, endpoint, provider hostname, or topology field.
Unknown tiers fail through enum/type validation. Source search found no
inappropriate RTX 3060/4090, P100/V100, GPU, model, endpoint, or provider
binding; the hardware terms in tests/documentation are used to check that such
coupling is absent. This is consistent with the F1 scope.

### Advisory authority boundary — PASS for implemented contract

`CognitionResult` restricts `authority_scope` to advisory/diagnostic scopes and
rejects an `execute` scope. The valid home/high/external result tests preserve
advisory output. No F1 result can independently accept work, merge code,
execute protected action, or widen Grace authority through this field.

This validates the contract boundary only; execution authorization remains
outside F1 as required by GRC-003.

### Truthful failure and live-generation safeguards — PASS for implemented cases

The result status/failure-code enums represent unavailable, denied, timeout,
malformed, policy refusal, capacity unavailable, classification refusal,
correlation mismatch, and expired outcomes. Non-success outcomes require
`live_generation=False`, and deterministic-substrate results cannot claim live
generation. Actor classes distinguish deterministic substrate, Grace home/high,
external reasoning, Codex worker execution, engineering validation, and Steward
decision. These safeguards do not repair the missing identity/provenance fields
identified above.

### Boundedness — PARTIAL; not sufficient for acceptance

The packet has bounded text/ref/constraint limits and no `transcript` field;
the source and tests reject an injected transcript field. No unrestricted
transcript surface was found in the implemented F1 dataclasses. However, the
required bounded context components and their omission/provenance semantics
are not all represented, so the packet cannot yet serve as the complete F4
bounded context contract.

## Independent test execution

Executed with the dependency-complete Python environment at
`A:\Riverview\repo\.venv\Scripts\python.exe` and `PYTHONPATH` including the
nested Riverview source:

```text
pytest -q
  Riverview/tests/test_cognition_contracts.py
  Riverview/tests/test_provider_neutral_contracts.py
  Riverview/tests/test_resident_context.py
  Riverview/tests/test_resident_runtime.py
  Riverview/tests/test_grace_authority.py
  tests/test_grace_consultation_loop.py
  tests/test_autonomous_reason_execute_loop.py
  tests/test_governed_provider_scheduler.py
```

Result: **73 passed in 4.75s**.

The tests meaningfully exercise valid tiers, required basic identity,
no-transcript behavior, advisory authority, separated escalation booleans,
provider/resource topology neutrality, typed failures, correlation/tier/
classification mismatches, expiry, deterministic live-generation rejection,
and serialization. They do not cover the missing GRC-002 fields or the missing
office/implementation correspondence, so the passing count is not sufficient
to establish F1 acceptance.

An initial collection attempt using the Estate virtual environment failed
because `psycopg` was unavailable there; this was an environment dependency
failure, not treated as an implementation result. The dependency-complete
rerun above passed.

## Future hardening / non-blocking observations

- Add broader adversarial tests for every GRC-002 packet/result field once the
  required contract surface is repaired.
- Add provenance event emission and live provider execution in the later
  packages identified by GRC-003; their absence is expressly out of scope for
  GRC-004.
- A worker actor class with `live_generation=True` is retained as its own actor
  class rather than Grace cognition. This is not treated as a defect because
  GRC-002 requires worker/validation/Steward attribution to remain distinct;
  later provenance integration must preserve that distinction.
- No model, provider, GPU, endpoint, scheduler, CME, or Campaign Runner work
  was required for this F1 validation.

## F4 readiness

**REPAIR_REQUIRED.** F4 depends on F1 and would currently have to define the
missing state, evidence, ambiguity, prior-decision, output-schema, egress,
budget, office, implementation, and provenance semantics itself. After the
minimum contract correction and corresponding tests, F4 can implement bounded
context assembly without redefining F1.

## Grace implementation readiness

**REPAIR_REQUIRED.** The implementation is not ready for the next GRC package
until the three blocking contract-surface defects above are corrected and
independently revalidated.

