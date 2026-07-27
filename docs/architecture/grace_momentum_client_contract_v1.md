# Grace Momentum client contract v1

The public contract is `estate.grace-momentum-client.v1`, published at
`collaboration/workstreams/WP-4229/grace_momentum_client_contract.v1.json`.
Both UI lanes must send the listed envelope fields unchanged and must not infer
lifecycle state or authority locally. `GraceMomentumClient.send()` returns an
`unauthorized` response instead of exposing a transport exception.

## Authentication and authority

An authenticated actor has `actor_id`, `represented_office`, and a non-empty
`authority_source`. Reads require an authenticated actor. Mutations fail closed
unless the represented office is explicitly allowed for that action. Missing,
expired, or invalid sessions receive `{disposition:"unauthorized",
error:{code:"invalid_or_expired_session"|"unauthorized",retryable:false}}`.
Idempotency keys return the original complete response for the same key; clients
must generate one key per intended mutation and may safely retry that mutation.

## Deep links

Clients use these canonical templates, URL-encoding identifiers:

- Estate UI objective: `/estate/objectives/{objective_id}`
- Estate UI directive: `/estate/directives/{directive_id}`
- Estate UI lifecycle: `/estate/objectives/{objective_id}/lifecycle?cursor={cursor}`
- Open WebUI conversation: `/open-webui/conversations/{conversation_id}?objective_id={objective_id}&directive_id={directive_id}`

The optional `links` object on a response carries `objective_url`,
`directive_url`, `lifecycle_url`, and `conversation_url`. Deep links are
navigation only; they grant no authority.

## Consumption, projections, and availability

`client.replay(cursor, limit=100)` is the canonical bounded-polling/replay
mechanism. `client.subscribe()` is an equivalent alias, not a long-lived socket.
The cursor is an exclusive durable event position. The response contains
`next_cursor`, `has_more`, and ordered events; consumers store `next_cursor`
only after rendering or otherwise durably handling the full page.

`client.availability()` exposes health, readiness, mode, and the replay policy.
The production binding is JSON HTTP on loopback: `POST /v1/commands`,
`GET /v1/events?cursor=N`, `GET /v1/lifecycle/{objective_id}`,
`GET /v1/health`, and `GET /v1/readiness`. The JSON `X-Estate-Claims` mapping
requires issuer (`iss`), actor (`sub`), office (`office`), authority source,
and an active session. Deployment validates the issuer through
`ProductionControlConfig`; missing/invalid claims fail closed.

Every production GET route requires the same active `X-Estate-Claims` context
as commands. Missing, malformed, unknown-issuer, incomplete, inactive, or
read-unauthorized claims return a fail-closed 401/403 response.

`GraceMomentumClient` is explicitly an in-process client retained for the fake
and embedded-runtime compatibility path. Production consumers use
`LoopbackGraceMomentumClient(base_url, claims, timeout_seconds=2.0)` and may
only target `127.0.0.1` or `localhost`. It sends commands, replay cursors,
availability, and lifecycle reads through the HTTP binding. Refused connection,
timeout, non-2xx response, malformed JSON, or a non-object response raises a
fail-closed `TransportError` or `MalformedResponseError`; callers must not
substitute cached lifecycle truth for a failed request.

The documented availability interpretation is `operationally_available`: true
only when `health.healthy` and `readiness.ready` are true,
`readiness.provider_effects_enabled` is false, and mode is not `disabled`.
Missing/malformed fields mean false. This is an interpretation field produced by
the HTTP client, not a server-side authority or a new lifecycle state.

The emitted event inventory is identical in the client and control contracts.
The runtime conformance test enumerates emitted command/recovery events against
that declared set, including `directive.transitioned`, `progression.inspected`,
and `dispatch.requested`; no undeclared event type is permitted.

`client.lifecycle_projection(objective_id)` returns the full ordered timeline,
directive state, responsible office, blocker, next lawful action, replay cursor,
and fact-only stage records for Helen capability, Engineering commission, CME
evaluation, provider governance, execution authorization, Dispatch,
reconciliation, validation, Grace receipt, and completion. It is a read model;
it cannot authorize a lifecycle transition.
