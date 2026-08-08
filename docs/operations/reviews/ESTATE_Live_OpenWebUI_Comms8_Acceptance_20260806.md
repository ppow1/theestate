# Estate Live Open WebUI Comms8 Acceptance — 2026-08-06

Status: `ROLLED_BACK_BEFORE_LIFECYCLE`.

Open WebUI configuration was backed up before editing. A distinct
`Estate Comms8 Live` MCP entry was temporarily created and then removed
during rollback; the final Open WebUI tool-server configuration contains no
Live Comms8 connector.

The Live endpoint itself passed independent authenticated health:

- initialize: 200;
- notifications/initialized: 202;
- tools/list: exactly seven tools;
- three sequential read-only calls: 200, 200, 200.

Open WebUI 0.10.2 discovery failed at its Streamable HTTP compatibility
boundary. The Live implementation returned its accepted legacy JSON-RPC
`application/json` response, which Open WebUI's Streamable HTTP MCP client
could not parse as the required response/session contract. No request was
created, claimed, acknowledged, responded to, resolved, or retrieved.

First failure: `OPENWEBUI_MCP_PROTOCOL_INCOMPATIBLE`.

Decision: `LIVE_ESTATE_PROMOTION_ROLLED_BACK`.

No secret values are recorded. Blue remains healthy on 11808/11809; Green
remains unchanged.

## Accepted continuation

The transport-only Streamable HTTP adapter was validated and installed
under Live identity. Open WebUI 0.10.2 connected to
`https://estate-comms8-live.ionoge.com/mcp`, discovered exactly seven
tools, and completed a read-only list operation across three sequential
discovery cycles.

The single Live request `ec8-6a850f4ab32743d2` completed all lifecycle
states with worker `openwebui`. Local and public terminal records matched,
Grace retrieval passed, and the completed request remained readable after
controlled Live restart. No retry or second request was issued.

Final acceptance: `LIVE_ESTATE_PROMOTION_ACCEPTED`.
