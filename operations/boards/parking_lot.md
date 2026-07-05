# Parking Lot

Status: Active
Owner: Alfred / Chief of Staff
Classification: Estate Internal
Updated: 2026-07-05

## Purpose

The Parking Lot captures valuable ideas without interrupting current execution.

It preserves institutional thinking while protecting implementation velocity.

The Parking Lot is not a backlog. Ideas remain here until intentionally selected for active work.

## Fields

Each item should include:

- ID
- Idea
- Category
- Priority
- Originator
- Date captured
- Status
- Optional target milestone
- Promotion condition

## Status Values

- Captured
- Clarify Later
- Reconsider
- Promoted
- Closed

## Priority Values

- Low
- Normal
- High
- Strategic

## Parking Lot Items

| ID | Idea | Category | Priority | Originator | Date Captured | Status | Target Milestone | Promotion Condition |
|---|---|---|---|---|---|---|---|---|
| PL-0001 | Automate Operations Board aggregation after manual pattern stabilizes | Automation | Strategic | Worker #1 | 2026-06-30 | Captured | Post-v1 validation | Same update pattern repeats three times |
| PL-0002 | Add audit checks for Operations Board required files | Audit | Normal | Worker #1 | 2026-06-30 | Captured | After board stabilizes | Board file shape remains unchanged |
| PL-0003 | Add Alfred daily briefing output sourced from Operations Board | Alfred | Strategic | Worker #1 | 2026-06-30 | Captured | Alfred coordination milestone | Daily board proves useful manually |
| PL-0004 | Investigate Organizational Reputation and Service Record System for persistent Estate personnel; not gamification, but professional service records across achievement, authority, trust, experience, and reputation | Organizational Architecture | Strategic | Pat / Steward | 2026-06-30 | Captured | ADR-0001 organizational model is stable and personnel/state architecture is ready for investigation |
| PL-0004 | Office of Chief Architect lifecycle, including occupancy, succession, retirement, mentorship, historical identity, and active assignment | Institutional Governance | High | Chief Architect #1 / Steward | 2026-06-30 | Captured | Office lifecycle review | Collaboration layer and operations board are stable enough to formalize office succession |
| PL-0005 | Institutional Trust Principle: distinguish proposed work, attempted work, and verified work before admitting claims as institutional fact | Engineering Philosophy | High | Chief Architect #1 / Steward | 2026-06-30 | Captured | Audit/history standards review | History queue and audit result workflow are stable |
| PL-0006 | Architect Once. Automate Many Times as a strategic engineering principle for compounding automation investment | Engineering Philosophy | High | Chief Architect #1 / Steward | 2026-06-30 | Captured | Engineering Matrix revision | Governance v1 is reopened for a scheduled philosophy update |
| PL-0007 | Rule of Three automation standard with Observation Trigger and Design Trigger | Engineering Standards | High | Chief Architect #1 / Steward | 2026-06-30 | Captured | Automation standards review | Repeated manual workflow patterns are being converted into formal automation criteria |
| PL-0008 | Chief Architect final memorandum standard for retiring architects to leave lessons learned, mistakes, surviving principles, and guidance | Institutional Architecture | Normal | Chief Architect #1 / Steward | 2026-06-30 | Captured | Chief Architect lifecycle implementation | Office lifecycle policy is active |
| PL-0009 | Eleanor and Marie knowledge architecture with spider-based indexing of A drive and GitHub into a searchable tag-based institutional knowledge base | Institutional Memory | Strategic | Steward | 2026-06-30 | Captured | Institutional memory phase | Collaboration, audit, history queue, and operations board are operational and Discovery is ready for knowledge indexing |
| PL-0010 | Institutional memory progression model from chat context to GitHub, Parking Lot, institutional documents, curated knowledge base, and institutional reasoning | Institutional Architecture | Normal | Chief Architect #1 / Steward | 2026-06-30 | Captured | Knowledge architecture planning | Eleanor and Marie knowledge architecture is promoted for design |
| PL-0011 | Mailbox Synchronization Duty Standard: define when Estate personnel must check institutional mailboxes, with different synchronization modes for local workers, ChatGPT workers, Alfred, Audit, Chief Architects, and future autonomous workers; avoid fixed polling intervals until HR/security/worker runtime authority matures | Personnel Operations | High | Steward / Chief Architect #3 | 2026-07-01 | Captured | HR/personnel governance phase | Helen/HR and mailbox authority are mature enough to define duty, cadence, and implementation modes |
| PL-0012 | Treat onboarding as an institutional capability driven by a canonical onboarding manifest that serves as the configuration for repeatable onboarding rather than documentation; include ordered entries with purpose, required status, canonical path, and lifecycle state while keeping meaning in the referenced documents | Institutional Onboarding | High | Chief Architect #4 / Steward | 2026-07-02 | Captured | HR onboarding implementation | Alfred and Helen onboarding workflow is being formalized |

