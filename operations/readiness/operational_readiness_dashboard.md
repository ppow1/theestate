# Operational Readiness Dashboard

Generated: 2026-07-04T01:21:26Z
Overall readiness status: blocked
Recommended next operational action: Resolve blocking issues in the linked source artifacts before autonomous or steward-assisted operation.

Read-only aggregation. Authoritative state remains in the linked source artifacts; this dashboard does not execute work or change governance.

## Blocking Issues
- autonomous_operations_not_clear: Autonomous control loop decision is pause. (`runtime/autonomy/autonomous_operations_state.json`)

## Degraded Subsystems
- unavailable_subsystems: One or more source artifacts are unavailable. (`multiple`)

## Active Recalls
- None

## Worker Availability
- available: False

## Validation Health Summary
- available: False

## Drill-Down Links
- mission_control: `runtime/steward/mission_control_workspace.json` (unavailable; status: unavailable)
- validation_metrics: `runtime/validation/validation_metrics_dashboard.json` (unavailable; status: unavailable)
- worker_runtime_monitor: `runtime/workers/worker_runtime_monitor.json` (unavailable; status: unavailable)
- autonomous_operations_control_loop: `runtime/autonomy/autonomous_operations_state.json` (available; status: paused_or_unknown)
- notification_center: `runtime/notifications/notification_center_workspace.json` (unavailable; status: unavailable)
- steward_presence_state: `runtime/steward/steward_presence_state.json` (unavailable; status: unavailable)
- operations_board: `runtime/operations/operations_board.json` (unavailable; status: unavailable)

## Unavailable Artifacts
- unavailable_artifact: Artifact is unavailable: runtime/steward/mission_control_workspace.json (`runtime/steward/mission_control_workspace.json`)
- unavailable_artifact: Artifact is unavailable: runtime/validation/validation_metrics_dashboard.json (`runtime/validation/validation_metrics_dashboard.json`)
- unavailable_artifact: Artifact is unavailable: runtime/workers/worker_runtime_monitor.json (`runtime/workers/worker_runtime_monitor.json`)
- unavailable_artifact: Artifact is unavailable: runtime/notifications/notification_center_workspace.json (`runtime/notifications/notification_center_workspace.json`)
- unavailable_artifact: Artifact is unavailable: runtime/steward/steward_presence_state.json (`runtime/steward/steward_presence_state.json`)
- unavailable_artifact: Artifact is unavailable: runtime/operations/operations_board.json (`runtime/operations/operations_board.json`)
