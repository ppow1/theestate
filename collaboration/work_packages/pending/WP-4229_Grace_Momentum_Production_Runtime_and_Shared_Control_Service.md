# WP-4229 — Grace Momentum Production Runtime and Shared Control Service

Status: Pending
Primary campaign: Estate Production Run-Up
Owner: Runtime / platform implementation lane
Mode: production implementation, shared-contract first
Depends on: accepted Grace Momentum / CME / Engineering Progression fixture baseline
Blocks: WP-4232

## Objective

Promote the accepted fixture lifecycle into one authenticated, versioned Estate runtime service that is the canonical command, query, event, persistence, recovery, governance, and audit authority for Open WebUI, Estate UI, CLI, workers, and tests.

## Scope

- Host Grace directives, CME evaluation, Engineering progression, Dispatch authorization/reconciliation/validation/completion, and canonical lifecycle queries without changing office ownership.
- Publish a versioned control contract before runtime completion: commands for objective correlation, directive controls, evaluation/progression/reevaluation and inspection; queries for lifecycle state, ownership/blockers/next lawful action, governance, Dispatch, validation, replay, and audit; and the complete event vocabulary named in the campaign assignment.
- Require every command and event to contain schema version, identifier, correlation/causation, objective/directive identifiers when applicable, actor, represented office, authority source, timestamp, idempotency key, disposition, diagnostic reference, and audit reference.
- Implement production-only record locations for objectives, directives/transitions, evaluations, checkpoints, completed effects, progression/governance evidence, authorization, Dispatch, reconciliation, validation, receipt, and audit. Production services MUST NOT read or write fixture roots.
- Implement authenticated Office context, authorization, correlation propagation, event subscriptions, health/readiness, diagnostics, feature flags, execution modes (`fixture`, `shadow`, `bounded_live`, `disabled`), provider-effect suppression, checkpoint/replay, duplicate suppression, and rollback.
- Deliver schemas, fake/contract-test server, sample events, test identities, and client reference behavior so WP-4230 and WP-4231 can proceed independently.

## Non-goals / do not touch

- Do not duplicate lifecycle policy in either UI or make either UI a runtime authority.
- Do not enable a live provider, bypass execution mode, or use acceptance fixture roots as production storage.
- Do not redesign established Estate command surfaces or alter office authority: Steward; Grace momentum; CME event continuation; Helen capability; Engineering technical progression/authorization; Dispatch logistics; provider governance revalidation.

## Required reading

- `src/estate/core/grace_momentum_directive.py`
- `src/estate/core/cme_engineering_progression.py`
- `src/estate/core/engineering_commission_progression.py`
- `src/estate/core/grace_helen_engineering_composition.py`
- `src/estate/core/runtime_recovery.py` and `src/estate/core/runtime_replay.py`
- `tests/test_grace_momentum_acceptance_matrix.py`, `tests/test_grace_momentum_engineering_progression.py`, and `tests/test_grace_helen_engineering_composition.py`
- `docs/architecture/campaign_momentum_observer_contract.md`

## Dependencies

| ID | Type | Required state | Verification |
|---|---|---|---|
| Fixture baseline | evidence_required | accepted and retained | focused fixture suite passes |
| Canonical Estate authentication | evidence_required | reused or narrow Office boundary specified | authorization tests |
| WP-4230 / WP-4231 | start_to_start | contract consumers may use fake server | contract compatibility only; no internal dependency |

## Ownership and collision control

- Branch: `wp-4229-production-runtime`; implementation root: `collaboration/workstreams/WP-4229/` for contract/fake artifacts before production installation.
- Own production service host, service API/client, runtime persistence/configuration, authentication adapter, event transport, audit/health, contract schemas, and runtime tests.
- Shared seams: public schemas, client SDK/reference client, status vocabulary, and feature-mode policy. WP-4229 owns their compatibility decision; consumers propose additions through versioned contract changes.
- WP-4230 and WP-4231 own no lifecycle handler, persistence, authority, or provider-governance code.

## Deliverables

- Versioned command/query/event schema set and normative contract specification.
- Authenticated production service, fake server, client reference, identities, samples, production configuration, rollback procedure, and observability catalog.
- Unit, contract, authentication/authority, persistence/replay, ordering, malformed-record, duplicate-suppression, shadow, and rollback tests.

