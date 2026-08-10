# EC-000222 — P100 governed compute-lane qualification

Status: **Accepted / governed P100 lane qualified; simultaneous dual-GPU execution remains unproven**

Predecessor: `feature/ec-000221-grace-governed-gpu-placement` at `6842df3dafa949e392f888af28559d1888b419ef`
Branch: `feature/ec-000222-p100-governed-compute-lane`

## Scope and safety boundary

This qualification used one lightweight local text model on one GPU. It did not run concurrent work, P100 32B, SDXL, stress, benchmark, reset, reboot, or driver operation. The dirty primary checkout `A:\theestate` was not modified.

Fresh preflight verified both devices by physical identity: P100 `GPU-6785b322-899d-8eec-e817-31d83279a414`, PCI `00000000:04:00.0`, PnP OK; RTX 4090 `GPU-46f3fd00-5454-4536-4196-5d8b727e14f2`, PCI `00000000:07:00.0`, PnP OK. No ordinal was used as identity.

## P100 lane

`llama3.2:3b` was already installed locally (`ollama list`, 2.0 GB; no download). Its standard llama architecture, Q4_K_M size, and modest bounded context make it the smallest suitable installed candidate; the user-mentioned Qwen2.5-1.5B model was not installed. The existing `qwen.local.text` adapter was reused through provider instance configuration `config/providers/qwen_local_text_p100.json`.

Registered lane: `qwen.local.text.p100-1`
Endpoint: `http://127.0.0.1:12100`
Model: `llama3.2:3b`
Admission floor: 4096 MiB
Binding: `CUDA_VISIBLE_DEVICES=GPU-6785b322-899d-8eec-e817-31d83279a414`

Lane-only health passed: the process binding evidence recorded the full P100 UUID, loopback endpoint, and no ordinal binding. Required resource and UUID selection excluded the RTX 4090 and had no fallback. The provider config path is repository-relative and cannot be injected from browser content.

## Direct governed acceptance

One direct bounded request completed through the existing architecture:

`Grace -> PTM -> Helen -> Engineering -> reservation -> Dispatch -> qwen.local.text adapter -> provider receipt`

Objective `grace-obj-1260f92f8cd2`; action `grace-act-0f614b4745ed`; PTM resolution `res_01KZMP84SEJJB292SJQME5TA2P`; Helen `heldet-0471ae0cf0af`; Engineering commission `engcom-ce8329ace9ce`; authorization `engauth-968bbcfe34ae`; reservation `gpu-reservation-grace-obj-1260f92f8cd2`; Dispatch `dispatch-c5c6ae6b273b`; adapter `adapter-dispatch-c5c6ae6b273b`.

Receipt: `runtime/engineering_adapter_receipts/grace_bounded_local_text_grace-obj-1260f92f8cd2.json`. It records model `llama3.2:3b`, lane `qwen.local.text.p100-1`, allocated UUID, runtime-bound UUID, and resource ID. Equality proven:

`required_gpu_uuid = allocated_gpu_uuid = runtime_bound_gpu_uuid = GPU-6785b322-899d-8eec-e817-31d83279a414`
`required_resource_id = allocated_compute_resource_id = DESKTOP-JA3RPNQ:nvidia:GPU-6785b322-899d-8eec-e817-31d83279a414`

The generated artifact was a bounded operational-checkpoint sentence; placement truth came from allocation/lane/receipt evidence, not model prose. Grace presentation now populates `gpu_uuid` from authoritative runtime receipt metadata.

## Grace/Open WebUI attempt and blocker

Candidate green Open WebUI reached `OPENWEBUI_READY`, Grace was visible, and the persistent profile was reused. The single visible request evidence is `runtime/evidence/openwebui-operator/openwebui-operator-20260810020425856-9ae00508`.

