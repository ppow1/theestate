# Parking Lot

Status: Active
Owner: Alfred / Chief of Staff
Classification: Estate Internal
Updated: 2026-07-09

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
| PL-0015 | Work Package Duration Estimation: estimate likely execution time before assigning a work package to Codex or another coding worker, using historical work package outcomes, complexity, dependency count, implementation size, and worker performance history; improve estimates as actual completion data accumulates | Planning / Scheduling | Normal | Pat / Steward | 2026-07-05 | Promoted | WP-4214 — Staged Work Package Duration Estimation | External worker telemetry and enough historical completion data exist to produce useful estimates; close only after merged implementation, passing required tests, validation evidence, and a complete implementation receipt |
| PL-0016 | Parallel Worker Orchestration: coordinate multiple AI coding workers simultaneously rather than serially, including work allocation, dependency management, progress monitoring, merge coordination, and workload balancing across local and external workers | Operations / Worker Coordination | High | Pat / Steward | 2026-07-05 | Promoted | WP-4215 — Staged Parallel Worker Orchestration | Close only after merged staged implementation, passing required tests, validation evidence, and a complete implementation receipt; production integration requires a separate install-handoff |
| PL-0017 | Office Snapshot Export: add a one-click Office Snapshot button to the Office of the Steward that exports the current page/interface into a portable review package containing rendered HTML, CSS, JavaScript, visible panels, navigation structure, active workspace, DOM state, UI metadata, and future screenshot/runtime artifact support for drag-and-drop AI-assisted UI review | Developer Experience / UI Tooling | High | Pat / Steward | 2026-07-05 | Closed | Implemented through WP-0117 / merged PR #145 | Verified implementation, tests, validation report/runtime evidence, and completion receipt; screenshot support remains the documented future enhancement |
| PL-0018 | Live Office State Updates: the Office of the Steward must not behave as a static generated page that requires browser refresh to reflect Estate changes; implement local-only live update behavior so changes to authoritative Estate artifacts, including Parking Lot entries, boards, mailboxes, notifications, and runtime reports, are detected and reflected in the open UI automatically without manual page reload | Office UI / State Synchronization | High | Pat / Steward | 2026-07-05 | Promoted | WP-4216 — Staged Live Office State Updates; extends WP-0511 / PR #215 settings and WP-0085 / PR #92 activity stream | Original idea and Pat / Steward provenance retained; close only after production implementation is merged, required tests pass, validation evidence exists, and a complete implementation receipt confirms existing Office systems were reused |
| PL-0019 | Local Git Synchronization Friction: resolve the workflow problem where local generated/runtime changes and stash conflicts repeatedly block or complicate pulling GitHub-originated Estate updates, causing Parking Lot and other institutional changes made through ChatGPT/GitHub to require multiple manual recovery steps before they appear locally | Development Workflow / Repository Hygiene | High | Pat / Steward | 2026-07-05 | Promoted | WP-4217 — Staged Local Git Synchronization Assistant; reuses Operational Readiness, governed Publication, Post-Merge Audit, Execution Control, and repository validation | Original idea and Pat / Steward provenance retained; close only after isolated staging, separate production install, merged implementation, passing no-mutation tests, validation evidence, and a complete implementation receipt |
| PL-0020 | Command Chair macro controller integration: integrate the ordered Koolertron 9-key/2-knob controller, AI-KSEN 3-key/LCD/encoder controller, and AliExpress 3-key/1-knob pair into the chair-mounted command station; evaluate keys, encoders, RGB, LCD mode display, Stream Deck mode selection, Window Swapper/KVM mappings, and whether the devices can become an Estate Peripheral Service / local notifier surface | Command Chair / Estate Peripheral | High | Pat / Steward | 2026-07-07 | Captured | Command Chair peripheral evaluation | Prototype devices arrive and their configuration software, HID behavior, RGB/LCD control limits, and chair mounting options are inspected |
| PL-0021 | Command Chair Corne keyboard and mouse tray integration: phase in the ordered 4x6 Corne split keyboard with dual encoders; design and print chair-mounted keyboard holders; revise the mouse tray with a raised retaining lip or equivalent guard so the mouse does not slide off; evaluate keyboard, mouse, Stream Deck, and macro controller placement as one operator console | Command Chair / Human Interface | High | Pat / Steward | 2026-07-07 | Captured | Command Chair ergonomic integration | Corne keyboard arrives and practical chair tests identify stable dimensions for printed holders and tray revisions |
| PL-0022 | Command Chair Bluetooth coverage and headset rotation: integrate the ordered Hakimonoe Class 1 Bluetooth 5.4 adapter with external antenna; test placement on an existing USB extension mounted high in the office, then reassess after any garage relocation; evaluate Linux compatibility, onboard Bluetooth replacement, multi-device pairing, and rotating between multiple charged Bluetooth headsets | Command Chair / Communications | High | Pat / Steward | 2026-07-07 | Captured | Communications reliability evaluation | Bluetooth adapter arrives and testing confirms range, reconnect behavior, Linux support, headset microphone behavior, and multi-device stability |
| PL-0023 | Garage command center cable bill of materials: build a purchase and installation list for extending workstation/server access to the garage, including long HDMI runs, powered USB extension options, Ethernet, power injection needs, attic and garage route planning, wall plates, conduit, pull strings, labels, and spare capacity before buying or pulling cable | Infrastructure / Garage Command Center | High | Pat / Steward | 2026-07-07 | Captured | Garage infrastructure planning | Garage workstation location and cable route are measured closely enough to produce a reliable materials list and installation sequence |
| PL-0024 | Reusable portable command node architecture: develop a reusable field/control-node pattern using commodity macro pads with buttons, encoders, RGB, or LCD; ESP32-S3-class USB host hardware; Wi-Fi; optional battery operation; and 3D-printed enclosures so command nodes can be deployed without custom PCBs or full Raspberry Pi builds. Potential uses include Command Chair controls, printer panels, CueMastery demo controls, robotic landscaping operator pendants, trailer maintenance consoles, garage nodes, and context-recovery buttons that can emit standard prompts such as GitHub/Parking Lot reorientation instructions when a conversation or connector drifts | Estate Hardware / Distributed Control | High | Pat / Steward | 2026-07-07 | Captured | Portable node architecture exploration | Prototype one portable command node from off-the-shelf hardware and validate it across at least two roles before standardizing firmware, enclosure, and Estate service integration |
| PL-0025 | Role/task security classification should determine onboarding depth, so Ingrid can assign security levels appropriate to the role and work package; narrowly scoped workers receive bounded onboarding while higher-trust or broader-authority workers receive deeper governance, security, and institutional context | Institutional Onboarding / Security | High | Pat / Steward | 2026-07-07 | Captured | Ingrid security/onboarding implementation | Ingrid has enough security classification authority and onboarding manifest work is promoted from Parking Lot into active implementation |
| PL-0026 | Proposed onboarding addendum for lessons learned during initial Estate operations: add a section to the onboarding or new-hire handbook capturing conventions that were not obvious during ad hoc onboarding, including that user-pasted artifacts are review requests by default, screenshots and logs often represent engineering state transitions, audit is distinct from validation, validation should produce executable PowerShell command sequences using Estate formatting conventions, GitHub merge is not validation, the work package is the contract while handoff is only the standard Read path and Do exactly what it says instruction, and recurring operational conventions with institutional value should be captured in the Parking Lot at operations/boards/parking_lot.md. Include authoritative source paths: daily_board at operations/boards/daily_board.md, active_work at operations/boards/active_work.md, daily_board_integration at runtime/operations/daily_board_integration.json, parking_lot at operations/boards/parking_lot.md, work_package_pipeline at runtime/work_packages/assignment_queue.json, and alfred_operational_briefing at operations/alfred/operational_briefing.md | Institutional Onboarding | High | Pat / Steward | 2026-07-07 | Captured | Orientation handbook update | The next onboarding handbook revision is opened and these discovered operating conventions can be converted from proposal into canonical guidance |
| PL-0027 | Command Chair Architecture and Mobile Workstation Environment: redesign the Estate operator workstation around a tethered powered recliner command node, standing service station, separated KVM and daily-driver USB paths, voice-first command workflow, compact split keyboard, mouse shortcuts, control pod, Stream Deck strategy, modular chair accessories, and Bambu-printed mounting hardware | Hardware / Ergonomics / Infrastructure | High | Pat / Steward | 2026-07-08 | Captured | Command Chair architectural planning | Hardware priorities, budget, measurements, and implementation sequencing justify promotion into one or more focused work packages |
| PL-0028 | Canonical nomenclature and dictation normalization guard: maintain a small Estate glossary for dictation-sensitive terms such as CueMastery and IONOGE, including canonical spelling, pronunciation, lowercase machine identifiers, forbidden variants, and validation hooks so speech-recognition errors do not propagate through resident, work-package, or Character Architecture artifacts | Institutional Documentation / Validation | High | Pat / Steward | 2026-07-09 | Captured | Post-WP-0225 terminology repair | At least three dictation-sensitive Estate terms are identified, or a future work package repeats a forbidden variant after WP-0225 |
| PL-0029 | Orientation handbook update loop and onboarding coverage repair: create a mechanism to capture onboarding lessons discovered during active chats, update the orientation handbook or handbook addenda, and ensure new ChatGPT/Codex workers actually consume the relevant guidance instead of falsely claiming onboarding after reading only partial search excerpts; include discovered issues from this onboarding session such as standard Codex handoff format, Parking Lot procedure, merge-versus-validation distinction, work-package lane discipline, GitHub state verification before handoffs, canonical nomenclature, and the limitation that search snippets may not cover the full handbook | Institutional Onboarding / Knowledge Transfer | Strategic | Pat / Steward | 2026-07-09 | Captured | Orientation handbook and onboarding manifest revision | Repeated onboarding misses or handbook-glossing incidents show that critical operating knowledge is not reliably reaching new chats/workers, or the next onboarding handbook revision is opened |

