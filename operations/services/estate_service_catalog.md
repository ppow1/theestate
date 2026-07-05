# Estate Service Catalog

Read-only aggregation. This report is not the source of truth and does not create a duplicate command registry.

Generated: 2026-07-05T14:59:02+00:00

## Summary
- Services: 10
- Registry services: 3
- Warnings: 0

## Services

### Ledger Service (SVC-000001)
- Owner: Archives
- Resident: Eleanor
- Operational status: Active
- Validation status: ready
- Capabilities: None recorded
- Interfaces: None recorded
- Command aliases: None recorded
- Source artifacts: data/registry/services.json

### Registry Service (SVC-000002)
- Owner: Archives
- Resident: Eleanor
- Operational status: Active
- Validation status: ready
- Capabilities: None recorded
- Interfaces: None recorded
- Command aliases: None recorded
- Source artifacts: data/registry/services.json

### Capability Service (SVC-000003)
- Owner: Administration
- Resident: Alfred
- Operational status: Draft
- Validation status: metadata_only
- Capabilities: None recorded
- Interfaces: None recorded
- Command aliases: None recorded
- Source artifacts: data/registry/services.json

### Helen HR Employee Onboarding (derived:helen_hr_employee_onboarding)
- Owner: Human Resources
- Resident: Helen
- Operational status: implemented
- Validation status: source_links_checked
- Capabilities: employee.onboard, personnel.registry, mailbox.provision
- Interfaces: CLI
- Command aliases: hr-onboard, helen-onboard
- Source artifacts: src/estate/core/hr_onboarding.py, src/estate/cli/main.py, docs/onboarding/Helen_HR_Operational_Onboarding.md

### Mission Control Workspace (derived:mission_control_workspace)
- Owner: Operations Center
- Resident: Alfred
- Operational status: implemented
- Validation status: source_links_checked
- Capabilities: mission.control, operations.workspace
- Interfaces: CLI, runtime artifacts
- Command aliases: operations-board, daily-board, steward-command-center
- Source artifacts: src/estate/core/mission_control_workspace.py, src/estate/core/operations_board.py, src/estate/core/steward_command_center.py, src/estate/cli/main.py, docs/operations/Mission_Control_Workspace_v1.md, docs/operations/Operations_Board_Runtime_Integration.md

### Operational Validation (derived:operational_validation)
- Owner: Validation
- Resident: Judy
- Operational status: implemented
- Validation status: source_links_checked
- Capabilities: validation.run, work_package.validate, readiness.report
- Interfaces: CLI, PowerShell scripts, runtime artifacts
- Command aliases: operational-validation, estate-validate-local, validate-work-package, validation-metrics-dashboard, validation-handoff-artifact-workflow, validation-observations
- Source artifacts: src/estate/core/operational_validation.py, src/estate/core/local_operational_validation.py, src/estate/core/work_package_validation.py, src/estate/cli/main.py, docs/operations/Operational_Validation_Reporting.md, operations/validation/validation_handoff_artifact_workflow.md

### Notification Router (derived:notification_router)
- Owner: Operations Center
- Resident: Alfred
- Operational status: implemented
- Validation status: source_links_checked
- Capabilities: notification.route, steward.recall
- Interfaces: CLI, Gotify adapter
- Command aliases: notification-router, gotify-send-test
- Source artifacts: src/estate/core/notification_router.py, src/estate/core/gotify_adapter.py, src/estate/cli/main.py

### Mailbox Operations (derived:mailbox_operations)
- Owner: Collaboration
- Resident: Alfred
- Operational status: implemented
- Validation status: source_links_checked
- Capabilities: mailbox.index, message.ack, message.reply, mailbox.sync
- Interfaces: CLI, collaboration mailboxes
- Command aliases: mailbox-index, mailbox-sync-duty, message-ack, message-reply, worker-inboxes
- Source artifacts: src/estate/core/mailbox_index.py, src/estate/core/mailbox_sync_duty.py, src/estate/core/collaboration_messages.py, src/estate/core/collaboration_ops.py, src/estate/cli/main.py, docs/collaboration/Mailbox_Infrastructure_v1.md

### Worker Runtime Management (derived:worker_runtime_management)
- Owner: Operations Center
- Resident: Alfred
- Operational status: implemented
- Validation status: source_links_checked
- Capabilities: worker.heartbeat, worker.monitor, worker.launch
- Interfaces: CLI, worker launch adapter
- Command aliases: worker-heartbeat, worker-runtime-summary, worker-runtime-monitor, autonomous-work-queue-scheduler
- Source artifacts: src/estate/core/worker_runtime_heartbeat.py, src/estate/core/worker_runtime_monitor.py, src/estate/core/autonomous_work_queue_scheduler.py, src/estate/cli/main.py, docs/collaboration/Worker_Runtime_Contract_v1.md, docs/collaboration/Local_Worker_Launch_Adapter_v1.md

### Alfred Orchestration (derived:alfred_orchestration)
- Owner: Operations Center
- Resident: Alfred
- Operational status: implemented
- Validation status: source_links_checked
- Capabilities: alfred.plan, alfred.execute, alfred.request
- Interfaces: CLI, runtime jobs
- Command aliases: alfred, alfred-request, alfred-requests, alfred-promote, alfred-plan, alfred-run, alfred-execute, alfred-status, ask-alfred
- Source artifacts: src/estate/core/alfred.py, src/estate/cli/main.py, docs/alfred_v1_operator_completion.md, docs/alfred_v1_status.md
