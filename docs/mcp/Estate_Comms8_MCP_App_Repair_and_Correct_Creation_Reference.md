# Estate Comms8 MCP App Repair and Correct Creation Reference

Version: 1.0  
Status: Operational repair record and future implementation reference  
Date: 2026-08-04  
Owner: Office of the Steward / Estate Engineering  
Scope: Estate Comms8 ChatGPT MCP App creation, authentication, compatibility repair, end-to-end validation, and remaining persistence work

## 1. Purpose

This document records exactly what had to be diagnosed and repaired to connect the Estate Comms8 candidate to ChatGPT as an MCP App. It also defines the process that should have been completed during the preparatory implementation before the candidate was presented as ready.

This is a factual repair record based on the live candidate observed on August 4, 2026. It is not proof that the current temporary process topology is durable, promoted, or restartable.

No secret values are recorded here. Credential names describe roles only.

## 2. Executive summary

The preparatory work established much of the intended infrastructure, but it did not prove that the endpoint behaved like a complete ChatGPT-compatible MCP server.

The endpoint could answer an authenticated MCP `initialize` request. That was necessary but insufficient. ChatGPT performs a sequence that includes initialization notifications and tool discovery. The candidate server mishandled JSON-RPC notifications without an `id`, which caused the upstream route to surface `502 Bad Gateway`. ChatGPT reduced this to the generic message:

> Failed to add connector link

The successful repair required:

1. Identify the live Windows candidate process and actual port.
2. Verify the Windows-to-VPS reverse SSH tunnel.
3. Verify the Caddy public route.
4. Determine which credential belonged at each authentication boundary.
5. Test authenticated MCP requests locally and publicly.
6. Reproduce the MCP notification failure encountered by ChatGPT.
7. Add a temporary MCP compatibility proxy.
8. Redirect the reverse SSH tunnel through that proxy.
9. Create and connect a new ChatGPT App using the correct Bearer credential.
10. Refresh and verify all seven MCP actions.
11. Invoke a real read-only tool from a ChatGPT conversation.

The app connected and became functional. The runtime remains temporarily dependent on live Windows processes and is not yet fully restartable.

## 3. Observed working architecture

The repaired request path is:

```text
ChatGPT Estate Comms8 App
    |
    | HTTPS with ChatGPT-facing Bearer credential
    v
Caddy on the Ionoge VPS
    |
    v
VPS loopback 127.0.0.1:11808
    |
    | reverse SSH tunnel
    v
Windows MCP compatibility proxy 127.0.0.1:11809
    |
    | ordinary MCP requests forwarded with upstream authentication
    v
Original Estate Comms8 candidate 127.0.0.1:11808
```

The public candidate MCP endpoint is:

```text
https://estate-comms8-blue-candidate.ionoge.com/mcp
```

### Authentication boundaries

Two distinct authentication boundaries were observed:

| Boundary | Credential role |
|---|---|
| ChatGPT to public Caddy/MCP endpoint | ChatGPT-facing candidate Bearer credential |
| Compatibility/ingress layer to the original Blue candidate | Blue upstream Bearer credential |

The candidate material also contained an older upstream credential. Similar-looking credentials with different roles caused avoidable ambiguity. Future deployments must document credential roles explicitly without recording secret values.

## 4. Initial failure

The original ChatGPT App, `Estate Comms8_2`, displayed:

> Failed to add connector link

That message did not identify whether the failure involved:

- DNS;
- TLS;
- Caddy routing;
- the reverse SSH tunnel;
- Bearer authentication;
- MCP initialization;
- MCP notification handling;
- or tool discovery.

Each layer therefore had to be tested independently.

## 5. Windows candidate process discovery

Windows port inspection found:

```text
Local address: 127.0.0.1
Port: 11808
Process: python.exe
Observed PID: 3524
```

The command line was:

```text
C:\Python314\python.exe -m estate_comms8.candidate_server
    --host 127.0.0.1
    --port 11808
    --root A:\theestate-data\candidate-blue-runtime
```

This established that:

- the MCP candidate was running on Windows;
- the service intentionally listened only on loopback;
- port `11808` was correct;
- the intended runtime root was `A:\theestate-data\candidate-blue-runtime`;
- public access depended on the reverse tunnel.

An unauthenticated local request returned:

```text
HTTP/1.0 401 Unauthorized
```

This proved the service was reachable locally and authentication enforcement was active.

## 6. Reverse SSH tunnel verification

The original tunnel was:

```text
ssh.exe -N -T
    -o ExitOnForwardFailure=yes
    -o ServerAliveInterval=30
    -o ServerAliveCountMax=3
    -R 127.0.0.1:11808:127.0.0.1:11808
    root@64.227.21.54
```

This provided:

