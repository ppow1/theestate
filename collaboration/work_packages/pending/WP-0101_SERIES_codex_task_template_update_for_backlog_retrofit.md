# SERIES TASK WP-0101 — Codex Task Template Update for Backlog Retrofit

## Codex Command
Read `collaboration/work_packages/pending/WP-0101_SERIES_codex_task_template_update_for_backlog_retrofit.md` and do exactly what it says.

## Mission
Have Chief Architect #4 define the updated Codex task template requirements that must be applied to the unprocessed backlog before those packages are sent through Codex.

This work package exists because the Steward has an implementation backlog reaching back to approximately WP-0086. The backlog is operationally acceptable, but the Codex task template has evolved. The pending backlog must therefore be retrofitted before execution so older queued work packages carry the updated instruction structure.

## Context
The Steward is currently the intentional implementation bottleneck. Chief Architects may continue producing work packages ahead of Codex execution, but queued packages must remain compatible with current Codex operating expectations.

The immediate problem is that WP-0086 through WP-0100 include pending or reserved work that may not yet contain the updated Codex task template content. Chief Architect #4 must first author the template update. After that template is available, Chief Architect #3 or the next assigned architect will retrofit the queued backlog files.

## Scope
Chief Architect #4 should produce the updated Codex task template specification, including:

- required heading structure
- required Codex command wording
- required execution constraints
- required validation expectations
- required completion signal format
- required merge class guidance
- required backlog-retrofit note, if any
- required distinction between authored, implemented, validated, and institutionalized work
- required handling for reserved work package numbers
- required handling for Steward bottleneck / backlog-aware execution

## Required Output
Create or update an appropriate template or specification document using existing repository conventions.

The output must be explicit enough that another architect can apply it mechanically to pending work package files without guessing.

## Backlog Retrofit Target Range
After this template update exists, the pending backlog retrofit should apply to queued work package files in the WP-0086 through WP-0100 range that exist in the repository and remain unprocessed.

Known relevant numbers include:

- WP-0086 — Chief Architect #4 validation continuation #3, reserved/validation stream.
- WP-0087 — Operator verbosity and filter profiles.
- WP-0088 — Operations Center layout framework.
- WP-0089 — Operations Center workspace profiles.
- WP-0090 — Operations Center command console.
- WP-0091 — Chief Architect #4 validation continuation #4, reserved/validation stream.
- WP-0092 — Operations Center help and about.
- WP-0093 — Operations Center settings manager.
- WP-0094 — Operations Center status bar.
- WP-0095 — Chief Architect #4 validation continuation #5, reserved/validation stream.
- WP-0096 — Operations Center notification center.
- WP-0097 — Operations Center local server bootstrap.
- WP-0098 — Operations Center launch script.
- WP-0099 — Operations Center pre-handoff readiness check.
- WP-0100 — Chief Architect #3 transition and backlog continuity.

## Architectural Rules
- Do not retrofit backlog files in this package unless the updated template is also produced and the scope remains safe.
- Prefer producing the template/specification first, then performing the backlog retrofit as a follow-up package.
- Do not claim queued work has been implemented or validated.
- Do not erase package-specific intent while adding standard template material.
- Do not alter Chief Architect #4's validation stream without preserving its purpose.
- Do not edit `estate_ledger/ledger.md` or `development/devlog.md`.

## Follow-Up Work
After Chief Architect #4 completes this package, the next architectural task should apply the approved template update to existing pending work package files from WP-0086 through WP-0100.

That follow-up should fetch each target file, preserve its mission and package-specific requirements, add the updated Codex template material, and update the file in place with clear commit history.

## Tests
Verify that the produced template/specification:

- is clear enough for mechanical retrofit
- distinguishes authored/pending work from implemented/validated work
- accounts for Steward backlog bottleneck
- preserves reserved validation work packages
- includes completion-signal guidance
- includes execution and authority constraints

## Completion Signal
Create `collaboration/work_packages/completions/WP-0101_codex_done.json` using the standard completion schema.

## Merge Class
Class A unless template changes alter governance or authority semantics; escalate to Class B if governance semantics are changed.
