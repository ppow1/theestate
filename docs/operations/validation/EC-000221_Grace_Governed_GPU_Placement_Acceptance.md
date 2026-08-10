# EC-000221 — Grace governed GPU placement acceptance

Status: **Blocked after one bounded visible task; streaming dispatch repaired, provider contract/receipt persistence prevented completion**
Predecessor: `origin/feature/ec-000220-openwebui-auth-attention` at `0f209dd0de042245db985c85c9c17cbbfe8bfc57`  
Lane: `feature/ec-000221-grace-governed-gpu-placement`

## Profile continuity correction

The EC-000220/EC-000221 continuity defect was confirmed in the Playwright harness:
`defaultProfilePath()` was derived from `ROOT/runtime/browser/...`, so every isolated
worktree selected a different Chromium profile. The canonical resolver now uses:

`--profile` → `ESTATE_OPENWEBUI_PROFILE` → `%LOCALAPPDATA%\TheEstate\browser\openwebui-operator-profile`

The default symbolic profile identifier is `estate-openwebui-operator-profile`.
Both normal acceptance and `auth-bootstrap` call the same resolver. Evidence records
the symbolic identifier and persistence class only; cookies, databases, localStorage,
tokens, credentials, and absolute profile paths are not evidence.

The inactive EC-000220 profile was migrated once, without any owning Chromium process,
to the machine-local path. The prior profile remains intact. No profile contents are
tracked by Git and the accidental worktree `.webui_secret_key` is ignored.

Deterministic tests prove worktree-independent resolution, two-root equivalence,
CLI/environment precedence, outside-repository placement, shared auth-bootstrap and
acceptance resolution, symbolic evidence, and existing attention/privacy behavior.

## Candidate surface repair

The first EC-000221 candidate launch was not an Open WebUI frontend defect. It was a
server launch defect: Open WebUI was started directly from the EC-000221 worktree,
without the canonical controller environment. Its log recorded generation of a new
worktree-local `.webui_secret_key`; it therefore did not use the EC-000220 external
Open WebUI data directory, database, or secret.

Read-only HTTP probes showed the server and frontend were alive (`/`, `/auth`,
`/api/config`, and `/health` returned successfully; static assets returned 200), while
unauthenticated `/api/models` returned 401. The correction was to stop that candidate
and restart only the green candidate through the existing controller contract, using
the EC-000221 source root for Grace/Gateway and the existing external Open WebUI
state (`A:\AI\OpenWebUI\EstateCanonicalData`, its `webui.db`, and existing secret).
Production/canonical Open WebUI was not changed, accounts were not reset, and no
credentials were created.

The corrected candidate controller reported `validated`, `bridge_ready=true`, Grace
catalog present, and governed readiness enabled. Headed Playwright reached
`OPENWEBUI_READY` with Grace visible and the composer usable. Evidence:
`runtime/evidence/openwebui-operator/openwebui-operator-20260810010507681-a3558220`.

## GPU and lane evidence

Before dispatch, both Windows PnP devices were `OK` and `nvidia-smi` verified:

| Physical GPU | UUID | PCI bus | State |
|---|---|---|---|
| Tesla P100-PCIE-16GB | `GPU-6785b322-899d-8eec-e817-31d83279a414` | `00000000:04:00.0` | healthy, idle |
| NVIDIA GeForce RTX 4090 | `GPU-46f3fd00-5454-4536-4196-5d8b727e14f2` | `00000000:07:00.0` | healthy, 21.9 GiB free |

The existing 8192 MiB `qwen3:8b` floor selected only the RTX 4090 UUID and excluded
the P100. `qwen.local.text.4090` reported the same full UUID in its lane binding,
`CUDA_VISIBLE_DEVICES`, and compute resource identity. No P100 workload, stress,
benchmark, reset, reboot, or driver operation occurred.

## Candidate-only bridge routing repair

The canonical owner of the stale `11435` endpoint was the shared external
Open WebUI database row `config.key = openai.api_base_urls`; it was not browser
state, Grace model-picker metadata, or a candidate process environment. The
blue/green controller already owned the Gateway slot map (`blue=11435`,
`green=11436`) but did not bind that slot identity into the persisted WebUI
endpoint before candidate readiness.

