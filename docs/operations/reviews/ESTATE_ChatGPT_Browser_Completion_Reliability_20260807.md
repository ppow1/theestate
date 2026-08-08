# Estate ChatGPT Browser Completion Reliability

## Failure classification

The first resident live run narrowed the failure to
`CHATGPT_GENERATION_EXCEEDED_TIMEOUT` at the old browser boundary. The
request was claimed and acknowledged, the browser subprocess timed out at
240 seconds, and Comms8 later recorded the response and resolution. This was
not a failed claim, duplicate processing, or fabricated completion.

## Completion state machine

The browser adapter now records metadata-only transitions:

`TARGET_SELECTED` → `READINESS_PROBED` → `PROMPT_INSERTED` →
`SUBMIT_CONFIRMED` → `GENERATION_STARTED` → `RESPONSE_PROGRESS` →
`FINAL_ASSISTANT_MARKER` or `FINAL_ASSISTANT_STABLE` → authoritative
Comms8 reconciliation.

The trace contains elapsed milliseconds, target URL without query data,
workspace/readiness booleans, assistant counts, output lengths, stop-
generating presence, and tool-card counts. It does not store credentials or
full conversation content. The last trace is written to
`A:\theestate-data\chatgpt-mailbox-worker\browser-diagnostics.json`.

## Timeout contract

Composer/readiness checks remain bounded separately from generation. The
browser waits up to 45 seconds for generation to start and up to 540
seconds for bounded completion. The Python child-process ceiling is 600
seconds, leaving a reconciliation margin within the existing lease window.
The browser returns a precise failure classification when either bound is
reached.

Generation is considered complete visually only after a final marker or a
new assistant response has remained stable for four seconds with no active
stop-generating signal. Tool cards alone never complete the operation.
Python then requires authoritative Comms8 state plus response before
returning `WORKER_COMPLETE`.

## Lease and recovery

An active lease, including one owned by `chatgpt`, is never duplicated by a
second browser submission. A terminal expired request remains immutable and
uses the accepted transport-recovery path. A browser timeout therefore does
not create a reasoning continuation or replacement request by itself.

## Live acceptance

- Root `6.00` completed information-only after the first long-generation
  run was reconciled; no duplicate request was created.
- Genuine continuation `6.01` completed through the generic worker path and
  Grace automatic readback. It returned an authoritative structured
  information-only result.
- Both requests were claimed by `worker_id=chatgpt`; no request ID was
  supplied in the browser prompt.

## Activation

- **REQUIRED:** mailbox worker relaunch after deploying the changed Python
  runner; verify the worker uses the 600-second child ceiling and writes a
  metadata-only browser trace.
- **CONDITIONAL:** Grace/CME owner restart if loading changed resident code;
  ChatGPT reconnect/new conversation or dedicated browser restart only if
  the current authenticated Live target is unavailable.
- **NOT REQUIRED:** Open WebUI, Comms8, MCP adapter, execution provider,
  router, or workstation restart for this browser-boundary repair.
