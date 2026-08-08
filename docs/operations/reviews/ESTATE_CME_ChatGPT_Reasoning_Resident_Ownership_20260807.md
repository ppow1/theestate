# Estate CME ChatGPT Reasoning Resident Ownership — 2026-08-07

Status: **accepted — CME ownership and late authoritative reconciliation complete**

The accepted process-ownership unit proof is complete under the detached
`tools/cme_owner_isolation.py` harness. The focused ownership suite completed
5 tests independently of the Codex runner. No live state was used by that
proof.

## Ownership contract

- Codex launches the detached harness and performs later read-only inspection.
- CME is the only authorized owner for a normal ChatGPT mailbox activation.
- The canonical mailbox worker uses generic `claim_next` with
  `worker_id=chatgpt`; no request ID is supplied to ChatGPT.
- A stale CME state may be reclaimed only when recorded PIDs are dead, no
  authoritative lease is active, and consultation 7.00 remains eligible.
- Failed activation history is retained separately from a replacement
  activation.

## Current evidence

The original request `ec8-198ea46afd3e4b93` was queued during initial
preflight, then authoritatively expired because its expiry time had elapsed.
The existing logical consultation `7.00` was preserved. Governed transport
recovery created replacement request `ec8-4ce9c5dc3e8a4c74`; it was claimed and
acknowledged by `chatgpt`.

The detached live run is recorded under
`runtime/evidence/cme-owner-isolation/cme-owner-20260807T162309848276Z-986c30040b`.
The browser reached a stable assistant response, but the selected ChatGPT
target was `Request Processing Limitation`; no authoritative Comms8
`responded` or `resolved` event was produced. The live acceptance therefore
did not pass and must not be represented as resident-ownership ready.

Root cause classification remains:
The browser first reported `WORKER_COMPLETE` before Comms8 reconciliation;
this was classified as `WORKER_COMPLETE_BEFORE_COMMS8_RECONCILIATION` and,
after the later lifecycle completion, `LATE_AUTHORITATIVE_COMPLETION`.
The original CME owner termination cause remains:
`ORIGINAL_CME_OWNER_TERMINATION_CAUSE_UNPROVEN`.

## Activation requirements

| Requirement | Classification | Evidence/condition |
|---|---|---|
| Detached CME acceptance harness launch | REQUIRED | Accepted and used |
| CME owner relaunch | REQUIRED | Required after active lease is safely terminal |
| Mailbox worker manual relaunch | NOT REQUIRED | Must remain CME-owned |
| Grace restart | NOT REQUIRED | Existing runtime was reachable |
| Open WebUI restart | NOT REQUIRED | Existing runtime was reachable |
| Comms8 restart | NOT REQUIRED | Adapter answered; lifecycle completion failed |
| MCP adapter restart | NOT REQUIRED | Read/creation calls were reachable |
| ChatGPT reconnect/new conversation | CONDITIONAL | Required only to clear the processing-limitation target |
| Browser restart | CONDITIONAL | Use only if the accepted target cannot be repaired in place |
| Workstation reboot | NOT REQUIRED | No evidence requires it |

The replacement request reached
`responded` and `resolved`, Grace readback is authoritative, CME returns to a
truthful idle/completed state, and a duplicate tick launches nothing.

All conditions are now evidenced: CME is `IDLE`, the lock is absent, the
consultation is `resolved`, and the duplicate tick returned `EMPTY_QUEUE`.
