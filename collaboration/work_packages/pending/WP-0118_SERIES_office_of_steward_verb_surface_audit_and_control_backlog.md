# SERIES TASK WP-0118 — Office of the Steward Verb Surface Audit and Control Backlog

## Codex Command
Read collaboration/work_packages/pending/WP-0118_SERIES_office_of_steward_verb_surface_audit_and_control_backlog.md and do exactly what it says.

## Mode
SERIES

## Mission
Audit the Office of the Steward UI and convert it from a mostly noun/status/view surface into an explicit action/control surface backlog, organized by tab/workspace, with safe local-first verbs, authority boundaries, and follow-up implementation work packages.

The goal is to make the Office of the Steward feel like a control room, not just a report board.

## Background
The Office of the Steward currently exposes many useful nouns:

- Home
- Mission Control
- Alfred
- Helen
- Resident Conversations
- AI Services / Models
- Daily Board
- Projects
- Roadmap
- Parking Lot
- Work Packages
- Mailboxes
- Recalls
- Notifications
- Validation
- Search
- Settings
- Help
- About

Most of these surfaces primarily report state. That was appropriate for the early Office shell because the first need was visibility: show resident cards, show boards, show mailboxes, show notifications, show validation status, show search, and show artifacts.

The next maturity step is controlled action. The Steward needs the UI to expose verbs: refresh, open, inspect, acknowledge, validate, export, promote, queue, assign, draft, archive, run safe local command, start conversation, submit batch, and request review where authority allows.

This package does not implement every verb. It creates the durable action/control model and decomposes the Office into implementation work packages by workspace/tab.

## Scope
Inspect the current Office of the Steward implementation and produce an actionable verb-surface backlog.

In scope:

1. Enumerate every current Office tab/workspace from the implemented UI.
2. For each tab, identify what it currently displays.
3. For each tab, define the verbs/actions it should eventually support.
4. Classify each verb by authority and safety.
5. Distinguish local read-only actions from local mutating actions.
6. Distinguish UI actions from institutional actions.
7. Identify which actions can be implemented immediately and which require prerequisite systems.
8. Produce a follow-up work package breakdown grouped by coherent tab/workspace families.
9. Create a reusable action-surface template future Office UI work packages can use.
10. Add a validation recipe for WP-0118.
11. Create a WP-0118 completion receipt.

## Out of Scope
Do not implement all Office actions in this package.

Do not grant new authority to Alfred, Helen, residents, Codex, or the UI.

Do not let UI buttons bypass existing validation, Steward approval, merge authority, or governance.

Do not implement destructive actions without explicit confirmation and authority design.

Do not convert every tab into a command surface prematurely.

Do not add cloud calls, external APIs, or telemetry.

Do not change production-readiness semantics.

Do not redesign the visual layout unless a minor affordance is needed for documenting the action model.

Do not edit estate_ledger/ledger.md or development/devlog.md unless current repository standards require it.

## Required Behavior
Create a durable Office action/control planning document.

Recommended path:

`docs/operations/Office_of_the_Steward_Verb_Surface_Control_Backlog_v1.md`

The document must include at least these sections.

### 1. Current Noun Surface Inventory
List every current Office tab/workspace and the primary nouns/statuses it displays.

Use the implemented UI source as the source of truth, not memory.

### 2. Verb Surface Philosophy
Define the design philosophy:

- Noun surfaces show state.
- Verb surfaces let the Steward act on state.
- Every visible state should eventually answer: what can I do with this?
- UI actions must remain bounded by institutional authority.
- A control is not the same as permission.
- A button may draft, request, validate, or queue, but must not silently authorize where authority is required.

### 3. Action Classification
Define action classes such as:

- read / inspect
- refresh / regenerate local artifact
- export / snapshot
- open source artifact
- copy command
- create draft
- queue request
- acknowledge / mark reviewed
- validate
- start local service
- stop local service
- run safe local command
- promote parking-lot item to proposed work package
- submit sequential batch manifest
- request Chief Architect review
- destructive / authority-gated action

Classify each action as one of:

- safe read-only
- safe local generated-artifact update
- Steward-confirmed local mutation
- authority-gated institutional action
- prohibited until future governance/tooling exists

### 4. Per-Tab Verb Matrix
For each current Office tab/workspace, create a table with:

- tab/workspace name
- current noun/status surface
- proposed verbs/actions
- authority class
- implementation complexity
- prerequisite systems
- recommended work package
- notes/risks

