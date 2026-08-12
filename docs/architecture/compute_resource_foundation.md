# Estate Compute Resource Foundation

Status: EC-000096 integrated on current main

The Estate represents physical NVIDIA devices as `ComputeResourceObservation`
records in `src/estate/core/compute_resources.py`. The durable identity is
`host_id:nvidia:<NVIDIA UUID>`. Exact name, PCI bus, PnP/NVML state, and runtime
ordinals are supporting evidence; CUDA/NVIDIA ordinals are never placement
identity.

`ComputeResourceRequirements` is an optional provider-neutral execution
constraint. It carries GPU requirement, minimum free VRAM, required/preferred
resource or UUID, exclusions, compatibility tags, reservation reference,
evidence reference, and freshness. Required placement fails closed. Preferred
placement can explain an eligible alternate. No CPU, GPU, model, runtime, or
provider fallback is implicit.

Health, capability, and capacity remain separate. Health classifies identity,
NVML visibility, Windows PnP evidence, and telemetry freshness. Capacity
classifies VRAM and admission availability. `ComputeReservationLedger` is an
exclusive-resource hook under the existing governed scheduler runtime; it is
not a scheduler or provider registry. The existing scheduler remains the owner
of reservation decisions and Execution Dispatch remains the only execution
release path.

Dispatch carries `compute_resource_requirements` alongside, and without
replacing, current Grace objective/action, Helen, Engineering commission and
authorization, PTM readiness, classification, scope, decision, and boundary
fields. The provider-neutral adapter carries the same field and validates it
through the current adapter schema.

Office of the Steward exposes a read-only, N-device Compute projection from
`runtime/compute_resources/gpus.json`, including current resource evidence and
canonical reservation references where present. Office is not the scheduler
and has no GPU mutation or recovery authority. Grace can inspect evidence and
request governed execution constraints through existing Dispatch/provider
paths; it cannot issue hardware commands.

This foundation intentionally does not implement multi-host orchestration,
multi-GPU allocation policy, production P100 32B service deployment, or
aggressive concurrency. PL-0042 remains the preserved crash-forensics and
heavy-SDXL non-action boundary.
