# SERIES TASK WP-0061 — Mission Control Workspace

## Codex Command
Read `collaboration/work_packages/pending/WP-0061_SERIES_mission_control_workspace.md` and do exactly what it says.

## Mission
Create the Mission Control Workspace for the Estate Operations Center.

Mission Control becomes the Steward's operational overview for the Estate, providing one place to understand what is happening, what is blocked, what requires attention, and what should happen next.

## Scope
Create an Operations Center workspace that aggregates existing institutional information without becoming the source of truth.

Display information from existing artifacts where available:

- Active Work Package Pipeline
- Daily Board
- Operations Board
- Notification Center
- Steward Recall
- Validation and Estate Health
- Mailbox summary
- Resident status
- Worker heartbeat
- Morning Briefing outputs

## Workspace Sections
Include at least:

- Mission Status
- Operational Summary
- Critical Alerts
- Active Workers
- Current Missions
- Pending Steward Decisions
- Recent Completions
- Blocked Activities
- Recommended Next Actions

## Behavior Requirements
- Quiet background refresh.
- No full page redraw.
- Respect verbosity settings.
- Support drill-down into source artifacts.
- Missing data must degrade gracefully.
- Follow UI principles established in WP-0046.
- Remain compatible with the Estate Visual Manifest.

## Constraints
Do not duplicate authoritative data. Do not create new governance. Do not execute commands automatically. Do not implement AI decision making. Do not edit `estate_ledger/ledger.md` or `development/devlog.md`.

## Tests
Verify rendering with healthy Estate, degraded Estate, missing artifacts, blocked work, active recalls, and no active missions. Verify links back to authoritative artifacts.

## Completion Signal
Create `collaboration/work_packages/completions/WP-0061_codex_done.json` using the standard completion schema.

## Merge Class
Class A.
