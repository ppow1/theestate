# SERIES TASK WP-0116 — Sequential Pending Queue Batch Execution Standard

## Codex Command
Read collaboration/work_packages/pending/WP-0116_SERIES_sequential_pending_queue_batch_execution_standard.md and do exactly what it says.

## Mode
SERIES

## Mission
Create the Estate standard and reusable template for executing multiple explicit pending work packages in a single Codex run, sequentially, with individual package receipts, validation results, and one auditable batch report.

This package formalizes the pattern proven by WP-0114 and WP-0115, where Codex successfully operated across many historical work packages in one controlled sweep, and adapts that pattern for future pending implementation work.

## Background
The Estate initially used one work package per Codex run because the early foundation work touched shared code and needed strict sequencing to avoid merge conflicts, hidden dependency failures, and source-of-truth ambiguity.

Recent work demonstrated that Codex can safely operate across many work packages in one run when the task is bounded, the selection criteria are explicit, and results are recorded per package:

- WP-0114 performed a historical production-readiness sweep across many packages.
- WP-0115 performed a historical validation recipe bootstrap sweep across many packages.

Those sweeps were validation and repair oriented, not general implementation. This package creates the next standard: a controlled sequential batch executor model for pending work packages.

The goal is to let the Steward submit one batch instruction such as "execute WP-0120 through WP-0124 in this explicit order" and allow Codex to process them sequentially without requiring the Steward to submit, wait, submit, wait, and submit again.

This is not parallel execution. It is hands-off sequential execution.

This is also not open-ended queue discovery. A batch must name the work packages explicitly. Codex must not decide its own workload by scanning the pending directory or relying on GitHub search for "next pending" decisions.

## Scope
Design and implement the first Estate standard for sequential pending queue batch execution.

The standard must define:

- when a sequential batch is allowed
- when a sequential batch is prohibited
- how the package list is declared
- how execution order is declared
- how stop/continue behavior is declared
- how per-package completion receipts are created or updated
- how per-package validation is run
- how a batch-level report is created
- how failure, skipped packages, and partial completion are represented
- how batch execution differs from SERIES and PARALLEL-STAGED work
- how future batch work packages or manifests should be authored

## Out of Scope
Do not implement or execute a real batch of future pending packages in WP-0116.

Do not convert existing pending work packages into batch mode automatically.

Do not permit Codex to choose arbitrary pending packages by scanning GitHub or the pending directory.

Do not replace WP-0112 parallel workstream isolation and install handoff.

Do not implement autonomous scheduling or unattended repository mutation beyond the explicit batch instruction pattern.

Do not change merge authority, Steward authority, Chief Architect authority, Resident authority, validation authority, or production-readiness meaning.

Do not weaken completion receipt requirements, validation recipe requirements, or production-readiness requirements.

Do not edit estate_ledger/ledger.md or development/devlog.md unless current repository standards require it.

## Required Behavior
Create a durable standard or operational document that future pending work packages can reference when they should be submitted as a batch.

The document should cover at least the following concepts.

### 1. Execution Mode Definitions
Define execution modes including at least:

- SERIES — one work package per run; appropriate for high-risk, shared-file, or architecturally uncertain work.
- SEQUENTIAL-BATCH — multiple explicit work packages executed in one Codex run, one after another, with per-package receipts and validation.
- PARALLEL-STAGED — parallel-safe staged work as defined by WP-0112, using isolated workstreams and install handoff.
- INSTALL-HANDOFF — review/install step for staged work.

State clearly that SEQUENTIAL-BATCH is not parallel execution.

### 2. Batch Manifest Requirement
Define a batch manifest/template that future batch submissions must use.

The manifest must include:

- batch ID
- title
- author/requesting office
- purpose
- package list
- explicit execution order
- stop policy
- branch/PR expectation
- validation expectation
- production-readiness expectation
- per-package receipt requirement
- batch report requirement
- known dependency assumptions
- expected conflict surfaces
- packages intentionally excluded
- rollback/recovery notes
- authority constraints

