# Estate Comms8 Consultation Transport Recovery

Status: accepted for consultation `3.00` and continuation `3.01`.

## Contract

The durable consultation turn and Comms8 transport attempt are separate.
An unanswered turn may retain multiple immutable transport attempts. A
terminal `expired` attempt is never reopened or rewritten. Recovery reserves
one replacement attempt atomically, preserving the same logical consultation
ID and recording `supersedes_request_id`.

Retry is allowed only when the current Comms8 record is `expired`, has no
response or resolution, and no active replacement exists. Other terminal or
active states fail closed. Repeated recovery returns the existing creating or
active replacement and cannot allocate another attempt.

## Live evidence

Consultation `3.00`:

- attempt 1: `ec8-8db54efb5c234f0a`, expired after the wrong-worker lease;
- attempt 2: `ec8-61b2b5c9191b4822`, claimed, acknowledged, responded, and
  resolved by `worker_id=chatgpt`;
- consultation response persisted and logical ID remained `3.00`.

The original request remains immutable and queryable. No Comms8 requeue or
reopen semantics were added.

Continuation `3.01` was created only after `3.00` returned. Its request
`ec8-a68e19268f9e444e` completed with `worker_id=chatgpt`, and its response is
persisted under `3.01`.

## Failure distinction

Attempt 1 is recorded as `wrong_worker_lease_expired`, a transport failure,
not failed reasoning. The replacement carries the same consultation envelope
and a transport-specific idempotency key. A genuine new question/evidence
allocates a continuation; transport retry does not.

## Tests and activation

Focused consultation, Grace loop, and mailbox worker tests pass (`27 passed`
before the final worker reconciliation changes; the directly affected suite
was rerun after those changes). Tests cover immutable expired attempts,
single replacement reservation, response/active-attempt rejection, and
same-turn recovery.

`mailbox worker relaunch` is REQUIRED after worker/store source changes.
ChatGPT fresh conversation/reconnect is CONDITIONAL when the existing Live
attached target is unavailable. Open WebUI, Grace Gateway, Comms8, MCP
adapter, Runtime Host, and workstation restarts are NOT REQUIRED.
