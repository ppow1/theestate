# WP-4231 — Estate UI Grace Momentum and Engineering Operations Control Surfaces

Status: Pending
Primary campaign: Estate Production Run-Up
Owner: Estate UI / operations control lane
Mode: parallel consumer implementation against WP-4229 contract fixtures
Depends on: WP-4229 published contract v1 (start-to-start; fake server permitted)
Blocks: WP-4232

## Objective

Connect existing Estate UI command, inspection, audit, replay, recovery, diagnostic, and administrative surfaces to the same canonical runtime used by Open WebUI.

## Scope

- Wire Execution Control, Engineering Dashboard, Operational Activity, Notifications, Validation, audit, replay/recovery, and diagnostics to WP-4229 queries, commands, and subscriptions.
- Display active objective/directive/momentum/lifecycle/responsible office/blocker/next lawful action, CME, Helen, commission, provider governance, authorization, Dispatch, validation, completion, and canonical events.
- Display the complete correlation chain from Open WebUI conversation through Grace receipt/completion; link safely to the correlated conversation.
- Expose only canonical controls: authorize, pause, resume, stop, revoke, supersede, reevaluate, inspect, escalate, and canonical recovery. Controls must render server-authorized availability and never impersonate an office.
- Provide read-only checkpoint, replay reconstruction, completed-effect, command audit, governance, Dispatch, validation, and receipt evidence. Recovery views must state recovered boundary, completed/suppressed effects, next lawful transition, and required authority; no arbitrary rerun buttons.
- Implement component, contract, authentication/role/server-authority, event-update/blocker, replay/audit, refresh, cross-link, and duplicate-action browser tests.

## Non-goals / do not touch

- Do not create a second runtime, client-side lifecycle engine, direct production-record access, or competing recovery pathway.
- Do not remove established command surfaces or duplicate Open WebUI resident behavior.

## Dependencies

| ID | Type | Required state | Verification |
|---|---|---|---|
| WP-4229 contract v1 | start_to_start | schemas, fake server, identities, status/event vocabulary published | consumer contract suite against fake |
| WP-4229 real service | finish_to_start for integration only | authenticated endpoint available | real-service contract suite |
| WP-4230 | related | shared objective/correlation/status/deep-link conventions only | WP-4232 cross-surface tests |

## Ownership and collision control

- Branch: `wp-4231-estate-ui-operations`; implementation root: `collaboration/workstreams/WP-4231/` until approved installation.
- Own Estate UI routes/components/data adapter/subscription client/browser tests and UI-specific accessibility/role visibility.
- The status vocabulary, deep-link template, public client, and schemas are compatibility-owned by WP-4229. Do not change Open WebUI assets.

## Deliverables and acceptance

Provide live-runtime adapter, preserved control surfaces, dashboards/timeline/notifications, audit/replay/recovery views, cross-navigation, and tests. The Estate UI must inspect the full fixture lifecycle, exercise lawful controls, update from events, show blockers/responsible office, inspect audit/replay, and navigate to its Open WebUI conversation.

## Authority, data contract, and persistent evidence

Estate UI is the structured command, inspection, audit, recovery, validation, diagnostics, and administrative client of WP-4229. It uses `GraceMomentumClient`, the versioned command/query/event contracts, and lifecycle cursor `GET /estate/objectives/{objective_id}/lifecycle?cursor={cursor}`; it never writes runtime persistence. Objective and directive detail use `/estate/objectives/{objective_id}` and `/estate/directives/{directive_id}`. Conversation navigation uses `/open-webui/conversations/{conversation_id}?objective_id={objective_id}&directive_id={directive_id}`.

Execution Control presents objective, directive, momentum state, phase, responsible office, blocker, next lawful action, latest CME evaluation, Helen capability state, Engineering commission, provider-governance state, authorization, Dispatch, validation, and completion. Engineering Dashboard presents the complete chain: Open WebUI conversation → objective → directive → Helen determination → Engineering commission → CME evaluation → progression → governance → authorization → Dispatch → result → reconciliation → validation → Grace receipt → completion. Operational Activity and Notifications render canonical event/audit fields: event type, timestamp, actor, office, correlation, disposition, and diagnostic reference.

Validation/audit views are read-only for checkpoints, replay reconstruction, completed effects, commands, provider-governance evidence, Dispatch evidence, validation, and Grace receipt. Recovery controls expose only the canonical service action and must display recovered boundary, completed/suppressed effects, next lawful transition, and authority required.

## Authentication, failures, and validation

Role visibility is advisory; every mutation sends authenticated actor/represented-office context to the service and renders service denial without retrying through a different client. Controls cover authorize, pause, resume, stop, revoke, supersede, reevaluate, inspect, and escalate only when the service advertises them. A visible button is never office authority.

Surface capability gap, expired/paused/revoked authority, governance/provider/capacity failure, failed Dispatch/reconciliation/validation, replay conflict, escalation, and completion with owner, evidence, next lawful action, and cross-surface correlation. Cursor disconnects/reconnects rebuild from canonical query state before rendering incremental events; duplicate events/actions are suppressed by canonical identifiers.

Run component, contract/fake-service and real-service tests; authentication, role visibility, server-denial, event-update, blocker, replay/audit, duplicate-action, browser refresh, and cross-link tests. Operator documentation covers filters, evidence export, recovery authority, event cursor diagnostics, and Open WebUI navigation. Anti-patterns are a second runtime, client-side transitions, direct record mutation, arbitrary rerun controls, authority bypass, fabricated status, or Open WebUI implementation. Handoff provides UI contract-version evidence, role matrix, screenshots/browser evidence, recovery-view behavior, and WP-4232 integration notes.
