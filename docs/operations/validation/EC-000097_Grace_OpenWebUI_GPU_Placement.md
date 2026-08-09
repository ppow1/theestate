# EC-000097 — Grace Open WebUI GPU placement acceptance

Status: **BLOCKED — acceptance not performed**
Base: `46661d4279ce1e70662867efcf9c087c3210a834`
Branch: `feature/ec-000097-grace-openwebui-gpu-placement`

## Purpose

This record preserves the first bounded real-workload placement attempt. It is
not an acceptance claim. No provider workload was started because the required
browser/runtime and governance preconditions were not simultaneously present.

## Browser boundary

The repository-owned Playwright harness is `tools/openwebui_operator_acceptance.cjs`.
It uses Playwright Chromium, a persistent repository-owned profile at
`runtime/browser/openwebui-operator-profile`, model-picker verification for
Grace, and redacted evidence under `runtime/evidence/openwebui-operator/<run-id>`.
Credential-bearing evidence is disabled. Deterministic harness tests passed.

The live readiness probe on 2026-08-09 returned `OPENWEBUI_UNAVAILABLE`:
`http://127.0.0.1:8080/` refused the connection. Therefore no operator
conversation, Grace resident selection, prompt submission, response, or
browser-visible placement explanation was captured.

## Backend and hardware preflight

The current Open WebUI engineering workflow remains an advisory Grace/Helen
workflow and explicitly returns `provider_execution_performed: false`; it does
not invoke the governed Qwen Dispatch/adapter chain from resident chat. The
canonical runtime configuration points at `A:\theestate-wp4233`, a different
dirty worktree, rather than this checkout. Starting that configuration would
not exercise this base and would violate isolation.

Read-only NVIDIA preflight:

| UUID | Name | PCI bus | VRAM free / total |
|---|---|---|---:|
| `GPU-46f3fd00-5454-4536-4196-5d8b727e14f2` | NVIDIA GeForce RTX 4090 | `00000000:07:00.0` | approximately 1.8 GiB / 24 GiB |
| `GPU-6785b322-899d-8eec-e817-31d83279a414` | Tesla P100-PCIE-16GB | `00000000:04:00.0` | approximately 4.3 GiB / 16 GiB |

The configured governed local text provider is `qwen.local.text`, adapter
`qwen-local-ollama-text-adapter@1.0.0`, model `qwen3:8b`. Ollama was readable
at loopback and the model was already present; no model download or provider
invocation was performed. The target RTX 4090 did not satisfy a demonstrated
conservative VRAM admission margin, and no current governed reservation or
capacity record was available to clear admission.

## Missing correlation

No Dispatch ID, adapter request/attempt ID, reservation/allocation ID, Grace
session ID, or physical placement result exists for EC-000097. It would be
incorrect to infer placement from provider capability or runtime ordinal.

## Safety result

No workload was launched. No SDXL, stress kernel, maximum-load benchmark, P100
32B endpoint, uncontrolled concurrency, GPU reset, device disable/enable,
driver operation, reboot, shutdown, or cold-cycle recovery was performed.
PL-0042 remains canonical crash evidence and was preserved.

## Required next integration action

Add the smallest governed Grace/Open WebUI command binding that calls the
existing `GraceHelenEngineeringComposition` → PTM/Helen/Engineering → Dispatch
→ `run_registered_handoff_adapter` path, carrying the EC-000096 physical
resource requirement. Run it only after the canonical runtime is configured to
this clean checkout (or current published lineage is proven), fresh provider
health/capacity and PTM evidence exist, and the RTX 4090 has a truthful VRAM
admission margin. Then rerun the existing Playwright harness and correlate its
conversation/session with durable Dispatch, adapter, reservation, receipt,
and UUID evidence.
