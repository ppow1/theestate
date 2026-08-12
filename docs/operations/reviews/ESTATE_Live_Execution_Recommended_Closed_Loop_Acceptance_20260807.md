# Live Execution-Recommended Closed-Loop Acceptance

Date: 2026-08-07

## Result

The live autonomous chain is proven through the existing Grace,
Comms8, ChatGPT, consultation, execution-provider, and readback seams.

The acceptance used one Grace-originated consultation root, `5.00`, and
same-consultation continuations caused by context/schema/evidence findings.
No execution request or request ID was supplied by the Steward.

## Live chain evidence

The successful decision turn was `5.03`:

- Comms8 request: `ec8-9414869698c643a6`
- worker: `chatgpt`
- authoritative lifecycle: created, claimed, acknowledged, responded,
  resolved
- structured classification: `EXECUTION_RECOMMENDED`
- required capability: `software_engineering_test`
- allowed scope: `tests/fixtures/ptm_read_only_adapters`
- prohibited scope included `src`, `runtime`, and `.git`
- consultation correlation: `5.03`

The Estate automatically created exactly one logical execution request:

- execution request: `exec-458e60d1e581`
- provider selected by capability routing: `codex-cli-openai`
- physical attempt: `attempt-223685fd445d`
- provider result: `completed`
- sandbox: read-only
- live provider called: true
- execution events: validation passed, job accepted, execution started,
  result returned, execution complete
- result persisted under the consultation

The Codex-specific prompt-source requirement was handled at the provider
adapter boundary. The neutral objective remains neutral; the adapter uses
an existing bounded source when supplied and otherwise materializes only the
bounded prompt text in its runtime prompt area before bridge validation.

## Automatic reevaluation

Execution evidence exposed a real constraint: the provider reported that the
targeted pytest run was blocked by the absence of a usable temporary
directory. The Estate allocated continuation `5.04` from that evidence and
created Comms8 request `ec8-0073d9c34cb74d5e` without operator request IDs.

ChatGPT autonomously processed the continuation and returned:

- classification: `MORE_REASONING_REQUIRED`
- reason: the execution result did not contain the required bounded README
  findings, so the assumption could not yet be validated
- authoritative lifecycle: claimed, acknowledged, responded, resolved

The canonical worker reconciliation stored the result and Grace’s
authoritative readback path returned the resolved response. This proves:

`reason -> EXECUTION_RECOMMENDED -> route -> execute -> evidence -> reason`

No production files were modified by the acceptance task.

## Fail-closed findings retained

Earlier turns were preserved as evidence:

- `5.00`: `CONTEXT_REQUIRED`; no execution created
- `5.01`: equivalent `execution_specification` naming was rejected until
  normalized
- `5.02`: prose scope aliases were rejected and the provider attempt was
  blocked before live execution

These failures did not fabricate authority or create execution from prose.

## Durable history and provider neutrality

The consultation store reconstructs turns `5.00` through `5.04`, their
Comms8 identities, the structured decision, execution request, physical
attempt, provider result, and reevaluation. The router remains capability
based and accepts injected alternate providers in focused tests; the
consultation contract does not contain Codex-specific fields.

## Superseding evidence-acquisition continuation

The `5.04` reevaluation initially lacked a machine-readable evidence request.
The Estate now validates structured `MORE_REASONING_REQUIRED` evidence
requests and routes bounded acquisition through the neutral execution seam.
Turns `5.05` and `5.06` acquired the requested README evidence read-only and
automatically returned it to ChatGPT. ChatGPT reevaluated without Steward
copy/paste and truthfully requested another bounded evidence package on
`5.07`. Acquisition is capped at three attempts per consultation root.

Details are recorded in
`ESTATE_Autonomous_Evidence_Acquisition_20260807.md`.

## Final bounded acquisition outcome

The third permitted acquisition completed for `5.07`, and ChatGPT was
reevaluated automatically. The subsequent `5.08` request was not executed:
the consultation-root counter was already three and recorded
`EVIDENCE_ACQUISITION_LIMIT_REACHED`. No fourth provider request or attempt
exists. The final Grace-visible state is truthful unresolved evidence, not
fabricated closure.

## Verification

Focused suites after the live repair: `57 passed`.

## Activation

ACTIVATION REQUIRED:

1. Relaunch the mailbox worker through
   `tools/start_chatgpt_mailbox_worker_canonical.ps1` after worker or
   structured-decision source changes. Verify canonical preflight and the
   authoritative Comms8 lifecycle event.
2. Restart the Grace Gateway only when its long-running process must load
   changed Grace/reevaluation code.

Open WebUI, Comms8, MCP adapter, Runtime Host, dedicated browser, and
workstation restart are NOT REQUIRED by this integration. Execution-router
or Codex-adapter relaunch is CONDITIONAL when those components are separately
supervised. ChatGPT reconnect/new conversation is CONDITIONAL only when the
authenticated Live app target is unavailable.
