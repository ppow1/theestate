# WP-4232 readiness blocker report

Status: blocked by a canonical upstream capability gap. This report does not
authorize or perform bounded-live execution.

## Governing evidence

The merged runtime states in `src/estate/core/grace_momentum_service.py:1-6`
that it “never invokes a provider” and that `bounded_live` is a governed
recording mode until a separate provider-admission package installs an adapter.
The same service persists `provider_effects_enabled: false` in
`configure()` (`:110`) and returns that value from readiness (`:214`). Its
command responses also mark provider effects suppressed (`:182`), while the
Dispatch fallback records `recorded_no_provider_execution` and emits
`dispatch.requested` (`:180`).

The existing canonical commands and observed events are:

| Command | Observed event | Evidence |
| --- | --- | --- |
| `objective.create_or_correlate` | `objective.created_or_correlated` | fixture and shadow evidence |
| `momentum.authorize` | `directive.authorized` | fixture and shadow evidence |
| `cme.evaluate` | `cme.evaluation.persisted` | shadow evidence |
| `engineering.authorize` | `execution.authorized` | shadow evidence |
| `dispatch.request` | `dispatch.requested` | shadow evidence |
| `directive.stop` | `directive.stopped` | fixture evidence |

Replay, lifecycle projection, audit references, cursors, restart recovery,
rollback, and idempotency are recorded in
`acceptance_evidence.json`. No provider result is produced by this runtime.

## Missing-event classification

The six missing events are not equivalent:

| Event | Classification | Why it blocks WP-4232 |
| --- | --- | --- |
| `progression.changed` | Declared and reachable through `engineering.progress_commission`, but not used by the current acceptance path | The path used `engineering.authorize`, which emits `execution.authorized`; progression must be exercised through its canonical Engineering command. It is not itself a provider-admission substitute. |
| `dispatch.submitted` | Declared, but unreachable through the current `dispatch.request` implementation | `EVENT_FOR_ACTION` names `dispatch.submitted`, but the command branch emits `dispatch.requested` and explicitly records no provider execution. |
| `reconciliation.completed` | Declared but has no command or emitter in the merged runtime | Requires a persisted provider result and reconciliation owner. It depends on provider admission/execution. |
| `validation.succeeded` | Declared but has no command or emitter in the merged runtime | Requires Engineering validation of a real persisted result. It depends on provider admission/execution. |
| `grace.receipt.recorded` | Declared but has no command or emitter in the merged runtime | Requires durable evidence after validation. It depends on the missing completion path. |
| `objective.completed` | Declared but has no command or emitter in the merged runtime | Requires the complete lifecycle and durable Grace receipt. It depends on the missing completion path. |

The authoritative client and control contracts declare all six event types;
they do not provide an acceptance command that can lawfully create the missing
records. The provider-owned stages therefore remain `null` in the canonical
lifecycle projection.

## Why the gate remains closed

Completed gates are fixture acceptance, shadow suppression, emergency stop,
rollback, restart/replay, exactly-once duplicate suppression, authenticated
client transport, and dual-surface observation. The blocked gates are complete
lifecycle, provider result, Dispatch submission, reconciliation, Engineering
validation, durable Grace receipt, objective completion, and bounded-live
readiness. The machine-readable evidence records each missing event and its
classification.

Synthetic lifecycle, audit, replay, validation, receipt, or completion records
would create a competing authority and persistence model, contradict the
merged runtime’s provider boundary, and violate WP-4232’s explicit prohibition
on synthetic evidence. Bounded-live authorization cannot be accepted while the
readiness projection says provider effects are disabled and the completion
chain is absent. No bounded-live effect was executed.

## Proposed upstream corrective package

Proposed title: **WP-4232-U1 — Governed Local Provider Admission and Completion
Lifecycle**.

Owner review is required before implementation. The package must remain
upstream of WP-4232 and must not be implemented in this harness. Its minimum
scope is:

- install one governed local provider-adapter boundary;
- admit the adapter only when readiness proves local-only, no-network,
  no-egress, no-spend, healthy, and explicitly authorized conditions;
- execute one idempotent effect with durable completed-effect identity;
- emit and persist Dispatch submission/result records;
- perform reconciliation and Engineering validation through their canonical
  owners;
- persist a durable Grace receipt and objective completion;
- preserve emergency stop, rollback, restart/replay, and non-repetition;
- define and validate event, audit, cursor, checkpoint, and receipt contracts;
- fail closed on missing authority, unhealthy admission, malformed results,
  locality/egress/spend violations, duplicate effects, or persistence failure.

The package must preserve the existing Grace Momentum client boundary and must
not introduce a second lifecycle authority, persistence model, or provider
control plane.

## Local residue

The inaccessible `.pytest-wp4232/` directory is local test residue only. It is
not staged, committed, or incorporated into the work package and must not be
deleted as part of this closeout.
