# Codex Task Template Standard v1

## Purpose

This standard defines the required structure for future Estate Codex implementation work packages. Its purpose is to ensure each package leaves enough implementation evidence, reusable validation, and completion metadata for production-readiness review under the WP-0095 validation loop.

This standard applies prospectively. It does not retrofit existing work packages. Pending work packages WP-0086 through WP-0100 may be retrofitted by WP-0102 or a later mechanical retrofit package.

## Required Policy Decisions

1. Validation recipes are required for all implementation work packages unless explicitly not applicable.
2. Completion receipts are required for all Codex work packages.
3. Codex implementation-time testing is not sufficient by itself for production readiness.
4. Reusable local validation must be left behind for implementation work.
5. Production readiness must be checked by the WP-0095 loop when practical.
6. Documentation-only packages may omit validation recipes only with explicit not-applicable rationale.
7. Live GitHub metadata must not be required for local validation; the validation loop remains local-first.

## Standard Work Package Template

Use this template for future Codex implementation work packages.

```markdown
# SERIES TASK WP-XXXX — <Title>

## Codex Command

Read `<path>` and do exactly what it says.

## Mode

Specify the package mode: SERIES, ARCHITECTURE_FIRST, remediation, documentation-only, or another existing Estate mode.

## Mission

State the single operational mission in one or two sentences.

## Background

Summarize why the work exists and identify prior artifacts, decisions, standards, work packages, validation reports, or runtime outputs the work depends on.

## Scope

Define the files, behavior, commands, documents, tests, recipes, or artifacts that must be changed.

## Out of Scope

Define what must not be changed. Include explicit exclusions for backlog retrofits, governance changes, validation-runner redesigns, authority changes, or unrelated refactors when applicable.

## Required Behavior

List the required behavior in observable terms. Each item should be testable by reading an artifact, invoking a CLI command, running a local check, or inspecting a completion receipt.

## Safety and Authority Constraints

Include all applicable constraints:

- Do not change governance authority.
- Do not change validation authority.
- Do not automatically approve work packages.
- Do not modify `estate_ledger/ledger.md`.
- Do not modify `development/devlog.md`.
- Do not weaken Git safety behavior.
- Do not stage broad paths.
- Preserve local-first operation unless explicitly authorized.
- Do not require live GitHub metadata for local validation.
- Do not change merge authority or approval authority.

## Required CLI / Command Surface

If the package creates or changes commands, specify expected command names, options, JSON fields, stdout behavior, and acceptable alternatives. If no command surface is expected, state that explicitly.

## Required Artifacts

List expected files and runtime outputs, including durable documents, schemas, generated runtime artifacts, validation reports, completion receipts, and any generated files that must be ignored, regenerated, or reviewed.

## Generated Artifact Handling

State which outputs are canonical source artifacts and which are generated projections. For generated artifacts, specify the command that regenerates them, whether they may be committed, and how provenance or freshness is represented.

## Tests

Require unit tests, integration checks, and CLI smoke checks as appropriate. The package must distinguish implementation-time tests from reusable validation recipes. Implementation-time tests prove the current patch; reusable validation recipes allow future production-readiness evaluation.

## Validation Recipe Requirement

Add or update the validation recipe for this work package.
The recipe must be registered in the existing validation framework.
The recipe must not return `no_recipe`.
Classify checks as required or observational.
Use local-first, non-destructive commands.
Ensure the work package can be evaluated by:

```bash
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-XXXX --json
```

Ensure production readiness can be evaluated by:

```bash
PYTHONPATH=src python -m estate.cli.main validation-production-readiness --json
```

Documentation-only or otherwise non-applicable packages may omit a validation recipe only when they explicitly document the rationale and include a completion-receipt field marking the validation recipe as not applicable.

## Codex Completion Receipt Requirement

Create `collaboration/work_packages/completions/WP-XXXX_codex_done.json` before completion. The receipt must include at least:

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

Missing receipt metadata blocks production-readiness status under the WP-0095 validation standard.

## Production Readiness Requirement

The work must be compatible with the production-readiness validation loop. Run or document the equivalent of:

```bash
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-XXXX --json
PYTHONPATH=src python -m estate.cli.main validation-production-readiness --json
```

If the package is documentation-only and no recipe is applicable, explicitly document why and provide a receipt field marking validation recipe as not applicable.

## Demonstration Requirements

Document exact commands run, whether each command passed, failed, or was skipped, and the observed status or reason. Include CLI smoke output paths or JSON report paths when applicable.

## Explicit Known Limitations

List all known limitations. If there are none, state `None known`. Limitations must be auditable in the completion receipt.

## Final Steward/Codex Command Surfaces

When applicable, list final commands that the Steward, Chief Architect, or future Codex workers should run. Include command names, arguments, environment variables, and expected outputs. If no final command surface applies, state that explicitly.

## Completion Signal

The package is complete only when the completion artifact exists and required tests, receipt obligations, validation recipe obligations, and production-readiness compatibility checks have been satisfied or explicitly waived with a reason. `ready_for_ca_review=true` is valid only after those requirements are met.

## Merge Class

State the merge class and escalation triggers. Escalate if implementation changes governance authority, validation authority, merge authority, approval behavior, Git safety behavior, or local-first validation assumptions.
```

## Discoverability

This standard is registered in the Estate document registry as `DOC-CODEX-TASK-TEMPLATE-STANDARD` and is discoverable through local document-registry and Estate search commands.