At minimum cover:

- Home
- Mission Control
- Alfred
- Helen
- Resident Conversations
- AI Services / Models
- Daily Board
- Projects
- Roadmap
- Parking Lot
- Work Packages
- Mailboxes
- Recalls
- Notifications
- Validation
- Search
- Settings
- Help
- About

### 5. Immediate Implementation Breakdown
Produce a concrete follow-up work package plan.

The plan should group actions into implementation slices that avoid oversized PRs and minimize merge conflicts. Suggested groupings may include:

- Office action framework / command dispatch foundation
- Work Packages tab controls
- Validation tab controls
- Mailboxes and notifications controls
- Daily Board and Parking Lot controls
- Resident conversation controls
- AI services/model controls
- Mission Control and Projects controls
- Settings/help/about utility controls

The output should include recommended work package titles and draft missions for each follow-up package.

### 6. Control Safety Rules
Define standard safety rules for Office controls:

- Every mutating control must show what it will change before it changes it.
- Every authority-gated action must route through the correct authority path.
- Every generated artifact update must identify output paths.
- Every command-running action must be local-first and visible to the Steward.
- Destructive actions require explicit confirmation.
- Buttons must not silently execute pending work packages.
- Resident controls must respect the Resident Action Authority Boundary.
- Validation controls must not declare success by UI state alone.

### 7. Action Template
Create a reusable action template for future Office action work packages.

Recommended path:

`docs/templates/Office_Action_Surface_Work_Package_Template.md`

The template should require:

- target tab/workspace
- current noun/status surface
- new verbs/actions
- authority class
- confirmation behavior
- local command/API surface
- source artifacts read
- artifacts written
- UI placement
- failure handling
- tests
- validation recipe
- completion receipt

## Required Outputs
Create or update:

- `docs/operations/Office_of_the_Steward_Verb_Surface_Control_Backlog_v1.md`
- `docs/templates/Office_Action_Surface_Work_Package_Template.md`
- validation recipe for WP-0118
- validation report for WP-0118 under `operations/validation/reports/`
- runtime validation JSON for WP-0118 under `runtime/validation/work_packages/`
- updated production-readiness artifacts if required by the validation framework
- `collaboration/work_packages/completions/WP-0118_codex_done.json`

Do not implement broad UI controls beyond what is necessary to document or validate the action model.

## Required Tests
Add or update tests if code or validation recipe logic is changed.

At minimum, ensure the WP-0118 validation recipe verifies:

- the verb surface backlog document exists
- the action template exists
- the backlog document inventories current Office tabs/workspaces
- the backlog document distinguishes noun/status surfaces from verbs/actions
- the backlog document includes an action classification model
- the backlog document includes a per-tab verb matrix
- the backlog document includes follow-up work package recommendations
- the action template requires authority classification and validation behavior
- WP-0118 completion receipt is complete

Run relevant tests:

```bash
PYTHONPATH=src pytest tests/test_work_package_validation.py tests/test_production_readiness_validation.py -q
```

## Required Validation Commands
Run or document equivalent:

```bash
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0118 --json
PYTHONPATH=src python -m estate.cli.main validation-production-readiness --json
```

## Completion Artifact
Create:

`collaboration/work_packages/completions/WP-0118_codex_done.json`

It must include:

- `work_package_id = WP-0118`
- `codex_status = done`
- `completed_at`
- `branch`
- `pull_request_url` or `pull_request_url_not_applicable_reason`
- `summary`
- Office tabs/workspaces inventoried
- follow-up work packages recommended
- standard document path
- template path
- files changed
- tests run
- validation commands run
- known limitations
- `ready_for_ca_review = true`
- `merge_authority = ca_verified_auto_merge_allowed`

## Acceptance Criteria
WP-0118 is complete when:

1. The current Office of the Steward tabs/workspaces have been inventoried from source.
2. The noun/status problem has been documented clearly.
3. A safe action/verb classification model exists.
4. Every current tab/workspace has proposed verbs and authority classifications.
5. A concrete follow-up work package breakdown exists.
6. A reusable Office action-surface work package template exists.
7. WP-0118 validates and has a complete completion receipt.

## Merge Class
Class A if this package creates planning, standards, templates, validation recipes, and reports only.

Escalate to Class B if it implements mutating Office controls, command execution, authority changes, or broad runtime behavior changes.
