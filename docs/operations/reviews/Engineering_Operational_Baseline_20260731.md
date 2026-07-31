# Engineering Operational Baseline

Date: 2026-07-31  
Baseline commit: `95a56b729cbecab6a310d7d1a55b1c125e3f4b65`

## Department status

- Engineering Department: **Operational**
- Institutional Acceptance: **Not Granted** (`not_granted`)

Operational means the bounded, evidence-governed Engineering paths below are
available for ordinary authorized use. It does not grant institutional
acceptance or permit authority outside the stated scope.

## Supported providers and capabilities

The current provider catalog (`config/providers/catalog.json`, schema version
`1.0`) contains:

| Provider | Catalog status | Capabilities |
| --- | --- | --- |
| `stub.planning.echo` | implemented | planning, documentation_draft |
| `chatgpt.planning.external` | designed | planning, architecture_review, governance_draft, work_package_draft, documentation_draft, web_research, connector_context_read |
| `codex.execution.cli` | implemented | repository_implementation, code_review, documentation_draft, test_execution, bounded_repository_work |
| `ollama.local.reasoning` | designed | local_reasoning, classification_review |
| `qwen.local.text` | implemented | documentation_draft, text_generation, bounded_repository_read |
| `estate.audit.local` | implemented | audit_execution, validation_receipt, test_execution |
| `comfyui.local.image` | implemented | image_generation, image_iteration |

For bounded Engineering execution, the operationally supported provider
paths are:

- `qwen.local.text`, using the registered
  `qwen-local-ollama-text-adapter@1.0.0` and configured model `qwen3:8b`.
- `codex.execution.cli`, using the registered local Codex CLI adapter under
  explicit bounded authorization, declared outputs, and provider-receipt
  validation.

Planning, audit, and media providers remain available only under their own
catalog contracts; a catalog entry is not institutional acceptance of every
capability.

## Governance boundaries

Technical execution requires the complete production chain: Grace objective
and action, Helen qualification/availability/capacity/authorization and
provider-health evidence, PTM readiness, Engineering commission and durable
authorization, Operations execution decision, Dispatch queueing, final
adapter-handoff validation, registered-provider resolution, bounded execution,
artifact and receipt validation, Engineering completion, reconciliation, and
Grace terminal evidence.

The handoff remains bound to immutable prompt evidence, exact repository-
relative read and write scopes, expected outputs, provider and adapter
identity, expiry/freshness, and cross-record digests. Provider selection cannot
create authority. Direct provider or adapter invocation cannot bypass Dispatch
or the final validator. Institutional acceptance remains an external state
and is not granted by successful execution.

## Accepted operational scope

- Small bounded local Qwen documentation/text-generation tasks using
  `qwen3:8b`, exact authorized read files, exact create-once artifact and
  receipt paths, and no arbitrary writes.
- Bounded local Codex CLI documentation or repository tasks with explicit
  technical authorization, declared outputs, repository/workspace boundaries,
  and provider-receipt validation. Cloud execution, unrestricted flags, and
  implicit authority are outside this baseline.
- Steward technical intake through the canonical governed lifecycle.
- Deterministic validation, reconciliation, and provider-failure evidence
  paths without treating failure evidence as successful acceptance.

## Prohibited capabilities

Engineering execution may not grant shell execution as a general capability,
unrestricted or repository-wide reads/writes, arbitrary path selection,
unregistered providers or adapters, direct Grace-to-provider bypass, merge
authority, institutional-acceptance authority, model/configuration mutation,
or cloud/danger-full-access/bypass execution. A successful task does not
authorize any subsequent task.

## Runtime and catalog versions

- Provider catalog schema: `1.0`.
- Qwen adapter: `qwen-local-ollama-text-adapter@1.0.0`.
- Qwen configured model: `qwen3:8b`.
- Qwen endpoint policy: loopback Ollama HTTP, `http://127.0.0.1:11434`.
- Governed authority, Dispatch metadata, adapter-request, PTM, Operations,
  and receipt contracts are versioned schemas in the repository and are
  validated with Draft 2020-12 contracts where applicable.
- Codex adapter identity is the registered local execution adapter described
  by `codex.execution.cli`; its use remains subject to the explicit runtime
  profile and bounded-output contract.

## Deferred backlog

The following are deferred ordinary backlog items, not activation blockers:

- Web UI validation and Office UI consumption.
- Additional Codex quota/capacity/status characterization and authenticated
  multi-seat concurrency.
- OpenAI-backed billing/quota verification where separately authorized.
- Any Codex Cloud lifecycle/apply capability.
- Expansion of provider scope or institutional acceptance beyond this bounded
  baseline.

## Baseline disposition

This document is the Engineering baseline after activation. Future Engineering
work proceeds as ordinary feature development under these boundaries and its
own explicit authorization; this baseline does not authorize automatic scope
expansion.
