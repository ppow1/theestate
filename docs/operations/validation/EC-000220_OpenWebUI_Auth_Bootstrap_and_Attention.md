# EC-000220 — Open WebUI auth bootstrap and operator attention event

Status: **Implemented; live Grace/GPU acceptance blocked by P100 device-loss stop condition**  
Base: `87882b92cf17ddc04f565cc7ed7b42b2c66d7201`

## Boundary repaired

The existing `tools/openwebui_operator_acceptance.cjs` now treats
`LOGIN_REQUIRED` as an activation boundary. It emits one safe operator-attention
event for the run, closes the unauthenticated context, launches the existing
headed `auth-bootstrap` flow with the same persistent profile, waits for the
bounded authentication result, emits a correlated resolution/timeout/cancel
event, reopens the same profile, and resumes the original readiness/scenario
path after successful authentication.

The canonical profile remains
`runtime/browser/openwebui-operator-profile/`. Candidate and canonical URL
origins use that same profile; origin-specific cookies remain governed by
Open WebUI. Credential entry uses the existing bootstrap privacy mode:
screenshots, tracing, console/network capture, and credential persistence in
acceptance evidence are disabled. No credentials, cookies, bearer tokens, or
local-storage dumps are written by the harness.

## Event ownership

The durable producer target is the existing operational event contract in
`src/estate/core/operational_events.py`, under
`runtime/operations/events/YYYY-MM-DD.jsonl`. The harness-side producer is
`tools/openwebui-operator/operator-attention.cjs`; it writes only the existing
provider-neutral operational-event shape. The event types are:

- `Operator Attention Required`
- `Operator Attention Resolved`
- `Operator Attention Timed Out`
- `Operator Attention Cancelled`

The metadata includes only `operator_attention`, reason
`OPENWEBUI_AUTHENTICATION_REQUIRED`, sanitized surface URL, run ID, relative
profile path, required operator action, and lifecycle status. The deterministic
run-based event ID prevents notification spam during repeated polling. Existing
notification aggregation remains transport-independent; future Notifier
channels may consume this event without changing the browser producer.

## Evidence and limits

The prior EC-000219 acceptance stopped at `LOGIN_REQUIRED` because it reported
the harness result without invoking the already-supported interactive bootstrap.
This change repairs that transition. A real authenticated Grace conversation,
GPU placement, and provider receipt still require a safe GPU gate. Timeout or
cancellation deliberately submits no Grace prompt and does not invoke provider
execution.

## Live candidate observation

The approved green candidate ran on ports `8767`, `11436`, and `8081`. Harness
run `openwebui-operator-20260809225721242-67363b71` visibly opened headed
Chromium, printed `OPENWEBUI AUTHENTICATION REQUIRED`, used
`runtime/browser/openwebui-operator-profile`, detected the authenticated Grace
model picker, and automatically resumed with `OPENWEBUI_READY`.

The required event was
`ope-openwebui-auth-openwebui-operator-20260809225721242-67363b71-required` and
the correlated resolution was
`ope-openwebui-auth-openwebui-operator-20260809225721242-67363b71-resolved`.
No credentials or sensitive browser evidence were persisted.

Before a Grace prompt could be submitted, the fresh read-only NVIDIA gate
reported: `Unable to determine the device handle for GPU0: 0000:04:00.0: GPU
is lost`. The RTX 4090 remained visible with 21950 MiB free. Per PL-0042 and
the session stop rules, acceptance stopped immediately; candidate services
were shut down, no model or Grace prompt was launched, and no recovery was
attempted. Evidence is preserved at
`runtime/evidence/ec000220/gpu-loss-after-stop.txt` and the Playwright run
directory under `runtime/evidence/openwebui-operator/`.
