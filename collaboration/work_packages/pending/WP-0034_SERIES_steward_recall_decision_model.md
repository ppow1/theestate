# SERIES TASK WP-0034 — Steward Recall Decision Model

## Codex Command
Read `collaboration/work_packages/pending/WP-0034_SERIES_steward_recall_decision_model.md` and do exactly what it says.

## Mode
SERIES. Depends on WP-0033 Autonomous Estate Operations Charter.

## Mission
Create the Steward Recall Decision Model v1 so Alfred can determine when the Estate must recall the Steward instead of continuing autonomously.

## Why This Is Next
The Autonomous Estate Operations Charter defines the principle. This package turns that principle into a small, auditable decision model without giving Alfred constitutional authority.

## Scope
Create a decision model document such as:

- `docs/operations/Steward_Recall_Decision_Model_v1.md`

Optionally add a machine-readable policy file such as:

- `data/policy/steward_recall_reasons.json`

## Required Content
Define:

- recall principle
- Alfred's role as coordinator, not sovereign authority
- workers may request recall
- Alfred may issue recall only under approved policy
- recall reasons
- non-recall events
- required evidence for recall
- audit fields required for every recall

## Initial Recall Reasons
Support at least:

- constitutional
- architectural
- operational
- security
- HR

## Events That Shall Not Trigger Recall
Include at least:

- routine mail
- completed work
- normal validation
- normal board updates
- parking lot additions
- successful Codex runs
- informational status changes

## Expected Outputs
- Steward Recall Decision Model v1 document.
- Optional policy JSON if straightforward.
- Completion artifact for WP-0034.

## Constraints
Do not implement notifications in this package. Do not create final security clearance policy. Do not give Alfred independent constitutional authority. Do not bypass the Steward. Do not edit `estate_ledger/ledger.md` or `development/devlog.md`.

## Validation
If JSON is added, ensure it parses. Documentation should reference existing Autonomous Operations Charter if present.

## Completion Signal
Before finishing, create `collaboration/work_packages/completions/WP-0034_codex_done.json` with work_package_id, codex_status=done, completed_at, branch, pull_request_url, summary, files_changed, tests_run, known_limitations, ready_for_ca_review=true, merge_authority=ca_verified_auto_merge_allowed.

## Merge Class
Class B if authority language expands Alfred authority. Otherwise Class A documentation/policy model after CA verification.
