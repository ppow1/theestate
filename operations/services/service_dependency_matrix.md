# Estate Service Dependency Matrix

Read-only operational view. This document does not create a duplicate dependency registry and records only explicit source-backed service dependencies.

Generated: 2026-07-04T13:24:33+00:00

## Summary
- Services: 10
- Explicit service dependencies: 0
- Startup steps: 10
- Warnings: 9

## Startup order
1. `SVC-000001` — Ledger Service
2. `SVC-000002` — Registry Service
3. `SVC-000003` — Capability Service
4. `derived:alfred_orchestration` — Alfred Orchestration
5. `derived:helen_hr_employee_onboarding` — Helen HR Employee Onboarding
6. `derived:mailbox_operations` — Mailbox Operations
7. `derived:mission_control_workspace` — Mission Control Workspace
8. `derived:notification_router` — Notification Router
9. `derived:operational_validation` — Operational Validation
10. `derived:worker_runtime_management` — Worker Runtime Management

## Matrix

### Ledger Service (`SVC-000001`)
- Owner: Archives
- Operational status: Active
- Required services: None explicitly recorded
- Required providers: None explicitly matched
- Optional integrations: None explicitly recorded
- Startup after: No explicit startup prerequisite
- Failure impact: No explicit downstream dependents recorded.
- Source artifacts: data/registry/services.json

### Registry Service (`SVC-000002`)
- Owner: Archives
- Operational status: Active
- Required services: None explicitly recorded
- Required providers: None explicitly matched
- Optional integrations: None explicitly recorded
- Startup after: No explicit startup prerequisite
- Failure impact: No explicit downstream dependents recorded.
- Source artifacts: data/registry/services.json

### Capability Service (`SVC-000003`)
- Owner: Administration
- Operational status: Draft
- Required services: None explicitly recorded
- Required providers: None explicitly matched
- Optional integrations: None explicitly recorded
- Startup after: No explicit startup prerequisite
- Failure impact: No explicit downstream dependents recorded.
- Source artifacts: data/registry/services.json

### Alfred Orchestration (`derived:alfred_orchestration`)
- Owner: Operations Center
- Operational status: implemented
- Required services: None explicitly recorded
- Required providers: None explicitly matched
- Optional integrations: None explicitly recorded
- Startup after: No explicit startup prerequisite
- Failure impact: No explicit downstream dependents recorded.
- Source artifacts: docs/alfred_v1_operator_completion.md, docs/alfred_v1_status.md, src/estate/cli/main.py, src/estate/core/alfred.py

### Helen HR Employee Onboarding (`derived:helen_hr_employee_onboarding`)
- Owner: Human Resources
- Operational status: implemented
- Required services: None explicitly recorded
- Required providers: None explicitly matched
- Optional integrations: None explicitly recorded
- Startup after: No explicit startup prerequisite
- Failure impact: No explicit downstream dependents recorded.
- Source artifacts: docs/onboarding/Helen_HR_Operational_Onboarding.md, src/estate/cli/main.py, src/estate/core/hr_onboarding.py

### Mailbox Operations (`derived:mailbox_operations`)
- Owner: Collaboration
- Operational status: implemented
- Required services: None explicitly recorded
- Required providers: None explicitly matched
- Optional integrations: None explicitly recorded
- Startup after: No explicit startup prerequisite
- Failure impact: No explicit downstream dependents recorded.
- Source artifacts: docs/collaboration/Mailbox_Infrastructure_v1.md, src/estate/cli/main.py, src/estate/core/collaboration_messages.py, src/estate/core/collaboration_ops.py, src/estate/core/mailbox_index.py, src/estate/core/mailbox_sync_duty.py

### Mission Control Workspace (`derived:mission_control_workspace`)
- Owner: Operations Center
- Operational status: implemented
- Required services: None explicitly recorded
- Required providers: None explicitly matched
- Optional integrations: None explicitly recorded
- Startup after: No explicit startup prerequisite
- Failure impact: No explicit downstream dependents recorded.
- Source artifacts: docs/operations/Mission_Control_Workspace_v1.md, docs/operations/Operations_Board_Runtime_Integration.md, src/estate/cli/main.py, src/estate/core/mission_control_workspace.py, src/estate/core/operations_board.py, src/estate/core/steward_command_center.py

### Notification Router (`derived:notification_router`)
- Owner: Operations Center
- Operational status: implemented
- Required services: None explicitly recorded
- Required providers: None explicitly matched
- Optional integrations: None explicitly recorded
- Startup after: No explicit startup prerequisite
- Failure impact: No explicit downstream dependents recorded.
- Source artifacts: src/estate/cli/main.py, src/estate/core/gotify_adapter.py, src/estate/core/notification_router.py

### Operational Validation (`derived:operational_validation`)
- Owner: Validation
- Operational status: implemented
- Required services: None explicitly recorded
- Required providers: None explicitly matched
- Optional integrations: None explicitly recorded
- Startup after: No explicit startup prerequisite
- Failure impact: No explicit downstream dependents recorded.
- Source artifacts: docs/operations/Operational_Validation_Reporting.md, operations/validation/validation_handoff_artifact_workflow.md, src/estate/cli/main.py, src/estate/core/local_operational_validation.py, src/estate/core/operational_validation.py, src/estate/core/work_package_validation.py

### Worker Runtime Management (`derived:worker_runtime_management`)
- Owner: Operations Center
- Operational status: implemented
- Required services: None explicitly recorded
- Required providers: None explicitly matched
- Optional integrations: None explicitly recorded
- Startup after: No explicit startup prerequisite
- Failure impact: No explicit downstream dependents recorded.
- Source artifacts: docs/collaboration/Local_Worker_Launch_Adapter_v1.md, docs/collaboration/Worker_Runtime_Contract_v1.md, src/estate/cli/main.py, src/estate/core/autonomous_work_queue_scheduler.py, src/estate/core/worker_runtime_heartbeat.py, src/estate/core/worker_runtime_monitor.py

## Warnings
- incomplete_dependency_metadata: data/registry/services.json — SVC-000001 has no explicit service dependency metadata.
- incomplete_dependency_metadata: data/registry/services.json — SVC-000002 has no explicit service dependency metadata.
- incomplete_dependency_metadata: data/registry/services.json — SVC-000003 has no explicit service dependency metadata.
- unmatched_provider_service: data/registry/providers.json — Provider service field does not exactly match a catalog service id or name; not attached to the matrix.
- unmatched_provider_service: data/registry/providers.json — Provider service field does not exactly match a catalog service id or name; not attached to the matrix.
- unmatched_provider_service: data/registry/providers.json — Provider service field does not exactly match a catalog service id or name; not attached to the matrix.
- unmatched_provider_service: data/registry/providers.json — Provider service field does not exactly match a catalog service id or name; not attached to the matrix.
- unmatched_provider_service: data/registry/providers.json — Provider service field does not exactly match a catalog service id or name; not attached to the matrix.
- unmatched_provider_service: data/registry/providers.json — Provider service field does not exactly match a catalog service id or name; not attached to the matrix.
