# GRC-004R2 — Complete ResidentReasoningPacket Aggregate Context Bounding

Package: GRC-004R2  
Role: C3 targeted repair writer  
Status: REPAIR_COMPLETE_READY_FOR_REVALIDATION  
Date: 2026-08-25

## Exact C2 defect

The complete C2 revalidation report was read from
`docs/codex-reports/seat-2/GRC-004RV_Cognition_Contract_Repair_Revalidation.md`.
It reproduced that `ResidentReasoningPacket` accepted 64 individually valid
`operational_state_refs` values of approximately 500 characters each while
the other counted context was already approximately 60,133 characters. The
actual packet context was approximately 92,133 characters, exceeding
`MAX_CONTEXT_CHARS = 64_000`.

The root cause was a single omitted argument: `operational_state_refs` was
validated by `_context_refs` but was absent from the
`_packet_context_total(...)` call in `ResidentReasoningPacket.__post_init__`.
The aggregate calculation therefore did not account for every caller-
controlled context collection.

## Exact correction

Changed only:

`Riverview/src/riverview/reasoning/cognition_contracts.py`

The `ResidentReasoningPacket.__post_init__` call now passes
`self.operational_state_refs` exactly once to `_packet_context_total`, without
changing the 64,000-character limit or any identity/provider/authority
semantics.

## Complete packet aggregate inventory

The aggregate helper now accounts for every textual or collection context
path exactly once:

| Field | Classification | Aggregate treatment |
|---|---|---|
| `objective` | Counted as embedded context | Counted; max 4,000 chars |
| `question` | Counted as embedded context | Counted; max 4,000 chars |
| `operational_state_refs` | Reference-only but still size-bounded | Counted; max 64 refs, 500 chars each |
| `evidence_refs` | Reference-only but still size-bounded | Counted; max 64 refs, 500 chars each |
| `constraints` | Counted as embedded context | Counted; max 32 values, 4,000 chars each |
| `authoritative_current_state_refs` | Reference-only but still size-bounded | Counted; max 64 refs, 500 chars each |
| `unresolved_ambiguity` | Counted as embedded context | Counted; max 64 values, 4,000 chars each |
| `relevant_prior_decisions` | Reference-only but still size-bounded | Counted; max 64 refs, 500 chars each |
| `known_deterministic_results` | Counted as embedded context | Counted; max 64 values, 4,000 chars each |
| `home_assessment` | Counted as embedded context | Counted; max 4,000 chars |
| `requested_output_schema` | Counted as embedded context | Counted; max 4,000 chars |
| `egress_policy` | Counted as embedded context | Counted; max 4,000 chars |
| `packet_id`, `resident_id`, `occupant_id`, `office_id` | Identity/control field | UUID-typed; not context |
| `implementation_id`, `source_cognition_event_id`, `objective_id` | Identity/control field | UUID-typed; not context |
| `authority_ref`, `request_class`, `classification` | Non-context metadata/control | Individually bounded; not packet context |
| `cognition_tier`, `correlation_id` | Identity/control field | Enum/UUID-typed; not context |
| `packet_digest` | Non-context metadata | Fixed SHA-256 shape; not context |
| `source_context_id`, `causation_id` | Reference-only but structurally bounded | Optional UUID references; no embedded payload |
| `expires_at`, `max_budget`, `contract_version` | Identity/control field | Typed/bounded controls; not context payload |

Reference fields remain reference-only: callers cannot use them to embed an
arbitrary object or mapping. Their collection counts and per-reference lengths
are bounded, and all reference strings that carry packet context participate in
the packet-wide aggregate.

## Regression and boundary tests

Updated:

- `Riverview/tests/test_cognition_contracts.py`

Added `test_operational_state_refs_cannot_bypass_packet_aggregate_limit`,
which keeps all 64 state references individually legal, builds the other
counted context to one character below the limit, adds the state references,
and asserts construction fails with the aggregate-bound error.

Added inclusive boundary coverage:

- packet just below 64,000 characters: accepted;
- packet exactly at 64,000 characters: accepted under current `>` semantics;
- packet one character over: rejected;
- large operational-state collection causing aggregate overflow: rejected;
- normal reference-based packet: accepted.

## Verification

Required focused and adjacent suites completed:

`83 passed in 4.84s`

The run covered cognition contracts, provider-neutral contracts, resident
context/runtime, Grace authority, Grace consultation, autonomous
reason/execute, and governed provider scheduling. Python compileall also
passed for reasoning source and focused tests.

Existing independently passing behavior remains unchanged:

- Identity preservation: PASS;
- provider neutrality: PASS;
- advisory authority boundary: PASS;
- truthful live-generation behavior: PASS.

No model, GPU, endpoint, provider, runtime cognition, migration, F2/F3/F4,
policy, scheduler, or CME work was performed.

## F4 readiness

`ResidentReasoningPacket` now enforces its advertised aggregate context limit
across every currently defined context-carrying field, including
`operational_state_refs`. F4 can rely on the F1 packet for aggregate bounding
without repairing or reinterpreting this contract.

F4 contract readiness: `READY_FOR_REVALIDATION`.
