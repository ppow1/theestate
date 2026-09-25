# Tesla P100 Qualification and Device-Loss Forensics

Document version: 1.0.0  
Status: Continuation runbook; no workload authorization by itself  
Owner: Estate Engineering / Steward  
Related: EC-000222, EC-000223, PL-0047

## Purpose

This runbook preserves the focused Tesla P100-PCIE-16GB investigation so it can resume without reconstructing the campaign from chat history. It separates:

1. **Hardware health** — whether the physical P100 remains visible, stable, and recoverable.
2. **Inference capability** — which models, contexts, output limits, and durations are useful.
3. **Estate operating policy** — which measured limits should govern production dispatch.

This document does not authorize automatic reboot, GPU reset, driver/device mutation, unknown-process termination, or production configuration changes.

## Physical identity and installed conditions

- GPU: Tesla P100-PCIE-16GB
- UUID: `GPU-6785b322-899d-8eec-e817-31d83279a414`
- Observed PCI: `00000000:04:00.0`
- VRAM: 16 GiB
- Driver mode: TCC
- Negotiated PCIe under load: Gen3 x4
- Device maximum: Gen3 x16
- Installation: PCIe riser
- Cooling: fan and shroud providing forced airflow
- Power: existing 750 W PSU through a splitter
- Known-good mixed-GPU driver: NVIDIA 576.57 from CUDA 12.9.1 distribution

Power delivery and the riser remain possible variables, but neither is assumed causal and neither must be replaced before bounded evidence collection.

## Existing governed profile

Registered lane:

- Lane: `qwen.local.text.p100-1`
- Endpoint: `127.0.0.1:12100`
- Model: `llama3.2:3b`
- Backend: CUDA v12; Vulkan disabled
- Full UUID binding; no ordinal identity
- Concurrency: one; reject when busy
- Accepted conservative context: 1024
- Accepted conservative output cap: 32
- Admission floor: 4096 MiB free VRAM

## Historical device-loss event

EC-000223 preserved a real event in which the P100 reached 100% utilization and approximately 3373 MiB residency, after which NVIDIA reported:

`GPU 0000:04:00.0 is lost. Reboot the system to recover this GPU`

The RTX 4090 showed approximately 14249 MiB residency during that attempt. The historical record does not preserve enough information to prove whether both models were cold, what unrelated runtime residency existed, or which power transition immediately preceded loss.

Do not erase or reinterpret this event merely because later tests pass.

## Findings already established

The following clean, attributable tests did **not** reproduce device loss:

- P100-only `llama3.2:3b` at contexts 1024 and 2048.
- P100 utilization at 95–100%.
- P100 power approximately 152–158 W.
- P100 temperature approximately 41–44 C.
- P100 residency approximately 2584 MiB.
- P100 generation approximately 67–68 tokens/s.
- Brief warm dual-GPU overlap.
- RTX 4090 residency increased to approximately 13990 MiB.
- Simultaneous cold model loading with request launches 172 ms apart.
- Approximately 1.84 seconds of overlapping cold model loading.
- Approximately 4.668 seconds of cold request overlap.
- Combined simultaneous measured GPU power approximately 376.68 W.
- Stable P100 PCIe Gen3 x4 throughout tested loads.

No tested run produced CUDA loss, NVML loss, unhealthy PnP, NVIDIA/WHEA/PCIe/Kernel-PnP faults, thermal slowdown, or hardware-power throttling.

Consequences:

- The former `>80% utilization for two consecutive samples` condition is not a valid hardware-health rejection rule.
- High utilization alone is insufficient to explain loss.
- Brief concurrency alone is insufficient.
- Historical-scale RTX 4090 residency alone is insufficient.
- Simultaneous conservative cold loading alone is insufficient.
- The historical event remains unexplained and may have depended on duration, historical runtime state, an intermittent transition, or an unrecorded interaction.

## Important harness lessons

Before resuming, preserve these fixes:

1. PowerShell function control flow must not rely on `return` inside `% { }`; use a normal `foreach`.
2. Web calls use explicit parameters, for example:
   `Invoke-RestMethod -Method Get -Uri "$Endpoint/api/tags" -TimeoutSec 2`.
3. POST calls explicitly name `-Method`, `-Uri`, `-TimeoutSec`, `-ContentType`, and `-Body`.
4. Do not name parameters `Pid`; PowerShell's `$PID` is read-only.
5. Use `$true` and `$false`, never bare `true` or `false`.
6. Evidence helpers join relative paths to the evidence root exactly once; absolute paths remain unchanged.
7. Listener presence is not enough: record HTTP readiness, root PID, listener owner, command line, environment binding, and service-exit state.
8. Classify outcomes accurately:
   - `HARD_STOP`: GPU/NVML/PnP/WHEA/PCIe serious fault.
   - `HARNESS_FAILURE`: parser/path/readiness/test-code defect.
   - `FAILED`: provider/workload failure without device loss.
   - `STOPPED`: ownership or safety gate refusal.
   - `PASS`: every required stage and cleanup condition passed.
