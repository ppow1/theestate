# Grace Comms8 runtime recovery

The accepted Grace escalation surface is restored from the repository-owned
implementation lineage `867da12919c7a1dd64a373643bdc47632bb4270c` and its
compatible later repairs. The deployment is selective; it does not copy the
repository wholesale.

The governed overlay is produced by:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/deploy_grace_comms8_runtime.ps1
```

Target runtime: `A:\EstateRuntime\host\estate-main\current`.
The deployment receipt is written under the target runtime at
`runtime\deployments\grace_comms8_runtime_overlay.json`.

Grace retains `grace_runtime_bridge` and these action-qualified Comms8 IDs:

- `server:mcp:estate-comms8-live|estate_comms8_create_reasoning_request`
- `server:mcp:estate-comms8-live|estate_comms8_list_requests`
- `server:mcp:estate-comms8-live|estate_comms8_read_request`
- `server:mcp:estate-comms8-live|estate_comms8_claim_request`
- `server:mcp:estate-comms8-live|estate_comms8_acknowledge_request`
- `server:mcp:estate-comms8-live|estate_comms8_respond_request`
- `server:mcp:estate-comms8-live|estate_comms8_resolve_request`

The live logical server remains `server:mcp:estate-comms8-live`; its accepted
transport is the governed live MCP endpoint. The browser worker uses the
dedicated CDP/WebSocket ChatGPT bridge and does not bypass the Comms8 mailbox.

Activation is bounded and idempotent: one mailbox worker is allowed, requests
must remain correlated to the Grace workflow, and malformed responses or a
wrong browser target fail closed. Stop if a duplicate worker appears, the
request lifecycle is inconsistent, an unrelated production request is claimed,
or the browser bridge selects another page/session.

The Open WebUI database remains the canonical
`A:\AI\OpenWebUI\EstateCanonicalData\webui.db`. This recovery does not replace
or reset that database; its existing Grace association is verified before
activation. The P100/SillyTavern and Stream Deck lanes are outside this overlay.
