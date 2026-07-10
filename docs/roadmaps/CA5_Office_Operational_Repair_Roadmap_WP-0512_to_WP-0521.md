# CA5 Office Operational Repair Roadmap — WP-0512 through WP-0521

Status: Active implementation roadmap
Owner: Chief Architect #5
Created: 2026-07-10
Revised: 2026-07-10

## Objective

Turn the Office of the Steward from a mixed collection of reports, placeholders, and partial controls into a functioning local command center.

WP-0510 adds real execution-session controls.
WP-0511 audits the entire Office and fully repairs Settings.
WP-0512 through WP-0521 repair the rest of the Office as functioning operational surfaces.

## Non-Negotiable Control Contract

Every package in this roadmap is implementation work.

Every visible operational element introduced or retained by these packages must have a serviceable function tied to a real Estate capability.

```text
Rendered is not functional.
Clickable is not functional.
HTTP 200 is not functional.
Display-only is not a control surface.
A control must control something real.
```

A control is complete only when:

```text
browser input
-> structured Office action
-> canonical Estate handler
-> real runtime state or durable evidence change
-> refreshed Office payload
-> visible result
-> persistence after reload when applicable
-> deterministic test proof
```

Every package must include:

1. Named controls.
2. The canonical handler or runtime each control invokes.
3. Required input fields and confirmations.
4. The durable artifacts or state changed.
5. Truthful completed, blocked, and failed outcomes.
6. Immediate UI refresh after mutation.
7. Keyboard behavior where appropriate, including Enter-to-submit for primary chat inputs.
8. Browser-to-handler-to-state-to-render tests.
9. No placeholder completion claims.
10. No decorative buttons or permanently disabled mock controls counted as delivered work.

Any screen element that looks actionable must either work or be removed until it can work.

## Package Sequence

### WP-0512 — Office Shell, Navigation, Forms, and Action Transport Reliability

Repair the shared Office foundation that every real control uses.

Required controls and behaviors include:

- functioning tab navigation;
- direct links and browser back/forward;
- keyboard activation;
- Enter-to-submit for primary single-action forms;
- explicit loading/cancel/error states;
- retry for failed local requests;
- targeted refresh after mutations;
- visible artifact and diagnostic links;
- no dead buttons or silent failures.

### WP-0513 — Parking Lot, Roadmap, and Priority Control Surface

Turn Parking Lot and Roadmap into working planning controls.

Required controls include:

- create item;
- edit item;
- move item up/down;
- drag or reorder when practical;
- change priority;
- accept item;
- reject/archive item;
- promote item into an existing governed destination;
- assign owner;
- add notes;
- open source artifact;
- filter and search;
- undo the most recent local ordering/status action when safe.

Every action must update the canonical parking-lot/roadmap artifact and immediately refresh the page.

### WP-0514 — Personnel Directory, Org Chart, and Employee File Control Surface

Make the employee list and organization chart operational.

Required controls include:

- open employee details;
- open personnel file and related resident/worker artifacts;
- navigate manager/direct-report relationships;
- inspect role, office, mailbox, assignments, capabilities, and current status;
- open org-chart node details;
- filter/search personnel;
- route to employee mailbox or conversation where supported;
- invoke existing governed personnel actions only where canonical handlers exist.

No inert org-chart nodes or fake detail buttons.

### WP-0515 — Alfred Primary Interaction and Resident Chat Control Surface

Make Alfred’s page interaction-first.

Required controls include:

- move the Alfred chat composer to the top of the page;
- focus the composer on page entry where appropriate;
- Enter sends the message;
- Shift+Enter creates a new line;
- Send button invokes the same canonical action;
- stop/cancel generation when supported;
- clear or forget conversation through existing governed behavior;
- inspect conversation history;
- retry failed local response;
- request Alfred duties and briefings;
- show model/runtime/provider status truthfully;
- provide an integration path or launch link to Open WebUI when that becomes the primary resident interaction environment.

