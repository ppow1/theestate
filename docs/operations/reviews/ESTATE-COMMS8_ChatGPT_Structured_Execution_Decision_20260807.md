# Estate ChatGPT Structured Execution Decision Handoff

Date: 2026-08-07

## Current status

The structured decision contract is implemented locally, but live readiness is blocked by the ChatGPT worker activation environment:

`CHATGPT_WORKER_RUNTIME_ENVIRONMENT_UNAVAILABLE`

The current shell cannot run the Open WebUI Python environment without its governed `WEBUI_SECRET_KEY`; system Python lacks the compatible `pydantic_core` extension. The live test request `ec8-41aed424414e43fb` remains queued and untouched.

## Decision envelope

The accepted response shape is a complete structured object containing:

```json
{
  "reasoning": "human-readable reasoning",
  "decision": {
    "classification": "INFORMATION_ONLY",
    "rationale": "..."
  }
}
```

`EXECUTION_RECOMMENDED` additionally requires a provider-neutral bounded execution specification: objective, required capability, allowed scope, prohibited scope, evidence requirements, validation criteria, and consultation correlation. Optional provider preference does not replace capability routing.

The Estate parses only a complete JSON envelope or an explicitly stored structured decision. It does not infer authority from prose. It rejects unknown/provider-specific fields, unbounded or contradictory scopes, missing validation criteria, invalid capability names, and invalid consultation correlation.

## Worker behavior

The generic mailbox prompt now instructs ChatGPT to preserve human-readable reasoning and return the structured decision envelope. Legacy responses remain readable and are treated as information-only when no envelope is present.

Validated `INFORMATION_ONLY` responses complete without execution. Validated `EXECUTION_RECOMMENDED` responses are handed to the existing consultation execution orchestration through an injected decision handler. Missing or malformed execution decisions fail closed as `EXECUTION_DECISION_INVALID`; absent execution orchestration fails as `EXECUTION_DECISION_HANDLER_UNAVAILABLE`.

Grace now surfaces worker subprocess errors immediately instead of waiting for the full Comms8 response timeout.

## Validation

Focused consultation, execution, projection, Grace, worker, and structured-decision tests: `43 passed`.

Coverage includes information-only, valid execution recommendation, malformed decision, bounded scopes, legacy response compatibility, duplicate handoff prevention, provider-neutral fixture routing, evidence continuation, and execution retry separation.

## Live evidence/blocker

The first live information-only attempt created exactly one bounded request:

- request: `ec8-41aed424414e43fb`
- consultation: `4.00`
- authoritative state after timeout: `queued`
- claim: absent
- response: absent
- resolution: absent

No execution request was injected and no Comms8 lifecycle mutation occurred after creation. The attempted worker activation from system Python failed with `No module named 'pydantic_core._pydantic_core'`. The exact Open WebUI venv then failed before worker execution because `WEBUI_SECRET_KEY` was not present in the startup environment. The governed secret value was not logged or recorded.

The live information-only and execution-recommended acceptance therefore remain unproven until the worker is relaunched by the canonical Open WebUI startup owner with its existing environment.

## Superseding runtime activation note — 2026-08-07

The canonical runtime repair is now active. The worker was launched with the
Open WebUI venv, canonical `DATA_DIR`, canonical working directory, and the
existing governed secret source. The previously queued `ec8-41aed424414e43fb`
was processed once as `worker_id=chatgpt` and resolved with a validated
`INFORMATION_ONLY` decision; no execution request was created. See
`ESTATE-COMMS8_ChatGPT_Worker_Canonical_Runtime_Activation_20260807.md`.

## Activation

- ChatGPT mailbox worker relaunch: **REQUIRED** after deployment, from the canonical Open WebUI venv/startup environment.
- Grace Resident Gateway restart: **REQUIRED** only when its running process loads the updated worker-error/decision integration.
- Consultation worker relaunch: **CONDITIONAL**.
- Execution router/provider relaunch: **CONDITIONAL** if resident.
- Codex adapter relaunch: **CONDITIONAL** per execution.
- Open WebUI, Comms8, MCP adapter, Runtime Host/core, ChatGPT reconnect, dedicated browser restart, workstation reboot: **NOT REQUIRED** by the source change itself.

ACTIVATION REQUIRED:
Relaunch the mailbox worker through the canonical Open WebUI startup owner so the governed Open WebUI environment is inherited; verify the worker can perform its initial authoritative read without import or secret-environment errors. Restart Grace only if its process is being upgraded to load the changed error/decision code. Then test the still-queued `ec8-41aed424414e43fb`; do not create another request.
