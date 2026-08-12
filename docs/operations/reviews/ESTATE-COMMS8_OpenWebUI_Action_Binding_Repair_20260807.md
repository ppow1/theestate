# Estate Comms8 Open WebUI Action-Binding Repair

Result: OPENWEBUI_COMMS8_ACTION_BINDING_FIXED

## Root cause

Live MCP `tools/list` returned the seven canonical actions, but Open WebUI
exposed only the server-level pseudo-source `server:mcp:estate-comms8-live`.
The Grace model therefore had an enabled source without action bindings.
The first binding repair also preserved the qualified ID as the provider
function name; that prevented canonical action dispatch.

## Repair

- Resident Gateway catalog now advertises seven action-qualified IDs.
- Open WebUI action discovery expands the Live MCP source from `tools/list`.
- MCP binding parses the qualified ID, filters the requested action, and
  invokes the exact canonical MCP function name.
- Resident Gateway streaming tool-result responses now use streaming delta
  envelopes, preserving the authoritative result for Open WebUI.

## Evidence

- Live MCP client discovery: 7 actions on three consecutive reads.
- Open WebUI `/api/v1/tools/`: 7 action entries, exact names and IDs.
- Grace model metadata: 7 action-qualified Live IDs.
- Open WebUI execution emitted `estate_comms8_read_request` exactly.
- Follow-up result returned `request_id=ec8-3f24f4aadcd947c9`, the expected
  workflow ID, and `state=queued`; no mutation occurred.
- Local Live request state remains queued, unclaimed, and without response or
  resolution.
- Focused regression tests: 9 passed.

No credential values are recorded.

## Activation

Open WebUI application restart and Grace Resident Gateway restart are
required after these changes. A browser hard refresh and a new conversation
are required to refresh the user-facing picker/model context. The MCP
adapter, Estate Runtime Host, ChatGPT registration, dedicated browser, and
workstation do not require restart for this repair.
# Superseding invocation note

Action visibility and action-qualified binding are necessary but not
sufficient for Grace acceptance. The follow-up invocation repair found that
the Resident Gateway could still fall through to resident prose for
natural-language Comms8 requests. See
`ESTATE-COMMS8_Grace_OpenWebUI_MCP_Function_Invocation_Repair_20260807.md`.
