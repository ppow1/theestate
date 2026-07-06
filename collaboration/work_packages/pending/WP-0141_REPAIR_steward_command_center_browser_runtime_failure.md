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

This means WP-0140 did not repair the real browser/runtime failure. It may have made scripts syntactically valid in one validation context, but the actual generated page still does not function for the Steward.

## Browser Console Evidence From Steward Machine

### Evidence 1: Direct `file://` Open

The Steward opened the broken page directly as a local file:

```text
file:///A:/theestate/runtime/steward/command_center.html
```

Chrome console showed repeated failures equivalent to:

```text
Failed to load resource: net::ERR_FAILED
Access to fetch at 'file:///A:/status.json' from origin 'null' has been blocked by CORS policy: Cross origin requests are only supported for protocol schemes: chrome, chrome-extension, chrome-untrusted, data, http, https, isolated-app.
Unsafe attempt to load URL file:///A:/theestate/runtime/... from frame with URL file:///A:/theestate/runtime/...
file: URLs are treated as unique security origins.
GET file:///A:/status.json net::ERR_FAILED
```

This proves direct file mode cannot depend on browser `fetch()` for local runtime files.

### Evidence 2: Served Mode Still Broken

The Steward then served the Command Center locally:

```powershell
$env:PYTHONPATH = "src"
python -m estate.cli.main steward-command-center --serve --host 127.0.0.1 --port 8765
```

The server successfully served the page and `status.json`:

```text
Office of the Steward command center serving at http://127.0.0.1:8765/
127.0.0.1 - - [06/Jul/2026 11:50:47] "GET / HTTP/1.1" 200 -
127.0.0.1 - - [06/Jul/2026 11:51:18] "GET /status.json HTTP/1.1" 200 -
```

However, the browser console at:

```text
http://127.0.0.1:8765/
```

still shows:

```text
Uncaught SyntaxError: Invalid or unexpected token
(index):553
```

This is now the highest-priority grounded failure evidence.

Important: fetch is working correctly in served mode. The remaining served-mode failure is a generated JavaScript syntax error at or near line 553 of the served/generated HTML.

## Required Diagnosis Update

Codex must inspect the actual generated `runtime/steward/command_center.html` around the failing browser line, especially near line 553.

Do not rely only on `node --check` against extracted scripts unless the extraction exactly matches the browser-executed script. The browser is reporting a syntax error in the actual page.

Likely causes to inspect:

- unsafe newline embedded inside a JavaScript string literal;
- raw generated text injected into `<script>` without JSON encoding;
- raw `</script>` or backticks inside generated data;
- a Windows path such as `A:\...` or an artifact string escaping incorrectly;
- generated JSON embedded in executable script rather than `application/json` data block;
- invalid line continuation or unterminated quote;
- extraction/validation tests missing the exact script block that Chrome executes;
- served HTML differs from committed/generated HTML used in tests.

The repair must identify the exact generated token at browser line 553 and fix the generator so the browser can parse the actual served page.

## Correct Runtime Model

The Command Center has two supported modes:

### Served mode

```text
http://127.0.0.1:8765/
```

In served mode:

- `fetch('/status.json')` is allowed and expected;
- live refresh/polling may continue;
- fetch failures must still be caught and must not abort navigation;
- generated JavaScript must parse in Chrome.

### File mode

```text
file:///A:/theestate/runtime/steward/command_center.html
```

In file mode:

- required startup `fetch()` must not be used;
- local file fetches will be blocked by browser security;
- embedded static artifacts should be used;
- optional refresh should be disabled or show a safe diagnostic;
- navigation must still work.

## Critical Correction

Do not treat `node --check` as sufficient validation.

`node --check` only proves JavaScript parses in the tested script extraction. It does not prove:

