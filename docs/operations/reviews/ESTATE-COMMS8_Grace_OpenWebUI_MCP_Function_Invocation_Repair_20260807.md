# Estate Comms8 Grace/Open WebUI MCP Function Invocation Repair

## Result

`OPENWEBUI_TOOL_RESULT_REINJECTION_FAILED` — backend and synchronous
function invocation passed, but the post-activation authenticated Grace
browser surface could not be completed because the Open WebUI restart
invalidated the dedicated browser session and returned it to `/auth`.

## Evidence

- Live Comms8 queue was inspected read-only; no request was created or
  mutated by this package.
- The active Resident Gateway was restarted as PID 8080 with one owner on
  `127.0.0.1:11435`.
- The repaired gateway selects `estate_comms8_read_request` from an ordinary
  natural-language request containing an authoritative `ec8-*` identity.
- The synchronous Open WebUI path returned `finish_reason=tool_calls`, the
  exact canonical function name, and the authoritative result for
  `ec8-6a850f4ab32743d2`.
- Focused regression tests passed: `11 passed`.
- The actual browser request carried all seven action-qualified Live
  `tool_ids`, but its asynchronous Open WebUI task produced an empty
  assistant message. After the required Open WebUI restart, the browser
  session was at the sign-in page, so post-activation user-surface proof
  could not be completed without Steward authentication.

## Root cause and repair

The Resident Gateway previously dispatched Comms8 only when the exact
function name appeared in the user text. Natural-language read requests
fell through to the resident response path, allowing narration instead of
native execution. The repair adds bounded selection for enabled Comms8
read/list actions, extracts only the explicit request identity, and returns
a truthful no-call error for unsupported lifecycle claims. It also emits the
authoritative MCP result through the streaming response envelope.

No Comms8 schema, listener, credential, state, or lifecycle semantics were
changed.

## Activation

`ACTIVATION REQUIRED:`

1. Restart the Grace Resident Gateway.
2. Restart Open WebUI when its installed runtime or task pipeline has
   changed; this was performed for this package.
3. Ctrl+F5 the dedicated browser.
4. Sign in if Open WebUI invalidated the browser session.
5. Start a new Grace conversation and submit the read-only request.
6. Verify the visible native tool card names
   `estate_comms8_read_request` and the returned authoritative `ec8-*`
   record.

Resident Gateway restart is required. Open WebUI restart is conditional on
installed Open WebUI changes; it was used here to activate the user-facing
task path. Runtime Host/core, MCP adapter, ChatGPT reconnect, dedicated
browser restart, and workstation reboot are not required.

## Remaining gate

After the Steward signs the browser session back in, repeat only the
read-only Grace acceptance. Do not create or mutate a Comms8 request for
this repair. Do not claim the full product roundtrip from this receipt.
