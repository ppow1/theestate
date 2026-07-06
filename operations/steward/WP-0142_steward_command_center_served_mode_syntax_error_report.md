# WP-0142 Steward Command Center Served-Mode Syntax Error Report

## Root cause
The browser-visible failure was isolated to the generated executable script near the previously reported served HTML line 553. The suspect token was the raw Unicode ellipsis in the Office Snapshot status assignment:

```js
status.textContent='Building local snapshot ZIP…';
```

Although modern JavaScript accepts this when the document is decoded correctly, the raw non-ASCII token made the generated inline script brittle and was the exact token at the reported Chrome line. The generator now emits the string with an ASCII JavaScript escape:

```js
status.textContent='Building local snapshot ZIP\u2026';
```

This keeps the rendered UI text the same while removing the raw token from the executable script stream Chrome parses.

## Exact served-mode syntax error line/token
After regeneration and served-mode inspection, the formerly failing line is now:

```text
line 554: const status=document.querySelector('#office-snapshot-status'); if(status) status.textContent='Building local snapshot ZIP\u2026';
```

The repaired token is `\u2026`; the former raw token was `…` inside the JavaScript string literal.

## Why previous validation missed it
Previous validation did not assert over every executable `<script>` block exactly as emitted in `runtime/steward/command_center.html` and did not inspect the generated/served line corresponding to Chrome's line number. Partial script checks can miss inline generated content, data-bearing script tags, or a served response that differs from a separately checked source snippet.

## Before behavior
- Served mode returned `/` and `/status.json`, but browser initialization could stop at the inline script syntax error.
- If script initialization stopped, workspace navigation, top tabs, Alfred, AI Services / Models, and diagnostics could remain unbound.
- File mode still attempted startup fetches for local endpoints that are not available under `file://`.

## After behavior
- The generated and served executable script block parses with the emitted `\u2026` escape at the formerly failing line.
- The runtime diagnostic is visible and updated after initialization.
- Office navigation and workspace tabs are bound through delegated `data-tab` handling.
- `activateOfficeTab` updates `hidden`, `.active`, `aria-selected`, and `aria-current` consistently.

## Served-mode behavior
- Served mode remains a valid live mode.
- `/status.json` is still fetched by quiet refresh.
- Refresh failures are caught and logged without aborting navigation or shell initialization.
- Alfred history startup fetches remain enabled only in served mode.

## File-mode behavior
- File mode is detected with `location.protocol === 'file:'`.
- Startup Alfred history fetches are not required in file mode.
- Quiet refresh does not require `/status.json` in file mode and updates the diagnostic as static-safe.
- Embedded static artifacts remain available, so navigation and workspace switching can work without local fetches.

## Navigation binding
Navigation is delegated from a single document click listener. Any clicked element matching `[data-tab]` calls `activateOfficeTab(button.dataset.tab)`. The activator locates `workspace-<tab>`, hides all other workspace sections, marks the matching tab/nav item active, updates ARIA attributes, persists the active tab when allowed, and updates the visible runtime diagnostic.

## WP-0138 preservation
The AI Services / Models workspace remains present. Tests verify installed TextGen model rows still render when fixture data includes an installed `.gguf` model. No model inventory or governed-control behavior was removed.

## WP-0139 preservation
The Alfred form submit handler remains scoped to `#alfred-chat-form`, calls `preventDefault()` only for that form, preserves timeout/safe-failure behavior, and does not interfere with global delegated navigation binding.

## Tests run
- `PYTHONPATH=src pytest -q tests/test_steward_command_center.py`
- `PYTHONPATH=src pytest -q tests/test_resident_interaction.py`
- `PYTHONPATH=src pytest -q tests/test_ai_services_steward_model_selector.py`
- `PYTHONPATH=src pytest -q tests/test_steward_command_center.py tests/test_resident_interaction.py tests/test_ai_services_steward_model_selector.py`
- `PYTHONPATH=src python -m estate.cli.main steward-command-center`
- `PYTHONPATH=src python -m estate.cli.main steward-command-center --serve --host 127.0.0.1 --port 8765`
- Served response fetched from `http://127.0.0.1:8765/` and `/status.json`.
- Generated executable scripts extracted from `runtime/steward/command_center.html` and checked with `node --check` on each executable script block.

## Remaining limitations
- The validation uses Node parser checks for executable script syntax and static script-level assertions for DOM behavior; it does not launch Chrome in this environment.
- File mode cannot perform browser-blocked local fetches by design; it degrades to static embedded artifacts plus a visible safe-mode diagnostic.
