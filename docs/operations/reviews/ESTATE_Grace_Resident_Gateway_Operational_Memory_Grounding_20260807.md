# Grace Resident Gateway Operational Memory Grounding — 2026-08-07

## Reason for acceptance

The failed ordinary-language smoke test returned the invented identifier
`consultation-root-78942`, claimed reasoning-only completion, and asserted
full operational-memory access without evidence of a durable read. The old
path fell through to resident prose/fallback generation and persisted a
normal resident turn; it did not query the consultation store.

## Repair

The Grace gateway now detects only operational-state queries and invokes the
read-only `read_operational_snapshot` boundary before model generation. The
boundary reads the existing SQLite consultation store and CME state file,
normalizes continuations to their root, counts execution requests and
attempts, and returns per-fact provenance. It fails closed to
`STATE_UNAVAILABLE / unable to verify` when an authoritative source cannot
be read. No second database or prompt-injected consultation facts were added.

## Source-level gateway result

The exact smoke wording was sent to the local canonical gateway. The result
was authoritative and mutation-free:

- CME operational state: `IDLE` (`cme_runtime`);
- latest completed root: `9.00`, latest turn `9.04` (`consultation_store`);
- final turn state: `response_received`, classification
  `INFORMATION_ONLY`;
- execution occurred: true, two logical execution requests and two physical
  attempts;
- operational memory available: true (`consultation_store`);
- `mutation_performed: false`, `runtime_bridge_invoked: true`,
  `native_tool_call: false`.

The response did not contain the prior fake ID or any model-generated
operational-role claim. Direct SQLite bytes were identical before and after
the read.

## Open WebUI acceptance history

Before runtime normalization, the authenticated Open WebUI smoke reached the
pre-repair process on `127.0.0.1:11435` and returned unsupported persona
prose, including a non-canonical consultation identifier and a reasoning-only
claim. Its response carried no `operational_memory` envelope. This is
preserved as historical failure evidence. After runtime normalization, the
exact smoke passed on both Grace surfaces as recorded below.

## Test coverage

`tests/test_grace_operational_memory.py` covers continuation-to-root
normalization, execution-history detection, unavailable-store fail-closed
behavior, provenance, no mutation, fake-identifier exclusion, the narrow
operational-query boundary, and action-claim provenance. The detached suite
passed: 9 tests, run
`cme-owner-20260807T221754798975Z-fbd4f1facc` (12 tests, exit code 0).

## Activation requirements

| Component | Requirement |
|---|---|
| Grace Resident Gateway | REQUIRED only when deploying/reloading this code |
| Open WebUI | CONDITIONAL if its cached gateway/model binding is stale |
| CME | NOT REQUIRED |
| mailbox worker | NOT REQUIRED |
| Comms8 | NOT REQUIRED |
| MCP adapter | NOT REQUIRED |
| execution router/provider | NOT REQUIRED |
| ChatGPT reconnect | NOT REQUIRED |
| browser restart | NOT REQUIRED |
| workstation reboot | NOT REQUIRED |

This receipt does not rewrite the failed smoke test; that failure is the
reason the authoritative state-query boundary exists.

## Grounding closeout and action-claim guard

The normalized live runtime subsequently returned the same grounded result
through both `Grace` and `Grace (Estate Resident Gateway)`: `IDLE`, root
`9.00`, latest turn `9.04`, `response_received`, execution occurred with two
logical requests and two physical attempts, and operational memory available.
The two labels route through the same resident package and grounding filter;
the second is a presentation alias.

The read result carries `authoritative_read` provenance and records the
consultation-store and CME reads. No consultation, Comms8, execution, or
escalation mutation is part of the smoke operation. The repeated live result
is accepted as the grounding closeout after runtime normalization.

The final read-only probe measured canonical counts before and after as
unchanged: consultations `24`, transport attempts `24`, execution requests
`11`, execution attempts `12`, and escalations `1`; resident-session file
count also remained `283`. The live envelope reported
`runtime_bridge_invoked: true`, `authoritative: true`, and consultation-store
plus CME provenance.

The separate action-claim guard now rejects unsupported completion prose. It
allows `model_inference` for recommendations, requires `authoritative_read`
for verification claims, and requires successful `authoritative_action` for
write/record/update/tag/restart/send claims. The observed false closeout is
preserved as the regression case; it is not treated as evidence that the
requested records were written.

## Terminal provenance semantics closeout

The live provenance response initially ended with
`AUTHORITATIVELY_COMPLETED` even though it correctly stated that no
recording occurred. This fourth failure mode is preserved as
`GRACE_TERMINAL_PROVENANCE_STATUS_SEMANTICS_AMBIGUOUS`; it is distinct from
the hallucinated-state, composite-short-circuit, and unsupported-action-claim
failures.

Terminal selection now derives from the underlying action evidence after
composition. The exact reloaded live regression ends with
`INSUFFICIENT_EVIDENCE`, retains all five substantive answers, reports
`authoritative_read` only, and leaves the canonical counts unchanged. A
successful correlated `authoritative_action` is the only path to
`AUTHORITATIVELY_COMPLETED`; a genuinely requested pending action is the path
to `PENDING_EXECUTION`.

