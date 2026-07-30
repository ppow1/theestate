# Engineering Capability Lifecycle — Source-of-Truth Matrix

Status: Proposed reconciliation matrix.

| Concept | Canonical source | Current evidence | Must not be used as substitute |
|---|---|---|---|
| Worker identity | Existing personnel/worker identity records and `WorkerAssignmentRecord.worker_id` | `src/estate/core/worker_assignments.py`, personnel registries | Provider ID, model name, display name, or assigned label |
| Workforce qualification | Helen request/assessment and future qualification evidence referenced by assessment | `HelenWorkforceStore`, `runtime/workforce_development/` | Catalog capability claim |
| Capability declaration | `config/providers/catalog.json` capability descriptors; worker specification for human/worker capability | `ProviderCatalog`, `ProviderCapability` | `data/registry/capabilities.json` resource inventory alone |
| Capability qualification | Helen assessment plus qualification evidence and approved test result | Existing determination fields are partial | Declared status or implementation kind |
| Provider identity | `ProviderDescriptor.provider_id` in `config/providers/catalog.json` | `provider_catalog.py` | Legacy `data/registry/providers.json` IDs |
| Adapter implementation | Registered adapter class/implementation reference and version | `execution_provider_adapter.py`, Codex/ComfyUI adapters | Provider descriptor alone |
| Health | `ProviderHealthRecord` and current health projection | `provider_health.py`, Engineering health runtime | Process existence or catalog status |
| Availability/capacity | Provider capacity records and governed reservation evidence | `provider_capacity.py`, scheduler seam | Health alone |
| Authorization | PTM readiness, decision, boundary review, selection, reservation, Dispatch, and authority records | PTM/orchestrator and Dispatch contracts | Recommendation, receipt, or Helen assessment alone |
| Routing recommendation | `provider_routing_recommendations*` and Engineering routing view | Advisory only | Selection or Dispatch authorization |
| Provider selection | Authorized selector decision referencing recommendation and evidence | Required Gate-B extension | Catalog order or adapter default |
| Reservation | Governed provider scheduler reservation, reconciled with PTM eligibility | Existing scheduler seam; precedence unresolved | Dispatch queue state |
| Dispatch | `execution_dispatch.py` queue/event/snapshot and handoff | Canonical execution boundary | Direct worker/provider call |
| Artifact | Provider result plus artifact path/identifier/hash under approved scope | Adapter result and reconciliation | Process exit code |
| Receipt | Provider receipt/result and execution evidence | Adapter result/runtime artifacts | Worker `completed` status alone |
| Validation | Named package/commission recipe and independent validation result | Existing validation lifecycle | Provider success or registration |
| Acceptance | Chief Architect and Steward decisions, as applicable | Acceptance/closure model | Grace closure, Helen disposition, or test pass |
| Capability gap | Proposed future `capability_gap_v1` record linked to Helen assessment and Grace objective | No current authoritative record | Read-only gap report |
| Worker specification | Proposed `worker_specification_v1` record produced by Engineering consultation | No current authoritative record | Provider descriptor or job title |
| Enabling dependency | PTM/orchestrator dependency/readiness record linked to original objective and enabling project | No current standard join | A mutable note or chat message |
| Registration result | Proposed registration result linked to adapter/provider/capability versions and evidence | No current standard result | Editing catalog without evidence |
| Re-evaluation | Proposed Helen re-evaluation record against fresh evidence | No current standard record | Original assessment or stale snapshot |

## Conflict rule

When records disagree, preserve all records, mark the projection conflicted or
stale, and stop the dependent action. The source owner or Chief Architect
resolves semantic conflicts; no derived dashboard may overwrite canonical state.