```text
VPS 127.0.0.1:11808
    -> Windows 127.0.0.1:11808
```

The VPS listener was confirmed as an `sshd`-owned listener on loopback port `11808`.

The loopback-only design was appropriate: the Windows MCP service did not need to listen on a LAN or public interface.

## 7. Caddy route verification

The public hostname was already routed through Caddy:

```text
estate-comms8-blue-candidate.ionoge.com
```

Caddy terminated HTTPS and reverse-proxied requests to the VPS loopback listener on port `11808`.

The preparatory work had therefore established several correct components:

- public DNS;
- HTTPS;
- active Caddy service;
- candidate Caddy route;
- VPS loopback listener;
- reverse SSH reachability to Windows.

The ChatGPT connection failure was not merely an unreachable server.

## 8. Authentication diagnosis and correction

The first authenticated local request still returned:

```text
HTTP/1.0 401 Unauthorized
```

The relevant candidate secrets material was located beneath:

```text
A:\theestate-data\candidate-blue-runtime\
    comms8-package4-ingress\
    candidate-secrets.env
```

Three credential roles were present:

1. ChatGPT-facing candidate credential.
2. Older candidate upstream credential.
3. Blue upstream credential.

Testing established the correct mapping:

- The Blue upstream credential authenticated directly against the Windows candidate server.
- The ChatGPT-facing credential authenticated against the public candidate endpoint.

After the proper credential was used at each boundary, local and public initialization both returned `HTTP 200 OK` with an MCP result equivalent to:

```json
{
  "id": 1,
  "jsonrpc": "2.0",
  "result": {
    "capabilities": {
      "tools": {}
    },
    "protocolVersion": "2024-11-05",
    "serverInfo": {
      "name": "estate-comms8-candidate",
      "version": "estate.comms8.v1"
    }
  }
}
```

This proved:

- Bearer formatting was accepted;
- the public route preserved the Authorization header;
- Caddy reached the candidate;
- the server supported MCP initialization.

It did not yet prove ChatGPT compatibility.

## 9. MCP lifecycle defect

ChatGPT performs more than `initialize`. The startup sequence includes behavior equivalent to:

1. `initialize`
2. `notifications/initialized`
3. `tools/list`
4. subsequent tool calls

The candidate server handled JSON-RPC requests containing an `id`, but mishandled notifications that intentionally contain no `id`.

The important notification was:

```json
{
  "jsonrpc": "2.0",
  "method": "notifications/initialized"
}
```

A JSON-RPC notification does not require an ordinary JSON-RPC response. The server should accept it without trying to construct a normal request response.

The original candidate closed or failed the request incorrectly. Through Caddy, this appeared as:

```text
502 Bad Gateway
```

This explained why:

- manual `initialize` tests passed;
- the public endpoint appeared healthy;
- the Bearer token appeared valid;
- but ChatGPT still reported `Failed to add connector link`.

This was the principal protocol defect missed during preparation.

## 10. Why the original server could not be repaired directly

A fresh Python process could not import the running server module:

```text
ModuleNotFoundError: No module named 'estate_comms8'
```

Searches did not locate the original source file or a usable installed module in the expected runtime directories.

The service remained alive because PID `3524` had already loaded the implementation. That did not make it restartable.

Consequently, the live service could be inspected and called, but its original implementation could not be safely edited and restarted. A compatibility layer was required to complete the ChatGPT connection without terminating the surviving process.

## 11. Temporary MCP compatibility proxy

A temporary proxy was created at:

```text
A:\theestate-data\candidate-blue-runtime\
    comms8-package4-ingress\
    mcp_notification_proxy.py
```

It listens on:

```text
127.0.0.1:11809
```

Its observed behavior is:

| Incoming traffic | Proxy action |
|---|---|
| JSON-RPC request containing an `id` | Forward to the original MCP candidate on `127.0.0.1:11808` |
| JSON-RPC notification without an `id` | Accept locally and return `202 Accepted` |
| Authentication and ordinary MCP calls | Preserve or apply the appropriate upstream request information |
| Tool requests | Forward to the original candidate |

The proxy was observed as PID `39728`.

A local `notifications/initialized` test then returned:

```text
HTTP/1.1 202 Accepted
Content-Length: 0
```

## 12. Reverse tunnel correction

The original tunnel forwarded directly to the incompatible candidate:

```text
VPS :11808 -> Windows :11808
```

After installing the proxy, the tunnel was changed to:

```text
VPS :11808 -> Windows :11809
```

The corrected tunnel command was:

```text
ssh.exe -N -T
    -o ExitOnForwardFailure=yes
    -o ServerAliveInterval=30
    -o ServerAliveCountMax=3
    -R 127.0.0.1:11808:127.0.0.1:11809
    root@64.227.21.54
```