The preserved first request was observed by Playwright, but the candidate Gateway used the default active Grace runtime URL `127.0.0.1:8766` instead of green `127.0.0.1:8767`, yielding an authoritative `RUNTIME_UNAVAILABLE` response before bounded intent execution. The controller correction injects `ESTATE_GRACE_MOMENTUM_URL` from the selected slot; after restart, green readiness validated with Grace runtime, Gateway, and WebUI all ready and bridge `127.0.0.1:11436` consistent.

After that correction, exactly one further visible request was submitted and preserved at `runtime/evidence/openwebui-operator/openwebui-operator-20260810022309077-c275cc98`. It reached the green candidate and returned an authoritative runtime-availability response, but did not enter bounded execution. The exact prompt is classified as `execution_requested` by the bounded-intent grammar; however, `_grace_runtime_operation_response()` ran before the bounded handler and inferred a read-only runtime query from the ordinary words `checkpoint` and `provider`. No PTM, Helen, Engineering, reservation, Dispatch, adapter, or provider artifacts were created for this attempt. The smallest correction gives explicit bounded intent precedence over the read-only compatibility layer and adds a regression test; no retry was performed.

The single final visible request was then submitted after that correction at `runtime/evidence/openwebui-operator/openwebui-operator-20260810023945567-d63bcc32`. Intent precedence worked and the full governed chain was created, but the request was not P100-bound. The resulting authoritative Grace response and provider receipt report `qwen.local.text.4090`, model `qwen3:8b`, and RTX 4090 UUID `GPU-46f3fd00-5454-4536-4196-5d8b727e14f2`. The generated model prose was preserved separately as non-authoritative evidence. The objective/action execution authority, Engineering authorization, reservation, and adapter request all independently selected the 4090; setting `ESTATE_GOVERNED_LOCAL_TEXT_LANE=qwen.local.text.p100-1` did not propagate a required P100 resource into the browser-created governed request. This is a fail-closed resource-requirement propagation defect, not a P100 health failure. No retry was performed.

This leaves the Grace/Open WebUI P100 portion unaccepted in this session while preserving the successful direct P100 qualification. Future isolated worktrees can reuse the same machine-local Playwright profile; no browser credentials or session files entered Git. The remaining unproven boundary is visible Grace/Open WebUI P100 execution with a fail-closed required-resource propagation. Simultaneous dual-GPU work remains explicitly out of scope.

## Resource-propagation correction and safety stop

The canonical loss point was `_target_lane()` in the bounded Open WebUI workflow: without a symbolic physical-resource selector in the browser message, the Gateway defaulted to the ordinary qwen3:8b/4090 lane. The process environment hint `ESTATE_GOVERNED_LOCAL_TEXT_LANE` was not present in the candidate Gateway and was never a valid substitute for a required physical constraint. The correction recognizes only narrow symbolic P100 language, resolves it through the registered Tesla P100 observation and `qwen.local.text.p100-1` lane, writes the resulting required UUID/resource into objective metadata and the existing Engineering composition, and rejects raw UUIDs, arbitrary lane IDs, and unknown physical selectors.

Deterministic coverage passed for symbolic mapping, raw-placement rejection, no-fallback behavior, objective/Engineering path compatibility, and the existing 4090/P100/router/profile suites. A new live request was not submitted after this correction because the immediate preflight found an unrelated existing RTX 4090 `llama-server` workload at approximately 95% utilization and 340 W. The process was not launched or terminated by EC-000222. The P100 remained present and healthy, but the two-GPU safety baseline was not acceptable for another live attempt.

## Final live P100 result

After the published authorization-persistence correction, exactly one new visible request was submitted at `runtime/evidence/openwebui-operator/openwebui-operator-20260810031139491-b1a4ab9e`. Playwright reported `PASS`, reused the machine-local operator profile, and visibly observed this authoritative response: `status=completed`, provider `qwen.local.text`, model `llama3.2:3b`, lane `qwen.local.text.p100-1`, GPU UUID `GPU-6785b322-899d-8eec-e817-31d83279a414`, and physical resource `DESKTOP-JA3RPNQ:nvidia:GPU-6785b322-899d-8eec-e817-31d83279a414`.

