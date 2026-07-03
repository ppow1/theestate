# Mission Control Workspace v1

Mission Control is the local-first overview layer for the Estate Operations Center. It assembles a read-only picture of operational readiness, work execution, communications, decisions, recalls, validation, and worker health from existing Estate artifacts.

## Boundaries

- Mission Control is an overview workspace, not a source of truth.
- It does not approve work, launch workers, send recalls, or mutate governance records.
- Missing optional artifacts are shown as warnings instead of hard failures.
- Significant actions must be performed through the source artifact or the relevant governed subsystem.

## Runtime Artifact

The workspace payload is written to:

- `runtime/steward/mission_control_workspace.json`

The Office of the Steward command center includes the workspace as a top-level Mission Control tab and navigation item.

## Lanes

Mission Control groups sources into three lanes:

1. **Operations** — command center, validation, roadmap.
2. **Work Execution** — work packages, worker runtime monitor, worker heartbeat.
3. **Communications** — mailbox sync, notification center, decisions, recalls.

## Degraded Mode

When a source artifact is not present, Mission Control records:

- source name
- expected path
- `missing` state
- warning message

This keeps the workspace usable while making data gaps visible.