The standard should recommend a repository location for batch manifests. Possible locations may include:

- collaboration/work_packages/batches/
- collaboration/batches/
- operations/batches/

Choose a location consistent with existing repository conventions.

### 3. Explicit Package List Rule
Require every sequential batch to name the exact packages it may execute.

Codex must not interpret instructions such as:

- execute the next 10 pending packages
- scan pending and run what looks ready
- choose packages until blocked

unless those instructions are backed by a generated manifest that lists exact IDs before execution begins.

If a batch refers to a range such as WP-0120 through WP-0124, the range must be expanded into an explicit list in the batch manifest before implementation begins.

### 4. Stop Policy
Define allowed stop policies, such as:

- stop_on_first_failure
- stop_on_blocking_failure
- continue_on_non_blocking_failure
- validate_only_after_each_package
- validate_after_batch_only, if explicitly justified

The default should be stop_on_blocking_failure.

A blocking failure should include at least:

- pending file missing
- package instructions ambiguous
- unsafe or unauthorized behavior required
- tests fail in a way that invalidates subsequent packages
- validation cannot run for a required package
- implementation would require changing authority or scope beyond the package
- merge conflict or file collision that cannot be resolved mechanically

### 5. Per-Package Execution Contract
For each package in the batch, Codex must:

1. Read the exact pending work package file.
2. Execute only that package's instructions.
3. Preserve package scope and authority constraints.
4. Create or update that package's completion receipt.
5. Run required tests or document justified limitations.
6. Run or register package validation as required.
7. Record status in the batch report before moving to the next package.

A package is not considered complete merely because the batch completed.

### 6. Batch Report Contract
Define required batch reports:

- human-readable report
- machine-readable JSON report

Recommended paths:

- operations/validation/batch_reports/BATCH-XXXX_report.md
- runtime/validation/batch_reports/BATCH-XXXX_report.json

The batch report must include:

- batch ID
- packages requested
- packages attempted
- packages completed
- packages failed
- packages skipped
- packages not attempted
- stop policy applied
- failure reason for each failed/skipped package
- per-package completion receipt paths
- validation commands run
- tests run
- production-readiness status before and after, if run
- generated artifacts changed
- known limitations
- final recommendation for Chief Architect review

### 7. Template for Future Batch Packages
Create a reusable template for future sequential pending queue batch work packages.

The template should be suitable for packages such as:

- BATCH-0001 — Execute WP-0120 through WP-0124
- BATCH-0002 — Execute WP-0125 through WP-0129
- BATCH-0003 — Execute selected resident runtime follow-up packages

The template must make it easy for the Steward or Chief Architect to paste in a package list and stop policy.

### 8. Relationship to WP-0112
State that WP-0116 complements WP-0112.

WP-0112 governs parallel staged work and install handoff.
WP-0116 governs hands-off sequential execution of explicit pending package lists.

A package may be batched only if its own instructions and conflict surfaces make sequential execution appropriate. If the package requires parallel staging or install handoff, it should follow WP-0112 instead.

### 9. Safety Boundaries
Sequential batch execution must preserve all existing authority boundaries.

The standard must explicitly prohibit:

- autonomous selection of unlisted packages
- broad implementation beyond listed packages
- marking unattempted packages complete
- suppressing individual package failures
- fabricating completion receipts
- skipping required validation silently
- using batch success as a substitute for per-package evidence
- bypassing Chief Architect review or Steward merge authority

## Required CLI / Command Surface
If repository tooling supports it, add a small local command surface for inspecting batch manifests and reports. Acceptable commands may include:

```bash
PYTHONPATH=src python -m estate.cli.main batch-manifest inspect --id BATCH-XXXX --json
PYTHONPATH=src python -m estate.cli.main batch-manifest validate --id BATCH-XXXX --json
```

If adding CLI support is too large for WP-0116, document the commands as future work and provide manual validation rules instead.

