# Estate Comms8 Autonomous ChatGPT Mailbox Worker

> Continuation note (2026-08-07): transport recovery now distinguishes an
> unanswered logical consultation from its Comms8 attempts. See
> `ESTATE-COMMS8_Consultation_Transport_Recovery_20260807.md`.

Status: Implemented and locally validated  
Date: 2026-08-07

## Scope

This increment is the first runtime consumer of the durable consultation
store. It does not implement Grace delegation, Grace readback, PTM mutation,
Comms8 redesign, or GitHub-dependent processing.

Implementation:

- `src/estate/core/autonomous_chatgpt_mailbox_worker.py`
- `tools/chatgpt_mailbox_worker_browser.cjs`
- `tests/test_autonomous_chatgpt_mailbox_worker.py`

## Lifecycle

The worker selects the oldest consultation in `awaiting_reasoning`, verifies
that it has an attached `ec8-*` transport reference, persists worker state,
and sends one generic instruction to the existing authenticated ChatGPT Live
CDP target. The browser prompt contains no request ID.

ChatGPT performs `claim_next`, processes only the returned request, and owns
the authoritative Comms8 claim/acknowledge/respond/resolve lifecycle. After
the browser reports `WORKER_COMPLETE`, the worker reads the known linked
request through Live MCP, requires `resolved` plus a stored response, appends
that response to the consultation store, and marks the consultation resolved.

`EMPTY_QUEUE` is truthful and causes no request mutation. `CONTEXT_REQUIRED`
changes the consultation to `continuation_required`. Browser, Comms8, or
result-verification failures remain `ERROR` and do not fabricate completion.

The persisted worker states are `IDLE`, `CHECKING_QUEUE`, `PROCESSING`,
`WAITING_FOR_RESPONSE`, `ERROR`, and `STOPPED` in:

`A:\theestate-data\chatgpt-mailbox-worker\worker-state.json`

## Activation model

`--once` performs one activation and one request maximum. `--watch` uses a
bounded two-second consultation-database mtime check because the current
SQLite foundation has no notification bus. It exits after the bounded timeout
or after one completed activation. This is bounded activation polling, not an
unbounded browser or Comms8 polling loop.

Examples:

```text
PYTHONPATH=A:\theestate\src C:\Python314\python.exe -m estate.core.autonomous_chatgpt_mailbox_worker --once
PYTHONPATH=A:\theestate\src C:\Python314\python.exe -m estate.core.autonomous_chatgpt_mailbox_worker --watch --max-seconds 300
```

The existing dedicated browser/CDP owner remains authoritative. The worker
requires an authenticated page titled `Estate Comms8 Live` on CDP `9224` and
does not create a second browser automation framework.

## Failure and restart behavior

- Browser restart/disconnect: worker records `ERROR`; a later activation can
  retry through `claim_next`, subject to Comms8 lease expiry.
- Comms8 outage: authoritative completion is not claimed locally; worker
  records `ERROR` and does not update the consultation as resolved.
- ChatGPT response ambiguity: missing `WORKER_COMPLETE` fails closed.
- GitHub outage: no effect; GitHub remains projection-only.
- Open WebUI outage: the worker does not depend on Open WebUI; it uses the
  existing ChatGPT Live browser/app path.
- Worker restart: state JSON remains available; Comms8 lease semantics and
  idempotent lifecycle are authoritative safeguards against duplicate work.

The worker never injects an `ec8-*` ID into ChatGPT. The only request ID used
afterward is the consultation store's already-established correlation for
authoritative verification.

## PTM and consultation integration

PTM project/work-item references remain untouched. Standalone consultations
are valid. Logical consultation IDs, context, evidence, response, and
validation remain in the Estate consultation SQLite store. The worker does
not read GitHub for context and does not create duplicate PTM objects.

## Operator visibility

Inspect `worker-state.json` for current state, logical consultation ID,
result, error, and timestamps. Inspect the linked Comms8 request through the
governed Live MCP service for authoritative lifecycle and response evidence.

## Activation requirements

- Open WebUI restart: NOT REQUIRED
- Grace Resident Gateway restart: NOT REQUIRED
- Comms8/MCP adapter restart: NOT REQUIRED
- ChatGPT plugin reconnect: CONDITIONAL — only if the existing Live app page
  is absent or disconnected
- Dedicated browser restart: CONDITIONAL — only when CDP `9224` has no
  authenticated `Estate Comms8 Live` target
- Workstation reboot: NOT REQUIRED

For this source-only worker, no existing Estate service requires restart.
Start the worker after the dedicated browser and Live app are healthy.

## Controlled Live acceptance

On 2026-08-07 one consultation was allocated as `1.00` and linked to one
Live request `ec8-0e79af4e9c6b4f7a`. The browser instruction was generic and
contained no request ID. ChatGPT used the Live app's `claim_next` flow and
the authoritative request recorded exactly one `chatgpt` claim, one
acknowledgement, one stored response, and one resolution. The final response
contained exactly three concise recommendations.

The first worker process timed out at the browser completion-observation
boundary after ChatGPT had already completed the authoritative lifecycle.
The browser helper had targeted ChatGPT's hidden fallback textarea; the
existing visible ProseMirror `contenteditable` composer and submit control
are now used. The worker also has a recovery guard that reconciles a linked
already-resolved Comms8 record before opening ChatGPT again. This prevents a
browser observation failure from causing duplicate processing.

The recovery activation marked consultation `1.00` `resolved` and persisted
the authoritative response ID without another claim. Final worker state was
`STOPPED / WORKER_COMPLETE`; Live state and consultation state agree.

Focused worker and consultation tests: `15 passed`.

## Attachment-readiness continuation

The worker now performs a pre-submit CDP readiness check. It requires the
exact `Estate Comms8 Live` app outside sidebar conversation labels and all
seven canonical action names. Failure classifications include
`CHATGPT_NOT_AUTHENTICATED`, `LIVE_APP_NOT_FOUND`,
`LIVE_APP_TOOL_DISCOVERY_FAILED`, and `COMPOSER_NOT_READY`. The generic
prompt is not submitted on readiness failure.
