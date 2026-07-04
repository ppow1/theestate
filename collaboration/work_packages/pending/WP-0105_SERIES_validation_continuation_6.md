# SERIES TASK WP-0105 — Validation Continuation #6

## Codex Command
Read `collaboration/work_packages/pending/WP-0105_SERIES_validation_continuation_6.md` and do exactly what it says.

## Mode
SERIES

## Mission
Reserve WP-0105 for Chief Architect #4 to continue the validation stream after the Chief Architect Operating Manual and backlog template retrofit work.

## Background
The Estate has maintained a separate Chief Architect #4 validation continuation stream so validation work remains independent from implementation backlog generation. This package preserves that stream and gives Chief Architect #4 the next reserved work package number.

## Scope
Chief Architect #4 should define the exact validation continuation scope based on the current production-readiness report, validation coverage manifest, recent completion receipts, and pending implementation backlog.

Recommended focus areas include:

- recent completion artifacts after WP-0101 through WP-0104
- validation coverage for newly created operational manuals and onboarding references
- readiness status of the Operations Center backlog
- validation implications of Resident Runtime work beginning with WP-0106
- any missing or stale validation recipes identified by the WP-0095 production-readiness loop

## Out of Scope
Do not implement resident runtime features in this package.

Do not alter Steward authority, merge authority, or governance authority.

Do not rewrite Chief Architect #4's validation methodology unless Chief Architect #4 explicitly chooses to do so.

## Required Behavior
- Preserve this package as Chief Architect #4's validation continuation slot.
- Base validation work on repository artifacts and generated validation evidence, not chat summaries.
- Document exact validation targets and findings in durable artifacts.
- Keep validation independent from implementation authorship.

## Safety and Authority Constraints
- Do not mark work production-ready without evidence.
- Do not treat authored/pending work as implemented.
- Do not change governance authority.
- Do not broad-stage generated artifacts.
- Do not edit `estate_ledger/ledger.md` or `development/devlog.md` unless explicitly authorized by the final Chief Architect #4 scope.

## Required CLI / Command Surface
Use existing validation commands where applicable, including:

```bash
PYTHONPATH=src python -m estate.cli.main validation-production-readiness --json
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-XXXX --json
```

Use the PowerShell validation wrappers if they are the current local standard.

## Required Artifacts
Chief Architect #4 should determine final artifacts. At minimum, create:

`collaboration/work_packages/completions/WP-0105_codex_done.json`

If validation findings warrant a report, place it in the existing validation report structure rather than inventing a new one.

## Tests
Run or document the validation commands used. Record missing recipes, incomplete receipts, blockers, non-blocking findings, and recommendations.

## Validation Recipe Requirement
If the validation framework requires a recipe for validation-continuation packages, add or update the recipe for WP-0105. If not applicable, record the rationale in the completion receipt.

## Codex Completion Receipt Requirement
Create `collaboration/work_packages/completions/WP-0105_codex_done.json` with standard receipt fields, including scope selected by Chief Architect #4, tests run, findings, known limitations, and readiness for CA review.

## Production Readiness Requirement
Do not claim production readiness for any target unless the WP-0095 loop or an equivalent local validation process supports it.

## Demonstration Requirements
Include exact validation commands and generated artifact paths used in review.

## Completion Signal
Create `collaboration/work_packages/completions/WP-0105_codex_done.json`.

## Merge Class
Class A unless validation authority, governance authority, or merge authority is changed; escalate to Class B if those semantics are altered.
