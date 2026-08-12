# Estate CME Stale-Owner Recovery Live Acceptance — 2026-08-07

Status: **accepted — late authoritative completion reconciled**

## Boundary

The live acceptance was launched with:

`python tools/cme_owner_isolation.py launch-live --timeout-seconds 900`

The launch returned immediately. A separate `inspect` command read the durable
manifest. The harness, acceptance child, and canonical worker were outside the
Codex command-runner process tree.

## Preflight and recovery

Preflight recorded consultation 7.00, the original Comms8 request, CME state,
stale lock, recorded PIDs, PID liveness, lease state, and current worker
process metadata. Recorded CME PIDs `33292` and `37696` were dead. No active
lease existed on the original request at recovery time.

The original request later became `expired`; this was an unavoidable terminal
expiry rather than a new consultation request. The same logical consultation
was retained and the existing transport-recovery identity produced
`ec8-4ce9c5dc3e8a4c74`. Its lifecycle reached `claimed` and `acknowledged` by
`worker_id=chatgpt`.

## Failure evidence

The canonical browser adapter initially reported `ASSISTANT_RESPONSE_STABLE` after
selecting the ChatGPT target titled `Request Processing Limitation`. It did
not produce those events immediately; the worker therefore correctly failed
closed with `authoritative_comms8_completion_not_proven`. The same attempt
later completed authoritatively: `responded` at `16:29:27Z` and `resolved` at
`16:31:07Z`. The MCP trace records successful `respond_request` and
`resolve_request` calls.

The late-completion reconciliation read the authoritative receipt, performed
Grace readback, reconciled CME to `IDLE`, removed the stale lock, and ran a
duplicate tick that returned `EMPTY_QUEUE`. No second consultation or
transport was created after the replacement.

## Acceptance result

The final evidence is under
`runtime/evidence/cme-owner-isolation/cme-owner-20260807T162309848276Z-986c30040b`.
`grace-readback.json` is authoritative, `final-cme-state.json` records
`IDLE`/no lock/`resolved`, and the post-reconcile detached manifest completed
successfully.

Required final evidence remains:

- queued → claimed → acknowledged → responded → resolved;
- response and lease identity;
- Grace authoritative readback;
- stale activation history plus separate successful CME activation;
- truthful CME idle/completed state and no stale lock;
- duplicate tick with no second launch or claim.

Root cause remains unproven:
`ORIGINAL_CME_OWNER_TERMINATION_CAUSE_UNPROVEN`.
