# WP-0140 Steward Command Center UI Regression Repair Report

## Root cause

WP-0139 left the Command Center vulnerable to browser-surface breakage in the static HTML generator. The generated shell had three related defects:

1. The executable Office Snapshot JavaScript embedded Python-interpreted newline characters inside single-quoted JavaScript strings. That produced an unterminated JavaScript string in the generated page and stopped the global browser script from running.
2. JSON intended for `<script type="application/json">` blocks was HTML-entity escaped. That avoided raw HTML but made `textContent` unsuitable for `JSON.parse`, so the global search palette could throw during page load.
3. The initial active workspace profile was `mission-control`, but the tab bar and nav renderer always marked the first tab (`home`) as active. Before JavaScript repaired state, the DOM advertised inconsistent active/hidden semantics.

## Exact broken behavior reproduced

- Regenerated `runtime/steward/command_center.html` rendered the Office header and a Mission Control workspace, but the global script block could be syntactically invalid in browser/Node parsing because of raw newlines in single-quoted JavaScript strings.
- Because the global script block owns tab switching, layout restore, global palette rendering, Alfred history loading, pending attachment rendering, and Office Snapshot export, one syntax error made the surface appear like a static broken dump rather than a usable website.
- The page also contained JSON script data encoded with `&quot;`, which could corrupt `JSON.parse(dataEl.textContent)` for the search palette.

## Fixed behavior

- Added script-safe JSON helpers for JSON script tags and JavaScript literals.
- Escaped JavaScript newline literals inside the Office Snapshot export script so executable scripts parse cleanly.
- Aligned initial nav and workspace-tab active state with the selected workspace profile.
- Kept inactive workspaces hidden by default and active workspace visible by profile.
- Regenerated `runtime/steward/command_center.html` after the repair.

## Root-cause questions

1. **Why did the regenerated Command Center appear broken after WP-0139?**  
   The global browser script was vulnerable to syntax failure from generated raw newlines in JavaScript string literals, and script-owned tab/navigation behavior therefore did not run reliably.

2. **Did WP-0139 break tab navigation, CSS visibility, JavaScript execution, HTML structure, or all of the above?**  
   The primary break was JavaScript execution. Tab navigation depends on that script, so navigation appeared broken. CSS visibility rules were present, but initial active tab/nav state was inconsistent with the profile. HTML structure was mostly intact, but JSON/script embedding was not defensive enough.

3. **Did the generated HTML include malformed attributes or script content?**  
   It included malformed executable script content due to raw newlines inside single-quoted JavaScript strings. Alfred's `data-state="idle"` attribute was valid after inspection and remains covered by tests.

4. **Did the active workspace profile or generated tab state incorrectly expose all sections or leave the wrong panel active?**  
   The active profile selected Mission Control, but tabs/nav initially marked Home active. The repair renders active nav/tab state from the same `active_tab` used to choose the visible workspace. Inactive workspace sections retain `hidden`.

5. **Did Alfred-specific changes leak into global navigation or global rendering?**  
   Alfred submit/diagnostic code did not directly alter nav generation, but because Alfred's handler lived in the same global script block, any script-generation error could disable both Alfred behavior and global navigation. The repair preserves Alfred diagnostics while hardening the shared script.

## Changed files

- `src/estate/core/steward_command_center.py`
- `tests/test_steward_command_center.py`
- `runtime/steward/command_center.html`
- `operations/steward/WP-0140_steward_command_center_ui_regression_repair_report.md`
- `runtime/steward/WP-0140_steward_command_center_ui_regression_repair_report.json`
- `collaboration/work_packages/completions/WP-0140_codex_done.json`

## Preserved from WP-0138

- AI Services / Models workspace remains present and selectable via `data-tab="ai-services-models"` / `workspace-ai-services-models`.
- Installed TextGen model inventory still renders with model id, model name, service, installed role, approvals, service details, and command hooks.
- Added a regression test with a discovered TextGen model fixture (`Qwen3.gguf`).

## Preserved from WP-0139

- Alfred chat form remains present.
- Alfred timeout handling (`resident_chat_timeout_after_30s`) remains present.
- Safe failure text remains present.
- Adapter diagnostics guidance remains present.
- Alfred response state continues to use `data-state="idle"` and runtime state changes.

## Generated HTML validation performed

- Static tests verify nav controls, workspace panels, hidden inactive panels, global tab script presence, Alfred submit script presence, safe JSON script embedding, and absence of obvious malformed `data-state` / unterminated script strings.
- Regenerated the local Command Center with `PYTHONPATH=src python -m estate.cli.main steward-command-center`.
- Extracted executable script blocks from the regenerated `runtime/steward/command_center.html` and validated them with `node --check`.

## Tests run

- `PYTHONPATH=src pytest -q tests/test_steward_command_center.py tests/test_resident_interaction.py tests/test_ai_services_steward_model_selector.py` — pass, 55 tests.
- `PYTHONPATH=src python -m estate.cli.main steward-command-center` — pass.
- `python - <<'PY' ... extract executable scripts ... PY` followed by `node --check` on extracted scripts — pass.

## Remaining limitations

- Validation is static and syntax-level; no browser automation framework was available or required by the work package.
- The default workspace profile remains Mission Control by existing settings/profile design; this repair aligns visible, tab, and nav state rather than changing Steward workspace policy.
