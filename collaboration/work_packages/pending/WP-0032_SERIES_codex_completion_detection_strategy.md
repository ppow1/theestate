# SERIES TASK WP-0032 — Codex Completion Detection Strategy

## Codex Command
Read `collaboration/work_packages/pending/WP-0032_SERIES_codex_completion_detection_strategy.md` and do exactly what it says.

## Mode
SERIES.

## Mission
Design and implement a local strategy for detecting Codex task completion without relying on merged GitHub state.

## Scope
Document current completion flow, identify observable signals before merge, evaluate local artifacts, task outputs, completion records, and future Codex API integration. Add helper support where appropriate for consuming completion records produced by work packages.

## Deliverables
- `docs/operations/Codex_Completion_Detection_Strategy_v1.md`
- Optional helper module for reading completion records.
- Completion record for WP-0032.

## Constraints
Do not require Enterprise APIs. Do not depend on merged GitHub state as the primary completion signal. Preserve Steward approval before merge.

## Completion Signal
Create `collaboration/work_packages/completions/WP-0032_codex_done.json` with the standard completion fields.

## Merge Class
Class A.
