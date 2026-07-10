# WP-0514 - Personnel Directory, Org Chart, and Employee File Control Surface

Status: Proposed
Priority: High
Owner: Chief Architect #5
Classification: Estate Internal

## Mission

Turn the Office personnel directory and organization chart into working control surfaces connected to real Estate personnel, mailbox, assignment, capability, and resident artifacts.

Every employee row, resident card, worker card, and org-chart node that appears actionable must open real details or invoke a supported canonical action. No inert detail buttons, decorative nodes, or placeholder drawers.

## Required Controls

At minimum implement:

- Open employee details
- Open personnel file
- Open resident or worker profile artifact
- Open mailbox
- Open active assignments
- Open capabilities and dependencies
- Open manager
- Open direct reports
- Navigate org-chart parent/child relationships
- Filter by office, role, status, capability, and worker/resident type
- Search by name, title, employee ID, mailbox ID, office, or capability
- Sort by name, role, office, status, or employee ID
- Copy employee ID and mailbox ID
- Open related work packages or operational evidence where indexed
- Route to the employee or resident conversation surface where supported
- Route to the mailbox control surface where supported
- Refresh personnel and org-chart data

Supported state-changing personnel actions may be exposed only when an existing canonical handler and authority path already exist. Do not invent personnel authority in the Office.

## Primary Interaction Rules

- Clicking an employee name, card, row, or org-chart node opens the same canonical employee-detail panel.
- Detail controls must appear near the top of the detail panel.
- Back/forward navigation must preserve the selected employee and filters.
- Direct links to employee details must resolve by stable employee ID.
- Keyboard Enter opens the selected employee or org-chart node.
- Escape closes a detail drawer or modal without losing the current list position.
- Loading, blocked, missing-file, and malformed-record states must be visible and truthful.

## Employee Detail Contract

The detail surface must show real available data, including:

```text
employee_id
mailbox_id
display_name
current_title
office or organizational unit
worker/resident classification
manager
manager_employee_id
direct_reports
status
active assignments
capabilities
capability dependencies
mailbox path and unread/attention summary when available
resident card/profile path when applicable
worker card/profile path when applicable
related work packages
related validation or operational evidence
source artifact references
last refreshed timestamp
warnings for missing or conflicting records
```

Do not fabricate fields that are not available. Missing data must be labeled unavailable and traced to the missing source artifact.

## Canonical Data and Handler Requirements

Inspect and reuse existing personnel, mailbox, resident, worker, assignment, capability, organization, and service-catalog modules and artifacts.

Likely sources include, but are not limited to:

```text
data/registry/personnel.json
data/registry/mailboxes.json
data/registry/offices.json
resident and worker profile/card artifacts
assignment queue artifacts
capability registry and dependency artifacts
collaboration/messages
collaboration/work_packages
```

Create a focused aggregator or action adapter only when the Office lacks a canonical callable seam. Do not create a second personnel registry or org-chart database.

Every Office action must define:

```text
action_id
label
required inputs
canonical handler
artifacts read
artifacts written
runtime state changed
authority gating
completed/blocked/failed result
```

Read-only actions must still return actual artifact references and truthful errors.

## Org Chart Requirements

The org chart must be serviceable, not merely visual.

Required behavior:

- every node with a known employee ID is clickable and keyboard accessible;
- clicking opens the canonical employee detail view;
- manager and direct-report links navigate to real records;
- office/group nodes can filter the personnel list;
- unknown or orphaned relationships are visibly flagged;
- duplicate employee IDs, missing manager IDs, cycles, and disconnected nodes are detected;
- the chart can focus on a selected employee or office;
- reset restores the full organization view;
- node labels remain readable and do not hide the employee ID entirely.

## Mailbox and Conversation Routing

When supported by existing Office surfaces:

- Open Mailbox must route to the mailbox page with the employee mailbox selected.
- Open Conversation must route to the resident/worker conversation page with the employee selected.
- Route actions must preserve employee ID and mailbox ID in the URL or Office state.
- Missing mailbox or conversation capability must produce a specific blocked result, not a dead button.

