# EC-000219 — Enable candidate Grace governed execution acceptance

Status: **Implemented; live browser acceptance blocked by authentication**  
Base: `28375d257b749e422fa766cc4ba72a635c53826c`  
Candidate branch: `feature/ec-000219-grace-governed-execution-acceptance`

## Policy owner and enablement

`GraceMomentumService` in `src/estate/core/grace_momentum_service.py` is the
canonical owner. Readiness derives both governed flags from
`execution_mode == governed_local_test`, an authenticated Engineering
`provider.admit` record, and a healthy inactive emergency stop. The default
execution mode remains `shadow`; production was not changed.

The candidate was started from `A:\theestate-ec000219` on the green slot and
enabled with `scripts/enable_grace_candidate_governed_execution.py`, which
uses the existing authenticated provider-admission contract and verifies that
the runtime storage is inside the requested candidate root. Admission is
candidate-local. Restarting the candidate runtime is the reload boundary; no
machine reboot is involved.

Observed candidate ports were Grace `8767`, Resident Gateway `11436`, and Open
WebUI `8081`. Candidate command lines carried the candidate root. Readiness was
`ready: true`, with both governed flags true, `local_only: true`,
`egress_disabled: true`, and `spend_disabled: true`.

## Capacity and lane gate

Read-only NVIDIA evidence at `2026-08-09T22:36Z`:

| Device | UUID | PCI | Used / free / total MiB | Utilization | Temperature |
|---|---|---|---:|---:|---:|
| Tesla P100-PCIE-16GB | `GPU-6785b322-899d-8eec-e817-31d83279a414` | `04:00.0` | 9 / 16280 / 16384 | 0% | 38C |
| NVIDIA GeForce RTX 4090 | `GPU-46f3fd00-5454-4536-4196-5d8b727e14f2` | `07:00.0` | 2062 / 22081 / 24564 | 11% | 51C |

`config/providers/qwen_local_text.json` now carries a model-specific
`qwen3:8b` admission floor of 8192 MiB. This replaces the former generic 512
MiB request so missing or unsafe model capacity fails closed. The P100 remains
unqualified for this acceptance. The registered 4090 lane started successfully
without loading a model; its evidence recorded `CUDA_VISIBLE_DEVICES` as the
full 4090 UUID, `OLLAMA_HOST=127.0.0.1:12409`, process identity
`ollama.exe serve`, and lane `qwen.local.text.4090`.

A later read-only refresh, before any model invocation, observed 4090 free
9709 MiB and P100 free 7572 MiB. The lane was stopped without invoking a model;
no capacity was created by killing or unloading unrelated workloads.

## Browser result

The repository-owned Playwright harness is `tools/openwebui_operator_acceptance.cjs`.
Candidate Open WebUI returned a login surface for the dedicated operator
profile, so the harness classified the run as `LOGIN_REQUIRED` before Grace
selection or prompt submission. No model invocation occurred and there are no
Dispatch, reservation, attempt, or provider-receipt IDs. Human authentication
through the existing `auth-bootstrap` procedure is the next prerequisite.

No SDXL, stress, P100-32B, destructive GPU operation, reboot, or driver/device
operation was performed. PL-0042 remains canonical crash evidence.
