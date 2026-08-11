# PL-0047 — Tesla P100 Stability Envelope and Device-Loss Forensics

Status: Captured
Priority: High
Category: GPU Reliability / Compute Runtime / Hardware Forensics
Originator: Pat / Steward
Date Captured: 2026-08-11
Target Milestone: After EC-000223 conservative Grace dual-GPU parallelism acceptance

## Idea

Perform a dedicated, evidence-driven investigation of the Tesla P100-PCIE-16GB stability envelope and repeated device-loss behavior under heavy or concurrent use.

The purpose is to determine the P100's safe production operating envelope, identify which factors correlate with device loss, and decide whether Grace/the compute scheduler should permanently derate or otherwise constrain this resource.

THIS INVESTIGATION IS NOT PART OF EC-000223 ACCEPTANCE.

EC-000223 should finish conservative Grace parallelism first. This item remains parked until the Steward deliberately promotes it.

## Known Device Identity

Tesla P100-PCIE-16GB

- NVIDIA UUID: `GPU-6785b322-899d-8eec-e817-31d83279a414`
- Typical PCI topology observed: `00000000:04:00.0`
- 16 GiB VRAM
- TCC
- Compute capability 6.0
- Driver family used during current work: 576.57

Physical identity must continue to be based on host + NVIDIA UUID. PCI topology is corroborating/observational evidence and may change with hardware enumeration.

## Historical Facts To Preserve

The P100 has successfully:

- completed independent CUDA compute;
- sustained approximately 8.47 TFLOPS FP32 matrix workload;
- run local Qwen2.5-1.5B-Instruct inference in FP32;
- partially offloaded and interactively run a Qwen3 32B Q5_K_M GGUF;
- reached 44 GPU layers for that prior 32B model/context test while 45 failed;
- produced valid SDXL images with explicit all-FP16 configuration;
- run bounded simultaneous CUDA workloads with the RTX 4090;
- completed governed single-P100 Grace/local-text execution using the CUDA-only runtime path;
- recovered cleanly after complete cold power cycles.

Do not characterize the P100 as failed hardware. Independent successful workloads and cold recovery demonstrate that the device remains functional.

The P100 has also exhibited serious loss behavior under heavier concurrent conditions:

- disappearance from NVML/CUDA while Windows initially retained the device;
- later Windows `CM_PROB_PHANTOM` state after at least one loss event;
- failure to recover through process cleanup, hardware rescan, or warm reboot in earlier testing;
- recovery only after complete cold power cycle in earlier incidents;
- a prior whole-system `0x133 DPC_WATCHDOG_VIOLATION` event during heavy concurrent GPU experimentation;
- most recently, physical P100 execution during a simultaneous Grace dual-GPU attempt followed by `nvidia-smi` reporting the P100 as lost and requiring reboot/cold recovery.

Historical PL-0042 / EC-000223 evidence should be treated as source material rather than repeated unnecessarily.

## Questions To Answer

When promoted, determine:

1. What repeatable utilization, power, temperature, VRAM, and workload envelope is safe for sustained P100 operation?
2. Is sustained 100% GPU utilization causal, merely correlated, or unrelated to device loss?
3. Does P100 power draw or a power-transition condition correlate more strongly than utilization percentage?
4. Does VRAM allocation/residency or memory-pressure behavior correlate with failures?
5. Does the failure reproduce during P100-only workloads, or only when the RTX 4090 is active concurrently?
6. Does workload type matter: CUDA compute, llama.cpp/Ollama inference, image generation, batching, context size, or model offload pattern?
7. Do CUDA backend, TCC mode, Pascal architecture compatibility, driver version, CUDA runtime/toolkit version, or Windows scheduling behavior contribute?
8. Does PCIe topology, link state, motherboard resource allocation, slot behavior, power delivery, or enumeration state contribute?
9. What Windows Event Viewer, NVIDIA/NVML, WHEA, bugcheck, minidump, or other system evidence appears immediately before and after loss?
10. Why does cold power removal recover the device when warm recovery sometimes does not?
11. Can the failure be predicted early enough for Grace to stop dispatch before device loss?
12. Should the Estate permanently derate the P100 with a scheduler-side operating envelope?
13. If derating is appropriate, what limits belong in production policy: workload class, concurrency, context, batch, VRAM floor, utilization/power guardrails, cooldown, or some combination?

## Future Test Method

Testing must be progressive and deliberately separated from EC-000223.

Start from a known healthy cold baseline and increase load in bounded steps. Prefer realistic workloads over synthetic maximum stress.

Potential future sequence, subject to an approved work package:

1. read-only baseline telemetry and Windows/NVML/PnP identity;
2. known-good light P100-only inference;
3. stepped P100-only workload duration/intensity;
4. stepped memory residency/context/offload changes;
5. only after single-device behavior is understood, conservative 4090 + P100 overlap;
6. compare telemetry and system-event evidence across successful and failed intervals;
7. stop on the first meaningful instability signal rather than pushing through failure.

Do not repeat the known heavy simultaneous SDXL race as a diagnostic shortcut.

## Evidence To Capture

For each future acceptance/forensics run, preserve as applicable:

- exact timestamp window;
- NVIDIA UUID/name and current PCI topology;
- PnP status / Config Manager condition;
- NVML visibility;
- CUDA/runtime visibility;
- model/backend/runtime instance and version;
- workload parameters;
- process tree and ownership;
- VRAM used/free;
- GPU utilization;
- temperature;
- power draw;
- relevant clocks/link data if available read-only;
- provider/runtime logs;
- NVIDIA/NVML errors;
- Windows System/Application events;
- WHEA events;
- bugcheck/minidump references where applicable;
- exact device-loss message;
- whether warm reboot recovered the device;
- whether complete cold power removal was required.

Evidence should be preserved before recovery actions whenever safe.

## Hard Stops

Stop testing immediately if:

- the P100 disappears from NVML/CUDA;
- PnP becomes unhealthy or phantom;
- repeated CUDA device-loss symptoms appear;
- Windows responsiveness materially degrades;
- cleanup fails materially;
- NVIDIA reports GPU loss;
- WHEA/driver/bugcheck evidence indicates an active severe fault;
- testing approaches a previously known severe crash path without explicit authorization.

If a severe event occurs: stop, preserve evidence, and do not "try again harder."

## Explicit Non-Action

This item is parked.

Do not perform the P100 stability study during EC-000223.

Do not perform, as part of creating or maintaining this parking-lot item:

- stress testing;
- synthetic CUDA saturation;
- heavy SDXL concurrency;
- P100 32B qualification;
- GPU reset;
- driver change;
- clock or power-limit changes;
- device disable/enable;
- reboot/cold-cycle testing except when separately authorized by a future promoted investigation.

## Promotion Condition

Promote only after conservative Grace parallelism is completed or otherwise formally closed, and the Steward explicitly authorizes a dedicated P100 stability/forensics investigation with preserved stop conditions and recovery procedures.

## Expected Outcome

The future investigation should produce a defensible production operating policy for the P100: either a validated safe scheduler envelope, a clearly bounded workload role, or evidence that the card should not participate in certain concurrent workload classes. The investigation should explain the observed device-loss behavior as far as the available hardware/software evidence permits without assuming the card is failed simply because it has entered recoverable loss states.
