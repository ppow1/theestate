# Compute Resource Foundation

Status: C462 implementation slice

The Estate represents physical NVIDIA devices as `ComputeResourceObservation`
records in `src/estate/core/compute_resources.py`. The canonical identity is
`host_id:nvidia:<NVIDIA UUID>`; GPU names, PCI bus IDs, and runtime ordinals
are supporting observations. Runtime ordinals are never placement identity.

The Grace expected inventory is explicit in `GRACE_EXPECTED_GPUS`: the P100
UUID is `GPU-6785b322-899d-8eec-e817-31d83279a414` at `04:00.0`, and the RTX
4090 UUID is `GPU-46f3fd00-5454-4536-4196-5d8b727e14f2` at `07:00.0`. Current
`nvidia_smi_index` and `cuda_index` values are joined observations and may
reverse independently. A record is `HEALTHY`, `DEGRADED`, `LOST`, or
`UNKNOWN`; `dispatch_allowed` is false unless physical identity, Windows,
NVML/CUDA evidence (when collected), and fresh telemetry agree. Missing or
contradictory evidence fails closed for that physical GPU and never reroutes
to its sibling. The P100 cold-recovery condition and prohibited heavy race
remain documented by reference in PL-0042.

`ComputeResourceRequirements` is the provider-neutral placement contract. It
supports GPU requirement, minimum free VRAM, compute capability, preferred or
required physical resource, exclusions, compatibility tags, reservation
reference, and evidence reference. `select_resource` returns explainable
placement evidence and fails closed for a required resource. It never falls
back to CPU, another GPU, model, or provider.

Health and capacity are separate fields. Health is deterministic from
visibility, identity, PnP evidence, and telemetry freshness. Capacity records
availability, VRAM sufficiency, and reservation state. The
`ComputeReservationLedger` is only a constrained-resource reservation hook
under `runtime/engineering_scheduler`; governed provider scheduling and
Execution Dispatch remain the authority boundaries.

Dispatch carries `compute_resource_requirements` unchanged. The provider
neutral adapter carries the same snapshot in metadata for the concrete adapter
to enforce or report. Office of the Steward reads the dynamic projection at
`runtime/compute_resources/gpus.json` through the `compute` surface.

No module in this slice performs CUDA work, model inference, GPU reset, driver
change, device reconfiguration, reboot, or automatic recovery.
