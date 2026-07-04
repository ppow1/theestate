# SERIES TASK WP-0101 — Codex Task Template Standard

## Codex Command

Read `collaboration/work_packages/pending/WP-0101_SERIES_codex_task_template_standard.md` and do exactly what it says.

## Mode

SERIES

## Mission

Define and finalize the Estate's standard Codex task template so all future implementation work packages include the evidence needed for production-readiness validation.

This package does not retrofit existing work packages. It creates the approved template that WP-0102 or a later mechanical retrofit package can apply to pending work packages.

## Background

The Estate now has a production-readiness validation loop that audits:

- Codex completion receipts
- local validation recipes
- validation reports
- production readiness gates
- coverage manifest status

The production-readiness report exposed a process gap: many earlier work packages had implementation-time testing and completion records, but they did not consistently require reusable validation recipes or complete receipt metadata.

Going forward, every Codex implementation work package must include its own validation and receipt requirements so production-readiness review does not require after-the-fact reconstruction.

## Scope

Create a standard Codex task template for future Estate work packages.

The template must require:

1. implementation instructions
2. safety constraints
3. tests
4. Codex completion receipt
5. validation recipe registration
6. production-readiness compatibility
7. generated artifact handling
8. explicit known limitations
9. final Steward/Codex command surfaces when applicable

Do not rewrite the backlog in this package.

Do not edit pending work packages WP-0086 through WP-0100 in this package except to reference them as future retrofit targets.

Do not redesign the validation runner.

Do not change governance authority, merge authority, or approval authority.

## Required Output

Create or update a durable template document such as:

`docs/operations/Codex_Task_Template_Standard_v1.md`

If an existing better location already exists for Codex handoff standards, use that location and document the choice in the completion artifact.

The standard must be discoverable through the document registry or search if that pattern exists for similar operational standards.

## Required Template Sections

The approved template must include these sections or clear equivalents:

### Title

Format:

`# SERIES TASK WP-XXXX — <Title>`

### Codex Command

Required wording:

`Read <path> and do exactly what it says.`

### Mode

Specify whether the package is SERIES, ARCHITECTURE_FIRST, remediation, documentation-only, or another existing mode.

### Mission

State the single operational mission.

### Background

Summarize why the work exists and what prior artifacts it depends on.

### Scope

Define what must be changed.

### Out of Scope

Define what must not be changed.

### Required Behavior

List required behavior in observable terms.

### Safety and Authority Constraints

Must include, where applicable:

- do not change governance authority
- do not change validation authority
- do not automatically approve work packages
- do not modify `estate_ledger/ledger.md`
- do not modify `development/devlog.md`
- do not weaken Git safety behavior
- do not stage broad paths
- preserve local-first operation unless explicitly authorized

### Required CLI / Command Surface

If the package creates or changes commands, specify expected command names and acceptable alternatives.

### Required Artifacts

List expected files and runtime outputs.

### Tests

Require unit tests, integration checks, and CLI smoke checks as appropriate.

### Validation Recipe Requirement

Every implementation work package must include or update a validation recipe unless explicitly marked documentation-only or not applicable.

The template must require wording equivalent to:

```text
Add or update the validation recipe for this work package.
The recipe must be registered in the existing validation framework.
The recipe must not return no_recipe.
Classify checks as required or observational.
Use local-first, non-destructive commands.
Ensure the work package can be evaluated by:
python -m estate.cli.main validate-work-package --id WP-XXXX --json
Ensure production readiness can be evaluated by:
python -m estate.cli.main validation-production-readiness --json
```

### Codex Completion Receipt Requirement

The template must require creation of:

`collaboration/work_packages/completions/WP-XXXX_codex_done.json`

with at least:

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
- final command surfaces or Steward commands when applicable
- validation recipe status
- production readiness command status if run

The template must explain that missing receipt metadata blocks production-readiness status under the WP-0095 validation standard.

### Production Readiness Requirement

The template must require compatibility with the production-readiness validation loop.

It must require Codex to run or document equivalent of:

```bash
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-XXXX --json
PYTHONPATH=src python -m estate.cli.main validation-production-readiness --json
```

If the package is documentation-only and no recipe is applicable, the package must explicitly document why and provide a receipt field marking validation recipe as not applicable.

### Demonstration Requirements

Require Codex to document the exact commands run and observed status.

### Completion Signal

Require the completion artifact and state that `ready_for_ca_review=true` is only valid when required tests, receipt, and validation recipe obligations have been satisfied or explicitly waived with reason.

### Merge Class

Require merge class and escalation triggers.

## Required Policy Decisions

The standard must answer these questions directly:

1. Are validation recipes required for all implementation work packages? Yes, unless explicitly not applicable.
2. Are completion receipts required? Yes.
3. Is Codex implementation-time testing sufficient by itself for production readiness? No.
4. Must reusable local validation be left behind? Yes, for implementation work.
5. Must production readiness be checked by the WP-0095 loop? Yes, when practical.
6. Can documentation-only packages omit recipes? Yes, only with explicit not-applicable rationale.
7. Can live GitHub metadata be required for local validation? No, the validation loop remains local-first.

## Tests / Verification

Add tests only if there is existing machinery for validating standards or document registry entries.

At minimum, run or document a search/check proving the new template standard exists and is discoverable.

Recommended checks:

```bash
PYTHONPATH=src python -m estate.cli.main document-registry --json
PYTHONPATH=src python -m estate.cli.main estate-search "Codex Task Template" --json
PYTHONPATH=src python -m estate.cli.main validation-production-readiness --json
```

Use actual available commands if names differ.

## Completion Signal

Create:

`collaboration/work_packages/completions/WP-0101_codex_done.json`

using the standard completion schema.

Include:

- `work_package_id`
- `codex_status = done`
- `completed_at`
- `branch`
- `pull_request_url` or `pull_request_url_not_applicable_reason`
- `summary`
- `files_changed`
- `tests_run`
- `known_limitations`
- `ready_for_ca_review = true`
- `merge_authority = ca_verified_auto_merge_allowed`
- path to the approved template standard
- whether a validation recipe was added or why it is not applicable
- production-readiness command status if run

## Acceptance Criteria

WP-0101 is complete when:

1. A durable Codex task template standard exists.
2. The template requires complete Codex receipts.
3. The template requires validation recipes for implementation work packages.
4. The template distinguishes implementation-time tests from reusable local validation.
5. The template states that production readiness is evaluated through the WP-0095 loop.
6. Documentation-only exceptions are explicit and auditable.
7. The template is discoverable through existing Estate search or registry mechanisms where practical.
8. The completion artifact records the template path and any limitations.
9. No backlog retrofit is performed in this package.

## Merge Class

Class A.

Escalate only if implementation changes governance authority, validation authority, merge authority, or automatic approval behavior.
