# Estate-Owned Riverview Bounded Doorbell Bridge

Version: 1.0.0
Date: 2026-08-14

## Ownership

The Estate owns browser authentication, the persistent Chromium profile, the
local CDP endpoint, exact target resolution, the fixed wake action, and
metadata-only evidence. Riverview calls only
`tools/riverview_doorbell_bridge.cjs --ring`.

The pre-existing `chatgpt_mailbox_worker_browser.cjs` remains an Estate-only
worker. Its generic prompt, target fallbacks, DOM utilities, and recovery
operations are intentionally not exposed through this bridge.

## Local configuration

The bridge reads `A:\theestate-data\chatgpt-mailbox-worker\riverview-doorbell.json`
or the path in `RIVERVIEW_DOORBELL_CONFIG`. The file contains only:

```json
{"conversation_id":"00000000-0000-4000-8000-000000000000"}
```

The example value is a placeholder. The real value remains local and is never
written to Riverview, GitHub, PostgreSQL, MCP output, or diagnostics.

## Bounded operation

The sole operation is `ring_riverview_doorbell`. Its input is an operation name,
request ID, correlation ID, and timeout. The bridge resolves exactly one page
whose ChatGPT path is `/c/<configured conversation ID>`, verifies a usable
authenticated composer, and submits the constant:

`Riverview doorbell v1: inspect the Riverview MCP mailbox.`

No response is scraped. Results contain only IDs, bridge version, hashed target
reference, timestamps, status, failure class, and local evidence reference.

Successful request/correlation pairs are idempotent through the local
metadata-only evidence journal. A known success is reconciled without another
wake.

## Preflight

```powershell
node A:\theestate\tools\riverview_doorbell_bridge.cjs --preflight
```

Preflight does not submit the fixed action and reports only boolean readiness
facts.

## Deliberate exclusions

The bridge has no public prompt, selector, URL, navigation, click, keypress,
JavaScript, target enumeration, conversation recovery, scraping, credential,
cookie, or browser-storage interface. RV-008.3 live acceptance remains a
Steward checkpoint.
