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
blocked without provider invocation or repository mutation. If a live request
with valid receipt authority fails, the adapter writes a truthful failure
receipt to that exact declared path with bounded error details, failed result
and validation states, timeout/cancellation state, and an empty artifact list.
If document writing succeeds but receipt writing fails, the adapter returns
failure and removes the newly created document when it did not pre-exist; it
does not claim successful completion.

Both files use exclusive creation, but exclusive creation alone does not imply
complete persistence. The helper encodes once and loops until every byte has
been written. A `None`, zero, negative, oversized, or otherwise invalid write
result fails closed; zero progress is never retried indefinitely. The helper
then flushes, fsyncs, and closes before returning success. It owns a newly
created file until all of those operations succeed and records the
creation-time file identity. A stat followed by pathname unlink is not
considered race-safe. Cleanup atomically creates an invocation-owned private
same-parent quarantine directory with exclusive mkdir semantics, then moves
the governed file into its fixed internal name. The destination cannot be
occupied before the move, and `os.rename()` is not treated as a portable
no-overwrite primitive on its own. The private container is the ownership and
no-overwrite boundary. Cleanup verifies the moved object's identity, closes
the verification handle, rechecks immediately before final deletion, and
deletes only the verified private entry. Pre-existing or competing files are
never removed. Cleanup errors do not mask the original persistence error.

If document persistence fails, no partial document remains and a truthful
failure receipt may be written when its fresh declared target is available. If
success receipt persistence fails, the newly created document is removed and
the adapter makes one bounded attempt to write a truthful failure receipt; it
does not report completion. If failure-receipt persistence itself fails, the
partial receipt is removed, no recursive retry occurs, and the result reports
that durable evidence could not be persisted. Document rollback compares the
current path identity with the ownership token; if a replacement has appeared,
rollback is skipped and a bounded warning is surfaced. Private-container
collisions fail closed without overwriting the competing container. A
post-move identity mismatch preserves the quarantined evidence. Cleanup
warnings are appended in bounded form to the primary persistence error and
there is no recursive receipt-writing loop. The adapter never deletes the
governed pathname after a separate identity check. A late collision therefore
fails closed; the competing file is never overwritten. A collision before
provider execution produces no receipt because no valid live execution began.

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