The Office must retain working text access even when Open WebUI becomes the preferred resident interface. Audio access is a later enhancement, not a reason to leave text chat broken.

### WP-0516 — Mission Control, Daily Board, and Operational Activity Controls

Convert high-level operational views into working command surfaces.

Required controls include:

- refresh live operational state;
- open active item details;
- acknowledge attention items;
- route to the controlling workspace;
- record existing operations decisions;
- request briefings;
- promote or defer actionable items through canonical mechanisms;
- open related evidence and artifacts;
- filter by state, owner, priority, and attention requirement.

### WP-0517 — Projects, Work Packages, and Assignment Control Center

Make Projects and Work Packages operational.

Required controls include:

- open package source and completion receipt;
- refresh queues;
- assign/reassign through existing governed mechanisms;
- change supported priority/status;
- promote a pending package into the next canonical workflow state;
- open validation evidence;
- route to related PR/commit/evidence;
- filter, search, and sort;
- expose blockers and required next action.

### WP-0518 — Validation, Audit, and Verdict Control Center

Expose real validation and audit operations.

Required controls include:

- inspect pending/running/completed validation;
- open validation evidence and completion receipts;
- request supported validation or revalidation;
- acknowledge failures;
- open audit/verdict artifacts;
- inspect automatic-validator status;
- retry only through existing governed mechanisms;
- filter by result, package, date, and attention state.

Validation evidence must never be mislabeled as institutional acceptance.

### WP-0519 — Mailbox, Notifications, and Attention Control Center

Make communication and attention surfaces serviceable.

Required controls include:

- open message details;
- acknowledge locally;
- mark read/unread where supported;
- route or reply through canonical communication mechanisms;
- open sender/recipient employee details;
- clear resolved local attention;
- inspect delivery failures;
- filter/search/sort;
- refresh mailbox state.

### WP-0520 — AI Services, Local Runtime, Search, and Command Palette Controls

Replace AI-service placeholders and make cross-Office navigation actionable.

Required controls include:

- refresh service and model inventory;
- start/stop/restart approved local services through canonical service controls;
- load/unload supported models where implemented;
- inspect logs and failures;
- search Office artifacts and people;
- open results directly;
- invoke only registered safe actions from the command palette;
- launch or route to Open WebUI and other approved local interfaces;
- never accept arbitrary shell commands.

### WP-0521 — Office End-to-End Regression, Recovery, and Operational Acceptance

Prove the entire Office works through real controls.

Required demonstrations include:

- Settings persistence;
- execution controls;
- parking-lot reorder and promotion;
- employee/org-chart detail navigation;
- Alfred Enter-to-send chat;
- Mission Control action routing;
- work-package operation;
- validation operation;
- mailbox/notification action;
- AI-service control;
- cross-surface search and navigation;
- reload/restart persistence;
- truthful recovery from failures.

Produce an operational readiness verdict and a narrow remaining-defect inventory.

## Dependency Flow

```text
WP-0510 Execution Controls
        |
WP-0511 Audit + Settings Repair
        |
WP-0512 Shared Shell / Forms / Action Transport
        |
        +--> WP-0513 Parking Lot / Roadmap
        +--> WP-0514 Personnel / Org Chart
        +--> WP-0515 Alfred / Resident Chat
        +--> WP-0516 Mission Control / Daily Board
        +--> WP-0517 Projects / Work Packages
        +--> WP-0518 Validation / Audit
        +--> WP-0519 Mailboxes / Notifications
        +--> WP-0520 AI Services / Search / Command Palette
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
10. Do not prioritize visual redesign over operational behavior.
11. Primary actions must be positioned where the user naturally begins the workflow.
12. Keyboard behavior must match normal application expectations.
13. If a screen cannot support its implied function, remove or relabel the element until it can.

## Expected Outcome

At the end of WP-0521, the Office should support real local operation of established Estate capabilities without forcing the Steward back to PowerShell for routine work.

The Parking Lot must be manageable, the org chart must open real personnel details, Alfred chat must be immediately usable, and every retained actionable element must perform a real serviceable function.