- the browser receives the same exact script text;
- browser event listeners are attached;
- tab buttons switch workspaces;
- CSS is loaded/applied;
- hidden workspaces are actually hidden;
- inline scripts run when opened as a local file;
- DOMContentLoaded timing works;
- query selectors match generated HTML;
- buttons have correct types and handlers;
- Alfred submit works;
- AI Services / Models can be opened from the browser;
- `fetch()` works under `file://` browser security;
- served-mode HTML has no syntax error at browser line 553.

The repair must validate real browser-facing behavior at the generated HTML level, not only script syntax.

## Primary Failure To Reproduce

Generate `runtime/steward/command_center.html`, serve it, and inspect the actual browser surface.

Verify whether:

1. Chrome reports `Uncaught SyntaxError: Invalid or unexpected token` at or near line 553.
2. The exact generated source line around 553 contains malformed JavaScript.
3. The page is styled.
4. Workspace tabs/buttons are clickable.
5. Clicking Alfred shows Alfred and hides Mission Control.
6. Clicking AI Services / Models shows AI Services / Models and hides Mission Control.
7. Office Navigation buttons work.
8. The duplicate top tab bar is intentional and functional, or removed if confusing/broken.
9. Only one workspace is visible at a time.
10. The Alfred submit form works or shows a safe failure.
11. The browser console has no uncaught initialization errors.
12. File mode avoids required startup fetches that target `file://`, `/A:/...`, `status.json`, or other local artifacts directly.

If browser automation is unavailable, use static generated-HTML tests plus a minimal DOM simulation sufficient to prove event handlers attach to the generated elements and no initialization error can abort the shell.

## Required Repair Outcomes

### 1. Fix The Served-Mode Syntax Error

The generated Command Center served at `http://127.0.0.1:8765/` must not throw:

```text
Uncaught SyntaxError: Invalid or unexpected token
```

Codex must identify the exact generated line/token and repair the generator.

The repair must include a test or validation that checks the exact generated executable scripts from `runtime/steward/command_center.html` as served/generated, not a sanitized or partial approximation.

### 2. Command Center Must Not Depend On `fetch()` Under `file://`

The Command Center can be opened locally as:

```text
A:\theestate\runtime\steward\command_center.html
```

Therefore the generated static shell must not require browser `fetch()` to read local files in file mode.

Required direction:

- Embed required local data at generation time into safe `<script type="application/json">` blocks or static HTML.
- Do not require `fetch('status.json')`, local runtime JSON, or local file paths from a `file://` page.
- Any optional live refresh that requires HTTP must be disabled under `file://` and must not break navigation.
- All fetch failures must be caught and must not abort global initialization.
- If a feature requires serving over HTTP, the UI must show a safe diagnostic and preserve the rest of the shell.

### 3. Make Navigation Work Without Fragile Script Assumptions

The Steward Command Center must work in both supported modes:

```text
http://127.0.0.1:8765/
file:///A:/theestate/runtime/steward/command_center.html
```

Navigation must not depend on brittle script timing, external assets, or successful optional refresh fetches.

Preferred implementation:

- Keep the static HTML local-first architecture.
- Add robust inline JavaScript that attaches handlers after DOM is available and also works if the script is loaded after the DOM.
- Use event delegation on a stable root element rather than per-button fragile binding.
- Ensure both Office Navigation and workspace tab buttons use the same switching function.
- Update `hidden`, `.active`, `aria-selected`, and `aria-current` consistently.
- Prevent default form/button behavior where needed.
- Catch all optional feature errors so one failing feature cannot disable navigation.

If JavaScript is unavailable, the page should still degrade visibly and explain that tabs require JavaScript rather than appearing silently broken.

### 4. Ensure CSS Is Present And Applied

Verify generated HTML includes required inline CSS.

If the current page looks like plain unstyled document text or only partially styled, diagnose why:

- missing `<style>` block;
- malformed `<head>`;
- stylesheet placed outside `<head>`;
- broken HTML before style/script blocks;
- browser treating file as text/html but style invalid;
- generated CSS selectors not matching DOM;
- initialization failure leaves the layout in fallback/plain state.