9. Runtime evidence is appended/flushed continuously. Do not buffer until completion.
10. Stop only positively owned test roots and descendants.

The repaired local harness was reported as `tools/Invoke-P100ProgressiveCampaign.ps1`. On resumption, verify whether that file is present in the actual local checkout and compare its SHA-256 to the most recent validated copy. Do not assume an uncommitted or Downloads copy is durable repository state.

## Required pre-execution validation

Before any model load:

1. Read `AI_HINTS.md`, applicable engineering guidance, EC-000222, EC-000223, PL-0047, and this runbook.
2. Inventory the current branch, revision, dirty state, runtime paths, and harness location.
3. Verify both GPU UUIDs and PCI identities.
4. Verify both devices are PnP OK and NVML visible.
5. Record driver version and P100 PCIe current/max generation and width.
6. Confirm ports 12100 and 12409 are free.
7. Inventory Ollama/llama/CUDA workers and ownership.
8. Record and preserve the pre-existing shared Ollama PID.
9. Refuse unknown-process termination.
10. Parser-check the harness.
11. Enumerate every web request and confirm explicit named parameters.
12. Validate relative and absolute evidence paths without starting a GPU service.
13. Run one no-model dry run:
    - start UUID-bound P100 service;
    - GET `/api/tags`;
    - prove listener ownership;
    - start UUID-bound RTX service;
    - GET `/api/tags`;
    - prove listener ownership;
    - load no model;
    - clean both owned trees;
    - prove both ports free and both GPUs healthy.

The completed dry-run evidence reported in the originating session was:

`runtime/evidence/p100-overnight/20260813T111402Z`

Local runtime evidence may not exist in Git and must not be committed.

## Progressive campaign

Maximum wall time: four hours. Execute each stage at most once. Stop the entire campaign on the first failed or stopped stage. Never invent another stage.

### Stage 0 — Idle baseline

- Duration: 5 minutes.
- No test runtime or model.
- Establish idle temperature, power, VRAM, PCIe state, telemetry reliability, and host heartbeat.

### Stage 1 — Known-good cold control

- P100 only.
- `llama3.2:3b`.
- Context 2048.
- Output 64.
- One cold request.
- Timeout 120 seconds.
- Unload and cool down for 3 minutes.

### Stage 2 — Repeated allocation transitions

- P100 only.
- `llama3.2:3b`.
- Context 2048.
- Output 64.
- Five cycles maximum.
- Each cycle: cold load, one request, unload with `keep_alive=0`, verify return near baseline, cool down 60 seconds.
- Stop on the first abnormal cycle.

### Stage 3 — Historical P100 residency

- P100 only.
- `llama3.2:3b`.
- Context 9216.
- Output 64.
- Target residency: 3300–3450 MiB.
- If outside the band, stop without adjusting and retrying.
- Sequential requests for 10 minutes.
- Unload and cool down for 5 minutes.

### Stage 4 — Sustained proven-profile inference

- P100 only.
- `llama3.2:3b`.
- Context 2048.
- Output 128.
- Sequential requests for 30 minutes.
- Concurrency one.
- Record five-minute summaries.
- Unload and cool down for 10 minutes.

### Stage 5 — Warm dual-GPU overlap

Run only if Stages 0–4 pass.

P100:

- `llama3.2:3b`
- Context 2048
- Output 128

RTX 4090:

- `qwen3:8b`
- Context 4096
- Output 128
- `think=false`

Warm and prove both placements. Run sequential synchronized request pairs for 10 minutes, one request per GPU. Unload and cool down for 10 minutes.

### Stage 6 — Historical dual-residency target

Run only if Stage 5 passes.

P100:

- `llama3.2:3b`
- Context 9216
- Output 64
- Required residency: 3300–3450 MiB

RTX 4090:

- `qwen3:8b`
- Context 40960
- Output 128
- `think=false`
- Required residency: 13800–14250 MiB

Preload sequentially and verify both bands before overlap. If either misses, stop without adjustment. Run synchronized sequential request pairs for 10 minutes, one request per GPU. Unload and cool down for 10 minutes.

### Stage 7 — Simultaneous cold transition

Run only if Stages 0–6 pass.