## Refresh Requirements

Refresh Personnel must:

- rebuild the Office personnel/org-chart payload from canonical artifacts;
- preserve the selected employee where possible;
- show added, changed, removed, duplicate, orphaned, and malformed record counts;
- never silently discard malformed source records;
- write audit evidence for detected structural conflicts when an existing audit path supports it.

## Scope

Implement the real personnel directory, employee detail surface, and org-chart interactions within the existing Office.

Likely integration points:

```text
src/estate/core/steward_command_center.py
src/estate/core/office_command_surface.py
src/estate/core/resident_cards.py
src/estate/core/assignment_queue.py
src/estate/core/mailbox_index.py
src/estate/core/capability_dependency_visualization.py
```

Create a focused module if needed, preferably:

```text
src/estate/core/office_personnel_directory.py
```

Create tests:

```text
tests/test_office_personnel_directory.py
tests/test_office_org_chart_controls.py
```

Create documentation:

```text
docs/integration/office_personnel_org_chart_control_surface.md
```

Create completion receipt:

```text
collaboration/work_packages/completions/WP-0514_codex_done.json
```

Register a WP-0514 validation recipe.

## Test Requirements

Tests must prove:

- all valid personnel records appear once;
- employee row/card click resolves to the correct stable employee ID;
- org-chart node click opens the same canonical detail surface;
- manager and direct-report navigation works;
- direct employee URL/deep link works;
- Enter opens the selected record;
- Escape closes detail view safely;
- filters and search work across required fields;
- sort behavior is deterministic;
- mailbox routing selects the correct mailbox;
- conversation routing selects the correct resident/worker when supported;
- missing mailbox or conversation capability is blocked truthfully;
- source artifact links are real and correct;
- duplicate employee IDs are detected;
- orphaned manager relationships are detected;
- org-chart cycles are detected;
- malformed personnel records do not crash the Office;
- refresh reflects changed canonical artifacts;
- selected employee and filters survive targeted refresh where possible;
- no second registry or parallel org-chart data store is introduced.

## Out of Scope

Do not:

- create or edit employee identities without an existing governed personnel handler;
- invent a new HR or personnel authority model;
- create a second personnel registry;
- create a second mailbox system;
- redesign all resident pages;
- implement Alfred chat behavior in this package;
- expose private secrets or unrestricted filesystem access;
- create decorative org-chart interactions that do not resolve to real records.

## Acceptance Criteria

1. Employee names, cards, rows, and org-chart nodes open real employee details.
2. Employee details link to real personnel, mailbox, assignment, capability, resident/worker, work-package, and evidence artifacts where available.
3. Manager and direct-report navigation works.
4. Search, filters, sort, and refresh are functional.
5. Mailbox and conversation routing work where supported and block truthfully where not supported.
6. Duplicate, orphaned, cyclic, missing, and malformed records are surfaced visibly.
7. Browser navigation and keyboard behavior are serviceable.
8. Focused tests and WP-0514 validation pass.
9. No parallel personnel registry, mailbox system, or org-chart database is created.

## Completion Receipt Assertions

The completion receipt must include and truthfully report:

```text
employee_detail_control_functional
org_chart_nodes_functional
manager_navigation_verified
direct_report_navigation_verified
mailbox_routing_verified
conversation_routing_verified
search_filter_sort_verified
refresh_verified
duplicate_detection_verified
orphan_detection_verified
cycle_detection_verified
new_personnel_registry_introduced
new_mailbox_system_introduced
```

Required final assertions:

```text
employee_detail_control_functional: true
org_chart_nodes_functional: true
manager_navigation_verified: true
direct_report_navigation_verified: true
search_filter_sort_verified: true
refresh_verified: true
new_personnel_registry_introduced: false
new_mailbox_system_introduced: false
```

## Codex Handoff

```text
Read collaboration/work_packages/pending/WP-0514_Personnel_Directory_Org_Chart_and_Employee_File_Control_Surface.md and do exactly what it says.
```
