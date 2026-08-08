# Estate Comms8 Grace Autonomous Consultation Loop

> Continuation note (2026-08-07): an expired unanswered transport attempt
> is replaced without allocating a consultation continuation; genuine new
> evidence allocates the next logical turn. See
> `ESTATE-COMMS8_Consultation_Transport_Recovery_20260807.md`.

Status: Implemented locally; Live acceptance blocked at the ChatGPT app/tool
attachment boundary

## Boundary

`estate.core.grace_consultation_loop.GraceConsultationLoop` is the narrow
Grace-side integration. It activates only for explicit natural-language
delegation such as “ask ChatGPT”, “get a second opinion”, or “consult
ChatGPT”. Ordinary Grace conversation remains on `process_chat`.

The loop allocates logical consultation IDs through `ConsultationStore`,
persists the consultation before transport, creates the Live Comms8 request,
attaches the resulting `ec8-*` identity, wakes the existing autonomous
ChatGPT mailbox worker with its generic prompt, and reads the resolved
request authoritatively. It persists the response and leaves the
consultation in `validating`; receipt of a response is not treated as
validation or closure.

## Continuations

An explicit follow-up containing new evidence, a failed recommendation, or
an after-restart constraint selects the latest compatible unresolved
consultation and allocates the next Estate-owned child (`N.01` through
`N.99`). The bounded context envelope includes the parent, prior response,
current evidence, PTM references, tags, and question. `.99` rollover remains
owned by the consultation store.

Create retries reuse a matching untransported consultation intent rather
than allocating another logical turn. A failed Comms8 create retains the
logical record and reports a truthful failure. GitHub is not consulted and
does not block the foreground operation.

## Worker relationship

Grace never supplies a request ID to ChatGPT. The existing worker receives
only its generic mailbox instruction and performs `claim_next` as
`worker_id=chatgpt`. Grace verifies the worker result against the Live
authoritative read path; generated prose such as `WORKER_COMPLETE` is not
accepted without a resolved request and stored response.

The system-Python Resident Gateway invokes the accepted Open WebUI MCP client
through the Open WebUI virtual environment helper
`estate.core.grace_live_mcp_cli`. This isolates the native `pydantic_core`
runtime dependency and does not alter Comms8 or the Streamable HTTP adapter.

## Validation and future boundaries

The response state is `validating`. Grace may later append expected result,
observed result, and evidence through the consultation store. Failed
validation creates a continuation; a successful recommendation may be
closed by the appropriate authority. PTM references remain references only.
GitHub remains an asynchronous projection. Automatic Grace execution,
general conversation routing, and Codex adapter changes are out of scope.

## Activation

Because `resident_gateway.py` changed, restart only the Resident Gateway
owner after the source is installed. Open WebUI, Comms8, the MCP adapter,
ChatGPT plugin, and the workstation do not require restart. A new Grace
conversation or Ctrl+F5 is conditional on the UI holding old model/session
state. The running PID and port must be verified before acceptance.

## Local validation

Focused loop, worker, consultation, and Resident Gateway tests pass. The
controlled Live attempt allocated a root and created one queued Live request,
but ChatGPT returned generic `WORKER_COMPLETE` prose without a corresponding
Live `claim_next` event. The worker correctly failed closed, leaving the
request queued and preventing a false acceptance. Root and continuation Live
acceptance remain blocked until the authenticated ChatGPT Live app/tool
attachment is restored and positively evidenced.

The attachment continuation confirms the current target is authenticated
with a ready composer but lacks a provable production Live app attachment
and complete seven-action discovery. The existing queued request remains the
sole active acceptance artifact.