## Review Guidance

During planning, ask whether each idea is still valuable, whether the timing is right, and whether it should become active work, remain deferred, or be closed.

## PL-0027 Detail: Command Chair Architecture and Mobile Workstation Environment

Status: Parking Lot Proposal
Priority: Medium (Architectural Project)
Type: Hardware / Ergonomics / Infrastructure
Scope: Complete redesign of the Estate operator workstation centered around a mobile Command Chair.

### Objective

Transform the existing office workstation from a traditional desk-centered environment into a mobile, ergonomic Command Chair that better supports the Estate development workflow.

The Command Chair is not intended to be a gaming chair or a high-end typing workstation.

It is intended to become the operator's primary human interface node while allowing continuous movement throughout the workshop during AI processing and long-running development tasks.

### Background

Current development consists largely of orchestrating AI systems rather than continuously typing.

The operator now works primarily through:

- Voice dictation
- AI conversations
- Mouse shortcuts
- Command orchestration
- Brief keyboard interactions

Typing has become a secondary activity.

If text exceeds approximately 100 words, voice dictation is almost always preferred.

The workstation should therefore optimize for command availability and ergonomics rather than typing performance.

### Design Philosophy

The computer is no longer the destination.

The room is the workspace.

The computer is simply one tool within that workspace.

