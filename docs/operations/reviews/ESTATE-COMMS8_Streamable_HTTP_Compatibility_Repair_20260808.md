# Estate Comms8 Streamable HTTP Compatibility Repair

## Proven distinction

`MCP_INITIALIZE_READY` is not equivalent to `MCP_TRANSPORT_READY`.

The Open WebUI 0.10.2 path reached the existing Estate Comms8 endpoint and
successfully completed `initialize`, `notifications/initialized`, and
`tools/list`, but its session stream GET received HTTP 404. Open WebUI then
reported the browser worker failure and cancellation-scope diagnostic without
allocating a new Grace root.

## Repair boundary

The existing Live compatibility boundary was repaired in place:

- the deployed Streamable HTTP adapter now authenticates session GETs,
  returns `text/event-stream`, emits bounded keepalive comments, refreshes the
  session TTL, and handles disconnects without propagating cancellation errors;
- the existing public Caddy route now includes GET in its `/mcp` method matcher;
- only the Live adapter and the public Caddy configuration boundary were
  restarted/reloaded. Grace, Resident Gateway, CME, Open WebUI, and the
  original candidate were not broadly restarted for this repair.

The original seven-tool contract and public HTTPS route were preserved.

## Deterministic probes

The sanitized detached transport probe verifies, in order:

1. authenticated initialize returns 200 and a session;
2. initialized notification returns 202;
3. tools/list returns 200;
4. authenticated session GET returns 200 `text/event-stream`;
5. DELETE closes the session.

The local adapter and public route both passed this sequence. Credentials,
cookies, request bodies, and authorization headers are not persisted in probe
output.

## Recovery rule

Do not declare the endpoint ready from POST initialize alone. A future recovery
must prove the stream checkpoint and then complete a real Open WebUI Grace
round-trip. The smallest safe restart boundary is the compatibility adapter;
the public Caddy reload is required only when the route matcher is stale.
