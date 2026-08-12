# Estate ChatGPT Autonomous Reasoning Resident

## Ownership and wakeup

ChatGPT remains a bounded resident, not a free-running agent. The
`ChatGPTReasoningResident` evaluates the consultation store for
`awaiting_reasoning` work and invokes the existing canonical mailbox worker
once. The mailbox worker still owns Comms8 claim/acknowledge/respond/resolve
processing, and Comms8 remains authoritative.

The smallest eligible transition is a consultation or continuation entering
`awaiting_reasoning` with its existing queued `ec8-*` transport attached.
Grace’s explicit delegation path, execution/evidence continuation paths,
and the existing worker activation wrapper are the current wake sources.
They all remain one-shot and idempotent at the logical consultation layer.

The existing Continuous Momentum Engine is not a scheduler, dispatcher, or
browser owner. Its `reasoning_wakeup_candidate` projection can be consumed
by CME/Grace evaluation with canonical source references, but activation
remains with the existing Grace/runtime owner. No second scheduler was
introduced.

## Durable context

Before activation, `build_durable_context_package` creates a bounded
package containing root/current/parent IDs, objective/question, compact
summary, prior recommendation, current evidence, bounded execution
evidence, PTM references, tags, and escalation state when present. Grace
places this package in the Comms8 request envelope. ChatGPT retrieves it
through the generic mailbox flow; no request-specific browser prompt or
physical-chat memory is required.

The package is capped to the compact summary and latest five turns’ bounded
execution references. SQL consultation history remains authoritative for
deeper recovery.

## Resident states

The resident state file uses:

`CHATGPT_REASONER_IDLE`, `CHATGPT_REASONER_WAKE_PENDING`,
`CHATGPT_REASONER_PROCESSING`, `CHATGPT_REASONER_WAITING_FOR_EXECUTION`,
`CHATGPT_REASONER_WAITING_FOR_EVIDENCE`, `CHATGPT_REASONER_ESCALATED`, and
`CHATGPT_REASONER_ERROR`.

`EMPTY_QUEUE`, terminal conclusions, and unresolved escalation leave the
resident quiet. `STEWARD_DECISION_REQUIRED` suppresses further wakeups for
that root until an explicit valid Steward event creates a new
`awaiting_reasoning` continuation.

## Physical conversation policy

The worker continues to use the existing Live app readiness and generic
mailbox prompt. A healthy attached conversation may be reused by the
existing browser owner; otherwise the existing attachment/recovery boundary
may create a fresh conversation. No logical consultation identity depends
on the physical chat.

## Continuations and recovery

Execution evidence and evidence acquisition already create durable
continuations and wake the canonical worker. Steward resume uses the
existing consultation lineage path. A worker relaunch reconstructs
eligibility from SQLite and processes at most one request; it does not
duplicate completed work.

## Activation

- **REQUIRED:** CME/Grace owner restart only if deploying a changed
  resident/coordinator module into a long-lived owner; verify the resident
  state file and bounded context digest.
- **REQUIRED:** canonical mailbox-worker relaunch when worker source changes;
  verify canonical runtime preflight and generic prompt operation.
- **CONDITIONAL:** Grace Gateway restart when its long-lived process loads
  changed context/wakeup code; execution/provider or consultation-worker
  relaunch only when those supervised components changed.
- **NOT REQUIRED:** Open WebUI, Comms8, MCP adapter, Runtime Host,
  ChatGPT reconnect, dedicated browser, or workstation restart for the
  coordinator-only change.

The smallest order is deploy the coordinator/Grace code, restart only the
affected long-lived owner, then relaunch the mailbox worker if its code was
changed. No broad restart is required.

## Live acceptance note — 2026-08-07

The ordinary-language Grace acceptance created consultation `6.00` and
transport `ec8-d4319629b9b34d46` without a request-specific ChatGPT prompt.
The worker claimed it as `chatgpt`, but the old browser automation timed out
before authoritative response/resolution. The request later completed
authoritatively and was reconciled without duplication. The browser repair
and the genuine `6.01` continuation completion are documented in
`ESTATE_ChatGPT_Browser_Completion_Reliability_20260807.md`.
