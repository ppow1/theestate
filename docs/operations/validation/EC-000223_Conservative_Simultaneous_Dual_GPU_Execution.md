# EC-000223 — Conservative Simultaneous Dual-GPU Execution

**Current status: Accepted — final conservative Grace dual-GPU acceptance completed 2026-08-12.**

Historical attempts and their failure outcomes below remain preserved as evidence;
the final acceptance record is appended at the end of this document.

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

## Final authorized retry hard-stop

After publication, runtime status showed both registered roots stopped and both
ports free. The exact canonical preflight at `2026-08-11T19:55:56.0444361Z`
returned `PASS`, exit code `0`; the 4090 had 21,319 MiB free and the P100 had
16,280 MiB free.

Exactly one final synchronized attempt was launched. Task A used objective
`grace-obj-4331fc0c79fa`, action `grace-act-a9f2cda43062`, PTM
`res_01KZS6BXDJF99Q60GKHZ5ZCJ0T`, Helen `heldet-56771eda1e49`, commission
`engcom-e94b58e880d0`, authorization `engauth-887b3d18b3d8`, reservation
`gpu-reservation-grace-obj-4331fc0c79fa`, Dispatch `dispatch-fe19ae236e89`,
adapter `adapter-dispatch-fe19ae236e89`, provider receipt
`runtime/engineering_adapter_receipts/grace_bounded_local_text_grace-obj-4331fc0c79fa.json`,
and Grace receipt `gracereceipt-a7fdb677350b`. It ran from `19:56:38Z` to
`19:56:55Z` and proved CUDA0, NVIDIA GeForce RTX 4090, PCI `07:00.0`, and
UUID `GPU-46f3fd00-5454-4536-4196-5d8b727e14f2`.

Task B used objective `grace-obj-3eb4f8beb67c`, action
`grace-act-f828e135ac00`, PTM `res_01KZS6BXDJF99Q60GKHZ5ZCJ0S`, Helen
`heldet-27bb8f811ce2`, commission `engcom-fb7589afbfbe`, authorization
`engauth-1b0bd8f5575d`, reservation
`gpu-reservation-grace-obj-3eb4f8beb67c`, and Dispatch
`dispatch-dceb0916e682`. Its adapter invocation failed at `19:56:54Z` with
`HTTP Error 500: Internal Server Error`; the provider receipt has no actual
runtime identity and `placement_match=false`.

During the attempt, the P100 reached 100% utilization and 3,373 MiB while the
4090 reached 93% utilization and approximately 14,249 MiB. Immediately after,
`nvidia-smi` reported `GPU 0000:04:00.0 is lost. Reboot the system to recover
this GPU`. Only the 4090 remained enumerated. This is a hard-stop device-loss
condition. No provider overlap is accepted because Task B has no successful
provider receipt or physical identity. No retry, reset, reboot, driver/device
operation, or cleanup action was performed after the loss; live evidence was
preserved exactly.

EC-000223 remains **Not Accepted — P100 device loss during final retry**.

## Post-cold-restart recovery verification

The host cold-restart recovery was verified at `2026-08-11T20:42:06.8442056Z`;
Windows reports the last boot at `2026-08-11T16:23:08-04:00`. No Grace,
Ollama, Qwen, or concurrent workload was launched after restart.

The repository-owned canonical preflight
(`powershell -ExecutionPolicy Bypass -File tools/gpu-parallel-preflight.ps1 -Json`)
returned `PASS`, exit code `0`, with no warnings or reasons. Direct `nvidia-smi`
and Windows PnP checks agreed with the canonical result. The complete recovery
observation is appended to `operations/diagnostics/ec-000223-preflight-observation.json`.

P100 recovery classification: **RECOVERED_HEALTHY**. NVML is visible; PnP is
present and `OK`; the full UUID is
`GPU-6785b322-899d-8eec-e817-31d83279a414`; current PCI is
`00000000:04:00.0`; health is `OK`; and no device-loss symptom was observed.
Idle telemetry was 9 MiB used / 16,280 MiB free, 0% utilization, 38 C, and
26.27 W. Lane port 12100 was not listening and had no owner.

