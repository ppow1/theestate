# Engineering Capability and Adapter Inventory

Status: Discovery inventory updated for PR #496. The Codex adapter is authored
and locally validated on the review branch; provider qualification, health,
authorization, merge, and institutional acceptance remain pending.
Date: 2026-07-30

## Candidate inventory

| Candidate | Current state | Declared capability | Invocation | Receipt/artifact | Suitability |
|---|---|---|---|---|---|
| `codex.execution.cli` | Designed descriptor; bridge adapter is provider-neutral and dry-run unless an approved runner is supplied. | Repository, code, documentation, review-oriented work. | Explicit injected bridge runner through the adapter contract. | Generic provider result contract; artifact and receipt policy still requires Gate-B registration. | Best first candidate for bounded repository/code/document work after qualification and authorization. |
| `comfyui.local.image` | Catalog descriptor and execution adapter exist; live submit is explicitly gated. | Local image generation and iteration. | Loopback ComfyUI `/prompt`, `/history`, `/view` through the governed adapter. | Image artifact, prompt ID, history and validation evidence. | Strong second candidate for image-specific enablement; not a general Engineering worker. |
| `ollama.local.reasoning` | Catalog descriptor is designed; no complete governed worker adapter was found. | Local reasoning/classification. | Not proven in the current worker path. | No complete production receipt contract found. | Candidate after adapter registration and health evidence. |
| `estate.audit.local` | Implemented deterministic audit/validation support. | Audit, test, validation receipt. | Local deterministic adapter. | Validation receipt, not a production work product. | Supporting validator, not a general execution adapter. |
| `stub.planning.echo` | Implemented fixture/stub. | Planning/documentation echo. | Deterministic fixture. | Fixture output only. | Test-only; cannot support truthful production completion. |
| Engineering Worker Runtime | Generic worker host implemented by PR #495. | Receives governed commissions and reconciles truthful lifecycle evidence. | Dispatch package/worker runtime. | Worker lifecycle records. | Host, not an implementation provider or adapter. |
| Residential Gateway | OpenAI-compatible transport bridge. | Request routing. | HTTP gateway. | Gateway request/response evidence. | Transport; not a worker or provider adapter. |

## Authority and registration gaps

The provider catalog, capability registry, health/capacity records, worker
identity, qualification, authorization, adapter implementation, and Dispatch
receipt are separate concepts. The repository currently contains descriptors and
adapter seams, but not one authoritative registration result that proves all of
those facts for a concrete worker. The next governed package must define that
join using the canonical reuse map before any live adapter is selected.

## Recommendation and implementation state

`codex.execution.cli` was recommended and is now implemented on PR #496 as the
first concrete adapter for a
bounded repository/code/document commission. This is a recommendation only. It
requires an approved registration, capability claims, health/capacity evidence,
qualification tests, authorization scope, receipt/artifact contract, timeout,
cancellation, and operator procedure. `comfyui.local.image` should remain a
separate media adapter candidate.
