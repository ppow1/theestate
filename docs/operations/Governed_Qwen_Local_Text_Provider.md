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
write scope. Governed document and receipt outputs are create-once for a
commission: callers must provide fresh commission-specific paths, and
pre-existing files or directories block before the health check or generation
request. Historical artifacts and receipts are never rewritten.

Successful execution writes only the explicitly authorized document and
receipt paths. The receipt records provider and adapter identity, configured
and actual model identity, request and Dispatch references, Grace/Helen
references, source commit, boundary, prompt digest, artifact SHA-256 values,
timestamps, timeout and cancellation state, local endpoint determination, and
validation result. It never records the complete prompt or secrets.

If pre-invocation receipt authority is absent or invalid, the request is
blocked without provider invocation or repository mutation. Every live
document and receipt is first written completely inside an invocation-owned
private staging directory. The writer loops until every encoded byte is
written, rejects `None`, zero, negative, oversized, and invalid progress, then
flushes, fsyncs, and closes.

Publication uses a governed no-replace abstraction: Windows uses native
`MoveFileExW` without `MOVEFILE_REPLACE_EXISTING`; Linux uses
`renameat2(..., RENAME_NOREPLACE)`. Platforms without a genuine no-overwrite
primitive fail closed and retain the staging directory. The implementation
does not use `exists()` then rename, `stat()` then rename, `os.replace()`, or
`stat()` then unlink as a safety primitive.

The document is published first and the success receipt second. Completion is
reported only after both publications succeed. If document publication fails,
the competing destination remains unchanged and staged evidence is retained for
reconciliation. If the document publishes but receipt publication fails, the
document is preserved as explicitly reported orphaned evidence with its path
and the SHA-256 computed from its complete staged bytes before publication; the
governed path is never reread as the authoritative transaction hash. It is
never rolled back by pathname deletion or rename. The adapter returns the
shared top-level `failed` status, while using a detailed
`failed_with_orphaned_document` transaction state in metadata and evidence;
Engineering completion remains blocked.

Failure receipts are staged and published once when the destination remains
available. The original transaction staging directory is never removed before
durable failure evidence exists. The failure receipt records
`retained_for_reconciliation` and its exact path; a retained path must still
exist when returned. If failure-receipt staging or publication fails, the
original and any failure-stage evidence remain available, no recursive retry
occurs, and the result is `failed_without_durable_receipt`. After a failure
receipt publishes, its temporary failure-stage directory may be removed; if
that cleanup fails, the durable receipt remains valid and the result reports a
bounded cleanup warning plus the retained failure-stage path. Requests blocked
before staging have no staging disposition. Failure receipts contain bounded errors, failed result and
validation states, timeout/cancellation state, an empty completed-artifact
list, and any orphaned-artifact path/hash. Cleanup warnings and
staging-retention details are surfaced without masking the primary persistence
failure. Institutional acceptance remains separate and is not granted.

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