Repair the generator so the page has a usable styled shell.

### 5. Eliminate Confusing Duplicate Navigation If Needed

The output currently shows Office Navigation and then a second list of the same workspaces immediately underneath.

If the second list is the tab bar and is intentional, it must be styled and functional.

If it is confusing in the plain fallback state, make the layout clear:

- sidebar navigation;
- top tabs;
- active workspace content.

Do not leave the Steward seeing two plain repeated lists and no usable controls.

### 6. Preserve Recent Functionality

Do not regress:

- WP-0138 AI Services / Models workspace;
- model inventory display;
- known installed TextGen models;
- WP-0139 Alfred diagnostics and timeout/safe failure behavior;
- Office Snapshot behavior unless it is the cause of the runtime failure.

### 7. Add A Built-In UI Self-Test Panel Or Diagnostic Banner

Add a local-only diagnostic indicator that makes browser runtime state visible, for example:

```text
UI runtime: scripts loaded / navigation bound / active tab: mission-control / mode: served
UI runtime: scripts loaded / navigation bound / active tab: mission-control / mode: file safe static
```

If scripts fail, the static fallback should visibly say:

```text
UI runtime: script not initialized; navigation may not work
```

If the page is opened under `file://`, the runtime diagnostic should explicitly say that network/file fetch refresh is disabled and that embedded static artifacts are being used.

This is to prevent future silent failures where the generated page looks present but is unusable.

### 8. Add Tests That Match The Steward's Failure

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
11. Generated HTML contains no required startup `fetch()` calls to `status.json`, local runtime JSON, `file://`, `/A:/`, or raw local artifact paths when in file mode.
12. Any optional `fetch()` call is wrapped in a catch/failure path and cannot abort initialization.
13. Generated HTML explicitly supports `file://` mode with embedded artifacts.
14. Generated served-mode executable scripts parse exactly as emitted in `runtime/steward/command_center.html`.
15. A regression test inspects the generated HTML around the formerly failing browser line/token and proves no invalid JavaScript token is present.

If a real browser test framework is unavailable, implement the strongest available generated-HTML and JavaScript behavior tests using local tooling already present in the repository.

## Local Commands To Run Or Document

Run or document equivalent:

```bash
PYTHONPATH=src pytest -q tests/test_steward_command_center.py
PYTHONPATH=src pytest -q tests/test_resident_interaction.py
PYTHONPATH=src pytest -q tests/test_ai_services_steward_model_selector.py
PYTHONPATH=src python -m estate.cli.main steward-command-center
PYTHONPATH=src python -m estate.cli.main steward-command-center --serve --host 127.0.0.1 --port 8765
```

Also add and run a validation that proves the generated page is not merely parseable, but browser-navigation capable and safe under `file://`.

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
- exact served-mode browser syntax error line/token;
- browser/runtime validation performed;
- before/after behavior;
- how navigation is now bound;
- how CSS/styling is guaranteed;
- what diagnostic indicator was added;
- what was preserved from WP-0138;
- what was preserved from WP-0139;
- how served mode supports live `status.json` fetch safely;
- how `file://` mode avoids CORS/local file fetch failure;
- tests run;
- remaining limitations.

## Acceptance Criteria

WP-0141 is complete when the locally generated Steward Command Center opens as a usable browser UI from both `http://127.0.0.1:8765/` and `file:///A:/theestate/runtime/steward/command_center.html`, has a visible runtime diagnostic, does not make required startup fetches blocked by CORS in file mode, has no served-mode browser syntax error, navigation and tab switching work in the browser, Alfred and AI Services / Models can be opened from the UI, the page no longer appears as a plain broken dump of headings/lists, and tests protect against this exact failure mode.

## Merge Class

Class A. Escalate if repair attempts to replace the static local Command Center architecture with an external framework, introduce cloud calls, remove Alfred governance boundaries, remove AI Services / Models functionality, or change Steward authority semantics.
