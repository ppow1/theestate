# Estate Comms8 Live ChatGPT App Identity — 2026-08-07

## Decision

`CHATGPT_APP_ADMIN_AUTH_REQUIRED`

No production ChatGPT app registration was accepted. The authenticated
workspace was inspected at `https://chatgpt.com/admin/apps`.

## Evidence

- `estate-comms8-live.ionoge.com` resolves to `64.227.21.54`.
- No specific AAAA record was returned for the Live hostname.
- The unauthenticated Live MCP probe returned HTTP 401, consistent with
  the protected production ingress.
- The only Estate registration visible in the workspace inventory was
  `Estate Comms8 Blue3`, described as the Blue candidate acceptance app.
- No `Estate Comms8 Live` registration was visible.
- Historical `Estate Comms8_5` remains a candidate/Blue registration and
  was not reused.

## Registration blocker

The custom-app form was populated with the production semantic identity
and endpoint:

- Name: `Estate Comms8 Live`
- Endpoint: `https://estate-comms8-live.ionoge.com/mcp`
- Authentication mode: `Access token / API key`

The supported form rendered only the header-scheme selector. It did not
render a credential/token input, Scan Tools, Connect, Save, or equivalent
credential-binding control. The Create control was tested after the
required trust acknowledgement; it produced no registration, and the
workspace inventory remained unchanged.

No credential value was entered, displayed, or recorded. No Live request
was claimed or otherwise mutated.

## Required next action

A supported ChatGPT workspace/app-administration path must be supplied
that permits binding the governed Live ChatGPT-facing credential to the
new app, or an administrator must repair/enable the missing API-key
registration controls. Do not repurpose Blue3 or Estate Comms8_5.

The queued Live request remains untouched and is not an acceptance result
until a distinct `Estate Comms8 Live` app is positively identified.
