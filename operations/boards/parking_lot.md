# Parking Lot

Status: Active
Owner: Alfred / Chief of Staff
Classification: Estate Internal
Updated: 2026-06-30

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
| PL-0004 | Investigate Organizational Reputation and Service Record System for persistent Estate personnel; not gamification, but professional service records across achievement, authority, trust, experience, and reputation | Organizational Architecture | Strategic | Pat / Steward | 2026-06-30 | Captured | After core organizational framework stabilizes | ADR-0001 organizational model is stable and personnel/state architecture is ready for investigation |
| PL-0004 | Office of Chief Architect lifecycle, including occupancy, succession, retirement, mentorship, historical identity, and active assignment | Institutional Governance | High | Chief Architect #1 / Steward | 2026-06-30 | Captured | Office lifecycle review | Collaboration layer and operations board are stable enough to formalize office succession |
| PL-0005 | Institutional Trust Principle: distinguish proposed work, attempted work, and verified work before admitting claims as institutional fact | Engineering Philosophy | High | Chief Architect #1 / Steward | 2026-06-30 | Captured | Audit/history standards review | History queue and audit result workflow are stable |
| PL-0006 | Architect Once. Automate Many Times as a strategic engineering principle for compounding automation investment | Engineering Philosophy | High | Chief Architect #1 / Steward | 2026-06-30 | Captured | Engineering Matrix revision | Governance v1 is reopened for a scheduled philosophy update |
| PL-0007 | Rule of Three automation standard with Observation Trigger and Design Trigger | Engineering Standards | High | Chief Architect #1 / Steward | 2026-06-30 | Captured | Automation standards review | Repeated manual workflow patterns are being converted into formal automation criteria |
| PL-0008 | Chief Architect final memorandum standard for retiring architects to leave lessons learned, mistakes, surviving principles, and guidance | Institutional Architecture | Normal | Chief Architect #1 / Steward | 2026-06-30 | Captured | Chief Architect lifecycle implementation | Office lifecycle policy is active |
| PL-0009 | Eleanor and Marie knowledge architecture with spider-based indexing of A drive and GitHub into a searchable tag-based institutional knowledge base | Institutional Memory | Strategic | Steward | 2026-06-30 | Captured | Institutional memory phase | Collaboration, audit, history queue, and operations board are operational and Discovery is ready for knowledge indexing |
| PL-0010 | Institutional memory progression model from chat context to GitHub, Parking Lot, institutional documents, curated knowledge base, and institutional reasoning | Institutional Architecture | Normal | Chief Architect #1 / Steward | 2026-06-30 | Captured | Knowledge architecture planning | Eleanor and Marie knowledge architecture is promoted for design |

## Review Guidance

During planning, ask whether each idea is still valuable, whether the timing is right, and whether it should become active work, remain deferred, or be closed.

---

## Connector-Independent GPT-to-Estate Command Bridge

Priority: Future Investigation  
Status: Captured Idea  
Category: Infrastructure / Transport Adapter

### Description

Investigate a connector-independent command bridge allowing ChatGPT or other external AI interfaces to send structured commands to Estate infrastructure without relying on the GitHub connector approval/wait cycle.

The idea is inspired by the prior QMaster / iEnergy-style pattern where a GPT application sent commands to a user-controlled internet server, which parsed the command and wrote structured task/request files into GitHub or another Estate transport.

### Problem

The current GitHub connector introduces unpredictable wait time and permission latency. This slows down rapid operational work and makes simple repository updates less reliable than local CLI workflows.

### Potential Direction

Investigate a secure server-side command relay that can:

- Receive structured commands from approved AI interfaces.
- Validate and parse the request.
- Write task/request artifacts into the appropriate Estate queue.
- Preserve auditability.
- Avoid exposing secrets.
- Respect Steward authorization and clearance boundaries.

### Constraints

- Do not bypass governance.
- Do not expose repository credentials.
- Do not weaken repository privacy.
- Must preserve audit trail and approval boundaries.
- Should be evaluated after current Collaboration Layer work stabilizes.

### Related References

- QMaster repository
- iEnergy / iEnergy7-style GPT command bridge
- Collaboration Layer transport adapter model
- Local Worker Launch Adapter
- GitHub as first transport adapter


---

## Worker Execution Report Standard

Priority: Near-Term Investigation  
Status: Captured Idea  
Category: Collaboration Layer / Worker Operations

### Description

Define a standard final report artifact that every worker produces after completing assigned work.

The Estate already captures launch prompts, transcripts, raw output, result JSON, and archived launch requests. However, as workers begin performing real operational work, the Estate also needs a clean institutional work report that summarizes what was actually done.

### Problem

Current artifacts prove that a worker launched and produced output, but they do not yet provide a standardized completion report suitable for audit, review, promotion, and institutional history.

### Candidate Report Contents

A worker completion report should include:

- Work Package ID
- Worker ID
- Assignment summary
- Work performed
- Files created or modified
- Validation run
- Evidence produced
- Blockers or unresolved questions
- Required Steward review
- Recommended next action
- Capability lifecycle impact, if any

### Potential Locations

Possible report locations include:

- `collaboration/reports/`
- `collaboration/work_packages/completed/<work_package_id>/final_report.md`
- `runtime/worker_sessions/<request_id>/final_report.md`

### Constraints

- Do not block current worker launch testing.
- Do not duplicate raw transcripts.
- Reports should summarize institutional evidence, not replace audit artifacts.
- Reports should support later History Queue / Drain workflows.

### Success Criteria

The Estate can determine what a worker accomplished without rereading the entire prompt and transcript.

