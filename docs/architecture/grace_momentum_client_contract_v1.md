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
