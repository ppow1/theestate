# SERIES TASK WP-0095 — Validation Finalization: Codex Receipts, Production Readiness Gate, and Coverage Manifest

## Codex Command

Read `collaboration/work_packages/pending/WP-0095_SERIES_validation_finalization_production_readiness.md` and do exactly what it says.

## Mode

SERIES

## Mission

Complete the Estate validation loop so Chief Architect review can move from mechanism-proving to production-readiness validation.

This is intended to be the final validation-mechanism continuation unless implementation reveals a major architectural defect.

The Estate already has a validation runner, recipe registry, report generation, latest pointer, safe commit wrapper, and recipe expansion pattern.

What is still missing is the complete production-readiness loop:

1. Codex delivery receipt validation.
2. Local execution validation.
3. Explicit production readiness gate.
4. Validation coverage manifest across merged work packages.
5. One command that produces a review-ready production readiness report.

After WP-0095, validation should no longer require discovering missing pieces one work package at a time through chat.

## Background

Current validation can run registered work-package recipes and produce Markdown and JSON reports.

That proves local execution behavior.

However, current validation does not yet fully verify Codex delivery accountability or production readiness.

For a work package to be considered ready to rely on, validation must answer more than "did the command run?"

It must also answer:

- Was there a Codex completion artifact?
- Was there a merged PR or equivalent delivery record?
- Does the completion artifact identify files changed, tests run, known limitations, branch, and PR URL?
- Does the local execution recipe pass?
- Is the work package production-ready or blocked?
- Are blockers distinct from non-blocking findings?
- Which merged work packages still lack recipes, receipts, or validation reports?

WP-0095 must close this loop.

## Existing Validation Foundation

Do not replace the existing validation framework.

Build on the existing components, including:

- `src/estate/core/work_package_validation.py`
- `operations/validation/scripts/validate_work_package.ps1`
- `operations/validation/scripts/run_and_commit_validation.ps1`
- `operations/validation/reports/`
- `runtime/validation/work_packages/`
- `runtime/validation/work_packages/latest.json`
- validation observations
- validation metrics dashboard
- validation handoff artifact workflow
- completion artifacts under `collaboration/work_packages/completions/`

## Scope

Implement the final validation loop.

Add or extend:

- Codex receipt validation
- completion artifact audit
- PR/delivery metadata audit where locally available
- production readiness gate
- production readiness report generator
- validation coverage manifest
- one-command production readiness PowerShell runner
- CLI support consistent with Estate conventions
- WP-0095 self-check recipe

Do not create a new validation institution.

Do not change governance authority.

Do not automatically approve work packages.

Do not weaken the safe Git wrapper.

Do not broad-stage or broad-commit generated artifacts.

## Required Conceptual Model

Validation must now separate these concepts:

### Execution Status

Whether the local validation recipe ran successfully.

Examples:

- `passed`
- `passed_with_findings`
- `failed`
- `no_recipe`

### Receipt Status

Whether the Codex delivery record is complete and auditable.

Examples:

- `complete`
- `incomplete`
- `missing`
- `not_applicable`

### Production Readiness

Whether the work package is ready to rely on operationally.

Required shape:

```json
{
  "production_ready": true,
  "blocking_reasons": [],
  "non_blocking_findings": [],
  "required_followups": []
}
```

A work package may pass local execution but still not be production-ready if receipt metadata is missing or a blocking limitation exists.

A work package may have non-blocking findings and still be production-ready if the report explains why.

## Codex Receipt Validation Requirements

For each validated work package, inspect the completion artifact:

`collaboration/work_packages/completions/<WP-ID>_codex_done.json`

Where a different valid completion filename already exists, support it gracefully and record the actual path.

Receipt validation must check for at least:

- completion artifact exists
- `work_package_id`
- `codex_status`
- `completed_at`
- `branch`
- `pull_request_url` or explicit explanation if not applicable
- `summary`
- `files_changed`
- `tests_run`
- `known_limitations`
- `ready_for_ca_review`
- `merge_authority` or explicit equivalent field

If fields are missing, record them as receipt gaps.

If `ready_for_ca_review` is not true, record it as a blocker unless there is an explicit documented reason.

If `known_limitations` includes a blocking limitation, production readiness must be false.

Do not assume a work package is production-ready solely because a completion artifact exists.

## PR / Delivery Metadata Requirements

The validator should verify PR/delivery metadata where available locally in completion artifacts.

Because local validation may not have internet or GitHub API access, do not require live GitHub access in the local runner.

Instead:

- Parse `pull_request_url` from the completion artifact if present.
- Parse branch name from the completion artifact if present.
- Parse merge or commit metadata if present.
- Record `pr_metadata_status = unavailable` when live PR metadata cannot be checked locally.
- Do not fail local validation solely because live GitHub metadata is unavailable.
- Treat missing `pull_request_url` in the completion artifact as a receipt gap.

If the repository already contains a local PR receipt, completion metadata, or merge record, use it.