| PL-0013 | Transition work package range allocation from current Chief Architect occupants to the persistent Office of Chief Architect once office/occupant separation is mature; current operations may assign ranges directly to active occupants until the institution is ready for office-owned allocation | Institutional Architecture | Normal | Chief Architect #4 / Steward | 2026-07-03 | Captured | Office/occupant governance evolution | The Office model is mature enough that range ownership should survive occupant succession without administrative reassignment |
| PL-0014 | External Worker Telemetry Adapter: create a monitoring and feedback mechanism for external AI workers, initially Codex, so the Estate can detect assignment acceptance, start, progress, completion, failure, stalls, and return execution state to Alfred and Helen; investigate official APIs first and consider browser automation or UI observation only if no cleaner integration is available | Worker Runtime / External Integration | High | Pat / Steward | 2026-07-05 | Captured | External worker supervision phase | Required before Alfred and Helen can reliably supervise Codex or other external coding workers as institutional workers |
| PL-0015 | Work Package Duration Estimation: estimate likely execution time before assigning a work package to Codex or another coding worker, using historical work package outcomes, complexity, dependency count, implementation size, and worker performance history; improve estimates as actual completion data accumulates | Planning / Scheduling | Normal | Pat / Steward | 2026-07-05 | Captured | Worker planning and scheduling phase | External worker telemetry and enough historical completion data exist to produce useful estimates |
| PL-0016 | Parallel Worker Orchestration: coordinate multiple AI coding workers simultaneously rather than serially, including work allocation, dependency management, progress monitoring, merge coordination, and workload balancing across local and external workers | Operations / Worker Coordination | High | Pat / Steward | 2026-07-05 | Captured | Multi-worker engineering phase | Worker runtime and telemetry are mature enough to manage concurrent coding assignments safely |
| PL-0017 | Office Snapshot Export: add a one-click Office Snapshot button to the Office of the Steward that exports the current page/interface into a portable review package containing rendered HTML, CSS, JavaScript, visible panels, navigation structure, active workspace, DOM state, UI metadata, and future screenshot/runtime artifact support for drag-and-drop AI-assisted UI review | Developer Experience / UI Tooling | High | Pat / Steward | 2026-07-05 | Captured | Office UI development phase | Office UI work continues to require high-bandwidth architectural review and shared visual/state context across AI collaborators |
| PL-0018 | Live Office State Updates: the Office of the Steward must not behave as a static generated page that requires browser refresh to reflect Estate changes; implement local-only live update behavior so changes to authoritative Estate artifacts, including Parking Lot entries, boards, mailboxes, notifications, and runtime reports, are detected and reflected in the open UI automatically without manual page reload | Office UI / State Synchronization | High | Pat / Steward | 2026-07-05 | Captured | Office UI development phase | The Office shell is promoted from static display board to active state-aware interface with file watching, polling, SSE, WebSocket, or equivalent local update mechanism |

## Review Guidance

During planning, ask whether each idea is still valuable, whether the timing is right, and whether it should become active work, remain deferred, or be closed.