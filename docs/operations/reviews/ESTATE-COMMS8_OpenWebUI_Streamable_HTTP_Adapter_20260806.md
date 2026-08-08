# Estate Comms8 Open WebUI Streamable HTTP Adapter — 2026-08-06

Status: `OPENWEBUI_ADAPTER_READY_FOR_LIVE`.

## Proven mismatch

The accepted Comms8 service exposed legacy JSON-RPC-over-HTTP behavior:
JSON responses, connection close, no `Mcp-Session-Id`, empty initialized
notification responses, and no routed MCP DELETE session termination.
The proven classifications were `MCP_SESSION_HEADER_MISSING`,
`INITIALIZE_NOTIFICATION_MISMATCH`, `CONNECTION_LIFECYCLE_MISMATCH`, and
`HTTP_STATUS_SEMANTICS_MISMATCH`.

## Transport-only boundary

`tools/comms8_streamable_http_adapter.py` owns only bounded in-memory
transport sessions. It issues a session ID on initialize, accepts the
initialized notification with HTTP 202, forwards unchanged JSON-RPC
bodies to the accepted Comms8 service, and returns unchanged tool results.
It owns no request state, queue, lease, response, or resolution behavior.

Blue validation used temporary `127.0.0.1:11812` and was stopped afterward.
Live uses the adapter as the sole 11811 boundary owner; the authoritative
Live Comms8 service remains on 11810.

## Evidence

- fixture tests: 4 passed;
- Python compilation passed;
- actual Open WebUI 0.10.2 MCP client: session initialization passed;
- seven tools discovered and read-only list passed;
- adapter restart followed by fresh-session discovery passed;
- one Blue adapter lifecycle completed all five states;
- three Live public Open WebUI-client discovery cycles returned seven tools;
- adapter logs contain no credentials or request bodies.

Evidence: `A:\theestate-data\openwebui-comms8-streamable-http-adapter-20260806`.