The corrected tunnel was observed as PID `7536`.

The public notification test then returned:

```text
HTTP/1.1 202 Accepted
Via: 1.1 Caddy
```

This proved notification compatibility across the complete public route.

## 13. Correct ChatGPT App configuration

A new app, `Estate Comms8_5`, was configured with:

| Setting | Correct value |
|---|---|
| MCP URL | `https://estate-comms8-blue-candidate.ionoge.com/mcp` |
| Authentication type | API key |
| Authorization scheme | Bearer |
| Credential | ChatGPT-facing candidate credential |
| Effective header | `Authorization: Bearer <credential>` |

Secret values must remain outside this document and outside ordinary repository history.

After the correct ChatGPT-facing credential was entered, the app connected successfully.

## 14. Action discovery

After connection, the app configuration was refreshed so ChatGPT would rescan MCP tools.

Seven actions were discovered:

1. `estate_comms8_create_reasoning_request`
2. `estate_comms8_list_requests`
3. `estate_comms8_read_request`
4. `estate_comms8_claim_request`
5. `estate_comms8_acknowledge_request`
6. `estate_comms8_respond_request`
7. `estate_comms8_resolve_request`

A connector can be technically connected while its displayed action list remains stale. Refresh and action-count verification are required acceptance steps.

## 15. End-to-end acceptance test

A real ChatGPT conversation was opened with `Estate Comms8_5` selected.

A read-only request-list operation was invoked. The app executed the Estate Comms8 list tool and returned:

```json
[]
```

The empty list was a valid application result: no requests were present.

This test proved together that:

- ChatGPT authorized successfully;
- public DNS and TLS worked;
- Caddy routed the request;
- the reverse SSH tunnel worked;
- the compatibility proxy accepted MCP initialization notifications;
- the original candidate answered ordinary MCP calls;
- `tools/list` worked;
- ChatGPT discovered and invoked an action;
- the tool response returned to the conversation.

No mailbox or request-state mutation was performed during this acceptance test.

## 16. What the preparatory work got right

The available evidence shows the preparation correctly established or anticipated:

- the public candidate hostname;
- the Caddy HTTPS route;
- the VPS loopback listener design;
- the Windows loopback candidate service;
- reverse SSH tunnel topology;
- Bearer authentication;
- an MCP initialization handler;
- seven Estate Comms8 tools;
- candidate/runtime directories;
- separate credential roles;
- candidate deployment material.

These components prevented the repair from becoming a completely new deployment.

## 17. What the preparatory work did not prove

The primary deficiency was incomplete acceptance testing.

| Required validation | Observed result |
|---|---|
| Unauthenticated request returns `401` | Passed |
| Authenticated local `initialize` returns `200` | Passed after credential mapping |
| Authenticated public `initialize` returns `200` | Passed after credential mapping |
| Credential role documented at each boundary | Initially ambiguous |
| `notifications/initialized` succeeds | Failed until proxy installation |
| Public notification succeeds through Caddy | Initially failed as `502` |
| `tools/list` exposes seven tools | Verified during repair |
| ChatGPT can add the connector | Initially failed |
| ChatGPT can refresh actions | Verified during repair |
| ChatGPT can invoke a real tool | Verified during repair |
| All service source/package files exist | Failed; original module unavailable |
| Stack survives termination or reboot | Not proven |
| Canonical controller owns all processes | Not implemented |

A successful `initialize` response alone must never be used as the readiness definition for a ChatGPT MCP App.

## 18. Correct process for future MCP App creation

### Phase A — Produce a restartable candidate package

Before launching:

1. Ensure `estate_comms8` exists in a governed repository.
2. Confirm the candidate server source is present.
3. Install it into a known Python environment or establish a documented `PYTHONPATH`.
4. From a fresh terminal, verify that the module imports and record its location.
5. Stop and restart the candidate at least once.
6. Confirm that it returns to port `11808`.
7. Record the exact source commit and package version.

A running process whose module cannot be imported from a fresh process is not deployable.

### Phase B — Validate local MCP behavior

Using the Blue/upstream credential:

1. Unauthenticated `initialize` returns `401`.
2. Authenticated `initialize` returns `200`.
3. `notifications/initialized` is accepted without a normal JSON-RPC response.
4. `tools/list` returns exactly seven expected tools.
5. A read-only tool invocation returns a valid JSON-RPC result.
6. An invalid credential returns `401`.
7. Malformed JSON-RPC returns a structured error instead of terminating the server.

### Phase C — Validate public ingress

Start the reverse tunnel and verify:

