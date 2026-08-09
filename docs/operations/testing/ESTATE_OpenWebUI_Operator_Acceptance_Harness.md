# Estate Open WebUI Operator Acceptance Harness

The canonical operator-level browser client is `tools/openwebui_operator_acceptance.cjs`.
It is an acceptance client, not an Estate authority: all mutation must begin as
ordinary text in the real Open WebUI. Backend adapters in the harness are
read-only validators only.

## Canonical invocation

```powershell
CLS
cd A:\theestate-openwebui-acceptance
node tools/openwebui_operator_acceptance.cjs readiness --headed
node tools/openwebui_operator_acceptance.cjs doctor --headed
node tools/openwebui_operator_acceptance.cjs scenario scenarios/grace_openwebui_basic.yaml --headed
```

If readiness reports `LOGIN_REQUIRED`, bootstrap the same persistent profile in
a visible browser:

```powershell
node tools/openwebui_operator_acceptance.cjs auth-bootstrap
```

The command waits for a human to complete login, records no console/network
credential evidence, and closes after the authenticated semantic surface is
detected. `--timeout` controls the bounded human wait (default: 30 minutes).
Ctrl+C cancels cleanly without deleting the profile.

For an already-authenticated visible browser, use a separate Open WebUI page
through the existing CDP endpoint:

```powershell
node tools/openwebui_operator_acceptance.cjs readiness --connect-cdp http://127.0.0.1:9224
```

The harness never stores passwords. A persistent Playwright profile defaults to
`runtime/browser/openwebui-operator-profile/`, which is ignored by Git. A
one-time human login may be completed in headed mode; rerun readiness afterward.

## Boundary and evidence

The harness discovers the configured URL from `ESTATE_OPENWEBUI_URL`, then uses
the local Estate default `http://127.0.0.1:8080` only when no environment value
is present. It selects residents from visible UI text, opens a fresh UI
conversation, submits through the visible composer, and waits for a new
assistant message to stabilize. It does not call the Gateway, SQLite, CME, or
Comms8 to create work.

Each run writes `runtime/evidence/openwebui-operator/<run-id>/` with a manifest,
scenario, screenshots, sanitized console/network records, response text, a
bounded DOM failure summary, trace, and completion marker. Query strings,
headers, cookies, and request bodies are not recorded.

Process-sensitive browser runs must be launched at the detached boundary used
by the Estate, for example:

```powershell
python tools/cme_owner_isolation.py launch -- node tools/openwebui_operator_acceptance.cjs scenario scenarios/grace_openwebui_basic.yaml --connect-cdp http://127.0.0.1:9224
```

Use the repository's actual isolation wrapper syntax if it differs; never make
Codex's process the owner whose survival defines acceptance.

## Result semantics

`PASS` means the UI interaction and declared scenario assertions passed.
`BLOCKED` preserves evidence and a classification such as
`OPENWEBUI_UNAVAILABLE`, `LOGIN_REQUIRED`, `RESIDENT_NOT_FOUND`,
`COMPOSER_NOT_FOUND`, `STREAM_TIMEOUT`, `NETWORK_ERROR`, or `UI_CHANGED`.
An Open WebUI answer is not backend proof: scenario validators must compare it
with separately read authoritative evidence.
