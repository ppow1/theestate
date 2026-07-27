# WP-4232 — Dual-Surface Integration, Shadow Production, and Bounded Live Acceptance

Status: Pending
Primary campaign: Estate Production Run-Up
Owner: integration / acceptance lane
Mode: convergence and closeout
Depends on: WP-4229, WP-4230, WP-4231 accepted integration candidates

## Objective

Converge the production runtime and both interfaces into one production candidate, prove dual-surface fixture operation and shadow operation, then perform one explicitly authorized bounded local live-provider proof with replay-safe recovery.

## Dependencies

| ID | Type | Required state | Verification |
|---|---|---|---|
| WP-4229 | finish_to_start | real authenticated service, modes, persistence, event/audit/replay, contract suite | runtime acceptance evidence |
| WP-4230 | finish_to_start | Open WebUI fixture lifecycle and browser evidence | integration candidate evidence |
| WP-4231 | finish_to_start | Estate UI fixture lifecycle/control/audit browser evidence | integration candidate evidence |
| Steward bounded-live authority | approval_required | explicit, current approval after readiness gate | recorded authorization |

## Scope

1. Reconcile schema/status/event ordering, idempotency, reconnect delivery, cross-surface state, auth/authority propagation, fixture residue, and production paths. Both UIs must demonstrate the same handler, result, stored state, event, and audit record for every shared operation.
2. Run full fixture acceptance from Open WebUI while verifying contemporaneous Estate UI state; pause in Open WebUI/resume in Estate UI; revoke across surfaces; duplicate approval; refresh/reconstruct both.
3. Run production shadow scenarios: eligible/absent/later capability, all directive controls and expiry/supersession, availability/capacity/privacy/egress/spend rejections, simulated Dispatch/reconciliation/validation failure, duplicate command, runtime/UI restarts, reconnect, and conflicting evidence. Record selection, governance, authorization, proposed Dispatch, suppressed effect, expected result, audit, and replay.
4. Publish and expose the readiness gate in both UIs: fixture/shadow/auth/persistence/events/replay/exactly-once/provider/Helen/commission/local-only/privacy/egress/no-spend/emergency-stop/rollback healthy plus explicit Steward authorization.
5. Run exactly one small deterministic, local, no-network, no-spend, short, repeatable, non-destructive task that cannot mutate protected repository or machine state. Initiate it in Open WebUI; inspect every one-to-one lifecycle record and post-restart non-repetition in Estate UI.
6. Prove refresh, both UI restarts, runtime/CME restart, pause/revoke restrictions, failed-validation non-completion, emergency stop, rollback, and operator runbook.

## Non-goals / do not touch

- No major redesign, new runtime, or extra initial-production package unless an evidenced canonical contradiction makes the existing scope impossible.
- No live effect before the readiness gate and explicit Steward authorization; no unbounded/nonlocal/network/spend/destructive provider task.

## Ownership and collision control

- Branch: `wp-4232-dual-surface-acceptance`; integration root: `collaboration/workstreams/WP-4232/`.
- Own integration configuration, compatibility shims approved by WP-4229, acceptance fixtures/evidence, shadow campaign, runbook, rollback proof, and end-to-end/browser tests.
- Do not refactor WP-4229/4230/4231 internals except a demonstrated contract contradiction with owner review.

## Deliverables and acceptance

Deliver contract-conformance results, fixture/shadow/live evidence, readiness projection in both UIs, operator runbook, rollback/emergency-stop proof, and final receipt. Completion requires all four stated campaign gates: fixture success through Open WebUI, full Estate UI visibility/control, successful shadow campaign, and one bounded live task with complete audit and no replayed completed effect.

## Governing integration contract and evidence

WP-4232 reconciles clients to the WP-4229 `GraceMomentumClient` rather than creating adapters around internal runtime modules. For every shared operation, verify identical canonical handler, actor/office authority result, idempotency behavior, persisted state, event, audit reference, objective/directive identifiers, and lifecycle cursor outcome. Verify the public object, directive, lifecycle, and Open WebUI correlation links; record schema/status-label/event-order compatibility decisions.

The authoritative persistent evidence set is objective/directive history, conversation correlation, Helen determination, commission/progression/governance evidence, authorization, Dispatch/result/reconciliation/validation, Grace receipt/completion, checkpoints, completed effects, event cursors, audit, diagnostics, readiness gate, and recovery/rollback records. Completion cannot be displayed until Engineering validation and Grace receipt are durable.

## Acceptance phases, failures, and recovery

Phase 1 integrates contracts, auth propagation, event stream/cursor semantics, deep links, status labels, and production paths. Phase 2 executes the fixture lifecycle through Open WebUI while Estate UI concurrently observes it; test pause in chat/resume in Estate UI, cross-surface revoke, duplicate approval, and browser refresh. Phase 3 runs production shadow scenarios for eligible/absent/later capability, every directive terminal/control state, provider/capacity/privacy/egress/spend rejection, simulated Dispatch/reconciliation/validation failure, duplicate command, conflicting evidence, runtime restart, and both UI reconnect/restart. Shadow must retain proposed provider effect as a suppression record.

Phase 4 exposes the readiness gate in both clients: fixture and shadow evidence, auth/storage/events/replay health, exactly-once proof, current Helen/provider/capacity/commission evidence, locality/privacy/egress/no-spend constraints, emergency stop, rollback, and explicit Steward bounded-live approval. Phase 5 is one short deterministic local/no-network/no-spend/non-destructive/repeatable task with one lifecycle chain and post-restart no-repeat proof. Fail closed and stop/escalate for any missing or conflicting evidence.

Test end-to-end contract conformance, browser state consistency, authority denials, event loss/duplication, cursor reconnect, restart/replay, recovery, shadow suppression, bounded-live controls, audit completeness, emergency stop, and rollback. The runbook covers launch, monitoring, incident/stop, rollback, evidence collection, and escalation. Anti-patterns are major redesign, client-side authority, unbounded live work, provider bypass, false completion, or an additional initial-production package without demonstrated contradiction. Handoff is the final production-readiness receipt with all evidence, limitations, rollback state, and recommended next authority decision.