The controller now performs a candidate-scoped binding through that existing
controller boundary. Before green WebUI readiness it resolves the one managed
local endpoint to `http://127.0.0.1:11436/v1`, and readiness fails closed unless
that exact endpoint matches the selected green Gateway slot. The prior endpoint
list is recorded without API keys and restored when green stops. Blue remains
bound to `http://127.0.0.1:11435/v1`; production was not promoted or repointed.
The browser cannot inject this endpoint. Deterministic coverage is in
`tests/test_canonical_webui_gateway_runtime.py` (18 passing tests).

The repaired green candidate reached `validated` with
`bridge_endpoint=http://127.0.0.1:11436/v1` and
`bridge_slot_consistent=true`. Its catalog contained `estate/grace`, and the
visible browser selected Grace. After shutdown the canonical database endpoint
was restored to `http://127.0.0.1:11435/v1`.

## Response correlation and governed-path correction

The prior `RESPONSE_NOT_OBSERVED` was CASE 3, not a Playwright timeout. The exact
prompt classified as `execution_requested / bounded_local_text`, but the
streaming Resident Gateway path omitted the bounded handler and fell through to
ordinary Grace conversation. The resulting 406-character assistant response was:

`Grace here. Pat, we move by sequence: stop the noise, pick the operational objective, assign the handoff, set the checkpoint, then close the loop. I am available as Director of Operations; give me the constraint and I will turn it into movement: Grace, run a small bounded local text task: write one short sentence confirming that this governed task used the UUID-bound RTX 4090 lane; include no secrets an`

The correction invokes the same bounded handler from streaming before ordinary
conversation. Deterministic coverage proves the exact live prompt and streaming
entry. No timeout was increased.

Exactly one additional bounded Grace task was then submitted through visible
Playwright using the machine-local profile. This time the response was visibly
observed and stabilized, but it was the truthful governed failure response:

`{"reason":"governed execution did not complete","status":"execution_failed"}`

Evidence:

`runtime/evidence/openwebui-operator/openwebui-operator-20260810012728987-58337d10`

The prior `Model '' was not found` evidence remains preserved at
`runtime/evidence/openwebui-operator/openwebui-operator-20260810010633934-fd967556`;
the new run did not reproduce it. The earlier response-observation evidence remains
preserved at `runtime/evidence/openwebui-operator/openwebui-operator-20260810011856906-97049da1`.
The governed chain was durably entered on the additional attempt: objective
`grace-obj-4467e057b928`, Helen determination `heldet-08d35f6843fc`, Engineering
commission `engcom-23777d25b083`, authorization `engauth-29697e395783`, PTM
readiness `res_01KZMMGVZ1GW2A2Q34TXC077M0`, reservation
`gpu-reservation-grace-obj-4467e057b928`, Dispatch `dispatch-6a2f115f8f7f`, and
adapter request `adapter-dispatch-6a2f115f8f7f`. The adapter result proves
`live_provider_called=true` and the selected lane was `qwen.local.text.4090`.

The provider response failed the governed artifact-content contract because the
short model response did not contain the required bounded capability statements.
While writing the truthful failure receipt, validation then rejected the five
placement correlation properties (`allocated_compute_resource_id`,
`allocated_gpu_uuid`, `runtime_bound_gpu_uuid`, `runtime_lane_id`, and
`runtime_process_id`) as undeclared inside `governed_correlation`. The schema now
declares those fields, preserving UUID evidence for future governed receipts.
Because this was the one permitted new live attempt and no successful provider
receipt exists, acceptance remains blocked; no retry was sent.

After stopping only the EC-000221 candidate services and the 4090 lane, both GPUs
remained healthy: P100 9 MiB used/0% utilization and RTX 4090 2424 MiB used/10%
utilization; both retained their verified UUID and PCI identity. The P100 remained
idle throughout.

This record preserves the blocked acceptance evidence and does not close PL-0042.