RTX 4090 recovery classification: **RECOVERED_HEALTHY** independently. NVML is
visible; PnP is present and `OK`; the authoritative full UUID is
`GPU-46f3fd00-5454-4536-4196-5d8b727e14f2`; current PCI is
`00000000:07:00.0`; health is `OK`; and WDDM/display residency is acceptable.
Telemetry was 2,534 MiB used / 21,609 MiB free, 18% utilization, 51 C, and
22.21 W. Lane port 12409 was not listening and had no owner; non-conflicting
WDDM clients are expected and do not constitute compute ownership.

The read-only GPU-runtime status found no live Estate-owned runtime, child PID,
provider invocation, reservation, or listening lane port. It did retain stopped
historical registry entries for both lanes and one pending P100 dispatch
reference; these are stale registry metadata, not live runtime residue, and no
cleanup or mutation was performed. The prior final-retry P100 device-loss
evidence remains unchanged. EC-000223 remains **Not Accepted**. Both GPUs are
`SAFE_FOR_NEXT_ENGINEERING_STEP=yes`, but this verification does not authorize
or perform another dual-GPU acceptance retry; the conservative P100 operating
envelope must be evaluated first.

## One conservative dual-GPU operating-envelope attempt

Before the live attempt, publication `72b76446f53493952f5ea7253e80b95053d59eba`
contained a generic bounded-runtime policy. It enforces one provider request per
runtime lane with reject-when-busy admission and uses supported Ollama request
options. The P100 profile was `llama3.2:3b`, `num_predict=64`, `num_ctx=2048`;
the 4090 profile was `qwen3:8b`, `num_predict=128`, `num_ctx=4096`. No power,
clock, driver, OS, or GPU controls were changed. Focused deterministic and
regression tests passed (`128 passed`); PowerShell parser and diff checks passed.

Exactly one new bounded attempt was launched at `2026-08-11T20:53:27Z` after
read-only status and preflight passed. The 4090 provider interval was
`20:53:36Z`–`20:53:41Z`; the P100 provider interval was
`20:53:36Z`–`20:53:44Z`, giving 5.0 seconds of positive provider overlap.

The P100 task completed through its governed chain: objective
`grace-obj-f636f083cad6`, action `grace-act-d3d76ad8787c`, PTM
`res_01KZS9M80CE1QT37AGYXNRPEF2`, Helen `heldet-ea1663be67ee`, commission
`engcom-7add155582e4`, authorization `engauth-a9a64a9ce9c1`, reservation
`gpu-reservation-grace-obj-f636f083cad6`, Dispatch `dispatch-46045e17928f`,
adapter `adapter-dispatch-46045e17928f`, and provider receipt
`runtime/engineering_adapter_receipts/grace_bounded_local_text_grace-obj-f636f083cad6.json`.
Owned runner evidence proves CUDA0, Tesla P100-PCIE-16GB, PCI `04:00.0`, and
UUID `GPU-6785b322-899d-8eec-e817-31d83279a414`; placement matched.

The 4090 task created its independent governed records through Dispatch
`dispatch-c3bd236b32a4` and adapter `adapter-dispatch-c3bd236b32a4`, but its
provider result failed closed with `Qwen returned a malformed or incomplete
response`. Its owned Ollama runner log independently shows CUDA0, NVIDIA
GeForce RTX 4090, PCI `07:00.0`, and the required UUID, but the adapter did not
accept this as a completed provider result. Therefore the attempt does not
meet EC-000223 acceptance: both provider calls did not complete successfully,
and no acceptance credit is taken for the 4090 task.

The lightweight monitor observed no P100 NVML loss, but its in-flight sample
stream was not durably emitted because the wrapper deadlocked buffering the
large governed JSON result after provider completion. Exact in-flight telemetry
peaks are therefore **not claimed**. Provider logs record model/KV buffers of
1,918.35/224 MiB on P100 and 4,643.78/576 MiB on 4090; these are runtime-log
allocations, not telemetry peaks and not a load qualification.

