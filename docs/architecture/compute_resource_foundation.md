# Compute Resource Foundation

Status: C462 implementation slice

The Estate represents physical NVIDIA devices as `ComputeResourceObservation`
records in `src/estate/core/compute_resources.py`. The canonical identity is
`host_id:nvidia:<NVIDIA UUID>`; GPU names, PCI bus IDs, and runtime ordinals
are supporting observations. Runtime ordinals are never placement identity.

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
