# CA5 Office Operational Repair Roadmap — WP-0512 through WP-0521

Status: Active planning roadmap
Owner: Chief Architect #5
Created: 2026-07-10

## Objective

Turn the Office of the Steward from a mixed collection of reports, placeholders, and partial controls into a functioning local command center.

WP-0510 adds real execution-session controls.
WP-0511 audits the entire Office and fully repairs Settings.
WP-0512 through WP-0521 execute the remaining repair program in bounded implementation waves.

## Governing Standard

```text
Rendered is not functional.
Clickable is not functional.
HTTP 200 is not functional.
A control is complete only when it reaches a canonical handler, changes durable state or evidence, refreshes the Office, survives reload where persistence is expected, and is proven by deterministic tests.
```

## Package Sequence

### WP-0512 — Office Shell, Navigation, and Action Transport Reliability

Repair the shared Office foundation: tab routing, navigation state, browser action transport, loading states, errors, refresh behavior, stale payload detection, and action-result rendering.

This package creates the reliable shell every later control surface depends on.

### WP-0513 — Mission Control Operational Workspace

Convert Mission Control from a summary/dashboard into an actual control workspace that can launch governed refreshes, route to relevant controls, inspect active work, acknowledge attention items, and invoke existing operational handlers.

### WP-0514 — Work Package and Assignment Control Center

Make Work Packages and Projects operational: inspect packages, refresh queues, assign or reassign through existing governed mechanisms, open validation and completion evidence, route packages, and expose real status transitions.

### WP-0515 — Validation, Audit, and Verdict Control Center

Expose real validation and audit operations: inspect pending validations, run supported validation actions, view receipts and verdict evidence, acknowledge failures, request reruns where authorized, and track automatic validator state.

### WP-0516 — Mailbox, Notifications, and Attention Control Center

Repair mailboxes and notifications into usable communication controls: inspect messages, acknowledge locally, route or respond through existing communication mechanisms, clear resolved attention, and surface delivery failures truthfully.

### WP-0517 — AI Services and Local Runtime Control Surface

Replace AI service placeholders with real governed local service controls: refresh inventory, inspect availability, start/stop/restart approved local services, load/unload supported models, and show process results and failures.

### WP-0518 — Resident Interaction and Duty Control Surface

Make Alfred, Helen, resident conversations, briefings, and resident duties operational from the Office: invoke real duties, inspect history, route requests, manage approved conversation state, and expose failures.

### WP-0519 — Traffic Controller and Operations Decision Workspace

Turn operational-activity and Traffic Controller views into a coherent decision workspace for existing decision artifacts, routing recommendations, movement authorization evidence, escalations, and attention handling—without granting new authority.

### WP-0520 — Office Search, Command Palette, and Cross-Surface Actions

Make Search and the command palette operational across the Office: locate artifacts and controls, jump to targets, invoke only registered safe actions, preserve context, and prevent arbitrary command execution.

### WP-0521 — Office End-to-End Regression, Recovery, and Operational Acceptance

Create the full Office regression and recovery harness. Demonstrate key workflows across Settings, Execution, Mission Control, Work Packages, Validation, Notifications, AI Services, Residents, Operations, and Search. Produce an operational readiness verdict and remaining defect inventory.

## Dependency Flow

```text
WP-0510 Execution Controls
        |
WP-0511 Audit + Settings Repair
        |
WP-0512 Shared Shell and Action Transport
        |
        +--> WP-0513 Mission Control
        +--> WP-0514 Work Packages
        +--> WP-0515 Validation / Audit
        +--> WP-0516 Mailboxes / Notifications
        +--> WP-0517 AI Services
        +--> WP-0518 Residents
        +--> WP-0519 Traffic Controller / Operations
        +--> WP-0520 Search / Command Palette
                         |
                         v
              WP-0521 End-to-End Acceptance
```

## Implementation Rules

1. Reuse canonical Estate runtimes and handlers.
2. Do not create a parallel Office, command bus, queue, registry, or event system.
3. Do not implement decorative controls.
4. Do not label a placeholder as a completed control.
5. Every state-changing action must produce durable evidence.
6. Browser results must distinguish completed, blocked, and failed.
7. Tests must exercise browser/request/handler/state/render behavior, not registration alone.
8. Do not perform live provider calls in deterministic validation.
9. Do not grant new authority to the Office.
10. Do not redesign visual styling until operational behavior is proven.

## Expected Outcome

At the end of WP-0521, the Office should support real local operation of the Estate’s established capabilities without forcing the Steward back to PowerShell for routine work.

The remaining defects should be explicit, prioritized, and narrow rather than hidden behind placeholders or attractive but nonfunctional panels.