The final detached suite passed 16 tests in run
`cme-owner-20260807T223309800694Z-3e84625a07`.

## Superseding composite-reasoning closeout

After grounding was accepted, the exact multi-question provenance prompt
exposed a separate short-circuit: the operational read returned immediately,
discarding the remaining user obligations. This is preserved as
`GRACE_OPERATIONAL_READ_SHORT_CIRCUITS_COMPOSITE_REASONING`, distinct from
the original pre-grounding hallucinated-state failure.

The gateway now classifies direct reads separately from grounded composite
reasoning. Composite requests preserve the full prompt, inject bounded
authoritative evidence into the existing resident reasoning path, apply the
action-claim guard after composition, and perform one completeness repair at
most.

The reloaded live Gateway answered the exact provenance prompt with no
recording action performed, no authoritative write evidence, the
authoritative operational read as the only executed action, explicit
requested/recommended/pending distinctions, and terminal classification
`INSUFFICIENT_EVIDENCE`. The live envelope recorded
`grounded_composite_reasoning`, `original_request_preserved: true`,
`model_reasoning_attempted: true`, `final_response_complete: true`, and
authoritative read provenance. Canonical and resident-session counts were
unchanged before and after.

## External reasoning provenance enforcement

The historical failure GRACE_EXTERNAL_REASONING_PROVENANCE_NOT_ENFORCED is
preserved: Grace previously narrated an external review without a
consultation root, Comms8 lifecycle, or provider response. The source repair
now recognizes the exact ordinary-language second-opinion request and routes
it through GraceConsultationLoop; fabricated external-review claims are
blocked unless current-request correlation has authoritative response
evidence.

Focused delegation and grounding tests pass (26 passed). The detached live
acceptance run cme-owner-20260807T231009185052Z-6e80eaf614 proved that the
exact phrase created root 11.00 and request ec8-a60d2a66ebba4e4b, with zero
execution request/attempt mutation. The provider failed before response
persistence, so Grace correctly returned Performed: No / Attempted: Yes /
chatgpt_worker_failed and did not claim a second opinion. A diagnostic
variant also left root 10.00 queued under an active lease; those durable
records are preserved and are not treated as successful acceptance.

The live success tokens are therefore not issued. Current blocker:
CHATGPT_WORKER_FAILED_BEFORE_AUTHORITATIVE_EXTERNAL_REASONING_RESPONSE.

## Existing root 11.00 continuation status

A subsequent authoritative read preserved root 11.00 without replacement:
the consultation is awaiting reasoning and remains attached to
ec8-a60d2a66ebba4e4b in queued state, with no claim, response, resolution, or
execution records. The CME owner state is stale IDLE
(updated 2026-08-07T18:54:53Z), while the mailbox worker reports
active_lease_in_progress for the earlier root 10.00 request. That earlier
request has an active lease and therefore blocks the queue selector ahead of
11.00. The safe classification is
ACTIVE_LEASE_WAIT_REQUIRED / CME_OWNER_STATE_STALE_AND_MAILBOX_WORKER_BLOCKED_BY_ACTIVE_LEASE.

No lock or lease was cleared, no worker was manually launched, no response
was injected, and root 11.00 was not replaced.

## Root 10 / root 11 reconciliation continuation

Root 10.00 subsequently completed authoritatively with response
`resp-40d3d909526247`. Its persisted response remains immutable. The
response contains `MORE_REASONING_REQUIRED` / `CONTEXT_REQUIRED`, but its
`evidence_request.allowed_scope` is empty. No schema/version marker proves
that this envelope predates the current contract; therefore it is recorded as
`CURRENT_CONTRACT_INVALID_EVIDENCE_REQUEST`, not silently treated as legacy.
The durable validation record marks the follow-up unactionable, preserves the
response, releases queue ownership, and records `execution_performed: false`.

Root 11.00 was preserved. Its original request
`ec8-a60d2a66ebba4e4b` expired under governed transport recovery and exactly
one same-root replacement, `ec8-c5171f00239545c8`, was created. CME then
claimed and acknowledged that replacement as `worker_id=chatgpt`; no manual
claim or worker targeting occurred. The authoritative provider response is
`resp-ac3e784fbca343`, persisted as `CONTEXT_REQUIRED`: the durable context
contains only the request for a second opinion and no proposition, prior
recommendation, artifact, evidence, or constraints. Its returned evidence
request also has empty `allowed_scope`, so the current validator correctly
failed closed with `EXECUTION_DECISION_INVALID:evidence_request_missing:allowed_scope`.

No execution request or attempt was created. CME ended `STOPPED` with
`AUTHORITATIVE_COMPLETE`; the mailbox worker recorded the schema failure.
The second-opinion acceptance remains blocked by
`ROOT_11_CONTEXT_REQUIRED_NO_PERSISTED_PROPOSITION` (with the independent
current-contract schema failure preserved). The next safe step requires a
governed continuation carrying the actual architectural proposition; no new
consultation root or fabricated provider conclusion is permitted.