## Governing principles and authoritative contract

Grace owns operational momentum; CME continues only from durable institutional events and only within a Grace directive. Helen determines capability. Engineering accepts commissions, revalidates provider governance, and alone authorizes technical execution. Dispatch owns logistics. A visible client control never grants represented-office authority.

Publish `GraceMomentumClient` and a versioned control service before consumer implementation. The public links are:

- `GET /estate/objectives/{objective_id}`;
- `GET /estate/directives/{directive_id}`;
- `GET /estate/objectives/{objective_id}/lifecycle?cursor={cursor}`;
- a versioned command endpoint and authenticated event subscription with cursor resume.

Commands cover create/correlate objective; authorize, pause, resume, stop, revoke and supersede directive; inspect/history; evaluate; progress Engineering commission; request reevaluation; inspect Dispatch correlation; and inspect validation/completion. Queries return objective summary, lifecycle timeline, responsible office, blocker, next lawful action, authority, capability, provider-governance, Dispatch, validation, replay, and audit state. Events include objective/directive lifecycle changes, capability determination, commission acceptance, CME evaluation, progression disposition, authorization, Dispatch lifecycle, reconciliation, validation, Grace receipt, completion, blocker, escalation, and recovery.

Every command, query result, event, and persistent envelope has schema version, immutable identifier, correlation and causation identifiers, objective/directive identifiers as applicable, actor, represented office, authority source, timestamp, idempotency key, disposition/result, diagnostic reference, and audit reference. Schema changes are additive or explicitly version-negotiated.

## Persistent records, runtime behavior, and security

Production records are separate from fixture roots and include objectives, directives and transitions, CME evaluations, Engineering progression and provider-governance evidence, authorization, Dispatch, provider result, reconciliation, validation, Grace receipt, completion, checkpoints, completed-side-effect identifiers, cursor positions, audit, and recovery decisions. Checkpoints bind durable event position and completed effects; replay verifies envelopes, reconstructs the lawful state, and suppresses completed effects before any authorization or Dispatch attempt.

The service accepts only authenticated actor and represented-office context. It denies anonymous, expired, invalid-actor, office-mismatch, unauthorized mutation, and unauthorized Engineering progression calls; inspection and mutation permissions are distinct and every decision is audited. Execution mode is persisted and enforced at the canonical boundary: `fixture`, `shadow`, `bounded_live`, or `disabled`. Shadow performs selection, governance, authorization, and Dispatch preparation but records a suppressed provider effect. `bounded_live` additionally requires explicit current authority; no client can bypass mode enforcement.

Health/readiness reports configuration, storage, event transport, cursor lag, replay status, mode, provider-effect suppression, and diagnostic references without exposing secrets. Recovery is plan-first, shows completed/suppressed effects and next lawful transition, and supports only canonical authorized recovery actions. Operator documentation covers startup/shutdown, configuration, authentication identities, cursor recovery, shadow operation, emergency stop, rollback, and evidence collection.

## Failure handling, validation, and handoff

Fail closed for malformed/unknown schemas, missing authority, cursor gaps, conflicting evidence, stale Helen evidence, unhealthy/unadmitted/uncapacitated provider, locality/privacy/egress/spend violation, invalid checkpoint, duplicate command, and storage/event failure. Emit an auditable blocker or escalation rather than infer continuation.

Validation includes unit tests for transitions and idempotency; schema/client/fake-service contract tests; authentication and office-authority denial tests; persistence, restart, cursor ordering and malformed-record tests; replay/duplicate side-effect tests; shadow-suppression and rollback tests; and real-service consumer contract tests. Handoff supplies the contract specification, schemas, `GraceMomentumClient`, fake/in-memory server, sample events, test identities, compatibility policy, and runbook to WP-4230/WP-4231. Anti-patterns are client-owned lifecycle truth, direct persistence writes, direct provider calls, synthetic progress, and arbitrary rerun behavior.

## Acceptance

The service starts with healthy readiness; production state survives restart; authorization/audit/event guarantees hold; fixture and shadow modes work; provider effects remain suppressed outside explicit bounded-live authorization; and both UI contract suites pass against the fake and real service. No live provider is enabled by this package.
