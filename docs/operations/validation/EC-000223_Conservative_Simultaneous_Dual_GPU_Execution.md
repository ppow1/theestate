# EC-000223 — Conservative Simultaneous Dual-GPU Execution

## Durable implementation

The read-only preflight utility is `tools/gpu-parallel-preflight.ps1`, with
deterministic fixture coverage in `tests/test_gpu_parallel_preflight.py`.
The utility does not launch workloads, unload models, stop or restart
processes/services, reset or reconfigure GPUs, mutate drivers/devices, or
reboot/shut down the host.

Physical identity is UUID-based and never ordinal-based:

| Resource | UUID | Lane | Port | Minimum free VRAM |
| --- | --- | --- | --- | ---: |
| RTX 4090 | `GPU-46f3fd00-5454-4536-4196-5d8b727e14f2` | `qwen.local.text.4090` | 12409 | 8192 MiB |
| Tesla P100 | `GPU-6785b322-899d-8eec-e817-31d83279a414` | `qwen.local.text.p100-1` | 12100 | 4096 MiB |

The JSON contract reports `status`, `timestamp`, `host`, `resources`,
`reasons`, `policy`, and `exit_code`. Resource records include UUID, name,
PCI bus, PnP status, NVML visibility, VRAM, utilization, temperature, power,
compute PIDs and Windows process details, lane/port ownership, and readiness.
Ownership is `ESTATE_OWNED`, `EXTERNAL`, or `UNKNOWN`; unknown process or port
ownership blocks conservatively. External material compute and externally
owned or unknown lane ports block preflight. VRAM residency alone is not
material when no conflicting activity is observed.

Exit codes are 0 `PASS`, 2 `PRECHECK_BLOCKED`, 3 `GPU_HEALTH_FAILURE`, and 4
`PREFLIGHT_TOOL_ERROR`. Human-readable output is the default; `-Json` emits
the structured output.

## Preflight correction and validation

- Physical resource identity remains `host_id + NVIDIA UUID`; PCI is recorded
  topology, not durable identity.
- Missing optional PnP properties are represented as null while required
  identity and health evidence remains fail-closed.
- Live P100 matching correlates Windows vendor/device identity, product name,
  instance identity, and health across `Get-PnpDevice` and CIM shapes.
- The final WDDM blocker was a live/fixture representation mismatch. Live
  process and GPU-engine records were `OrderedDictionary` values, while fixture
  records were `PSCustomObject`. `Get-Field` inspected only
  `PSObject.Properties`, so live dictionary values could not correlate. All
  NVIDIA, CIM, GPU-engine, and port-owner PIDs now use invariant positive
  decimal-string keys and dictionary access is explicit. A disappeared PID is
  `TRANSIENT_EXITED`; an active unresolved PID still blocks.
- Deterministic preflight fixture tests: `24 passed`.
- PowerShell parser validation: passed.
- Mutation audit: passed; no prohibited mutation or workload-launch command
  is present.

The published canonical preflight at `2026-08-11T18:06:33.9665550Z` returned
`PASS`, exit code `0`, with no reasons. The RTX 4090 was healthy/PnP OK at
`00000000:07:00.0`, had 21,099 MiB free against an 8,192 MiB floor, and its
correlated WDDM clients were `NON_CONFLICTING_WDDM`. The P100 was healthy/PnP
OK at `00000000:04:00.0` with 16,280 MiB free against a 4,096 MiB floor. Ports
12409 and 12100 were free, with no conflicting or unknown compute ownership.

## Live basic health gate

The permitted read-only health observation was blocked before preflight:

- RTX 4090: present in NVML with the required UUID, but observed PCI
  `00000000:06:00.0` instead of required `00000000:07:00.0`; PnP was `OK`.
- Tesla P100: required UUID was absent from NVML and no matching PnP device
  was observed.

