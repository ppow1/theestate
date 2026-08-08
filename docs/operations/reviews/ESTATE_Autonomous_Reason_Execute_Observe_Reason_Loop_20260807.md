# Estate Autonomous Reason → Execute → Observe → Reason Loop

Date: 2026-08-07

## Current classification

`CHATGPT_STRUCTURED_EXECUTION_DECISION_HANDOFF_NOT_IMPLEMENTED`

> Superseding continuation (2026-08-07): the structured decision envelope
> and worker handoff are now implemented and focused tests pass. Live
> acceptance is currently blocked by the canonical worker runtime
> environment, classified as `CHATGPT_WORKER_RUNTIME_ENVIRONMENT_UNAVAILABLE`.

The provider-neutral orchestration seam is implemented and tested, but the
full live loop is not accepted because the existing autonomous ChatGPT
mailbox worker emits/records a reasoning response and lifecycle completion;
it does not emit a structured execution decision for the execution router.

## Implemented bounded seam

`autonomous_reason_execute_loop.py` now:

- classifies structured reasoning decisions as information-only,
  execution-recommended, steward-decision-required, or more-reasoning;
- fails closed when execution fields are missing;
- creates only the existing provider-neutral execution request contract;
- routes by required capability through injected adapters;
- returns execution evidence to the consultation store;
- distinguishes provider retry from reasoning continuation;
- creates a continuation only for validation failure, hidden evidence, or an
  invalid assumption.

The fixture-provider tests prove provider neutrality. The existing Codex
provider remains behind `ExecutionProviderAdapter`; no Codex branch was added
to consultation orchestration.

## Evidence

Focused consultation, execution, worker, Grace, and projection tests pass:
`40 passed`.

The existing live consultation responses for `3.00` and `3.01` contain the
standard response envelope (`content`, response ID, receipt, and lifecycle
metadata), but no structured `EXECUTION_RECOMMENDED` decision or execution
specification. The mailbox worker source has no execution-decision handoff;
therefore no live ChatGPT-generated neutral execution request can yet be
proven without manual/programmatic injection.

The prior bounded Codex adapter acceptance (`exec-52c181ef25f7`) was
provider integration evidence, not proof of an autonomous ChatGPT-generated
execution decision.

## Required next seam

Extend the existing ChatGPT worker/Comms8 reasoning envelope so a bounded
reasoning response can carry a validated structured decision containing:

- `classification`;
- `objective`;
- `required_capability`;
- allowed/prohibited scope;
- evidence requirements;
- validation criteria;
- consultation correlation.

The worker must reject malformed execution specifications and preserve normal
information-only responses. Only then can the existing loop be invoked for
the required live hidden-constraint acceptance.

## Activation

No runtime activation was performed for the incomplete live loop. Once the
worker/envelope handoff is implemented, relaunch only the mailbox worker and
Grace owner that load the changed code. Open WebUI, Comms8, MCP adapter,
ChatGPT reconnect, browser restart, Runtime Host restart, and workstation
reboot are not inherently required.

## Superseding runtime activation note — 2026-08-07

The canonical mailbox-worker runtime activation is now proven for the
information-only path. Existing queued request `ec8-41aed424414e43fb` was
claimed, acknowledged, responded to, and resolved by `worker_id=chatgpt`
without creating another request. The structured result was
`INFORMATION_ONLY`, so no execution provider was activated. Runtime details
and reload boundaries are recorded in
`ESTATE-COMMS8_ChatGPT_Worker_Canonical_Runtime_Activation_20260807.md`.

## Superseding live execution acceptance — 2026-08-07

The execution-recommended seam is now proven live. Grace-originated
consultation `5.03` produced a validated neutral `EXECUTION_RECOMMENDED`
decision, which created one execution request, routed by capability to the
configured provider, and completed one read-only physical attempt. The
resulting constraint automatically created continuation `5.04`; ChatGPT
reevaluated it and returned `MORE_REASONING_REQUIRED` through authoritative
Comms8 readback. Details are recorded in
`ESTATE_Live_Execution_Recommended_Closed_Loop_Acceptance_20260807.md`.