Postflight preflight returned `PASS`, exit code `0`. P100 remained NVML/PnP
healthy at 9 MiB used, 16,280 MiB free, 0%, 38 C, 26.29 W; 4090 remained
healthy at 2,421 MiB used, 21,722 MiB free, 6%, 44 C, 21.64 W. Both ports were
free and both full UUIDs/PCI identities were unchanged. Governed quiesce
completed for both owned lanes with cleanup receipts
`gpu-cleanup-cb90c34e02db486581b8987f087f203b` and
`gpu-cleanup-1f41394c28a843eeab12fbf40a4668bf`; owned PIDs exited and no
unrelated process was modified.

EC-000223 remains **Not Accepted — conservative attempt had a 4090 provider
failure**. No retry was performed. Heavy parallelism, saturation, SDXL,
P100-32B, sustained throughput, and maximum-load operation remain unqualified.

## Final conservative acceptance — 2026-08-12

**Status: ACCEPTED.** This is the current authoritative EC-000223 result for
PR #529. The earlier failed attempts in this document remain historical records
and are not erased or rewritten.

### Durable evidence

- Runtime acceptance artifact:
  `A:\EstateRuntime\host\estate-main\current\runtime\acceptance\ec-000223-pr529-final-attempt.json`
- Acceptance artifact SHA-256:
  `2A8CF89D818A700DD3369E787B593A1252CF16AF7BE12F25F5F51CC1CBACE68E`
- RTX 4090 cleanup receipt:
  `gpu-cleanup-ce0bedbef3ed4872a9ac15f5a833e431`
  (SHA-256 `ADD3CD9A509522427A669731C06ECBBFEFA06AA31E09A449EAEB3F966D0C2B6`)
- Tesla P100 cleanup receipt:
  `gpu-cleanup-f6dcfd71889c4b278a571897330e87f2`
  (SHA-256 `16CCE9C9849C9F32E280FD60FA9CAC051D34A481660253C18F1D0E4B0659A21C`)

### Accepted governed executions

| Task | Objective | Action | PTM | Helen | Commission | Authorization | Dispatch | Adapter | Provider interval | Actual GPU UUID |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| RTX 4090 | `grace-obj-cda6af0bdc4c` | `grace-act-6910ae972cc0` | `res_01KZVB20TSH1XCSX5NJS408AFT` | `heldet-7789e265c8ee` | `engcom-d1768dda5a76` | `engauth-738e452c338a` | `dispatch-8b354c8d123c` | `adapter-dispatch-8b354c8d123c` | 15:57:05Z–15:57:10Z | `GPU-46f3fd00-5454-4536-4196-5d8b727e14f2` |
| Tesla P100 | `grace-obj-5cec94c466bd` | `grace-act-72404a347726` | `res_01KZVB1Z8VB2EAZPRN7JZVX64Z` | `heldet-748897907631` | `engcom-c8185d75d1b6` | `engauth-62e4975c6c07` | `dispatch-d04f085e21b5` | `adapter-dispatch-d04f085e21b5` | 15:57:03Z–15:57:09Z | `GPU-6785b322-899d-8eec-e817-31d83279a414` |

Provider intervals overlapped for **4 seconds**. Required, allocated, lane,
configured, and actual physical identities matched for both tasks; no
cross-assignment occurred. The existing P100 `>80%` for two consecutive
samples guard did not fire. The accepted P100 profile was `llama3.2:3b`,
context 1024, output cap 32, concurrency 1. The accepted 4090 profile was the
bounded qualified `qwen3:8b` profile, concurrency 1.

Both lanes were governed-cleaned, ports `12409` and `12100` were released,
both GPUs remained healthy with UUID/PCI identities unchanged, no P100 device
loss occurred, and no unrelated process was modified.

This acceptance proves conservative simultaneous governed execution only. It
does not qualify stress, benchmarking, SDXL, P100-32B, sustained throughput,
or maximum-load operation. P100 stability-envelope and prior device-loss
forensics remain owned by parking-lot item `PL-0047` and are explicitly outside
EC-000223.
