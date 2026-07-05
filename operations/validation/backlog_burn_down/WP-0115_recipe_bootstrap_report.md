# WP-0115 Recipe Bootstrap Report

## Production Readiness Totals Before

- total_blocked: 51
- total_incomplete_receipts: 5
- total_missing_receipts: 5
- total_missing_recipes: 47
- total_production_ready: 51
- total_work_packages_scanned: 102

## Production Readiness Totals After

- total_blocked: 12
- total_incomplete_receipts: 5
- total_missing_receipts: 4
- total_missing_recipes: 8
- total_production_ready: 90
- total_work_packages_scanned: 102

## Packages Considered
WP-0014, WP-0016, WP-0017, WP-0018, WP-0022, WP-0023, WP-0024, WP-0025, WP-0026, WP-0028, WP-0030, WP-0031, WP-0032, WP-0033, WP-0034, WP-0035, WP-0039, WP-0040, WP-0041, WP-0042, WP-0043, WP-0044, WP-0045, WP-0046, WP-0047, WP-0048, WP-0049, WP-0050, WP-0051, WP-0054, WP-0055, WP-0061, WP-0062, WP-0063, WP-0064, WP-0069, WP-0071, WP-0072, WP-0073, WP-0082, WP-0083, WP-0084, WP-0094, WP-0100, WP-0104, WP-0115, WP-9999

## Packages Selected for Recipe Generation
WP-0014, WP-0022, WP-0023, WP-0024, WP-0025, WP-0026, WP-0028, WP-0030, WP-0031, WP-0032, WP-0033, WP-0034, WP-0035, WP-0039, WP-0041, WP-0042, WP-0043, WP-0044, WP-0045, WP-0046, WP-0047, WP-0048, WP-0049, WP-0050, WP-0051, WP-0054, WP-0055, WP-0061, WP-0062, WP-0064, WP-0069, WP-0071, WP-0072, WP-0082, WP-0083, WP-0084, WP-0100, WP-0104

## Packages Skipped
- WP-0016: receipt_status=incomplete; ready_for_ca_review is not true.; Completion artifact is missing required metadata: merge_authority_or_equivalent, completed_at, summary, files_changed, tests_run, ready_for_ca_review; Execution status blocks readiness: no_recipe.
- WP-0017: receipt_status=incomplete; ready_for_ca_review is not true.; Completion artifact is missing required metadata: merge_authority_or_equivalent, completed_at, files_changed, tests_run, ready_for_ca_review; Execution status blocks readiness: no_recipe.
- WP-0018: receipt_status=incomplete; Completion artifact is missing required metadata: merge_authority_or_equivalent, completed_at, summary; Execution status blocks readiness: no_recipe.
- WP-0040: blocked by more than missing recipe: Blocking known limitation: Dependency and blocker extraction is limited to explicit fields and labelled Markdown sections.; Execution status blocks readiness: no_recipe.
- WP-0063: receipt-listed runtime artifacts are absent, so artifact presence recipe would fail
- WP-0073: receipt_status=missing; Completion artifact is missing.; Execution status blocks readiness: no_recipe.
- WP-0094: receipt_status=missing; Completion artifact is missing.; Execution status blocks readiness: no_recipe.
- WP-0115: receipt_status=missing; Completion artifact is missing.; Execution status blocks readiness: no_recipe.
- WP-9999: receipt_status=missing; Completion artifact is missing.; Execution status blocks readiness: no_recipe.

## Recipes Added by Template Class
- Artifact Presence Recipe: WP-0014, WP-0022, WP-0023, WP-0024, WP-0025, WP-0026, WP-0028, WP-0030, WP-0031, WP-0032, WP-0033, WP-0034, WP-0035, WP-0039, WP-0041, WP-0042, WP-0043, WP-0044, WP-0045, WP-0046, WP-0047, WP-0048, WP-0049, WP-0050, WP-0051, WP-0054, WP-0055, WP-0061, WP-0062, WP-0064, WP-0069, WP-0071, WP-0072, WP-0082, WP-0083, WP-0084, WP-0100, WP-0104
- WP-0115 Self-Validation Recipe: WP-0115

## Packages Successfully Validated
WP-0014, WP-0022, WP-0023, WP-0024, WP-0025, WP-0026, WP-0028, WP-0030, WP-0031, WP-0032, WP-0033, WP-0034, WP-0035, WP-0039, WP-0041, WP-0042, WP-0043, WP-0044, WP-0045, WP-0046, WP-0047, WP-0048, WP-0049, WP-0050, WP-0051, WP-0054, WP-0055, WP-0061, WP-0062, WP-0064, WP-0069, WP-0071, WP-0072, WP-0082, WP-0083, WP-0084, WP-0100, WP-0104

## Still Blocked

- Missing recipes: WP-0016, WP-0017, WP-0018, WP-0040, WP-0063, WP-0073, WP-0094, WP-9999
- Missing receipts: WP-0056, WP-0073, WP-0094, WP-9999
- Incomplete receipts: WP-0016, WP-0017, WP-0018, WP-0106, WP-0107
- Implementation or human review: WP-0016, WP-0017, WP-0018, WP-0040, WP-0056, WP-0073, WP-0089, WP-0094, WP-0106, WP-0107, WP-9999

## Helen Path Status
WP-0106 and WP-0107 remain blocked by incomplete receipts; no Helen-path package from the do-not-promote list was promoted.

## Recommended Next Batch
- Repair or review incomplete receipts WP-0016, WP-0017, WP-0018, WP-0106, WP-0107 only with human-confirmed evidence.
- Investigate missing receipt packages WP-0056, WP-0073, WP-0094, WP-0115, WP-9999.
- Review WP-0063 missing runtime artifact paths before adding a recipe.
