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

## Governed cleanup and P100 qualification result

The operator interfaces are read-only status:

`python -m estate.cli.main gpu-runtime status --json`

and confirmed, lane-scoped cleanup:

`python -m estate.cli.main gpu-runtime quiesce --lane <lane-id> --actor operator --confirm --json`

(`PYTHONPATH=src` is required when running directly from a source checkout.)
The command prints its proposed PID/tree, port, ownership, and all inactivity
gates before acting. Ordinary Grace conversation has no process-kill
authority. The schema-governed receipt records lane/resource/UUID, root and
children, reservation/Dispatch/provider/pending/reconciliation checks,
shutdown requests, verified exits, port release, pre/post telemetry, warnings,
errors, and result. Office receives the generic lane lifecycle states and the
canonical operational-event stream receives stale-candidate, cleanup-success,
or cleanup-failure events.

The large allocations observed at `18:39Z` were not cleaned by this operation.
The significant workers were `llama-server.exe` PIDs 9184 and 28892 under PID
28456, with neither registered lane port nor a registered-root relationship.
They were therefore `UNKNOWN`/external for cleanup authority and were refused;
they disappeared independently before the next attribution. The evidence does
not prove that the nearly full 4090 was abandoned Estate residue.

After a `PASS` preflight at `19:32:00Z`, a single small P100 governed task ran
from `19:33:48Z` to `19:33:54Z`. Its chain was objective
`grace-obj-ddc0633d49eb`, action `grace-act-397474d8132c`, PTM
`res_01KZS523XA0YSMHMDXAW0RZ1WM`, Helen `heldet-33f4f2a133d2`, commission
`engcom-3c64fea3f645`, authorization `engauth-6e6295a29497`, reservation
`gpu-reservation-grace-obj-ddc0633d49eb`, Dispatch `dispatch-570cdd3eac47`,
adapter `adapter-dispatch-570cdd3eac47`, provider receipt
`runtime/engineering_adapter_receipts/grace_bounded_local_text_grace-obj-ddc0633d49eb.json`,
and Grace receipt `gracereceipt-ce4b9f2927b0`. The owned runner log plus
`nvidia-smi` observed `CUDA0`, `Tesla P100-PCIE-16GB`, PCI
`00000000:04:00.0`, UUID
`GPU-6785b322-899d-8eec-e817-31d83279a414`, and placement match `true`.
P100 memory rose from 9 MiB to 3,373 MiB with 95% utilization and then returned
to 9 MiB. The 4090 retained its roughly 2.8 GiB desktop baseline and showed no
model allocation attributable to the task. Single-P100 physical-runtime
qualification therefore passed.

Exactly one authorized dual-resource retry was then attempted. Task A used
objective/action `grace-obj-e0aab6beb00b` / `grace-act-8289cb9e401d`, PTM
`res_01KZS54TANPVWZ4FY2WJQ40ZF6`, Helen `heldet-25c268009a5f`, commission
`engcom-b99ef5c4d2eb`, authorization `engauth-ca0c68e7ec19`, reservation
`gpu-reservation-grace-obj-e0aab6beb00b`, and Dispatch
`dispatch-490a9da42fd4`. It failed before adapter/provider invocation because a
concurrent Dispatch queue reader observed the queue during a non-atomic write.
The canonical Dispatch was recorded `Failed`; there is no Task A provider
receipt. Task B used objective/action `grace-obj-1182358a50dc` /
`grace-act-8e3f82c298df`, PTM `res_01KZS54TX600X0DWXWB9ZP4PAS`, Helen
`heldet-d29e039e48e3`, commission `engcom-3125459e034c`, authorization
`engauth-488a37b18803`, reservation
`gpu-reservation-grace-obj-1182358a50dc`, Dispatch `dispatch-074a851ecb05`,
adapter `adapter-dispatch-074a851ecb05`, provider receipt
`runtime/engineering_adapter_receipts/ec_000223_retry_b_grace-obj-1182358a50dc.json`,
and Grace receipt `gracereceipt-b73fc1057559`. It ran from `19:35:17Z` to
`19:35:23Z` and again proved the P100 UUID/PCI/CUDA placement. Because Task A
never invoked its provider, overlap was not established. Per the one-attempt
constraint, no retry was performed.

The subsequently launched lane roots were positively attributable and
quiescible: 4090 PID 22992 and P100 PID 33384 matched registered PID,
executable, command, creation time, port, lane, and resource identity, with all
work gates empty. Cleanup receipt
`gpu-cleanup-4ed91a214f804eada346d558281f6e33` verifies PID 22992 exited and
port 12409 released. Receipt
`gpu-cleanup-a228cd78ee974c4db9ed231dc24350c3` preserves a `FAILED` result even
though PID 33384 exited and port 12100 released: Windows refused the graceful
request and the then-current receipt logic retained that expected message as
an error after verified fallback. The contract was corrected so a successful,
identity-revalidated force fallback is a warning; real fallback, survivor, or
port errors still fail. The historical failed receipt was not rewritten.

Final canonical preflight at `2026-08-11T19:39:46.6123725Z` returned `PASS`,
exit code 0. The 4090 was healthy/PnP OK at PCI `00000000:07:00.0`, 2,813 MiB
used / 21,330 MiB free; the P100 was healthy/PnP OK at PCI
`00000000:04:00.0`, 9 MiB used / 16,280 MiB free. Both ports were free, both
UUIDs unchanged, and neither resource had conflicting or unknown compute.

EC-000223 remains **Not Accepted**: the P100 backend is now singly qualified,
but the sole concurrent retry produced no provider overlap because of the
Dispatch queue concurrency defect. That defect is the recommended next
milestone before any further dual-lane attempt.

## Dispatch persistence concurrency correction

The failed retry's exact exception was:

`ValueError: execution dispatch queue is malformed JSON: Expecting value: line 1 column 1 (char 0)`

from `load_dispatch_queue()` while another process was executing `_write_queue()`
against `runtime/execution_dispatch/queue.json`. `_write_queue()` previously
used `Path.write_text()`, which truncated the authoritative file before the
new JSON bytes were written. The reader observed that empty/partial interval;
this was a truncate/write race, not stale state, a missing replacement, or a
GPU/provider failure.

The correction keeps the existing whole-file queue format and adds a
cross-process lock file at `runtime/execution_dispatch/.queue.lock`. Every
queue read–modify–write mutation now performs: acquire lock, read the latest
complete queue, apply one mutation, write a unique same-directory temporary
file, flush/fsync, atomically `os.replace()` the authoritative queue, and
release the lock. Replace retries are bounded and only handle transient Windows
access transitions. Readers retry JSON decoding three times over a short
bounded interval, then fail closed on persistent malformed state. Stale temp
files are never authoritative. The critical section ends before events,
snapshots, or provider execution; it does not serialize Grace/provider work.

The deterministic queue suite has 19 passing tests: cross-process distinct
creation, concurrent readers, distinct state updates/lost-update protection,
stale temporary files, persistent-corruption fail-closed behavior, lock
timeout, lock release after exceptions, and provider-execution lock-scope
coverage. The focused Dispatch, preflight, provider, reconciliation, and
runtime-cleanup set has 134 passes. One unrelated pre-existing Windows path
separator assertion remains excluded from the baseline; no queue test depends
on it.