1. DNS resolution.
2. HTTPS certificate and hostname.
3. Caddy routing.
4. Authorization-header preservation.
5. Public authenticated `initialize`.
6. Public `notifications/initialized`.
7. Public `tools/list`.
8. Public read-only tool invocation.

Public tests must use the same ChatGPT-facing credential intended for the connector.

### Phase D — Create the ChatGPT App

Configure:

```text
MCP URL:
https://estate-comms8-blue-candidate.ionoge.com/mcp

Authentication:
API key

Authorization scheme:
Bearer

Credential:
ChatGPT-facing candidate credential
```

Then:

1. Connect the app.
2. Refresh actions.
3. Confirm exactly seven expected actions.
4. Start a new ChatGPT conversation.
5. Select the Estate Comms8 app.
6. Invoke `list_requests`.
7. Confirm a valid result.
8. Perform a controlled create/read/resolve lifecycle only when mutation testing is authorized.

### Phase E — Add governed persistence

Only after candidate acceptance:

1. Add Comms8 to the canonical Estate service controller.
2. Give every required process an explicit managed identity.
3. Add PID records and command-line identity validation.
4. Add logs for all managed components.
5. Add authenticated MCP readiness testing.
6. Add controlled stop and restart.
7. Ensure failed readiness prevents promotion.
8. Verify reboot recovery.
9. Verify tunnel-loss recovery.
10. Verify candidate-server failure and recovery.

## 19. Remaining technical debt

### Missing candidate source/package

The live candidate observed as PID `3524` could not be reproduced from the files found on disk. This is the most serious remaining issue.

### Temporary compatibility proxy

The proxy repairs notification handling externally. The permanent solution should correct the candidate server itself. Once native notification support passes acceptance testing, the proxy should be removed unless it has another explicitly approved ingress role.

### Unmanaged live processes

The working connection depended on:

| Component | Observed PID |
|---|---:|
| Original candidate server | `3524` |
| MCP compatibility proxy | `39728` |
| Reverse SSH tunnel | `7536` |

PIDs are observations, not durable identities. These processes were not yet a governed restartable service group.

### No reboot recovery

A Windows restart or permanent failure of any required process can break the app.

### Canonical controller extension required

The observed canonical WebUI/Gateway controller was hard-coded for:

- `grace_runtime`;
- `gateway`;
- `webui`.

Comms8 cannot be added purely through the existing configuration. It requires an intentional controller extension with readiness rules, lifecycle handling, process records, logging, candidate validation, and rollback.

### Operations Runtime Host is not the correct supervisor

The scheduled `Estate Operations Runtime Host` is an operational-work runtime, not the correct service supervisor for Comms8. It was also observed stale after a blocking Git operation. Comms8 must not be attached to it merely because its name includes “Runtime Host.”

## 20. Recommended permanent implementation

The permanent Comms8 service should ideally contain:

1. A corrected, restartable Estate Comms8 MCP server.
2. A managed reverse SSH tunnel.

The compatibility proxy should be removed after native notification handling is corrected and validated.

The canonical controller should validate:

- local port `11808`;
- authenticated MCP `initialize`;
- `notifications/initialized`;
- `tools/list`;
- exact seven-tool identity;
- a bounded read-only semantic test;
- public endpoint readiness;
- expected server name and version;
- tunnel process identity;
- candidate source commit;
- credential-file availability without logging secret values.

A service must not be reported healthy merely because a TCP port is open.

## 21. Definition of correctly created

The Estate Comms8 MCP App is fully created only when:

- the source package exists in a governed repository;
- a fresh Python process can import it;
- the server can be stopped and restarted;
- credential roles are unambiguous;
- local and public initialization succeed;
- notifications are accepted correctly;
- all seven tools are discoverable;
- ChatGPT connects successfully;
- ChatGPT refreshes all actions;
- a real tool invocation succeeds;
- the service survives or recovers from tunnel loss;
- the service recovers after Windows restart;
- logs and readiness evidence are preserved;
- the canonical Estate controller owns the complete lifecycle.

At the time of this repair, the functional ChatGPT connection and tool invocation were demonstrated through the compatibility repair. Restartability, governed supervision, and reboot recovery remained incomplete.

## 22. Relationship to Estate topology work

This document records the live MCP repair and must not be interpreted as authorization to bypass the Common/Blue/Green/Live/Backup migration or the Steward activation gate.

The pending topology package explicitly excludes Estate Comms8 implementation. The recoverable Comms8 package and canonical-controller extension belong in the appropriate later package after repository preparation and activation boundaries are satisfied.

## 23. Safety and secret-handling note

This reference intentionally records:

- credential roles;
- paths to the candidate secret material;
- authentication boundaries;
- expected header shape;
- and observed behavior.

It intentionally does not record any token or Bearer secret value. Token rotation remains a separate operational action after the durable service path is established.
