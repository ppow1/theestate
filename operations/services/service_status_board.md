# Operations Center Service Status Board

Read-only Operations Center view. This board aggregates existing artifacts and does not become the source of truth for service status.

Generated: 2026-07-05T04:12:43+00:00
Refresh behavior: quiet_refresh_no_disruptive_redraws

## Summary
- Overall state: degraded
- Services: 10
- Healthy: 9
- Degraded: 1
- Blocked: 0
- Unavailable: 0
- Unknown: 0
- Warnings: 12

## Services

### Ledger Service (`SVC-000001`)
- Board state: healthy
- Health: healthy
- Readiness: ready
- Validation: ready
- Dependencies: none_recorded
- Startup sequence: 1
- Failure impact: No explicit downstream dependents recorded.
- Source artifacts: data/registry/services.json
- Drill-down: catalog `runtime/services/estate_service_catalog.json`, dependencies `runtime/services/service_dependency_matrix.json`, health `runtime/services/service_health_registry.json`

### Registry Service (`SVC-000002`)
- Board state: healthy
- Health: healthy
- Readiness: ready
- Validation: ready
- Dependencies: none_recorded
- Startup sequence: 2
- Failure impact: No explicit downstream dependents recorded.
- Source artifacts: data/registry/services.json
- Drill-down: catalog `runtime/services/estate_service_catalog.json`, dependencies `runtime/services/service_dependency_matrix.json`, health `runtime/services/service_health_registry.json`

### Capability Service (`SVC-000003`)
- Board state: degraded
- Health: unknown
- Readiness: partial
- Validation: metadata_only
- Dependencies: none_recorded
- Startup sequence: 3
- Failure impact: No explicit downstream dependents recorded.
- Source artifacts: data/registry/services.json
- Drill-down: catalog `runtime/services/estate_service_catalog.json`, dependencies `runtime/services/service_dependency_matrix.json`, health `runtime/services/service_health_registry.json`

### Alfred Orchestration (`derived:alfred_orchestration`)
- Board state: healthy
- Health: healthy
- Readiness: ready
- Validation: source_links_checked
- Dependencies: none_recorded
- Startup sequence: 4
- Failure impact: No explicit downstream dependents recorded.
- Source artifacts: docs/alfred_v1_operator_completion.md, docs/alfred_v1_status.md, src/estate/cli/main.py, src/estate/core/alfred.py
- Drill-down: catalog `runtime/services/estate_service_catalog.json`, dependencies `runtime/services/service_dependency_matrix.json`, health `runtime/services/service_health_registry.json`

### Helen HR Employee Onboarding (`derived:helen_hr_employee_onboarding`)
- Board state: healthy
- Health: healthy
- Readiness: ready
- Validation: source_links_checked
- Dependencies: none_recorded
- Startup sequence: 5
- Failure impact: No explicit downstream dependents recorded.
- Source artifacts: docs/onboarding/Helen_HR_Operational_Onboarding.md, src/estate/cli/main.py, src/estate/core/hr_onboarding.py
- Drill-down: catalog `runtime/services/estate_service_catalog.json`, dependencies `runtime/services/service_dependency_matrix.json`, health `runtime/services/service_health_registry.json`

### Mailbox Operations (`derived:mailbox_operations`)
- Board state: healthy
- Health: healthy
- Readiness: ready
- Validation: source_links_checked
- Dependencies: none_recorded
- Startup sequence: 6
- Failure impact: No explicit downstream dependents recorded.
- Source artifacts: docs/collaboration/Mailbox_Infrastructure_v1.md, src/estate/cli/main.py, src/estate/core/collaboration_messages.py, src/estate/core/collaboration_ops.py, src/estate/core/mailbox_index.py, src/estate/core/mailbox_sync_duty.py
- Drill-down: catalog `runtime/services/estate_service_catalog.json`, dependencies `runtime/services/service_dependency_matrix.json`, health `runtime/services/service_health_registry.json`

