# Estate Grace Operational Reasoning and Action Architecture

Grace has two distinct response boundaries:

1. Ordinary conversation may use resident reasoning and bounded context.
2. Current or historical mutable Estate facts require the authoritative
   operational-memory read in `estate.core.grace_operational_memory`.

The operational read is read-only. It opens the existing consultation SQLite
store, reconstructs the latest completed root from ordered turn numbers and
durable timestamps, counts execution requests and physical attempts, and
reads the CME runtime state. It does not use GitHub projection, browser
conversation history, persona prose, or prompt-injected facts as authority.

`9.04` is therefore reported as a turn of root `9.00`, not as a new root.
Execution is determined from durable execution-request and attempt records,
not from the final reasoning classification.

Each returned fact carries source and authority metadata. If the store or
runtime state cannot be read, Grace returns `STATE_UNAVAILABLE / unable to
verify` rather than reconstructing a plausible answer. The gateway invokes
this boundary before resident prose generation, so an operational read does
not create a resident conversation turn or any consultation, Comms8, CME, or
execution mutation.

The boundary is intentionally narrow: conceptual questions continue through
the normal resident conversation path.

## Multi-step operational reasoning

The gateway distinguishes a pure operational lookup from a composite request.
A lookup such as “What is the latest completed consultation?” may return the
authoritative snapshot directly. A request that also asks for provenance,
explanation, comparison, recommendation, action categories, or a required
terminal token enters grounded composite reasoning.

For composite requests, the original user message is preserved and the
bounded operational snapshot is injected as per-request evidence into the
existing resident reasoning prompt. A successful read is not a terminal
answer by itself. One bounded completeness repair is allowed; if the
obligations still cannot be satisfied, Grace returns an explicit incomplete
or unavailable result rather than silently discarding subquestions.

Terminal provenance tokens describe the underlying action being evaluated,
not completion of the inquiry. `AUTHORITATIVELY_COMPLETED` requires a
successful correlated `authoritative_action`; `PENDING_EXECUTION` requires a
requested/authorized action still pending; otherwise a requested terminal
status is `INSUFFICIENT_EVIDENCE`. `authoritative_read` alone cannot prove a
write or recording action.

## Action completion claims require authoritative action provenance

Operational reads, model inference, and completed side effects are separate
claim classes. A resident may report a read fact only from the operational
snapshot, may offer inference as inference, and may report an action as
completed only when the runtime supplies a successful result marked
`authoritative_action` (or a verification marked `authoritative_read`).
Unsupported claims such as “I recorded,” “I documented,” “I tagged,” or “I
verified” are replaced with an explicit unperformed/unverified response.
## External reasoning provenance

External reasoning is an Estate event, not resident prose. Bounded phrases
such as “I want a second opinion on this, not from you” enter the existing
GraceConsultationLoop, which allocates the consultation, creates the Comms8
request, wakes the existing ChatGPT worker, and reads the durable response.
Grace may claim an external review only when the current request has a
correlated authoritative consultation, transport request, provider identity,
and response ID. Failed allocation, transport, timeout, or insufficient
provider response produces a truthful attempted/unavailable result and never
an invented provider conclusion.

## Execution and reevaluation boundary

When an authoritative reasoning turn contains a valid
`EXECUTION_RECOMMENDED` decision, the existing neutral execution router
creates the request and selects the provider by capability. After a terminal
provider result, the canonical handoff persists validation evidence and
automatically attaches one continuation under the same consultation root.
CME owns the next reasoning activation; Grace does not launch a provider or
invent a completion claim. The final Steward response must be grounded in the
execution request, physical attempt, provider result, and authoritative
reevaluation.