If not, report the limitation clearly and preserve local-first behavior.

## Production Readiness Gate Requirements

Each work-package validation report must include a production readiness section.

At minimum, the JSON report should include:

```json
{
  "production_readiness": {
    "production_ready": false,
    "blocking_reasons": [],
    "non_blocking_findings": [],
    "required_followups": [],
    "execution_status": "passed",
    "receipt_status": "complete",
    "coverage_status": "covered"
  }
}
```

Rules:

- `failed` execution status blocks production readiness.
- `no_recipe` blocks production readiness.
- missing completion artifact blocks production readiness.
- incomplete required receipt metadata blocks production readiness unless explicitly waived with reason.
- non-blocking observational findings do not automatically block production readiness.
- known blocking limitations block production readiness.
- unknown or unavailable live PR metadata should be a non-blocking finding if the completion artifact has sufficient local receipt data.

The Markdown report must make this readable to a Chief Architect without requiring raw JSON inspection.

## Coverage Manifest Requirements

Create a validation coverage manifest that answers, across merged or completed work packages:

- work package ID
- pending file path if known
- completion artifact path
- receipt status
- recipe status
- latest validation report path
- latest validation status
- production readiness status
- blockers
- required follow-ups

Required outputs:

- `operations/validation/validation_coverage_manifest.md`
- `runtime/validation/validation_coverage_manifest.json`

The manifest must be generated from repository artifacts, not chat memory.

At minimum, it should scan:

- `collaboration/work_packages/completions/`
- `collaboration/work_packages/pending/`
- `operations/validation/reports/`
- `runtime/validation/work_packages/`
- recipe registry in the validation engine

The manifest should gracefully handle old or non-Codex completion artifacts.

The manifest must identify work packages that are:

- validated and production-ready
- validated but not production-ready
- no recipe
- missing receipt
- incomplete receipt
- missing local validation report
- unknown legacy state

Do not require every historical work package to be modernized in WP-0095.

The point is to surface coverage clearly so future validation can operate from facts.

## Production Readiness Report Requirements

Create a production readiness report that summarizes the Estate validation state.

Required outputs:

- `operations/validation/production_readiness_report.md`
- `runtime/validation/production_readiness_report.json`

The report must include:

- generated_at
- git branch
- git commit
- total work packages scanned
- total production-ready
- total blocked
- total missing recipes
- total missing receipts
- total incomplete receipts
- open validation observations
- recent validation reports
- recommended next action
- list of blocking work packages
- list of work packages ready for Chief Architect production-readiness acceptance

## One-Command Runner

Add a PowerShell runner:

`operations/validation/scripts/validate_production_readiness.ps1`

It must:

1. run the production readiness validation locally
2. generate the coverage manifest
3. generate the production readiness report
4. print the report paths
5. not commit or push anything

Expected Steward command:

```powershell
CLS
Set-Location A:\theestate
.\operations\validation\scripts\validate_production_readiness.ps1
```

If a CLI command is added, prefer:

```bash
python -m estate.cli.main validation-production-readiness --json
```

The PowerShell runner may call this CLI command.

## Optional Safe Publish Wrapper

If adding a safe publish wrapper is straightforward, it may be added as:

`operations/validation/scripts/run_and_commit_production_readiness.ps1`

It must follow the same safety principles as the existing validation commit wrapper:

- refuse unrelated local changes
- stage only production readiness validation artifacts
- avoid `git add .`
- push only when explicitly configured

This wrapper is optional. The base one-command runner is required.

## Integration With Existing Work-Package Validation

Extend individual work-package validation reports, if practical, so each report includes:

- receipt validation summary
- completion artifact path
- receipt gaps
- production readiness gate

If this is too large for one safe change, implement production readiness in the aggregate report and document that per-WP report enrichment remains a follow-up.

However, the aggregate production readiness report is required.

## WP-0095 Self-Check Recipe

Add a validation recipe for WP-0095.

It should validate that the final validation loop can run.

Recommended commands:

```bash
python -m estate.cli.main validation-production-readiness --json
python -m estate.cli.main validate-work-package --id WP-0077 --json
python -m estate.cli.main validate-work-package --id WP-0078 --json
```

If command names differ, use the implemented names and document them.

The WP-0095 recipe must not return `no_recipe`.

## Required Tests

Add or update tests for:

- completion artifact receipt parsing
- missing completion artifact detection
- incomplete completion artifact detection
- receipt status calculation
- production readiness true when execution and receipt are sufficient
- production readiness false when execution failed
- production readiness false when no recipe
- production readiness false when receipt missing
- non-blocking findings do not automatically block production readiness
- coverage manifest generation
- production readiness report generation
- WP-0095 recipe registration
- unknown legacy completion artifacts handled gracefully
- existing validation runner tests still pass
- safe wrapper behavior is not weakened

## Demonstration Requirements

Before completion, run or document the equivalent of:

```powershell
.\operations\validation\scripts\validate_production_readiness.ps1
.\operations\validation\scripts\validate_work_package.ps1 -WorkPackageId WP-0095
```