The Command Chair should therefore support rapid interaction without requiring the operator to remain seated while waiting for AI models, Codex, renders, compiles, or long-running operations.

### Operational Modes

#### Mode 1 - Command Chair

Primary development mode.

Activities include:

- Estate development
- AI orchestration
- VS Code
- ChatGPT
- Codex
- ComfyUI
- debugging
- architectural review

Long-duration seated work.

#### Mode 2 - Shop Floor

Primary workshop mode.

Activities include:

- soldering
- hardware work
- electronics
- cable management
- organizing components
- 3D printing
- bench work

The operator periodically returns to the computer only long enough to:

- continue AI work
- approve responses
- press Enter
- press F12
- launch another task
- review output

The objective is minimizing commitment time.

### Standing Service Station

A secondary interaction point will exist behind the Command Chair.

Purpose:

- Provide immediate access to the workstation while standing.

Configuration:

- full-size keyboard
- duplicate mouse
- quick interaction only

Typical usage:

- Continue Codex
- Approve actions
- Press function keys
- Brief troubleshooting
- Return to workshop

This prevents unnecessary sitting during AI wait periods.

### Chair Philosophy

The chair becomes a mobile workstation node.

It is not wireless.

It is intentionally tethered.

### Chair Infrastructure

The chair already requires power because it is a powered recliner.

