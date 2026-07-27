# Grace Production Run-Up Campaign Execution Plan

## Parallel topology

`WP-4229 (contract + runtime)` publishes versioned schemas, fake server, identities, sample events, status vocabulary, deep-link format, and reference client first. `WP-4230 (Open WebUI)` and `WP-4231 (Estate UI)` then implement independently against that boundary. `WP-4232` starts integration only after all three candidates have their own contract evidence.

```text
WP-4229 ─┐
WP-4230 ─┼─> WP-4232
WP-4231 ─┘
```

WP-4230 and WP-4231 are start-to-start consumers of the WP-4229 published contract, not of its internals; their only finish-to-start dependency is real-service integration in WP-4232.

## Anticipated ownership

| Package | Exclusive ownership | Shared compatibility seam |
|---|---|---|
| WP-4229 | service host, schemas, public client, persistence, auth, events, audit, modes | versioned contract/status/deep-link policy |
| WP-4230 | Open WebUI adapter, resident/tools, conversation store, chat UI/tests | public client and correlation/deep-link vocabulary |
| WP-4231 | Estate UI adapters, controls/views, subscriptions/tests | public client and correlation/deep-link vocabulary |
| WP-4232 | environment integration, acceptance/runbook/evidence | compatible configuration only |

## Collision risks and controls

- Public schema/client/status/deep-link changes: WP-4229 compatibility owner; additive/versioned change only.
- Authentication claims and role labels: WP-4229 owns server interpretation; each UI owns display and token transport.
- Environment configuration/event endpoints: WP-4229 provides templates; WP-4232 owns assembled candidate configuration.
- Shared browser fixtures and end-to-end evidence: WP-4232 owns cross-surface variants; UI packages own isolated fixtures.
- Existing dirty fixture files: preserve them; baseline must be committed/merged independently before implementation branches are based.

## Merge, integration, and acceptance order

1. The fixture baseline merged through PR #485 at original campaign base `088ab55b03d07a558c694d622339440acb4ccc68`; it remains the common semantic baseline.
2. WP-4229 publishes its contract-first increment (`2a3afce68f3527540d4c0b2f7083eb31aed9e4c6`) and production-control contract implementation (`1556e95f`, PR #486) before consumer integration.
3. In parallel, merge WP-4230 and WP-4231 after each passes its fake-server contract suite; rebase only across public contract versions.
4. Merge WP-4232 integration configuration and run the same contract suite against the real service.
5. Accept fixture dual-surface flow, then shadow campaign, then readiness gate, then explicit-Steward-authorized bounded live proof, then recovery/rollback evidence and closeout.

## Contract and acceptance guardrails

The shared client contract uses `/estate/objectives/{objective_id}`, `/estate/directives/{directive_id}`, `/estate/objectives/{objective_id}/lifecycle?cursor={cursor}`, and `/open-webui/conversations/{conversation_id}?objective_id={objective_id}&directive_id={directive_id}`. WP-4229 owns compatibility, authentication interpretation, persistence, event/cursor semantics, audit, modes, provider-effect suppression, and lifecycle truth. WP-4230 and WP-4231 use fakes and contract fixtures in parallel; neither writes persistence nor owns a lifecycle transition.

The merge gate is contract evidence first, then independent consumer contract/browser evidence, then real-service conformance, dual-surface fixture acceptance, shadow campaign, readiness gate, explicit Steward approval, bounded-live proof, and restart/rollback evidence. Unresolved implementation choices are constrained—not deferred architecture redesigns: production configuration root, canonical authentication issuer/office claim mapping, event transport/cursor retention, the Open WebUI extension capability, Estate UI application boundary, and the admitted deterministic local provider. Any contradiction is recorded by WP-4232 and resolved by the owner of the affected canonical boundary.