New governed IDs: objective `grace-obj-de80132692f3`; action `grace-act-7c4d2dc4a75a`; PTM `res_01KZMTFGB9D3KMJTQZ7BJZNVF8`; Helen `heldet-16fff90f8a9d`; commission `engcom-aec2224c2293`; authorization `engauth-876a0e1a7fc0`; reservation `gpu-reservation-grace-obj-de80132692f3`; Dispatch `dispatch-cff6674588aa`; adapter `adapter-dispatch-cff6674588aa`; Grace receipt `gracereceipt-a0fd2f478e1e`; provider receipt `runtime/engineering_adapter_receipts/grace_bounded_local_text_grace-obj-de80132692f3.json`.

The new immutable Engineering authorization directly contains `execution_authority.compute_resource_requirements.required_gpu_uuid` equal to `GPU-6785b322-899d-8eec-e817-31d83279a414` and `required_resource_id` equal to `DESKTOP-JA3RPNQ:nvidia:GPU-6785b322-899d-8eec-e817-31d83279a414`. Those values remained equal through objective metadata, commission, reservation, Dispatch, adapter request, allocation, P100 lane binding, and provider receipt. The selected lane was `qwen.local.text.p100-1`; no `qwen.local.text.4090` selection or RTX 4090 allocation was observed.

The visible execution itself completed successfully. An immediate postflight observation was preserved as historical evidence: unrelated Ollama `llama-server.exe` processes were still resident on both GPUs, so that observation was not used as the final ownership determination. No process was killed or altered.

The later read-only closure observation found no listeners on `12100`, `8767`, `11436`, or `8081`; no EC-000222 candidate command line; and no temporary P100 lane process. Remaining GPU processes were independently identified as unrelated Ollama/UI processes. P100 telemetry was 0% utilization with 7,572 MiB free; both GPUs remained present with NVML visibility, unchanged UUID/PCI identities, and Windows PnP `OK`. No Estate workload remained active. Under the cleanup criterion, external residency did not prevent closure. EC-000222 is therefore **Accepted**. Simultaneous dual-GPU governed execution remains explicitly unproven.

After the safety baseline returned to a light state, exactly one visible request was submitted at `runtime/evidence/openwebui-operator/openwebui-operator-20260810030011068-c35952b4`. Playwright observed `OPENWEBUI_READY`, reused the machine-local profile, and observed Grace’s completed authoritative response. Objective `grace-obj-4ec15f18f471`, action `grace-act-0362f2ef0bd8`, PTM `res_01KZMSTFMSYN2GDVPD277KMHGY`, Helen `heldet-73c080c964ee`, Engineering commission `engcom-66cb782e81d2`, authorization `engauth-662ba4e13fc5`, reservation `gpu-reservation-grace-obj-4ec15f18f471`, Dispatch `dispatch-b9d17ceede33`, adapter `adapter-dispatch-b9d17ceede33`, and Grace receipt `gracereceipt-87999379541e` were created. The provider receipt is `runtime/engineering_adapter_receipts/grace_bounded_local_text_grace-obj-4ec15f18f471.json`.

Objective, commission, Dispatch, adapter request, allocation, runtime lane, and provider receipt all prove P100 UUID/resource equality. Post-run inspection found that the Engineering authorization’s nested `execution_authority` record did not retain `compute_resource_requirements`; the canonical authority normalizer had dropped that field before authorization persistence. This paragraph preserves that immutable historical blocker; the correction was subsequently published and the new rerun is recorded above.

Office Compute correlation is available through `runtime/execution_activity/current.json` and `runtime/execution_activity/report.md`; the canonical Stream Deck resource projection remains the same multi-GPU projection and exposes the P100 UUID/resource telemetry. Concurrency remains unproven and is the next milestone.