Because the basic health gate failed, the command
`powershell -ExecutionPolicy Bypass -File tools/gpu-parallel-preflight.ps1 -Json`
was not invoked. There is therefore no live preflight JSON or exit code for
this run. Live dual-GPU acceptance remains blocked, and no GPU workload was
launched.

That basic health section is preserved historical evidence. It is superseded
for acceptance by the later published canonical `PASS` and is not erased.

## Conservative simultaneous acceptance

| Task | Lane PID | Lane | Model | Full `CUDA_VISIBLE_DEVICES` UUID |
| --- | ---: | --- | --- | --- |
| A | 6840 | `qwen.local.text.4090` | `qwen3:8b` | `GPU-46f3fd00-5454-4536-4196-5d8b727e14f2` |
| B | 25528 | `qwen.local.text.p100-1` | `llama3.2:3b` | `GPU-6785b322-899d-8eec-e817-31d83279a414` |

Both endpoints passed `/api/tags`. Process binding evidence records each
endpoint, model, resource ID, full UUID, PID, and `ollama.exe serve` identity.
Both independent authority chains and simultaneous exclusive reservations on
different resource IDs existed before either provider invocation.

Task A:

`grace-obj-25a3b22e18f6` / `grace-act-9a451083e6d7` -> PTM
`res_01KZS0912RM54BC12V6KR6GP6K` -> Helen `heldet-defaa6f6d439` ->
commission `engcom-a8ec0d715c9e` -> authorization
`engauth-f2a3c584bf39` -> reservation
`gpu-reservation-grace-obj-25a3b22e18f6` -> Dispatch
`dispatch-aa8acb1ff5f9` -> adapter `adapter-dispatch-aa8acb1ff5f9` ->
provider receipt
`runtime/engineering_adapter_receipts/ec_000223_task_a_grace-obj-25a3b22e18f6.json`
-> Grace receipt `gracereceipt-369f85a0a9c6`.

Task B:

`grace-obj-33c55ec1c69f` / `grace-act-dadae608b1e8` -> PTM
`res_01KZS092VCFQN9XAK8H5Z4H16H` -> Helen `heldet-99b3e2d20b60` ->
commission `engcom-a168dfb1203e` -> authorization
`engauth-5476ead9f19e` -> reservation
`gpu-reservation-grace-obj-33c55ec1c69f` -> Dispatch
`dispatch-f6a0aea1bdfb` -> adapter `adapter-dispatch-f6a0aea1bdfb` ->
provider receipt
`runtime/engineering_adapter_receipts/ec_000223_task_b_grace-obj-33c55ec1c69f.json`
-> Grace receipt `gracereceipt-91b09258a6ab`.