Additional infrastructure will be integrated into the chair.

Possible onboard components include:

- USB hubs
- phone charging dock
- wireless phone charger
- keyboard interfaces
- control pod
- Stream Deck
- cable management
- future peripherals

### Tether

The chair will have a managed tether.

Likely contents:

- AC power
- dedicated USB connection for KVM/HID
- dedicated USB connection for daily-driver peripherals

Possible future additions if required.

The tether should:

- disconnect easily
- support rolling the chair away
- support room cleaning
- avoid interfering with the robot vacuum

Possible routing:

- elevated wall hook
- removable cable support
- quick-disconnect bundle

### KVM Architecture

Current switching environment consists of:

- 16x16 HDMI Matrix
- dedicated 16-port USB keyboard switch

These function together as a custom KVM environment.

The KVM USB path should remain dedicated to:

- keyboard
- mouse
- HID devices

The daily-driver USB path should support:

- Stream Deck
- control pod
- USB hub
- removable flash drives
- future peripherals

The two USB roles should remain architecturally separate.

### Input Philosophy

Primary Input: Voice.

Primary Command Interface: Mouse.

Secondary Interface: Compact split keyboard.

Auxiliary Interface:

- Control pod
- Stream Deck
- Mouse

The mouse is already the primary command interface.

Existing mappings include:

- Copy
- Paste
- Enter
- Screenshot
- Dictation

Future work should optimize this command hierarchy rather than duplicate functionality elsewhere.

### Split Keyboard

Typing speed is not a design objective.

Primary goals:

- always available
- ergonomic
- compact
- mounted directly to chair
- minimal footprint

Likely direction:

- wired
- hot-swappable
- Vial/QMK compatible
- Corne-class layout
- no emphasis on RGB
- OLED optional
- rotary encoders optional

The keyboard exists for:

- shortcuts
- modifiers
- quick edits
- passwords
- terminal commands
- occasional typing

### Control Pod

Instead of integrating encoders into the keyboard, investigate a dedicated control pod.

Potential controls:

- large volume encoder
- mute
- push-to-talk
- AI controls
- programmable buttons
- optional OLED

Purpose:

- Provide tactile controls without increasing keyboard complexity.

### Stream Deck Strategy

Existing Stream Deck remains valuable.

Future evaluation:

- retain existing Stream Deck
- determine whether additional Stream Deck or Stream Deck+ is justified
- compare against smaller encoder-based control pods

### Chair Integration

Investigate replacing existing armrests with modular side panels.

Potential concepts include:

- rotating keyboard pods
- flip-away keyboard mounts
- hidden keyboard storage
- removable modules
- interchangeable accessories

The keyboard should disappear when not needed.

### Mechanical Architecture

The Command Chair should support modular accessories rather than permanent installations.

Potential modules:

- keyboard halves
- Stream Deck
- control pod
- phone dock
- future accessories

Modules should be replaceable independently.

### 3D Printing

The Estate already includes a Bambu Lab printer.

Rather than purchasing generic mounts, custom hardware should be designed and printed.

Potential printed components:

- armrest pods
- keyboard mounts
- rotating mechanisms
- cable guides
- USB hub mounts
- phone dock
- tether management
- modular attachment system

Design for rapid iteration.

### Design Principles

- Infrastructure first.
- Reliability over appearance.
- Modular hardware.
- Easy servicing.
- Easy cleaning.
- Minimize operator commitment.
- Optimize for AI orchestration rather than typing.
- Build around actual workflow rather than traditional desktop assumptions.

### Expected Outcome

The completed Command Chair should function as a mobile operational workstation that:

- supports long development sessions
- supports rapid standing interactions
- minimizes idle waiting
- integrates cleanly with the Estate workstation
- provides ergonomic access to all primary interfaces
- serves as the primary operator interface for the Estate while allowing continuous movement throughout the workshop.

This proposal is intended as an architectural starting point for future parking-lot planning and subsequent work package development.
