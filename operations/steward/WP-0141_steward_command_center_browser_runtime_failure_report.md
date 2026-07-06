# WP-0141 Steward Command Center Browser Runtime Failure Report

## Root cause

The generated Command Center had syntactically valid JavaScript, but its browser runtime state was not observable and navigation relied on assumptions that were too fragile for a locally opened static file. Navigation controls did not explicitly declare `type="button"`, local preference writes could throw in constrained local-file browser contexts, and initialization was only validated as parseable rather than as a bound browser UI.

## Why WP-0140 did not fix the real failure

WP-0140 validated that executable scripts parsed, but `node --check` does not exercise DOM readiness, delegated click binding, workspace visibility, localStorage behavior, form submission isolation, Office Snapshot click handlers, or whether generated tabs map to generated workspaces. The Steward's reported page was therefore still able to appear as an unstyled or inert heading/list dump even though the script parsed.

## Exact generated HTML issue found

The generated page did include a style block and script block, but it lacked a visible runtime diagnostic and had no generated-HTML test proving that navigation buttons and tab buttons could actually target workspace sections. The page also did not make fallback/runtime state visible, so a browser script initialization failure looked like a broken static document rather than a diagnosed UI state.

## Browser/runtime validation performed

Validation now checks the generated HTML shell, inline style/script presence, visible UI runtime diagnostic, delegated navigation binding, DOM-ready initialization, `data-tab` to `workspace-<tab>` coverage, single initial visible workspace, simulated activation of Alfred and AI Services / Models, and isolation of Alfred submit and Office Snapshot click handling from global navigation binding.

## Before/after behavior

Before: the page could show repeated navigation labels and workspace headings with no visible indication that scripts were initialized or navigation was bound.

After: the static fallback says `UI runtime: script not initialized; navigation may not work`, and initialized browsers update the banner to `UI runtime: scripts loaded / navigation bound / active tab: <tab>`. Clicking Office Navigation or top tab controls switches to the requested workspace and hides the rest.

## How navigation is now bound

Navigation uses delegated click handling through a single `bindOfficeNavigation()` function initialized via `whenDomReady(initOfficeRuntime)`. Both sidebar Office Navigation and top workspace tabs use `data-tab`; the shared `activateOfficeTab()` function updates `hidden`, `.active`, `aria-selected`, and `aria-current` state consistently.

## How CSS/styling is guaranteed

The generator emits a complete document shell with `<html>`, `<head>`, inline `<style>`, `<body>`, and inline executable script. Tests now assert that the style block is inside the head and that generated workspaces are hidden by default except the configured active profile tab.

## Diagnostic indicator added

A visible local-only banner with `id="ui-runtime-diagnostic"` was added. Its static fallback reports that scripts are not initialized, and runtime code updates it after navigation binding or reports an error if a tab targets a missing workspace.

## Preserved from WP-0138

The AI Services / Models workspace, model inventory, TextGen model discovery display, and installed model rows remain rendered and covered by existing tests.

## Preserved from WP-0139

Alfred diagnostics, timeout behavior, safe failure messaging, resident chat form handling, and attachment handling remain intact. Alfred submit handling still prevents default form behavior and is tested not to replace navigation binding.

## Tests run

- `PYTHONPATH=src pytest -q tests/test_steward_command_center.py`
- `PYTHONPATH=src pytest -q tests/test_resident_interaction.py tests/test_ai_services_steward_model_selector.py`
- `PYTHONPATH=src python -m estate.cli.main steward-command-center`

## Remaining limitations

No external browser automation framework is available in this repository, so WP-0141 uses generated-HTML and DOM-behavior-oriented tests rather than a real browser screenshot test. Alfred chat history still requires the local HTTP endpoint to be available; when opened directly as a local file, its fetch failure is caught and shown safely.
