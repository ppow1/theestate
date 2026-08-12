# Estate Comms8 Grace Live Persona Dispatch Repair — 2026-08-07

Decision: `OPENWEBUI_USER_SURFACE_ACCEPTANCE_UNPROVEN`

## Safety inventory

Before mutation, local and public Live inventories contained zero records
for workflow `estate-comms8-live-grace-chatgpt-roundtrip-test` and
idempotency key `grace-chatgpt-roundtrip-20260807-01`. The prior blank UI
turns therefore did not create an authoritative request.

After the single permitted creation, exactly one matching request exists:

- request ID: `ec8-3f24f4aadcd947c9`;
- workflow: `estate-comms8-live-grace-chatgpt-roundtrip-test`;
- state: `queued`;
- claim, acknowledgement, response, and resolution: absent;
- local/public records: equal.

The request is intentionally left queued for the manual ChatGPT milestone.

## Root cause

The canonical `estate/grace` catalog advertised only
`grace_runtime_bridge` and `grace_runtime_grounding`. The persisted
`Grace (Estate Resident Gateway)` model advertised the Live MCP server, but
the Standard Grace surface did not. This allowed the runtime bridge to win
or prevented a Comms8 tool from being available at the actual surface.

The Resident Gateway also lacked explicit read-request argument handling.
Its transport result path now returns the supplied MCP tool result verbatim;
it does not synthesize IDs or lifecycle state.

## Repair

Changed canonical and deployed Resident Gateway catalog metadata so both
Grace personas advertise `server:mcp:estate-comms8-live` while retaining
their distinct runtime identities. Added explicit read-request delegation
for the required Resident Gateway read acceptance. No Comms8 schema, queue,
lease, lifecycle, authentication, or state semantics changed.

## Evidence

- initial inventory: `A:\theestate-data\grace-comms8-live-dispatch-repair-20260807\initial-request-inventory.json`;
- Standard native creation and authoritative result return:
  `A:\theestate-data\grace-comms8-live-dispatch-repair-20260807\grace-standard-live-creation.json`;
- Resident Gateway native read/result return:
  `A:\theestate-data\grace-comms8-live-dispatch-repair-20260807\resident-gateway-live-read.json`;
- prior manual UI correlation: Open WebUI chat records contained four blank
  exact-marker turns and one non-tool assistant turn; no native tool call or
  target request existed before repair;
- adapter trace records metadata-only MCP traffic and contains no secrets or
  request bodies.

## Validation

Focused regression suite: `25 passed`.

The repaired gateway emitted the exact Comms8 create tool call, the real MCP
client created `ec8-3f24f4aadcd947c9`, and the returned authoritative result
was reinjected through the Gateway. The Resident Gateway read path emitted
the exact read tool, returned the same request ID, and matched local/public
state.

The existing CDP browser target was recoverable, but the attempted actual
Open WebUI UI submission did not produce a persisted tool call or chat result;
therefore the required visible user-surface acceptance is not claimed.

## Blocker

`OPENWEBUI_USER_SURFACE_ACCEPTANCE_UNPROVEN`: the authoritative lower-level
Grace/Gateway and MCP paths pass, but a real Open WebUI conversation has not
yet visibly returned the queued request ID through the UI. No additional
request was created to compensate, and the one queued request remains ready
for the next manual milestone.