### Mission Control Workspace (`derived:mission_control_workspace`)
- Board state: healthy
- Health: healthy
- Readiness: ready
- Validation: source_links_checked
- Dependencies: none_recorded
- Startup sequence: 7
- Failure impact: No explicit downstream dependents recorded.
- Source artifacts: docs/operations/Mission_Control_Workspace_v1.md, docs/operations/Operations_Board_Runtime_Integration.md, src/estate/cli/main.py, src/estate/core/mission_control_workspace.py, src/estate/core/operations_board.py, src/estate/core/steward_command_center.py
- Drill-down: catalog `runtime/services/estate_service_catalog.json`, dependencies `runtime/services/service_dependency_matrix.json`, health `runtime/services/service_health_registry.json`

### Notification Router (`derived:notification_router`)
- Board state: healthy
- Health: healthy
- Readiness: ready
- Validation: source_links_checked
- Dependencies: none_recorded
- Startup sequence: 8
- Failure impact: No explicit downstream dependents recorded.
- Source artifacts: src/estate/cli/main.py, src/estate/core/gotify_adapter.py, src/estate/core/notification_router.py
- Drill-down: catalog `runtime/services/estate_service_catalog.json`, dependencies `runtime/services/service_dependency_matrix.json`, health `runtime/services/service_health_registry.json`

### Operational Validation (`derived:operational_validation`)
- Board state: healthy
- Health: healthy
- Readiness: ready
- Validation: source_links_checked
- Dependencies: none_recorded
- Startup sequence: 9
- Failure impact: No explicit downstream dependents recorded.
- Source artifacts: docs/operations/Operational_Validation_Reporting.md, operations/validation/validation_handoff_artifact_workflow.md, src/estate/cli/main.py, src/estate/core/local_operational_validation.py, src/estate/core/operational_validation.py, src/estate/core/work_package_validation.py
- Drill-down: catalog `runtime/services/estate_service_catalog.json`, dependencies `runtime/services/service_dependency_matrix.json`, health `runtime/services/service_health_registry.json`

### Worker Runtime Management (`derived:worker_runtime_management`)
- Board state: healthy
- Health: healthy
- Readiness: ready
- Validation: source_links_checked
- Dependencies: none_recorded
- Startup sequence: 10
- Failure impact: No explicit downstream dependents recorded.
- Source artifacts: docs/collaboration/Local_Worker_Launch_Adapter_v1.md, docs/collaboration/Worker_Runtime_Contract_v1.md, src/estate/cli/main.py, src/estate/core/autonomous_work_queue_scheduler.py, src/estate/core/worker_runtime_heartbeat.py, src/estate/core/worker_runtime_monitor.py
- Drill-down: catalog `runtime/services/estate_service_catalog.json`, dependencies `runtime/services/service_dependency_matrix.json`, health `runtime/services/service_health_registry.json`

## Warnings
- unmatched_provider_service: data/registry/providers.json — Provider service field does not exactly match a catalog service id or name; not attached to the matrix.
- unmatched_provider_service: data/registry/providers.json — Provider service field does not exactly match a catalog service id or name; not attached to the matrix.
- unmatched_provider_service: data/registry/providers.json — Provider service field does not exactly match a catalog service id or name; not attached to the matrix.
- unmatched_provider_service: data/registry/providers.json — Provider service field does not exactly match a catalog service id or name; not attached to the matrix.
- unmatched_provider_service: data/registry/providers.json — Provider service field does not exactly match a catalog service id or name; not attached to the matrix.
- unmatched_provider_service: data/registry/providers.json — Provider service field does not exactly match a catalog service id or name; not attached to the matrix.
- unmatched_provider_service: data/registry/providers.json — Provider service field does not exactly match a catalog service id or name; not attached to the matrix.
- unmatched_provider_service: data/registry/providers.json — Provider service field does not exactly match a catalog service id or name; not attached to the matrix.
- unmatched_provider_service: data/registry/providers.json — Provider service field does not exactly match a catalog service id or name; not attached to the matrix.
- unmatched_provider_service: data/registry/providers.json — Provider service field does not exactly match a catalog service id or name; not attached to the matrix.
- unmatched_provider_service: data/registry/providers.json — Provider service field does not exactly match a catalog service id or name; not attached to the matrix.
- unmatched_provider_service: data/registry/providers.json — Provider service field does not exactly match a catalog service id or name; not attached to the matrix.
