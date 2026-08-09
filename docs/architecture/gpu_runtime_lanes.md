# Governed GPU-pinned runtime lanes

EC-000217 adds a narrow runtime binding beneath the existing provider and
Dispatch contracts. A registered `RuntimeLane` is an isolated loopback Ollama
process configuration. Its durable physical identity is the full NVIDIA UUID;
runtime ordinals are not accepted as identity.

`config/runtime/gpu_runtime_lanes.json` is the registered lane contract. It
contains the lane, provider/model compatibility, loopback endpoint, resource
ID, UUID, and an allow-listed environment binding. The lane launcher starts a
candidate process with `CUDA_VISIBLE_DEVICES=<full UUID>` and records only
safe process/binding evidence in `runtime/compute_resources/runtime_lanes.json`.
The shared machine Ollama daemon remains an existing Core dependency; it is not
used as a fallback for a required pinned request.

When a request requires a GPU, the Qwen adapter requires a registered lane and
checks allocated resource ID and UUID equality before model execution. The
receipt records the lane, endpoint, allocated UUID, bound UUID, and process
identity. A mismatch or missing lane fails closed. Grace/operator text cannot
inject an endpoint; only governed lane IDs carried by the execution authority
are accepted.

Office Compute and the external Stream Deck bridge consume the same
Estate-owned operator projection. The projection is dynamic for N resources;
the current Stream Deck profile exposes two status meters, one per configured
physical UUID. The meter text is VRAM occupancy and its ring is actual GPU
utilization. Stale or unknown telemetry is not rendered as zero.

This increment does not implement multi-host orchestration, automatic recovery,
P100 32B deployment, or heavy workload acceptance.
