# First Vertical Slice Plan — Evelyn Image Iteration Through Engineering

**Plan status:** designed, not authorized for implementation
**Proof task:** produce and validate one Evelyn image-iteration run through the Engineering Department
**Expansion rule:** stop after one correlated task; do not generalize into a new workflow platform

## Proof boundary

After explicit authority is recorded, use one approved, non-sensitive Evelyn image-iteration objective. The proof succeeds only if every durable artifact uses stable campaign, work-package, Grace-objective, workforce-request/assessment, Dispatch, adapter-request/result, validation, message/thread, and momentum-cycle identifiers. It may use a fixture or dry-run provider if live-provider/spending authority is absent, but must label that boundary truthfully and may not claim live execution.

The slice must compose existing mechanisms. It must not create a scheduler, queue, state store, mailbox, provider registry, validator, campaign, officeholder, resident, voice, or acceptance path.

## Preconditions

1. Record a protected decision resolving the authorization ambiguity in `CURRENT_STATE_RECONCILIATION.md`.
2. Identify the existing Engineering campaign and work package authorized to own the proof; do not create a campaign merely for the proof.
3. Confirm the package's PTM/orchestrator readiness record and applicable architecture/validation gates.
4. Confirm an admitted image-capable provider and whether execution is dry-run or live; live mode additionally requires the existing spending, credential, privacy, and confirmation evidence.
5. Confirm Alfred's canonical Steward mailbox destination and the exact notification policy authority.

If any precondition is absent, record a blocker and stop.

## Minimal implementation sequence

1. **Objective intake.** Create a delegated `GraceObjective` requested by the Steward. Persist it through `GraceOperationsRuntime`, with the authorized campaign ID, work-package ID, approval evidence, and proof correlation ID.
2. **Engineering association.** Through the authorized Engineering composition adapter, verify the campaign/package definition and canonical readiness record. Persist only correlation evidence through an existing canonical evidence mechanism; do not invent an Engineering campaign store.
3. **Helen request.** Derive one correlated workforce/capability request through `HelenWorkforceStore`. Require image iteration capability, bounded duration, classification/privacy constraints, and campaign/package/objective evidence.
4. **Helen disposition.** Record Helen's machine-readable fulfillment, partial fulfillment, deferral, refusal, or protected-review result. Only a fully evidenced, unblocked disposition may satisfy the staffing gate.
5. **Provider route.** Query existing provider capability, health, capacity, and recommendation surfaces. Record the selected existing governed pathway and its evidence. Recommendation alone must not imply selection, reservation, or execution authorization.
6. **Dispatch and handoff.** Use the existing PTM/orchestrator eligibility path and sole Execution Dispatch queue. Enqueue exactly one idempotent Dispatch item carrying all correlation identifiers, then prepare the existing provider-adapter handoff. Record its Dispatch ID back as evidence associated with the package/objective.
7. **Progress return.** Reconcile accepted, progress, completed, failed, or blocked provider evidence through existing Dispatch/result reconciliation. Completion requiring validation must enter `Validation`, not accepted/closed.
8. **Grace reaction.** Project the returned canonical event to Grace. Invoke only a specifically authorized adapter action: advance an eligible next step, bounded retry/recovery, record blocker, or route escalation. Preserve Chief Architect acceptance gates.
9. **Alfred notification.** Route a canonical message only for Steward authority, blocker, significant milestone, or requested briefing. Assert routine queue/progress events do not notify the Steward. Alfred summarizes/routes only.
10. **Momentum reevaluation.** Feed the updated canonical projections to CME. Verify deterministic idempotency: unfinished eligible work is proposed once; duplicate evidence does not duplicate Dispatch or mail; missing/protected evidence holds or escalates.
11. **Validation.** Run the package's registered recipe plus the focused integration test. Preserve image artifact hashes/references, result reconciliation, validation verdict, and non-acceptance status.

## Focused tests after authorization

A single integration module should prove:

- stable identifiers survive objective → Engineering association → Helen → Dispatch → adapter result → validation → mail → CME;
- Helen can satisfy or block staffing but cannot prioritize, dispatch, or accept;
- Grace cannot bypass Engineering records or protected architecture/acceptance gates;
- only one Dispatch item and one handoff are produced under replay;
- image-capability routing fails closed when provider evidence is missing, stale, or unsuitable;
- completion returns to Validation when validation is required;
- failure/blocker returns to Grace and produces the proper bounded action;
- Alfred notifies on the four authorized conditions and suppresses routine progress;
- CME replay is deterministic and idempotent;
- neither provider completion nor mailbox acknowledgement accepts the work.

Targeted commands should be limited initially to the new integration module plus directly affected existing unit suites (Grace, Helen, Engineering integration, Dispatch/handoff/reconciliation, Alfred routing, and CME). Run the canonical work-package validator named by the authorizing package and `git diff --check` before a future implementation PR.

## Expected implementation surface after authorization

The protected authorization should name the owning package and canonical adapter location. Subject to that decision, the smallest anticipated surface is:

- one thin Engineering lifecycle composition adapter that calls existing stores/adapters and writes no independent state;
- minimal correlation support in existing Grace/Helen records only if their current metadata/evidence fields cannot express the contract;
- a caller-supplied CME action adapter that delegates to the same canonical composition adapter;
- one focused end-to-end integration test and fixtures;
- the authorizing work package's receipt/evidence updates.

Existing Dispatch, provider catalog, mailbox, Alfred routing, result reconciliation, and validation implementations should be reused unchanged unless a failing focused test proves a narrowly scoped defect.

## Stop points

Stop and escalate rather than infer authority when encountering protected approval, architecture acceptance, spending, privacy/safety confirmation, an unadmitted provider, stale/contradictory evidence, validation failure, or a request to accept/merge/deploy. Stop after the single proof task and report evidence before any expansion.
