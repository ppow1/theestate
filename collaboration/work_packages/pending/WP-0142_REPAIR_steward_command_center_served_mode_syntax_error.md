# REPAIR TASK WP-0142 - Repair Steward Command Center Served-Mode Syntax Error

## Codex Command

Read collaboration/work_packages/pending/WP-0142_REPAIR_steward_command_center_served_mode_syntax_error.md and do exactly what it says.

## Mode

REPAIR

## Correction

WP-0141 was already being run by Codex when the latest browser evidence arrived. Do not modify or depend on WP-0141 for this new evidence.

This WP-0142 carries the new diagnosis forward as a separate repair package.

## Problem

After WP-0140 / PR #148, the Steward Command Center still does not function in the browser.

The Steward tested both direct file mode and served mode.

Direct file mode produced CORS/local file fetch errors, which is expected if the page tries to fetch local files under `file://`.

Served mode was then tested with:

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

But the browser console still shows:

```text
Uncaught SyntaxError: Invalid or unexpected token
(index):553
```

Therefore the immediate failure is not CORS in served mode. In served mode, `fetch('/status.json')` works. The page is still broken because the generated browser-executed JavaScript contains an invalid token at or near line 553 of the served/generated HTML.

## Required Diagnosis

Inspect the actual generated `runtime/steward/command_center.html` around line 553 after running:

```bash
PYTHONPATH=src python -m estate.cli.main steward-command-center
```

Then also inspect the served response at:

```text
http://127.0.0.1:8765/
```

Codex must identify the exact generated JavaScript token that Chrome reports as invalid.

Do not rely only on `node --check` unless the tested script text is byte-for-byte the same executable script block Chrome receives.

Likely causes to inspect:

- unsafe newline embedded inside a JavaScript string literal;
- generated text injected into `<script>` without JSON encoding;
- raw `</script>` inside generated data;
- raw backticks or template literal delimiters inside generated data;
- Windows paths such as `A:\...` or artifact strings escaping incorrectly;
- generated JSON embedded in executable script rather than a safe `application/json` block;
- an unterminated quote;
- malformed inline event handler;
- script extraction tests missing the failing script block;
- served HTML differing from committed/generated HTML used in tests.

## Required Repair Outcomes

### 1. Fix Served-Mode Browser Syntax Error

The Command Center served at:

```text
http://127.0.0.1:8765/
```

must not throw:

```text
Uncaught SyntaxError: Invalid or unexpected token
```

The repair must include an explicit root cause identifying the line/token that broke Chrome.

### 2. Preserve Live Served Mode

Served mode is a valid operating mode.

In served mode:

- `fetch('/status.json')` is allowed and expected;
- live refresh/polling may continue;
- fetch failures must still be caught;
- a refresh failure must not abort navigation or shell initialization.

Do not remove served-mode live refresh just because file mode cannot use it.

### 3. File Mode Must Degrade Safely

Direct file mode is also used by the Steward at times:

```text
file:///A:/theestate/runtime/steward/command_center.html
```

In file mode:

- required startup fetches must not be used;
- local file fetches will be blocked by browser security;
- embedded static artifacts should be used;
- optional refresh should be disabled or show a safe diagnostic;
- navigation must still work.

### 4. Restore Navigation And Workspace Switching

After fixing the syntax error, verify:

- Office Navigation works;
- top workspace tabs work;
- clicking Alfred shows Alfred and hides Mission Control;
- clicking AI Services / Models shows AI Services / Models and hides Mission Control;
- only one workspace is visible at a time;
- `hidden`, `.active`, `aria-selected`, and `aria-current` are updated consistently.

### 5. Preserve WP-0138 And WP-0139

Do not regress:

- WP-0138 AI Services / Models workspace;
- model inventory display;
- known installed TextGen models;
- WP-0139 Alfred diagnostics and timeout/safe failure behavior;
- governed action boundaries.

### 6. Add Runtime Diagnostic

Add or preserve a visible UI runtime diagnostic such as:

```text
UI runtime: scripts loaded / navigation bound / active tab: mission-control / mode: served
UI runtime: scripts loaded / navigation bound / active tab: mission-control / mode: file safe static
```

The diagnostic should make it obvious whether the browser shell initialized.

## Tests Required

Add tests that would fail against the current served-mode browser error.

At minimum:

1. Generated served-mode executable scripts parse exactly as emitted in `runtime/steward/command_center.html`.
2. Regression test inspects the generated HTML around the formerly failing browser line/token and proves no invalid JavaScript token is present.
3. Generated HTML contains navigation buttons with `data-tab` values matching workspace sections.
4. Every `data-tab` has a corresponding `workspace-<tab>` section.
5. DOM-level or script-level test verifies clicking `data-tab="alfred"` hides Mission Control and shows Alfred.
6. DOM-level or script-level test verifies clicking `data-tab="ai-services-models"` hides Mission Control and shows AI Services / Models.
7. Alfred form submit handler does not break global navigation binding.
8. AI Services / Models installed model rows still render when fixture data includes installed models.
9. Served mode may fetch `/status.json`, but fetch errors are caught.
10. File mode does not require startup fetches that browser security will block.

## Local Commands To Run Or Document

Run or document equivalent:

```bash
PYTHONPATH=src pytest -q tests/test_steward_command_center.py
PYTHONPATH=src pytest -q tests/test_resident_interaction.py
PYTHONPATH=src pytest -q tests/test_ai_services_steward_model_selector.py
PYTHONPATH=src python -m estate.cli.main steward-command-center
PYTHONPATH=src python -m estate.cli.main steward-command-center --serve --host 127.0.0.1 --port 8765
```

Also run or document the strongest available generated-browser-script validation, not merely a partial `node --check` extraction.

## Required Report Artifacts

Create:

```text
operations/steward/WP-0142_steward_command_center_served_mode_syntax_error_report.md
runtime/steward/WP-0142_steward_command_center_served_mode_syntax_error_report.json
collaboration/work_packages/completions/WP-0142_codex_done.json
```

The report must include:

- root cause;
- exact served-mode syntax error line/token;
- why previous validation missed it;
- before/after behavior;
- served-mode behavior;
- file-mode behavior;
- how navigation is now bound;
- how WP-0138 was preserved;
- how WP-0139 was preserved;
- tests run;
- remaining limitations.

## Acceptance Criteria

WP-0142 is complete when the locally served Command Center at `http://127.0.0.1:8765/` has no `Uncaught SyntaxError`, navigation and tabs work in the browser, Alfred and AI Services / Models can be opened, `status.json` live refresh works or fails safely, direct file mode degrades safely without breaking navigation, and tests protect against the exact served-mode syntax error.

## Merge Class

Class A. Escalate if repair attempts to replace the static/local Command Center architecture with an external framework, introduce cloud calls, remove Alfred governance boundaries, remove AI Services / Models functionality, or change Steward authority semantics.
