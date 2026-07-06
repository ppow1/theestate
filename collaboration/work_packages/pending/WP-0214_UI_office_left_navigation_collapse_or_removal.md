# UI TASK WP-0214 — Office Left Navigation Collapse or Removal

## Codex Command
Read collaboration/work_packages/pending/WP-0214_UI_office_left_navigation_collapse_or_removal.md and do exactly what it says.

## Mode
UI IMPLEMENTATION

## Mission
Remove the Office of the Steward left-hand navigation menu as a persistent viewport-consuming element, or replace it with a collapsed-by-default navigation drawer that can be temporarily expanded when needed.

The Office currently has redundant navigation: the left-hand menu duplicates the top tab navigation, while the top tab navigation actually drives the active viewport. The left menu consumes valuable horizontal space and prevents the Steward from seeing the whole Office comfortably on one screen.

The goal is to maximize the usable Office viewport and make the operational workspace easier to see and use.

## Steward Direction
The Steward has determined that the left-hand menu system is not currently useful:

- everything on the left is already represented by tabs across the top,
- the top tab navigation changes the main viewport,
- the left menu mainly takes space away from the viewport,
- the Office should fit more of the working page on one screen,
- if the side navigation remains, it should be collapsed by default and expandable only when needed.

Codex should choose the cleanest implementation that satisfies this objective while preserving access to all Office tabs.

## Required Outcome
After this package is installed, the Steward should see substantially more usable horizontal workspace in the Office.

The left navigation must no longer permanently consume viewport space.

Acceptable implementations:

1. Remove the left-hand navigation completely if the top tab/navigation system provides full access to all Office areas.
2. Replace the left-hand navigation with a collapsed-by-default drawer or rail that overlays or expands temporarily.
3. Provide a compact toggle button that expands/collapses the navigation without shrinking the default working viewport.

The default loaded state must prioritize the main Office viewport, not the side menu.

## Scope
Inspect and update the Office of the Steward web UI/layout implementation.

Likely relevant files include, but are not limited to:

- `src/estate/core/steward_command_center.py`
- `runtime/steward/command_center.html`
- tests covering the Steward Command Center / Office UI
- settings or workspace profile code that controls left navigation or panel visibility

Codex must inspect the actual implementation before editing.

## Requirements

### 1. Preserve Tab Access
All Office areas must remain reachable after the change, including:

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

If the left menu is removed, the top navigation must still provide access to these areas.

### 2. Default Layout Must Maximize Viewport
The default Office layout must not reserve a wide left navigation column.

The main workspace should expand to use the recovered horizontal space.

### 3. Optional Collapsible Drawer Behavior
If Codex preserves the side menu as a drawer, it must be:

- collapsed by default,
- accessible through a clear toggle button,
- non-destructive to the main viewport when closed,
- able to close after selecting a destination,
- keyboard/mouse usable,
- visibly distinct from the main content.

### 4. Avoid Duplicate Navigation Confusion
If both top tabs and side navigation remain, the UI must make clear which navigation controls the active workspace.

Do not leave two competing full-size navigational systems visible by default.

### 5. Preserve Settings and Profiles Safely
If workspace profile/settings artifacts currently mention the left navigation as expanded, update or interpret that setting safely.

Do not break existing settings files if they contain older layout values. Prefer backwards-compatible handling such as:

- `left_navigation: collapsed`
- `left_navigation: hidden`
- migration fallback from `expanded` to `collapsed`

### 6. Responsive Layout
The Office should remain usable on narrower screens.

The implementation should avoid horizontal overflow caused by duplicated navigation.

### 7. No Operational Semantics Change
This package is layout/UI only.

Do not change Estate authority, validation behavior, resident behavior, AI service behavior, work package lifecycle, or command execution semantics.

## Required Report
Create:

`operations/steward/WP-0214_left_navigation_layout_report.md`

The report must include:

- what was changed,
- whether the left navigation was removed or collapsed,
- why the chosen approach was used,
- files changed,
- how tab access is preserved,
- how the main viewport gains space,
- compatibility handling for existing settings/profile state,
- manual verification steps,
- known limitations.

## Required Tests
Add or update tests proving:

1. the Office payload still exposes all expected tabs,
2. the default layout no longer uses an expanded left navigation state,
3. the main workspace is configured to use the freed viewport space,
4. if a drawer/toggle is implemented, the collapsed state is the default,
5. older workspace profile/settings values do not break rendering,
6. command center JSON generation still succeeds.

Run the most relevant existing Steward Command Center tests.

## Required Validation Commands
Run or document equivalent validation:

```bash
PYTHONPATH=src python -m pytest tests/test_steward_command_center.py
PYTHONPATH=src python -m estate.cli.main steward-command-center --json
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0214 --json
PYTHONPATH=src python -m estate.cli.main validation-production-readiness --json
```

If any command is unavailable or a test path differs, run the closest equivalent and document the substitution.

## Manual Verification Requirement
The report must include manual verification steps for the Steward:

1. Start the Office locally.
2. Open the Office in the browser.
3. Confirm the left menu is absent or collapsed by default.
4. Confirm the top tabs still change the active viewport.
5. Confirm all Office areas remain reachable.
6. Confirm the main workspace has more horizontal room than before.
7. If a drawer/toggle exists, confirm it opens, closes, and does not remain permanently in the way.

## Completion Artifact
Create:

`collaboration/work_packages/completions/WP-0214_codex_done.json`

It must include:

- `work_package_id`: `WP-0214`,
- `codex_status`,
- `completed_at`,
- `branch`,
- `pull_request_url` or reason not applicable,
- summary,
- chosen implementation: `removed`, `collapsed_by_default`, or `other_with_reason`,
- files changed,
- tests run,
- validation commands run,
- manual verification steps,
- known limitations,
- `ready_for_ca_review`: true,
- `merge_authority`: `ca_verified_auto_merge_allowed`.

## Acceptance Criteria
WP-0214 is complete when:

1. The left-hand navigation no longer permanently consumes viewport space.
2. The Office opens with the main workspace prioritized.
3. Top navigation still allows the Steward to reach all Office tabs.
4. If the side menu remains, it is collapsed by default and expandable only when needed.
5. The Office JSON/smoke command succeeds.
6. Tests validate the new default layout.
7. The Steward can visually confirm that more of the Office fits on one screen.
8. Report and completion receipt exist.

## Merge Class
Class B if active Office runtime/UI files are modified.

Class A only if the implementation proves this is purely configuration/documentation with no active runtime modification.
