# Estate Consultation Execution Provider Integration

Date: 2026-08-07

## Decision and protocol discovery

The existing `ExecutionProviderAdapter` contract remains authoritative. Its provider-neutral logical handoff identity is `adapter_request_id`; its physical attempt identity is the existing `execution_attempt_id` from `ExecutionAttemptRuntime`. `provider_id` and `provider_type` identify the selected adapter. Results use `ExecutionProviderAdapterResult` with neutral status, summary, artifacts, events, validation status, errors, warnings, and metadata.

The existing `CodexBridgeExecutionProviderAdapter` is a concrete adapter behind that contract. The existing dispatch queue and scheduler remain authority/scheduling surfaces; the new consultation seam does not replace them or create a persistent provider registry. Adapter bindings are injected by required capability, allowing the configured Estate router to supply the actual provider policy.

## Implemented integration

- `consultation_store.py` now persists execution-request links and physical execution-attempt links separately from consultation turns.
- `consultation_execution.py` creates provider-neutral adapter requests, persists them before execution, selects an injected adapter by capability, uses `ExecutionAttemptRuntime`, persists neutral results/evidence references, and prevents duplicate completed execution.
- `consultation_execution.py` can explicitly allocate a reasoning continuation from terminal execution evidence; execution failure alone does not allocate a continuation.
- `consultation_projection.py` renders execution requests, provider-neutral status, attempts, and result references into the existing one-artifact-per-root GitHub projection.
- `tests/test_consultation_execution.py` proves fixture-provider substitution, Codex adapter selection, logical-request/physical-attempt separation, duplicate prevention, and execution-evidence continuation.

Consultation-facing data contains no Codex-specific request/response fields. Codex-specific translation remains inside `codex_bridge_execution_provider_adapter.py`.

## Live bounded acceptance

Existing completed consultation `3.01` was used; no new Comms8 request or consultation turn was created.

- Logical execution request / existing adapter identity: `exec-52c181ef25f7`
- Consultation: `3.01`
- Dispatch: `dispatch-consultation-3-01-readonly`
- Selected provider: `codex-cli-openai`
- Physical attempt: `attempt-41ea6b224c49`
- Attempt status: `completed`
- Provider result: `completed`
- Validation: `passed`
- Sandbox: read-only
- Write scope: empty
- Result artifact: `runtime/execution_adapters/results/exec-52c181ef25f7.json`

The request went through `ConsultationExecutionRouter` and `CodexBridgeExecutionProviderAdapter` with the existing Codex Bridge runner. No direct Codex shell invocation exists in consultation code. The result and attempt are persisted and the execution link is visible in the single GitHub projection, [issue #518](https://github.com/ppow1/theestate/issues/518).

The provider returned a bounded clarification-style result rather than a repository mutation; this is still authoritative provider completion evidence, not a fabricated success claim.

## Reason → execute → observe → reason

The explicit `continue_from_execution` seam carries execution request ID, status, selected provider, result reference, and neutral result into `current_evidence` and allocates the next consultation turn only when the evidence changes the reasoning problem. Provider failure or retry remains an execution concern; it does not itself create a new consultation turn.

The fixture provider test uses the same adapter interface and neutral result shape, proving consultation code does not branch on Codex.

## Failure and retry behavior

Execution requests remain durable when a provider fails. Physical attempts remain queryable through the existing attempt runtime and consultation attempt links. A completed logical execution request cannot be submitted again. A failed attempt may be reviewed/retried under existing Estate execution authorization and retry semantics; this integration does not silently retry or switch providers.

PTM references remain consultation references and are not copied or mutated. GitHub is projection-only and non-blocking.

## Activation

- Execution provider/router process: **CONDITIONAL**—relaunch only if a long-lived process imports `consultation_execution.py`; verify the process can load the module and resolve the configured capability binding.
- Codex CLI adapter: **CONDITIONAL**—relaunch/reinvoke the adapter for the next execution; no resident adapter service exists.
- Consultation worker: **CONDITIONAL**—relaunch if persistent and loading this integration.
- Grace Resident Gateway, mailbox worker, Open WebUI, Comms8, MCP adapter, Runtime Host/core, ChatGPT, dedicated browser, workstation: **NOT REQUIRED** for this provider-integration acceptance.

ACTIVATION REQUIRED:
None for the completed bounded acceptance. For deployment into a persistent execution/consultation worker, relaunch that worker only, then verify capability resolution and the provider-neutral request/attempt artifacts before enabling execution.

