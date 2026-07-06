# REPAIR TASK WP-0141 - Repair Steward Command Center Browser Runtime Failure

## Codex Command

Read collaboration/work_packages/pending/WP-0141_REPAIR_steward_command_center_browser_runtime_failure.md and do exactly what it says.

## Mode

REPAIR

## Problem

After PR #148 / WP-0140 was merged, the Steward regenerated the Command Center locally and reports that nothing works and the page remains effectively broken.

Observed generated page:

```text
Office of the Steward — Local Command Center
Generated: 2026-07-06T15:57:18+00:00
Office Snapshot
Office Navigation
Home
Mission Control
Alfred
Helen
Resident Conversations
AI Services / Models
...
Home
Mission Control
Alfred
Helen
Resident Conversations
AI Services / Models
...
Mission Control Workspace
Mission Control
State: partial · Ready sources: 10 / 12
...
```

The Steward says:

```text
Nope nothing works it's absolutely still the same
```

This means WP-0140 did not repair the real browser/runtime failure. It may have made scripts syntactically valid, but the actual generated page still does not function for the Steward.

## Critical Correction

Do not treat `node --check` as sufficient validation.

`node --check` only proves JavaScript parses. It does not prove:

- browser event listeners are attached;
- tab buttons switch workspaces;
- CSS is loaded/applied;
- hidden workspaces are actually hidden;
- inline scripts run when opened as a local file;
- DOMContentLoaded timing works;
- query selectors match generated HTML;
- buttons have correct types and handlers;
- Alfred submit works;
- AI Services / Models can be opened from the browser.

The repair must validate real browser-facing behavior at the generated HTML level, not only script syntax.

## Primary Failure To Reproduce

Generate `runtime/steward/command_center.html`, open or inspect it as a browser surface, and verify whether:

1. the page is styled;
2. workspace tabs/buttons are clickable;
3. clicking Alfred shows Alfred and hides Mission Control;
4. clicking AI Services / Models shows AI Services / Models and hides Mission Control;
5. Office Navigation buttons work;
6. the duplicate top tab bar is intentional and functional, or removed if confusing/broken;
7. only one workspace is visible at a time;
8. the Alfred submit form works or shows a safe failure;
9. the browser console has errors.

If browser automation is unavailable, use static generated-HTML tests plus a minimal DOM simulation sufficient to prove event handlers attach to the generated elements.

## Required Repair Outcomes

### 1. Make Navigation Work Without Fragile Script Assumptions

The Steward Command Center must work when opened locally from:

```text
A:\theestate\runtime\steward\command_center.html
```

Navigation must not depend on brittle script timing or external assets.

Preferred implementation:

- Keep the static HTML local-first architecture.
- Add robust inline JavaScript that attaches handlers after DOM is available and also works if the script is loaded after the DOM.
- Use event delegation on a stable root element rather than per-button fragile binding.
- Ensure both Office Navigation and workspace tab buttons use the same switching function.
- Update `hidden`, `.active`, `aria-selected`, and `aria-current` consistently.
- Prevent default form/button behavior where needed.

If JavaScript is unavailable, the page should still degrade visibly and explain that tabs require JavaScript rather than appearing silently broken.

### 2. Ensure CSS Is Present And Applied

Verify generated HTML includes required inline CSS.

If the current page looks like plain unstyled document text, diagnose why:

- missing `<style>` block;
- malformed `<head>`;
- stylesheet placed outside `<head>`;
- broken HTML before style/script blocks;
- browser treating file as text/html but style invalid;
- generated CSS selectors not matching DOM.

Repair the generator so the page has a usable styled shell.

### 3. Eliminate Confusing Duplicate Navigation If Needed

The output currently shows Office Navigation and then a second list of the same workspaces immediately underneath.

If the second list is the tab bar and is intentional, it must be styled and functional.

If it is confusing in the plain fallback state, make the layout clear:

- sidebar navigation;
- top tabs;
- active workspace content.

Do not leave the Steward seeing two plain repeated lists and no usable controls.

### 4. Preserve Recent Functionality

Do not regress:

- WP-0138 AI Services / Models workspace;
- model inventory display;
- known installed TextGen models;
- WP-0139 Alfred diagnostics and timeout/safe failure behavior;
- Office Snapshot behavior unless it is the cause of the runtime failure.

### 5. Add A Built-In UI Self-Test Panel Or Diagnostic Banner

Add a local-only diagnostic indicator that makes browser runtime state visible, for example:

```text
UI runtime: scripts loaded / navigation bound / active tab: mission-control
```

If scripts fail, the static fallback should visibly say:

```text
UI runtime: script not initialized; navigation may not work
```

This is to prevent future silent failures where the generated page looks present but is unusable.

### 6. Add Tests That Match The Steward's Failure

Add tests that fail against the observed broken state.

At minimum:

1. Generated HTML contains a valid `<html>`, `<head>`, `<style>`, `<body>`, and executable script block.
2. Generated HTML contains a visible UI runtime diagnostic element.
3. Generated HTML includes navigation buttons with `data-tab` values matching workspace sections.
4. A static test verifies every `data-tab` has a corresponding `workspace-<tab>` section.
5. A DOM-level or script-level test verifies clicking `data-tab="alfred"` hides Mission Control and shows Alfred.
6. A DOM-level or script-level test verifies clicking `data-tab="ai-services-models"` hides Mission Control and shows AI Services / Models.
7. The active tab configured by the workspace profile is the only visible workspace on first load.
8. Alfred form submit handler does not break global navigation binding.
9. AI Services / Models installed model rows still render when fixture data includes installed models.
10. The Office Snapshot script does not break navigation binding.

If a real browser test framework is unavailable, implement the strongest available generated-HTML and JavaScript behavior tests using local tooling already present in the repository.

## Local Commands To Run Or Document

Run or document equivalent:

```bash
PYTHONPATH=src pytest -q tests/test_steward_command_center.py
PYTHONPATH=src pytest -q tests/test_resident_interaction.py
PYTHONPATH=src pytest -q tests/test_ai_services_steward_model_selector.py
PYTHONPATH=src python -m estate.cli.main steward-command-center
```

Also add and run a validation that proves the generated page is not merely parseable, but browser-navigation capable.

## Required Report Artifacts

Create:

```text
operations/steward/WP-0141_steward_command_center_browser_runtime_failure_report.md
runtime/steward/WP-0141_steward_command_center_browser_runtime_failure_report.json
collaboration/work_packages/completions/WP-0141_codex_done.json
```

The report must include:

- root cause;
- why WP-0140 did not fix the real browser failure;
- exact generated HTML issue found;
- browser/runtime validation performed;
- before/after behavior;
- how navigation is now bound;
- how CSS/styling is guaranteed;
- what diagnostic indicator was added;
- what was preserved from WP-0138;
- what was preserved from WP-0139;
- tests run;
- remaining limitations.

## Acceptance Criteria

WP-0141 is complete when the locally generated Steward Command Center opens as a usable browser UI, has a visible runtime diagnostic, navigation and tab switching work in the browser, Alfred and AI Services / Models can be opened from the UI, the page no longer appears as a plain broken dump of headings/lists, and tests protect against this exact failure mode.

## Merge Class

Class A. Escalate if repair attempts to replace the static local Command Center architecture with an external framework, introduce cloud calls, remove Alfred governance boundaries, remove AI Services / Models functionality, or change Steward authority semantics.
