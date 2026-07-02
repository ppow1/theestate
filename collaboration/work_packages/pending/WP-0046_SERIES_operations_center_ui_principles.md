# SERIES TASK WP-0046 — Estate Operations Center UI Principles

## Codex Command
Read `collaboration/work_packages/pending/WP-0046_SERIES_operations_center_ui_principles.md` and do exactly what it says.

## Mission
Create the foundational UI architecture specification for the Estate Operations Center. This document becomes the design contract for future UI work packages.

## Required Principles
- Local-first architecture.
- Functional before visual polish.
- UI evolves toward the Estate Visual Manifest.
- Collapsible navigation panel.
- Tabbed workspace.
- Persistent bottom status bar.
- Collapsible live activity/SCADA console.
- Command palette/console.
- Dynamic refresh without full-page redraws.
- Global and per-resident verbosity controls.
- Settings page (theme, refresh, filters, layout, notifications).
- About page with component/version inventory.
- Voice integration hooks (STT, TTS, SillyTavern) defined as interface adapters only.

## Visual Manifest
Document how the Operations Center should gradually reflect the Estate Visual Manifest while allowing an intentionally simple first implementation.

## Constraints
Do not build the UI in this package. Produce the architectural specification only. Do not edit `estate_ledger/ledger.md` or `development/devlog.md`.

## Completion Signal
Create `collaboration/work_packages/completions/WP-0046_codex_done.json` using the standard completion schema.

## Merge Class
Class A.
