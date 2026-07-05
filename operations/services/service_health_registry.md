# Estate Service Health Registry

Read-only aggregation. This registry does not replace monitoring systems or become the source of truth for service health.

Generated: 2026-07-05T19:16:42+00:00

## Summary
- Services: 10
- Healthy: 9
- Degraded: 0
- Unavailable: 0
- Unknown: 1
- Warnings: 6

## Health Entries

### Ledger Service (`SVC-000001`)
- Owner: Archives
- Health status: healthy
- Availability: available
- Operational status: Active
- Validation state: ready
- Dependency health: none_recorded
- Last-known update: 2026-07-05T19:16:42+00:00
- Health indicators: catalog status and validation metadata are healthy
- Authoritative sources: data/registry/services.json

### Registry Service (`SVC-000002`)
- Owner: Archives
- Health status: healthy
- Availability: available
- Operational status: Active
- Validation state: ready
- Dependency health: none_recorded
- Last-known update: 2026-07-05T19:16:42+00:00
- Health indicators: catalog status and validation metadata are healthy
- Authoritative sources: data/registry/services.json

### Capability Service (`SVC-000003`)
- Owner: Administration
- Health status: unknown
- Availability: available
- Operational status: Draft
- Validation state: metadata_only
- Dependency health: none_recorded
- Last-known update: 2026-07-05T19:16:42+00:00
- Health indicators: insufficient source metadata to determine health
- Authoritative sources: data/registry/services.json

### Helen HR Employee Onboarding (`derived:helen_hr_employee_onboarding`)
- Owner: Human Resources
- Health status: healthy
- Availability: available
- Operational status: implemented
- Validation state: source_links_checked
- Dependency health: none_recorded
- Last-known update: 2026-07-05T19:16:42+00:00
- Health indicators: catalog status and validation metadata are healthy
- Authoritative sources: docs/onboarding/Helen_HR_Operational_Onboarding.md, src/estate/cli/main.py, src/estate/core/hr_onboarding.py

### Mission Control Workspace (`derived:mission_control_workspace`)
- Owner: Operations Center
- Health status: healthy
- Availability: available
- Operational status: implemented
- Validation state: source_links_checked
- Dependency health: none_recorded
- Last-known update: 2026-07-05T19:16:42+00:00
- Health indicators: catalog status and validation metadata are healthy
- Authoritative sources: docs/operations/Mission_Control_Workspace_v1.md, docs/operations/Operations_Board_Runtime_Integration.md, src/estate/cli/main.py, src/estate/core/mission_control_workspace.py, src/estate/core/operations_board.py, src/estate/core/steward_command_center.py

### Operational Validation (`derived:operational_validation`)
- Owner: Validation
- Health status: healthy
- Availability: available
- Operational status: implemented
- Validation state: source_links_checked
- Dependency health: none_recorded
- Last-known update: 2026-07-05T19:16:42+00:00
- Health indicators: catalog status and validation metadata are healthy
- Authoritative sources: docs/operations/Operational_Validation_Reporting.md, operations/validation/validation_handoff_artifact_workflow.md, src/estate/cli/main.py, src/estate/core/local_operational_validation.py, src/estate/core/operational_validation.py, src/estate/core/work_package_validation.py

### Notification Router (`derived:notification_router`)
- Owner: Operations Center
- Health status: healthy
- Availability: available
- Operational status: implemented
- Validation state: source_links_checked
- Dependency health: none_recorded
- Last-known update: 2026-07-05T19:16:42+00:00
- Health indicators: catalog status and validation metadata are healthy
- Authoritative sources: src/estate/cli/main.py, src/estate/core/gotify_adapter.py, src/estate/core/notification_router.py

### Mailbox Operations (`derived:mailbox_operations`)
- Owner: Collaboration
- Health status: healthy
- Availability: available
- Operational status: implemented
- Validation state: source_links_checked
- Dependency health: none_recorded
- Last-known update: 2026-07-05T19:16:42+00:00
- Health indicators: catalog status and validation metadata are healthy
- Authoritative sources: docs/collaboration/Mailbox_Infrastructure_v1.md, src/estate/cli/main.py, src/estate/core/collaboration_messages.py, src/estate/core/collaboration_ops.py, src/estate/core/mailbox_index.py, src/estate/core/mailbox_sync_duty.py

### Worker Runtime Management (`derived:worker_runtime_management`)
- Owner: Operations Center
- Health status: healthy
- Availability: available
- Operational status: implemented
- Validation state: source_links_checked
- Dependency health: none_recorded
- Last-known update: 2026-07-05T19:16:42+00:00
- Health indicators: catalog status and validation metadata are healthy
- Authoritative sources: docs/collaboration/Local_Worker_Launch_Adapter_v1.md, docs/collaboration/Worker_Runtime_Contract_v1.md, src/estate/cli/main.py, src/estate/core/autonomous_work_queue_scheduler.py, src/estate/core/worker_runtime_heartbeat.py, src/estate/core/worker_runtime_monitor.py

### Alfred Orchestration (`derived:alfred_orchestration`)
- Owner: Operations Center
- Health status: healthy
- Availability: available
- Operational status: implemented
- Validation state: source_links_checked
- Dependency health: none_recorded
- Last-known update: 2026-07-05T19:16:42+00:00
- Health indicators: catalog status and validation metadata are healthy
- Authoritative sources: docs/alfred_v1_operator_completion.md, docs/alfred_v1_status.md, src/estate/cli/main.py, src/estate/core/alfred.py

## Warnings
- unmatched_provider_service: data/registry/providers.json — Provider service field does not exactly match a catalog service id or name; not attached to the matrix.
- unmatched_provider_service: data/registry/providers.json — Provider service field does not exactly match a catalog service id or name; not attached to the matrix.
- unmatched_provider_service: data/registry/providers.json — Provider service field does not exactly match a catalog service id or name; not attached to the matrix.
- unmatched_provider_service: data/registry/providers.json — Provider service field does not exactly match a catalog service id or name; not attached to the matrix.
- unmatched_provider_service: data/registry/providers.json — Provider service field does not exactly match a catalog service id or name; not attached to the matrix.
- unmatched_provider_service: data/registry/providers.json — Provider service field does not exactly match a catalog service id or name; not attached to the matrix.
