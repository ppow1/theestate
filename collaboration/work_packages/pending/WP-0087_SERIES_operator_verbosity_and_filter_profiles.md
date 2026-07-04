# SERIES TASK WP-0087 — Operator Verbosity and Filter Profiles

## Codex Command
Read `collaboration/work_packages/pending/WP-0087_SERIES_operator_verbosity_and_filter_profiles.md` and do exactly what it says.

## Mission
Implement configurable operator verbosity and filter profiles for the Operations Center so the Steward can tailor operational visibility by subsystem, office, worker, and event severity.

## Scope
Build on the Operator Activity Stream by introducing saved viewing profiles, verbosity levels, per-source filtering, severity filters, and user preferences suitable for Mission Control and the future dashboard.

## Behavior Requirements
- Read-only presentation controls.
- Support global and per-source verbosity.
- Persist named viewing profiles.
- Integrate with future light/dark UI settings.
- Default to concise operational summaries while allowing deep inspection.

## Constraints
Do not modify event sources. Do not duplicate logging infrastructure. Do not edit `estate_ledger/ledger.md` or `development/devlog.md`.

## Tests
Verify profile persistence, verbosity transitions, filter combinations, empty-state handling, and compatibility with the Operator Activity Stream.

## Completion Signal
Create `collaboration/work_packages/completions/WP-0087_codex_done.json` using the standard completion schema.

## Merge Class
Class A.