Also run or document the Python CLI equivalent if used.

The completion record must report:

- production readiness report path
- coverage manifest path
- WP-0095 validation status
- any known limitations

## Required Outputs

At completion, these files must exist or be intentionally documented as not applicable:

- `operations/validation/scripts/validate_production_readiness.ps1`
- `operations/validation/production_readiness_report.md`
- `runtime/validation/production_readiness_report.json`
- `operations/validation/validation_coverage_manifest.md`
- `runtime/validation/validation_coverage_manifest.json`
- `collaboration/work_packages/completions/WP-0095_codex_done.json`

If a CLI command is implemented, document the exact command in the completion record.

## Completion Signal

Create:

`collaboration/work_packages/completions/WP-0095_codex_done.json`

using the standard completion schema.

Include:

- `work_package_id`
- `codex_status = done`
- `completed_at`
- `branch`
- `pull_request_url`
- `summary`
- `files_changed`
- `tests_run`
- `known_limitations`
- `ready_for_ca_review = true`
- `merge_authority = ca_verified_auto_merge_allowed`
- exact production readiness command for the Steward
- exact WP-0095 validation command
- generated report paths
- generated manifest paths

## Acceptance Criteria

WP-0095 is complete when:

1. Codex receipt validation exists.
2. Completion artifacts are audited for required fields.
3. Production readiness is explicitly calculated.
4. Blocking reasons are separated from non-blocking findings.
5. A validation coverage manifest is generated from repository artifacts.
6. A production readiness report is generated from repository artifacts.
7. A one-command production readiness PowerShell runner exists.
8. WP-0095 has a registered validation recipe.
9. Existing work-package validation still works.
10. Missing recipes and missing receipts are visible in the manifest instead of discovered ad hoc through chat.
11. The validator remains local-first and does not require live GitHub access.
12. The safe Git behavior established by WP-0079 is preserved.


## WP-0102 Template Retrofit Notice

This section was added by WP-0102 as a mechanical template retrofit. It preserves the original mission and scope above. This pending package remains authored and queued; it is not implemented, validated, operationally validated, approved, or institutionalized by this retrofit.

## Out of Scope

- Do not change the original mission or core scope of WP-0095.
- Do not treat this pending package as already implemented or validated.
- Do not modify `estate_ledger/ledger.md` or `development/devlog.md` unless a future package explicitly authorizes it.
- Do not change governance authority, validation authority, merge authority, or automatic approval behavior.

## Required Behavior

- Execute the original package behavior described above when this package is later implemented.
- Preserve local-first operation unless the Steward explicitly authorizes networked behavior.
- Leave auditable evidence for every check, limitation, and generated artifact.
- Report known limitations explicitly instead of implying production readiness.

## Safety and Authority Constraints

- Do not change governance authority.
- Do not change validation authority.
- Do not automatically approve work packages.
- Do not modify `estate_ledger/ledger.md`.
- Do not modify `development/devlog.md`.
- Do not weaken Git safety behavior.
- Do not stage broad paths.
- Preserve local-first operation unless explicitly authorized.

## Required CLI / Command Surface

Use and preserve the validation command surfaces already named in this package. Do not change validation authority or reserved validation-stream semantics.

## Required Artifacts

- Implement the artifacts already specified by this pending package.
- Create `collaboration/work_packages/completions/WP-0095_codex_done.json`.
- Add or update the registered validation recipe for `WP-0095` unless this file explicitly states that the recipe is not applicable.

## Validation Recipe Requirement

Add or update the validation recipe for WP-0095. The recipe must be registered in the existing validation framework and must not return `no_recipe`. Classify checks as required or observational, use local-first non-destructive commands, and ensure future validation can evaluate this package with:

```bash
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0095 --json
PYTHONPATH=src python -m estate.cli.main validation-production-readiness --json
```

## Codex Completion Receipt Requirement

Create `collaboration/work_packages/completions/WP-0095_codex_done.json` with at least:

- `work_package_id`
- `codex_status`
- `completed_at`
- `branch`
- `pull_request_url` or `pull_request_url_not_applicable_reason`
- `summary`
- `files_changed`
- `tests_run`
- `known_limitations`
- `ready_for_ca_review`
- `merge_authority`
- validation recipe status or not-applicable rationale
- production readiness command status if run
- final command surfaces or Steward commands when applicable

Missing receipt metadata blocks production-readiness status under the WP-0095 validation standard.

## Production Readiness Requirement

This package must remain compatible with the production-readiness validation loop. When practical, run or document the equivalent of:

```bash
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0095 --json
PYTHONPATH=src python -m estate.cli.main validation-production-readiness --json
```

If readiness remains blocked by intentionally pending work, missing external dependencies, or a documented recipe exception, record that limitation in the completion receipt rather than claiming readiness.

## Merge Class

Class A.

Escalate only if implementation changes governance authority, approval authority, merge authority, automatic production approval behavior, or Git safety behavior.
