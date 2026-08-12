# Autonomous Evidence Acquisition

Date: 2026-08-07

## Contract

`MORE_REASONING_REQUIRED` remains distinct from `EXECUTION_RECOMMENDED`.
When additional information is required, ChatGPT may return a validated
`evidence_request` containing objective, evidence type/target,
provider-neutral capability, bounded allowed/prohibited scope, evidence
requirements, and consultation correlation.

Malformed, unbounded, provider-specific, or mismatched requests fail closed
before provider activation.

## Acquisition flow

The Estate checks current bounded evidence, compact history, and prior
execution evidence first. Only when those sources do not satisfy the request
does the existing capability router create an ordinary provider-neutral
execution request marked `EVIDENCE_ACQUISITION` in its metadata. It uses a
read-only scope and the existing adapter/attempt protocol.

The acquisition does not allocate a reasoning continuation merely because a
provider was invoked. After successful acquisition, the evidence package is
persisted and one continuation is created for ChatGPT reevaluation. The
canonical mailbox worker is woken with its generic prompt; no request ID is
injected.

Acquisition is bounded to three provider acquisitions across a consultation
root. Provider failure remains an execution-attempt failure; it does not
become a reasoning continuation. Missing evidence and acquisition-limit
conditions remain truthful outcomes.

## Live evidence

The existing consultation root `5.00` produced structured evidence requests
on `5.05` and `5.06`. Both were acquired through the real read-only provider
path and automatically reevaluated by ChatGPT. The acquisition execution
records and attempts are durable under the consultation projection. ChatGPT
continued to request bounded README facts on `5.07`, demonstrating truthful
bounded iteration rather than fabricated closure. The root projection was
updated idempotently and remains locally authoritative/pending for its
optional GitHub publisher.

The first attempt exposed and fixed a local-history false positive: the
request specification itself was excluded from the evidence search, so it
cannot satisfy its own request.

## Activation

ACTIVATION REQUIRED:

1. Relaunch the canonical mailbox worker after deploying evidence-contract
   or acquisition code. Verify canonical preflight, the generic prompt, and
   authoritative Comms8 events.
2. Restart Grace Gateway only when its long-running process must load changed
   Grace/acquisition code.

Execution router/provider relaunch is CONDITIONAL where separately
supervised. Open WebUI, Comms8, MCP adapter, Runtime Host, browser,
workstation restart, and ChatGPT reconnect are NOT REQUIRED unless the
existing authenticated target is unavailable.

## Tests

Evidence-contract, worker, Grace, execution, provider-adapter, store, and
projection suites: `62 passed`.

## Final bounded reevaluation — 2026-08-07

The existing root `5.00` completed its third and final provider evidence
acquisition for the authoritative `5.07` request:

- acquisition #1: `exec-699872282a3d`
- acquisition #2: `exec-325be6788bd4`
- acquisition #3: `exec-e8d7d5d891b5`
- all three used capability `repository_read` and completed read-only;
- no fourth provider acquisition was created.

ChatGPT reevaluation created `5.08`. Its additional evidence request was
persisted, but the budget guard returned `EVIDENCE_ACQUISITION_LIMIT_REACHED`
before capability/provider activation. Grace’s durable outcome is therefore
truthfully unresolved and available for Steward review.

The root projection was updated idempotently. The final focused suite after
atomic reservation and post-budget handling: `51 passed`.