## Required Artifacts
Expected artifacts may include:

- durable sequential batch execution standard document
- reusable batch manifest template
- optional JSON schema or example manifest
- optional CLI inspection/validation support
- tests if code or schema is added
- validation recipe for WP-0116
- `collaboration/work_packages/completions/WP-0116_codex_done.json`

Recommended document paths:

- `docs/operations/Sequential_Pending_Queue_Batch_Execution_Standard_v1.md`
- `docs/templates/Sequential_Batch_Work_Package_Template.md` or another existing template location if more appropriate

## Required Tests
Add or update tests for any implemented code, schema, or validation recipe.

At minimum, verify:

- WP-0116 validation recipe is registered and does not return no_recipe
- the standard document exists
- the batch template exists
- the template requires an explicit package list
- the template requires stop policy
- the template requires per-package receipts
- the template requires batch report output
- the template prohibits autonomous pending queue discovery
- production-readiness generation still works

Run existing validation tests if relevant:

```bash
PYTHONPATH=src pytest tests/test_work_package_validation.py tests/test_production_readiness_validation.py -q
```

Add targeted tests if new helper modules or CLI surfaces are introduced.

## Required Validation Commands
Run or document equivalent:

```bash
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0116 --json
PYTHONPATH=src python -m estate.cli.main validation-production-readiness --json
```

If CLI batch-manifest support is implemented, also run:

```bash
PYTHONPATH=src python -m estate.cli.main batch-manifest validate --id EXAMPLE --json
```

## Required Outputs
Update or create as applicable:

- `docs/operations/Sequential_Pending_Queue_Batch_Execution_Standard_v1.md`
- `docs/templates/Sequential_Batch_Work_Package_Template.md` or equivalent existing template path
- optional schema/example manifest
- optional CLI implementation files
- relevant tests
- validation report for WP-0116 under `operations/validation/reports/`
- runtime validation JSON for WP-0116 under `runtime/validation/work_packages/`
- updated production-readiness artifacts if required
- `collaboration/work_packages/completions/WP-0116_codex_done.json`

## WP-0116 Self-Validation Recipe
Add a recipe for WP-0116 that verifies:

- the standard document exists
- the template exists
- the standard distinguishes SERIES, SEQUENTIAL-BATCH, PARALLEL-STAGED, and INSTALL-HANDOFF
- the template requires an explicit package list
- the template prohibits open-ended pending queue discovery
- the template requires per-package completion receipts
- the template requires a batch report
- the template requires a stop policy
- the template preserves authority boundaries
- WP-0116 completion receipt is complete

Use cross-platform Python checks only.

## Completion Artifact
Create:

`collaboration/work_packages/completions/WP-0116_codex_done.json`

It must include:

- `work_package_id = WP-0116`
- `codex_status = done`
- `completed_at`
- `branch`
- `pull_request_url` or `pull_request_url_not_applicable_reason`
- `summary`
- standard document path
- template path
- CLI command surface or not-applicable reason
- files changed
- tests run
- validation commands run
- known limitations
- `ready_for_ca_review = true`
- `merge_authority = ca_verified_auto_merge_allowed`

## Acceptance Criteria
WP-0116 is complete when:

1. A durable sequential pending queue batch execution standard exists.
2. A reusable batch work package or manifest template exists.
3. The standard requires explicit package lists and prohibits autonomous discovery of pending workload.
4. The standard requires per-package receipts and validation evidence.
5. The standard requires one auditable batch report.
6. The standard clearly distinguishes SEQUENTIAL-BATCH from SERIES and PARALLEL-STAGED.
7. WP-0116 has its own validation recipe and completion receipt.
8. Production-readiness validation can evaluate WP-0116.

## Merge Class
Class A if this package creates standards, templates, schemas, tests, or non-invasive inspection tooling only.

Escalate to Class B if it changes execution authority, merge authority, validation semantics, production-readiness semantics, or permits autonomous package selection/execution beyond an explicit batch manifest.