For A, required = authorized = reservation resource = Dispatch = adapter =
allocation = lane = `CUDA_VISIBLE_DEVICES` = provider receipt runtime UUID =
`GPU-46f3fd00-5454-4536-4196-5d8b727e14f2`. The governed records for B also
claimed equality to `GPU-6785b322-899d-8eec-e817-31d83279a414`, but the owned
runtime log disproved the physical-runtime end of that chain after execution.
The P100 lane's Ollama runner selected `Vulkan0 (NVIDIA GeForce RTX 4090)
(0000:07:00.0)`, offloaded 29/29 layers there, and allocated 1,918.35 MiB of
model buffer plus 896 MiB of KV buffer on Vulkan0. All six P100 telemetry
samples remained at 9 MiB and 0% utilization. Thus Task B cross-assigned to the
4090 despite its CUDA UUID environment and its receipt's configured binding.

| Task | Provider start | Provider finish |
| --- | --- | --- |
| A / RTX 4090 | `2026-08-11T18:10:13Z` | `2026-08-11T18:10:25Z` |
| B / P100 | `2026-08-11T18:10:13Z` | `2026-08-11T18:10:21Z` |

`max(start) < min(finish)` by **8.0 seconds**. Six two-second telemetry samples
were collected. Representative UUID, PCI, utilization, memory, temperature,
and power samples are in
`operations/diagnostics/ec-000223-dual-gpu-acceptance.json`. This was
observability only, not a benchmark.

## Office, Stream Deck, and postflight

The Office execution-activity surface retained both intended Dispatch
assignments but previously
dropped physical resource context when normalizing cards. A small generic
N-resource repair now retains `compute_resource_id`, `gpu_uuid`,
`runtime_lane_id`, `model_identity`, and `reservation_reference`.
Deterministic coverage proves simultaneous assignments remain distinct. The
live completed projection contains both intended 4090/qwen3:8b and
P100/llama3.2:3b assignments. Office correlation is not physical placement
proof; the Task B runtime log remains authoritative over the configured lane
and receipt claim.

The canonical two-resource projection continues to expose health, VRAM
used/total, and utilization for each UUID, preserving existing Stream Deck
compatibility. No Office or Stream Deck redesign was made.

Immediate postflight at `2026-08-11T18:10:36Z` found both GPUs NVML-visible
and PnP `OK`, with unchanged UUID/PCI identities. Cleanup stopped only the two
recorded lane roots and their two child `llama-server.exe` workers. Both lane
ports became free and no owned process remained. Final health at
`2026-08-11T18:11:10Z` showed P100 16,280 MiB free at 0% and RTX 4090 21,175
MiB free at 8%; both remained healthy.

A later canonical read-only observation at `2026-08-11T18:14:04Z` returned
`PRECHECK_BLOCKED` because one 4090 aggregate sample was 21%, one point above
the named material-utilization threshold. Power was 22.2 W, ownership was
resolved non-conflicting WDDM, both ports were free, and neither GPU had a
health failure. Per the no-retry rule it was preserved and not retried; it does
not replace the pre-execution `PASS` or immediate healthy postflight evidence.

## Status and limits

EC-000223 is **Not Accepted — runtime placement mismatch**. The two governed
provider calls had 8.0 seconds of positive overlap and both GPUs stayed healthy,
but Task B executed through the 4090 Vulkan device instead of the required
P100. The receipt's `runtime_bound_gpu_uuid` reflected registered configuration,
not the runner's selected physical backend, so the full UUID equality criterion
and no-cross-assignment criterion failed. No retry was performed.

Heavy parallel workloads, SDXL parallelism, P100 32B parallelism, and
unrestricted scheduler saturation remain unqualified.

## Governed runtime cleanup continuation

The canonical preflight at `2026-08-11T18:39:17Z` found the RTX 4090 at
23,449 MiB used / 694 MiB free and the P100 at 11,900 MiB used / 4,389 MiB
free. Model workers included `llama-server.exe` PIDs 9184 and 28892 under PID
28456. Neither registered lane port was listening. The recorded EC-000223 lane
roots were PIDs 6840 and 25528, so the observed worker parent did not match a
registered lane root. Executable names and the shared Ollama model path were
not accepted as Estate ownership. Those workers therefore remained
external/ambiguous and were not terminated.

At the read-only lifecycle attribution on `2026-08-11T19:29:23Z`, the model
workers and parent were already absent without an Estate cleanup action. The
4090 had returned to 2,849 MiB used / 21,294 MiB free and the P100 to 9 MiB
used / 16,280 MiB free. Ports 12409 and 12100 were free. The new canonical
status command classified both historical registry roots as
`ESTATE_OWNED_STOPPED`; there was no live owned tree to quiesce. Consequently
the earlier allocation cannot be positively attributed to abandoned
EC-000223 residue, and no retrospective cleanup claim is made.

The runtime-lane lifecycle now requires PID, executable path, exact command
line, creation time, child tree, lane port, reservation, Dispatch, provider
activity, pending-task, and reconciliation agreement before quiescence. Any
unknown gate refuses termination. Cleanup is lane/resource scoped, records a
schema-governed receipt and operational event, and contains no GPU reset,
device mutation, reboot, or global process-kill capability.
