# PL-0042 — Dual-GPU Parallelism Stability and P100 Crash Forensics

Status: Captured
Priority: High
Category: GPU Infrastructure / Grace Parallelism / Reliability Engineering
Originator: Pat / Steward + ChatGPT
Date Captured: 2026-08-09
Target Milestone: Before Grace relies on sustained concurrent heavy RTX 4090 + Tesla P100 workloads

## Idea

Investigate and establish a conservative, evidence-backed Grace operating recipe
for a dual-GPU Estate host containing an NVIDIA Tesla P100-PCIE-16GB and an
RTX 4090. The future work must determine safe workload assignment, reliable GPU
identity pinning, bounded concurrent-use rules, health checks, stop conditions,
and recovery handling without treating the P100 as failed hardware by default.

The immediate dual-GPU commissioning objective was achieved: both cards
enumerated together, both performed real CUDA work, and the P100 produced useful
LLM and deterministic SDXL output. The parked problem is safe heavy parallel
use and crash forensics, not whether the P100 works at all.

## Why It Is Parked

Commissioning succeeded, but heavy concurrent SDXL activity produced two severe
stability signals. First, the P100 became unavailable to NVML and CUDA, survived
process cleanup, rescan, and a warm reboot, and returned only after complete
AC/PSU power removal. Later, a concurrent benchmark caused a whole-system
`0x00000133 DPC_WATCHDOG_VIOLATION` and reboot. The machine must not be placed
back into that failure path merely to collect more timing data.

Further investigation has real future value but should not interrupt current
Estate execution or be conducted without time for disciplined forensic analysis.

## Proven Observations

- Hardware: Tesla P100-PCIE-16GB, 16 GiB, compute capability 6.0; RTX 4090,
  24 GiB, compute capability 8.9; Gigabyte B550M DS3H AC, BIOS FA.
- The known-good shared driver configuration is NVIDIA 576.57. The CUDA 12.9.1
  installer package's `nv_dispui.inf` contained both physical-device IDs:
  `PCI\\VEN_10DE&DEV_15F8&SUBSYS_118F10DE` (P100) and
  `PCI\\VEN_10DE&DEV_2684` (RTX 4090). Observed `DriverVer` was
  `05/20/2025, 32.0.15.7657`. The P100 was TCC and the RTX 4090 WDDM.
- Both GPUs were simultaneously visible through `nvidia-smi` and PyTorch, with
  `cuda:0` = RTX 4090 and `cuda:1` = P100 in the healthy state.
- Independent P100 FP32 CUDA matrix multiplication passed at approximately
  8.47 TFLOPS. A simultaneous CUDA test passed at approximately 44.75 TFLOPS
  on the RTX 4090 and 8.11 TFLOPS on the P100.
- Explicit-FP32 Qwen2.5-1.5B-Instruct inference on the P100 generated useful,
  coherent output after a lower-precision sampling path hit a device-side
  assertion. This demonstrates backend/precision sensitivity, not general
  P100 inability.
- A 21.6 GiB Qwen3-32B Q5_K_M GGUF ran through partial P100 offload. Tested
  `n_gpu_layers` values were 20/30/38/42/43/44; 44 loaded and ran at about
  16,250 MiB, while 45 failed during CUDA allocation. At 42 layers, batched
  benchmarking with context/KV 4096, 512 prompt tokens, 128 generation tokens,
  and two parallel prompts measured about 69.15 prompt t/s, 5.32 generation
  t/s, and 20.34 overall t/s.
- SDXL 1024x1024, 30 steps, matched prompt/settings/seed: RTX 4090 best stable
  explicit-all-FP16 run was about 4.99 seconds at 10.48 GiB peak allocated;
  P100 best successful explicit-all-FP16 run was about 59.72 seconds at
  9.73 GiB, with warmed-run variability up to about 111.45 seconds. The P100
  image visually matched the RTX 4090 image under the effective deterministic
  settings. The measured ratio was approximately 12x, primarily a performance
  limitation. Full FP32 OOMed and mixed FP32-text/FP16-UNet failed with a
  Float/Half mismatch.
- The benchmark harness's first race was separately identified as a Windows
  output-file issue (`WinError 1224` from a user-mapped/open image file). The
  harness was changed to use unique per-run outputs and copy only completed
  results to canonical names. This is distinct from the later GPU/system crash.
