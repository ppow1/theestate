# WP-4230 — Open WebUI Grace Conversational Operations Integration

Status: Pending
Primary campaign: Estate Production Run-Up
Owner: Open WebUI / resident integration lane
Mode: parallel consumer implementation against WP-4229 contract fixtures
Depends on: WP-4229 published contract v1 (start-to-start; fake server permitted)
Blocks: WP-4232

## Objective

Make Open WebUI the primary conversational surface for Grace-led operations while using only the shared Estate service for lifecycle commands, state, progress, authority, and audit.

## Scope

- Integrate the Grace resident/model, authenticated Estate tools, conversation/message-to-objective/directive/commission/evaluation correlation, and Estate UI lifecycle deep links.
- Translate intentional natural-language requests to canonical commands only after objective, authority, ambiguity, safety, and expected-effect resolution. Ordinary discussion MUST NOT become execution.
- Deliver canonical event-driven progress and final completion messages; model inference MUST NOT invent status.
- Persist conversation ID, message ID, objective/directive/commission/evaluation IDs, lifecycle stage, delivered-event marker, pending approval, and receipt; suppress duplicate delivery after restart/reconnect.
- Implement approved/reject/inspect/pause/resume/stop/revoke interactions with native controls where safe, otherwise explicit confirmation and an expiring one-time approval token. Record actor, authority, conversation, requested action, expiration, idempotency key, and result.
- Present clear blocker/service-outage/correlation-conflict explanations naming what happened, responsible office, permitted automatic continuation, and available Steward action.
- Provide local-only browser and contract testing, including routing, correlation, duplicate delivery, approval/authority, refresh/reconnect, outage/malformed-event, and completion tests.

## Non-goals / do not touch

- Do not implement lifecycle transitions, office impersonation, persistence, governance, or Dispatch logic in Open WebUI.
- Do not make Open WebUI the sole Estate interface or remove CLI/Estate UI surfaces.
- Do not depend on WP-4229 private modules; use schemas, fake server, and public client only.

## Dependencies

| ID | Type | Required state | Verification |
|---|---|---|---|
| WP-4229 contract v1 | start_to_start | schemas, fake server, identities, status/event vocabulary published | consumer contract suite against fake |
| WP-4229 real service | finish_to_start for integration only | authenticated endpoint available | real-service contract suite |
| WP-4231 | related | shared correlation/status/deep-link conventions only | WP-4232 cross-surface tests |

## Ownership and collision control

- Branch: `wp-4230-open-webui-grace`; implementation root: `collaboration/workstreams/WP-4230/` until approved installation.
- Own Open WebUI resident/tool configuration, integration adapter, conversation-delivery store, UI components, browser fixtures, and Open WebUI-specific tests.
- Contract status labels and deep-link template are shared files: propose changes via WP-4229 compatibility review; do not edit Estate UI code.

## Deliverables and acceptance

Provide configuration, authenticated tool adapter, correlation/delivery repository, approval-token flow, status components, deep-link behavior, local-only test harness, and an operator guide. The Steward can state a fixture-backed objective, establish momentum, inspect, pause/resume, approve/reject, observe canonical progress, and receive validated completion in Open WebUI without CLI/PowerShell.

## Authority, schemas, and runtime behavior

Open WebUI is the primary conversational operating surface, not a lifecycle authority. It uses only the WP-4229 versioned `GraceMomentumClient`, its command/query/event schemas, and the canonical links `GET /estate/objectives/{objective_id}`, `GET /estate/directives/{directive_id}`, `GET /estate/objectives/{objective_id}/lifecycle?cursor={cursor}`, and `/open-webui/conversations/{conversation_id}?objective_id={objective_id}&directive_id={directive_id}`.

The resident distinguishes discussion from execution intent. Before a command it resolves objective, actor authority, ambiguity, safety, expected effect, current directive, and idempotency key; ambiguity or unsafe intent produces a clarification, not a mutation. All status, blocker, ownership, and completion prose is rendered from canonical query results or events, never inferred from model prose.

Persist the conversation correlation record separately from runtime truth: Open WebUI conversation/message identifiers; objective/directive/commission/evaluation identifiers; lifecycle stage; event cursor; delivered-event identifiers; pending approval; approval-token expiry; deep link; and receipt identifier. Delivery is idempotent across refresh, reconnect, resident restart, and replay. No Open WebUI component writes a runtime record directly.

## Interactions, failure handling, and audit

Expose inspect, approve, reject, pause, resume, stop, and revoke only when the client receives an allowed action from the service. Native controls are preferred; otherwise use an explicit confirmation exchange with a one-time expiring approval token. Every action sends authenticated actor/represented-office context, conversation and message correlation, requested action, idempotency key, and authority source; the canonical audit result is displayed or linked.

Event-driven messages cover authorization, Helen availability/gap, Engineering acceptance, CME evaluation, execution authorization, Dispatch start/completion, reconciliation, validation success/failure, Grace receipt, completion, blocker, and escalation. Failure responses identify what occurred, the responsible office, whether automatic continuation is lawful, and the available Steward action for capability absence, paused/revoked directive, provider/governance/capacity failure, Dispatch/reconciliation/validation failure, service outage, and correlation conflict.

## Validation, anti-patterns, and handoff

Tests include resident routing and tool-call schema contracts against the fake then real service; intent/clarification and authority tests; correlation, duplicate-delivery, approval-token, refresh/reconnect, malformed-event, outage, blocker, and final-completion tests; and local Open WebUI browser integration tests. Audit views link to canonical event/audit references and Estate UI lifecycle deep links. Operator documentation covers authentication setup, approval recovery, reconnect/cursor diagnostics, and safe escalation.

Anti-patterns are treating chat as approval, inventing progress, persisting lifecycle truth, impersonating an office, direct Dispatch/provider calls, replacing Estate UI, or accepting bounded-live work. Handoff to WP-4232 includes contract-version evidence, browser results, correlation/delivery migration notes, known UI capability limits, and Open WebUI-to-Estate link test evidence.
