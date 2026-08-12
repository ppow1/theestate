# Governed GPU-pinned runtime lanes

EC-000217 adds a narrow runtime binding beneath the existing provider and
Dispatch contracts. A registered `RuntimeLane` is an isolated loopback Ollama
process configuration. Its durable physical identity is the full NVIDIA UUID;
runtime ordinals are not accepted as identity.

`config/runtime/gpu_runtime_lanes.json` is the registered lane contract. It
contains the lane, provider/model compatibility, loopback endpoint, resource
ID, UUID, and an allow-listed environment binding. The lane launcher starts a
candidate process with `CUDA_VISIBLE_DEVICES=<full UUID>` and records only
safe process/binding evidence and owned runner-log paths in
`runtime/compute_resources/runtime_lanes.json`. Backend controls are also
allow-listed per runtime instance. For example, a CUDA-qualified instance can
select an installed Ollama CUDA library and disable Vulkan discovery so the
Vulkan scheduler cannot silently select another physical GPU.
The shared machine Ollama daemon remains an existing Core dependency; it is not
used as a fallback for a required pinned request.

When a request requires a GPU, the Qwen adapter requires a registered lane and
checks allocated resource ID and UUID equality before model execution. After
model execution it parses the owned backend's selected-device evidence and
correlates the reported PCI device to a fresh NVIDIA inventory. The receipt
keeps configured-required and configured-lane UUIDs separate from the actual
runtime identity. `runtime_bound_gpu_uuid` is actual evidence only; it is
never derived from the lane configuration. Missing or contradictory runtime
identity fails closed before a success artifact can be published. Grace/operator text cannot
inject an endpoint; only governed lane IDs carried by the execution authority
are accepted.

Office Compute and the external Stream Deck bridge consume the same
Estate-owned operator projection. The projection is dynamic for N resources;
the current Stream Deck profile exposes two status meters, one per configured
physical UUID. The meter text is VRAM occupancy and its ring is actual GPU
utilization. Stale or unknown telemetry is not rendered as zero.

This increment does not implement multi-host orchestration, automatic recovery,
P100 32B deployment, or heavy workload acceptance.

## Governed runtime lifecycle

The existing runtime-lane registry is also the root of cleanup authority. The
Estate does not provide a global GPU-memory flush and never resets a device.
`gpu-runtime status` correlates the registered root PID with its executable,
exact command line, process creation time, child tree, endpoint port,
reservations, Dispatch queue, provider activity, pending tasks, and
reconciliation state. Missing evidence produces `UNKNOWN`, not ownership.

A live root can be `IDLE`, `ACTIVE`, `STALE_CANDIDATE`, `QUIESCING`, or
`UNKNOWN`; a missing registered root is `STOPPED`. Age is only a stale signal.
Quiescence requires positive `ESTATE_OWNED` evidence and empty active,
pending, and in-flight gates. Children are eligible only through the verified
parent tree. Unrelated processes on the same GPU are never selected.

Operator commands are:

```text
python -m estate.cli.main gpu-runtime status --json
python -m estate.cli.main gpu-runtime quiesce --lane <registered-lane-id> --actor operator --confirm --json
```

The second command requests normal termination for the proven owned tree,
forces only verified survivors if necessary, verifies the owned PIDs and lane
port are gone, refreshes GPU telemetry, and writes
`estate.gpu-runtime-cleanup-receipt.v1` evidence under
`runtime/compute_resources/cleanup_receipts/`. Cleanup success or failure is
also emitted through the existing transport-neutral operational-event log.
Conversation-facing Grace has no direct quiesce or arbitrary PID authority.
