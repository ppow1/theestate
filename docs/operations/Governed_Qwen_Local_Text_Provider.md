# Governed Qwen Local Text Provider

`qwen.local.text` is Estate's first governed non-Codex text-generation
provider. It uses the existing local Ollama HTTP service through the
`qwen-local-ollama-text-adapter` and is deliberately separate from the Codex
CLI bridge.

## Authority and capabilities

The provider is subordinate to Grace, Helen, PTM, Engineering, Dispatch, and
the provider gate. Its initial capabilities are limited to:

- `documentation_draft`
- `text_generation`
- `bounded_repository_read`

It has no repository-implementation, code-execution, shell, merge, or
institutional-acceptance authority. It cannot create its own authorization,
select a different model, or write outside exact declared outputs.

## Local configuration

The canonical configuration is
`config/providers/qwen_local_text.json`. It identifies the provider and
adapter, loopback Ollama endpoint, configured Qwen model, context and output
limits, supported capabilities, health check, timeout, and evidence freshness
policy. The current development configuration uses `qwen3:8b` at
`http://127.0.0.1:11434`; no model download is part of this provider.

The adapter fails closed when configuration is missing or malformed, the
endpoint is not loopback HTTP, the model is missing or differs from the
authorized model, evidence is stale, the capability is unsupported,
cancellation is requested, the response is malformed, or an output is not an
exact bounded repository-relative path. It performs no shell execution and
does not follow redirects to remote services.

## Governed lifecycle

An ordinary request proceeds through:

`Steward → Grace objective and inquiry → Helen assessment → authoritative PTM
readiness → Engineering plan → Dispatch → qwen.local.text selection → artifact
and receipt validation → Engineering completion → Grace terminal state`.

The provider catalog entry is not current qualification or authorization.
Fresh Helen qualification, health, availability, capacity, and authorization
evidence remain required for each commission. The Codex commission validator
from PR #498 is for the Codex implementation commission; it is not an
authorization mechanism for Qwen execution.

## Receipt and artifact evidence

Every live request must declare both the document path and
`provider_receipt_path` in request metadata. Both paths must appear in
`expected_outputs` and `write_scope_paths`. The adapter never invents or
silently appends a receipt destination, and the shared
`runtime/engineering_adapter_receipts/` directory is never a valid broad
write scope.

Successful execution writes only the explicitly authorized document and
receipt paths. The receipt records provider and adapter identity, configured
and actual model identity, request and Dispatch references, Grace/Helen
references, source commit, boundary, prompt digest, artifact SHA-256 values,
timestamps, timeout and cancellation state, local endpoint determination, and
validation result. It never records the complete prompt or secrets.

If pre-invocation receipt authority is absent or invalid, the request is
blocked without provider invocation or repository mutation. If a live request
with valid receipt authority fails, the adapter writes a truthful failure
receipt to that exact declared path with bounded error details, failed result
and validation states, timeout/cancellation state, and an empty artifact list.
If document writing succeeds but receipt writing fails, the adapter returns
failure and removes the newly created document when it did not pre-exist; it
does not claim successful completion.

Provider execution and Engineering completion are evidence-producing states.
Neither grants institutional acceptance; acceptance remains a separate
authority decision.

## Operator troubleshooting

- Missing configuration: restore `config/providers/qwen_local_text.json` and
  validate its schema.
- Endpoint unavailable: confirm the existing Ollama service is running on the
  configured loopback address; do not install another stack or download a
  model without Steward authorization.
- Model unavailable: confirm the exact authorized Qwen model identity is
  already installed with `ollama list`.
- Stale evidence: obtain fresh Helen qualification, health, availability,
  capacity, and authorization evidence.
- Model mismatch: stop and obtain a new governed decision; do not substitute a
  different model.
- Output rejected: reduce the request to the exact declared artifact path and
  preserve the no-shell, no-merge, no-acceptance boundaries.
- Receipt or hash failure: keep the commission blocked and route the evidence
  to Engineering for reconciliation.
