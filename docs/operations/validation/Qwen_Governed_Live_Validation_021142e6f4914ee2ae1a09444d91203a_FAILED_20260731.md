# Qwen Governed Live Validation 021142e6f4914ee2ae1a09444d91203a — Preflight Failure

Date: 2026-07-31  
Validation branch: `operations/qwen-full-governed-live-validation-2`  
Main starting commit: `4526cd52f933bf02f1b402e00d6507414f4a77a0`

## Outcome

The fresh live validation stopped during production-path preflight. No fresh
Grace, Helen, PTM, Engineering, Dispatch, handoff, provider, artifact, or
receipt records were created by this attempt. No provider was invoked.

This is a production interface blocker, not a Qwen service or model failure.
The validation was stopped as required when the merged lifecycle was found to
omit metadata required by the registered Qwen adapter.

## Intended validation

The intended request was one bounded Markdown document for `qwen.local.text`
using only:

- `docs/operations/Governed_Qwen_Local_Text_Provider.md`
- `config/providers/qwen_local_text.json`

The intended fresh artifact and receipt paths were to be generated only after
the complete governed lifecycle was known to be valid. They were never
created, so no failed-attempt output path is available for reuse.

## Read-only preflight evidence

- Ollama endpoint: `http://127.0.0.1:11434`
- Endpoint is loopback: confirmed
- `GET /api/tags`: includes `qwen3:8b`
- Provider catalog: `qwen.local.text`, configured model `qwen3:8b`
- No generation request was sent to Ollama.

The historical provider receipt hash remained unchanged:

`runtime/engineering_adapter_receipts/qwen-adapter-dispatch-202d64f291cc.json`  
SHA-256: `12a50018f5ea9474306b361d8ae1f5ae867cce571fb8b25dd38edd84fb9ceda9`

The historical artifact hash was not located under this repository during the
read-only check; no artifact was modified. `A:\theestate` was not modified.

## Blocking production path

The affected path is:

`governed_commission_and_dispatch()` → `authorize_dispatch()` →
`DispatchRequest.provider_metadata` → `from_dispatch_record()` → final
handoff validation → registered `qwen.local.text` adapter.

`_canonical_execution_authority()` correctly supplies the canonical Grace
action prompt source, digest, read scope, write scope, and expected outputs.
However, `authorize_dispatch()` constructs `technical_metadata` from only
the fixed authority and lifecycle fields. It does not carry the Qwen adapter
runtime fields required by `_metadata_errors()` in
`qwen_local_text_execution_provider_adapter.py`:

- `requested_capability`;
- `evidence_observed_at`;
- `evidence_expires_at`;
- `authorized_model_identity`;
- `provider_receipt_path`.

The adapter therefore fails closed before live execution. Supplying these
values as arbitrary caller metadata would violate the canonical-authority
rule; they need a separately authorized production correction that preserves
the Grace/Engineering evidence chain and exact output scopes.

## Stage results

| Stage | Result |
|---|---|
| Fresh lifecycle IDs | None created; preflight stopped before lifecycle construction |
| PTM readiness | Not reached |
| Engineering commission | Not created |
| Engineering authorization | Not created |
| Operations decision | Not created |
| Dispatch queue item | Not created |
| Adapter request | Not published |
| Provider invocation | 0 |
| Artifact | Not created |
| Provider receipt | Not created |
| Engineering completion | Not created |
| Reconciliation | Not reached |
| Grace terminal receipt/state | Not reached |
| Institutional acceptance | Not granted |

## Preservation

- Source files: unchanged.
- Qwen source/configuration: unchanged.
- Model: no download or update; `qwen3:8b` was only observed through the
  read-only tags endpoint.
- Historical Qwen evidence: no writes performed; receipt hash above remained
  unchanged. The historical artifact was not found in this repository during
  the read-only scan.
- `A:\theestate`: untouched.
- Stashes: 16 preserved.
- No raw local runtime evidence, cache, temporary directory, or model data was
  added.

## Validation commands and runtime entry points

Read-only inspection covered the merged `GraceHelenEngineeringComposition`
implementation, `authorize_dispatch()`, `DispatchRequest` conversion,
`execution_adapter_handoff_runtime`, the registered Qwen adapter, provider
configuration, and the local model-presence endpoint. No lifecycle runner or
provider execution command was run after the blocker was confirmed.

Because execution stopped before any fresh record was created, lifecycle,
artifact, receipt, completion, and reconciliation tests were not run as part
of this operational attempt. The merged foundation’s prior bounded test
results are not represented as this validation’s live execution result.

## Required next Steward action

Authorize a separate source-correction project to propagate the Qwen-required
bounded capability, fresh evidence, model identity, and exact receipt-path
metadata through canonical Engineering authority and Dispatch construction,
with schema/correlation tests and no provider invocation during correction.
After that correction is merged, start another validation with entirely fresh
lifecycle IDs and exact new artifact/receipt paths. Do not reuse this
preflight attempt for live execution.