- Stop and clean both isolated runtimes.
- Prove both models unloaded and VRAM returned to baseline.
- Start both isolated services.
- Use `/api/tags` only for readiness; no warm-up.
- Launch exactly one request per GPU within one second:
  - P100: `llama3.2:3b`, context 9216, output 64.
  - RTX 4090: `qwen3:8b`, context 40960, output 128, `think=false`.
- Do not retry.
- End immediately after both requests finish.
- Unload and cool down for 10 minutes.

### Stage 8 — Final idle observation

- No workload.
- Duration: 15 minutes.
- Confirm both GPUs remain visible and stable.
- Confirm P100 returns to learned idle temperature, power, and VRAM.
- Check for delayed driver, PnP, WHEA, or PCIe events.

## Continuous evidence

Create a fresh root for every campaign:

`runtime/evidence/p100-overnight/<UTC timestamp>/`

Maintain:

- `campaign-manifest.json`
- `campaign-state.json` written atomically
- `telemetry.jsonl`
- `events/`
- `stages/<stage-id>/`
- `final-report.json`
- `final-report.md`

Sample both GPUs every second, including cooldowns:

- timestamp
- UUID and PCI
- NVML visibility
- PCIe generation and width
- utilization
- VRAM used/free
- temperature
- power
- P-state
- SM and memory clocks
- throttle reasons
- compute processes
- stage
- owned root/child PIDs

Every 30 seconds, record a lightweight host heartbeat. At stage boundaries capture PnP, `nvidia-smi -q`, relevant Windows events, listener state, and ownership.

Do not commit runtime evidence.

## Campaign hard stops

End the entire campaign immediately if:

- P100 disappears from a successful NVIDIA inventory.
- NVIDIA reports the P100 lost.
- CUDA or NVML reports device loss.
- P100 PnP becomes unhealthy, missing, phantom, or reports a problem code.
- WHEA, PCIe, or NVIDIA driver fault appears.
- P100 PCIe width drops below x4 during an active test.
- Telemetry fails for three consecutive samples.
- Host heartbeat fails three consecutive times.
- Runtime selects the wrong GPU.
- Unknown compute appears.
- Test-owned cleanup cannot be established.
- Temperature reaches 80 C.
- Hardware thermal slowdown activates.
- A provider request stalls longer than 180 seconds without measurable progress.
- Any unclassified condition makes continuation unsafe.

High utilization, including 100%, is not a hard stop.

## Fault procedure

On a hard stop:

1. Mark campaign `HARD_STOP`.
2. Issue no further requests.
3. Flush evidence.
4. Capture PnP, NVIDIA/NVML, WHEA, PCIe, listener, and process evidence.
5. Clean only positively owned test processes when safe.
6. Do not reset either GPU.
7. Do not disable/enable a device.
8. Do not change drivers.
9. Do not reboot automatically.
10. Do not retry.
11. Leave the machine for Steward review and manual recovery.

A harness defect is `HARNESS_FAILURE`, not `HARD_STOP`.

## Stage-pass and cleanup requirements

A stage passes only if:

- all required requests complete;
- actual physical placement is proven;
- P100 remains NVML visible and PnP OK;
- no relevant driver/WHEA/PCIe event appears;
- telemetry is complete;
- owned cleanup succeeds;
- required ports are released;
- after cooldown, P100 returns within 100 MiB and 5 W of its pre-stage idle baseline, or a remaining owned resident model explicitly explains the difference.

## Resumption procedure

When continuing later:

1. Do not automatically resume an interrupted campaign directory.
2. Read its `campaign-state.json`, `final-report.json`, and `final-report.md`.
3. Confirm whether the prior state was `PASS`, `STOPPED`, `FAILED`, `HARNESS_FAILURE`, or `HARD_STOP`.
4. Reconcile positively owned processes and ports without touching unknown processes.
5. Verify both GPUs and PnP state.
6. Start a new campaign root; never overwrite old evidence.
7. Repeat the no-model dry run if the harness hash, Ollama version, driver, runtime path, or machine boot identity changed.
8. Obtain explicit Steward authorization before launching workloads.
9. Execute only the approved stage range. Do not infer permission to repeat a failed or hard-stopped stage.

## Final interpretation

If all stages pass, the defensible conclusion is limited to:

> The tested clean, attributable workload envelope—including sustained P100 inference, repeated allocation transitions, historical-scale dual-GPU residency, warm dual-GPU overlap, and one simultaneous cold transition—was insufficient to reproduce P100 device loss.

Do not claim the historical event never occurred or that the hardware cannot fail. Preserve PL-0047 until the Steward intentionally closes or converts it into operating policy.