- Reusable benchmark code and recorded artifacts remain under `sdxl_benchmark/`,
  including `sdxl_worker.py`, `run_benchmark.py`, `collect_results.py`,
  `results.json`, `results.csv`, comparison images, and per-run records.

## Measured Failure and Recovery Evidence

### P100 device loss

During/after concurrent SDXL activity, `nvidia-smi` reported `GPU is lost;
Reboot the system to recover this GPU`, while fresh PyTorch saw only the RTX
4090. Initial Windows PnP state still showed the P100 OK with `CM_PROB_NONE` and
`nvlddmkm` bound. Terminating stale benchmark processes, hardware rescan, and a
normal Windows reboot did not restore visibility; after the warm reboot the P100
was `CM_PROB_PHANTOM`. A complete cold power cycle restored both cards to
`CM_PROB_NONE`, `nvidia-smi` visibility, and PyTorch GPU count 2.

### Whole-system crash

A later concurrent benchmark made Windows nearly unresponsive and ended in a
reboot. Post-crash evidence recorded bugcheck `0x00000133`
(`DPC_WATCHDOG_VIOLATION`) with parameters `1`, `0x1e00`, `0xfffff8058e9c53c8`,
and `0`. The crash dump is `C:\Windows\MEMORY.DMP` (approximately 3.16 GB); a
minidump is present at `C:\Windows\Minidump\080926-12546-01.dmp`. Kernel-Power
41 and unexpected-shutdown events were also recorded.

Observed recovery escalation was: process cleanup did not recover the lost
P100; hardware scan did not recover it; warm reboot did not recover it; full
cold power removal did recover it.

## Unresolved Issues and Hypotheses

The root cause is not established. Possible contributors include NVIDIA driver
behavior, PCIe topology or link state, motherboard/chipset behavior, PSU or
connector topology, PyTorch/Diffusers behavior, benchmark process isolation,
or Pascal-era driver/runtime interaction. None is proven. P100 hardware and
RTX 4090 hardware have not been proven defective. Grace must not automatically
dispatch arbitrary heavy dual-GPU jobs until this item is promoted and bounded
rules are established.

## Promotion Condition

Promote when Grace dual-GPU parallelism work resumes and there is time to:

1. Analyze `MEMORY.DMP` and the minidump with WinDbg, beginning with
   `!analyze -v`, including DPC/ISR and driver stacks.
2. Record PCIe topology/link status, motherboard/chipset behavior, and PSU/GPU
   power-connector topology as evidence, without presuming causality.
3. Establish a conservative GPU assignment policy, reliable identity pinning,
   `CUDA_VISIBLE_DEVICES`/ordinal handling, preflight and postflight health
   checks, disappearance/device-loss detection, and immediate scheduling-stop
   behavior when identity changes.
4. Define workload classes, prohibited overlaps, and the P100 recovery recipe.
5. Test low-risk bounded concurrency first and raise load gradually; do not
   begin with simultaneous full SDXL stress or deliberately reproduce the
   watchdog crash.

## Explicit Non-Action

Do not rerun the heavy simultaneous SDXL benchmark, run SDXL, stress either GPU,
reset/disable/enable/reconfigure either GPU, reinstall NVIDIA drivers, modify
CUDA, modify benchmark results, delete crash dumps or benchmark artifacts,
disturb Estate runtime services, or create a new scheduler/GPU framework from
this capture. Do not promote this item into active work.

Do not characterize the P100 as failed hardware. Preserve the known-good 576.57
dual-device driver configuration unless future forensic evidence justifies a
change. Keep the Stream Deck lesson parked as future work: distinct RTX 4090
and P100 utilization/VRAM/state reporting, including an explicit `P100 LOST`
state, may be considered later but is not implemented here.

## Related Evidence

- `PL-0040` / Estate Cookbook Troubleshooting: related evidence-driven,
  checkpoint-oriented troubleshooting and recovery discipline.
- `sdxl_benchmark/` recorded scripts, results, images, and run artifacts.
- `C:\Windows\MEMORY.DMP` and `C:\Windows\Minidump\080926-12546-01.dmp`.
- `AI_COMMUNICATION_HINTS.md` and `operations/boards/parking_lot.md`.
