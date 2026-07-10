# Cross-Department Operational Coordination

The cross-department coordination layer lets Operations coordinate approved campaign work across Engineering, Character Architecture, Workforce, and other departments without manual Steward relaying for routine sequencing.

## Boundary

- Operations Manager may sequence routine work only inside the `DepartmentAuthority` envelope.
- Departments retain their departmental authority and must acknowledge requests before work is treated as ready.
- Execution providers remain behind existing governed seams such as dispatch/adapters; this layer records the intended provider but does not execute provider work.
- Traffic Controller and Steward review remains required for unresolved contention, authority conflicts, missed commitments, and institutional acceptance.

## Model

`estate.core.department_coordination` provides durable data objects for:

- `DepartmentCoordination`: one campaign-level coordination record.
- `DepartmentRequest`: a department inbox item with commitment, execution-provider boundary, acknowledgement, sequence, evidence, dependencies, handoffs, blockers, and service-level expectations.
- `DepartmentDependency`: an upstream department request that must complete before downstream work releases.
- `DepartmentHandoff`: an outbox/inbox transfer between departments with evidence.
- `DepartmentBlocker`: unresolved operational issue that can be resolved routinely or escalated.
- `DepartmentAuthority`: the delegated Operations Manager authority envelope.

## Runtime

`estate.core.department_coordination_runtime.DepartmentCoordinationRuntime` stores records below `runtime/department_coordination/` and writes Collaboration Layer routing events below `runtime/collaboration/events/`.

Typical flow:

1. Register a `DepartmentCoordination` for an approved campaign.
2. Department requests are routed to department inbox views through Collaboration Layer events.
3. Departments acknowledge requests.
4. Operations sequences acknowledged work whose dependencies are released and blockers are resolved.
5. Completed upstream requests allow Operations to release downstream dependencies.
6. Handoffs are delivered and visible in department outbox views.
7. Unresolved contention or boundary conflict is escalated as a Traffic Controller / Steward review recommendation.

## Status Views

The runtime exposes:

- `department_view(department)`: inbox and outbox records for one department.
- `dependency_status(coordination_id)`: blocked and released cross-department dependencies plus escalations.
- `runtime/department_coordination/status.json`: summary for operations surfaces.

## Acceptance Mapping

- Campaigns can request work from multiple departments with acknowledgements through `register()` and `acknowledge()`.
- Dependencies block and release through `dependency_status()` and `release_dependency()`.
- Routine sequencing happens through `sequence_ready_work()` under the Operations Manager authority envelope.
- Department and provider boundaries are enforced by `DepartmentAuthority`, department checks, and execution-provider metadata that never invokes providers directly.
- Escalation happens through `escalate_unresolved()`, producing a `RecommendedAction` for Steward / Traffic Controller review.
