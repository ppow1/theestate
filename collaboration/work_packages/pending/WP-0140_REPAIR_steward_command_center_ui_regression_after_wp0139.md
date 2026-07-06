# REPAIR TASK WP-0140 - Repair Steward Command Center UI Regression After WP-0139

## Codex Command

Read collaboration/work_packages/pending/WP-0140_REPAIR_steward_command_center_ui_regression_after_wp0139.md and do exactly what it says.

## Mode

REPAIR

## Problem

After WP-0139 was merged and the Steward Command Center was regenerated locally, the Command Center website appears broken from the Steward's browser view.

Observed generated page:

```text
Office of the Steward — Local Command Center
Generated: 2026-07-06T15:46:30+00:00
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

The Steward reports that the entire website is now broken.

Likely regression area:

- `src/estate/core/steward_command_center.py`
- WP-0139 command-center UI changes around Alfred submit handling, diagnostics, `data-state`, timeout/transport failure rendering, form wiring, JavaScript, CSS, or workspace/tab visibility.

This is a Command Center surface regression. Repair it without losing WP-0138 AI Services / Models functionality and without losing WP-0139 Alfred response diagnostics.

## Critical Context

Recent merged work:

- WP-0138 completed the Office of the Steward AI Services / Models workspace and local model discovery.
- WP-0139 repaired Alfred resident chat behavior, intent gating, timeout handling, diagnostics, and governed-action guidance.

The new problem is not the original Alfred fallback bug. The new problem is that after WP-0139, the overall Command Center website surface is broken.

## Required Investigation

Inspect the generated HTML and the generator code end-to-end.

At minimum inspect:

- `src/estate/core/steward_command_center.py`
- generated `runtime/steward/command_center.html`
- tests for command center rendering
- tests added or changed by WP-0139
- any JavaScript submit handler added for Alfred
- any CSS or `hidden` / `active` / `data-state` / tab-switching logic
- any malformed string literal, incomplete attribute, malformed HTML, broken script block, or unclosed element introduced by WP-0139

Answer these root-cause questions in the report:

1. Why does the regenerated Command Center appear broken after WP-0139?
2. Did WP-0139 break tab navigation, CSS visibility, JavaScript execution, HTML structure, or all of the above?
3. Did the generated HTML include malformed attributes or script content?
4. Did the active workspace profile or generated tab state incorrectly expose all sections or leave the wrong panel active?
5. Did Alfred-specific changes leak into global navigation or global rendering?

## Required Repair Outcomes

### 1. Restore Command Center Shell

The Steward Command Center must render as a usable website again.

Required visible behavior:

- Office Navigation renders normally.
- Workspace tabs render normally.
- Only the active workspace is visible unless the user selects another workspace.
- Mission Control does not dump or expose unrelated workspace content as the only visible page.
- Navigation buttons switch workspaces.
- Existing local-only static HTML behavior is preserved.

### 2. Preserve WP-0138 AI Services / Models

Do not regress AI Services / Models.

After repair, the AI Services / Models workspace must still show:

- discovered services;
- known installed TextGen models;
- model inventory;
- approvals;
- service details;
- local command hooks.

Use fixtures or generated test data to confirm the installed model inventory still renders when present.

### 3. Preserve WP-0139 Alfred Repair

Do not remove Alfred diagnostics or response contract work.

After repair, Alfred must still support:

- visible response or safe failure state;
- no indefinite stuck state;
- intent-gated fallback for jokes/simple conversation;
- governed action guidance without execution;
- safe adapter diagnostics.

But Alfred-specific JavaScript or diagnostic elements must not break the global page.

### 4. Defensive HTML Generation

Harden the generator against malformed content.

Where practical:

- escape dynamic text used in HTML attributes;
- avoid raw JSON inside attributes unless safely encoded;
- keep large JSON in `<pre>` or script-safe encoded blocks;
- ensure all generated tags are closed;
- ensure generated IDs and `data-*` attributes are valid;
- keep script blocks syntactically valid even when artifacts contain quotes, newlines, braces, or backslashes.

### 5. Add Browser-Surface Tests

Add tests that would have caught this regression.

At minimum prove:

1. Generated Command Center contains valid navigation controls.
2. Generated Command Center contains valid workspace panels.
3. Only the active workspace is visible by default via `hidden`/active semantics.
4. The Alfred form/script additions do not remove or corrupt the global navigation script.
5. The generated HTML contains no obvious malformed `data-state` attribute or unterminated script string.
6. Mission Control, Alfred, and AI Services / Models workspaces are all present and individually selectable by `data-tab`/workspace id.
7. AI Services / Models still renders installed model entries when the model selector returns installed models.
8. Alfred failure/diagnostic UI still renders without breaking the page.

Use static HTML parsing or string-level assertions if a browser automation framework is not available.

## Local Validation Commands

Run or document equivalent:

```bash
PYTHONPATH=src pytest -q tests/test_steward_command_center.py
PYTHONPATH=src pytest -q tests/test_resident_interaction.py
PYTHONPATH=src pytest -q tests/test_ai_services_steward_model_selector.py
PYTHONPATH=src python -m estate.cli.main steward-command-center
```

If a stronger generated-HTML validation command exists, run it as well.

## Required Report Artifacts

Create:

```text
operations/steward/WP-0140_steward_command_center_ui_regression_repair_report.md
runtime/steward/WP-0140_steward_command_center_ui_regression_repair_report.json
collaboration/work_packages/completions/WP-0140_codex_done.json
```

The report must include:

- root cause;
- changed files;
- exact broken behavior reproduced;
- fixed behavior;
- what was preserved from WP-0138;
- what was preserved from WP-0139;
- generated HTML validation performed;
- tests run;
- remaining limitations.

## Acceptance Criteria

WP-0140 is complete when the generated Steward Command Center is usable again, global navigation and workspace tabs work, Alfred repair behavior remains intact, AI Services / Models remains intact, and tests protect against another full-page Command Center rendering regression.

## Merge Class

Class A. Escalate if repair attempts to remove Alfred governance boundaries, remove AI Services / Models functionality, replace the static local Command Center architecture with a new framework, introduce cloud calls, or change Steward authority semantics.
