# SERIES TASK WP-0107 — Alfred Online Duty Runner

## Codex Command
Read `collaboration/work_packages/pending/WP-0107_SERIES_alfred_online_duty_runner.md` and do exactly what it says.

## Mode
SERIES

## Mission
Create Alfred's first local online duty runner so Alfred can appear and operate as an Estate resident service with bounded duties, visible runtime state, mailbox awareness, and Operations Center presence.

## Background
The Estate has already created the Steward Command Center skeleton, Resident Card framework, Resident Conversations workspace, and the Resident Runtime Presence Model in WP-0106. Alfred now needs a bounded duty runner that can update his presence, inspect assigned local institutional inputs, and surface actionable operational summaries without becoming an autonomous governance authority.

Alfred is the Estate's coordination and chief-of-staff resident surface. Bringing Alfred online means making him operationally visible and duty-aware, not granting him unrestricted authority or external agency.

## Scope
Implement a local-first Alfred duty runner that builds on the resident presence model from WP-0106.

The runner should support, at minimum:

- loading Alfred's resident identity and mailbox linkage from existing Estate artifacts where available
- updating Alfred's runtime presence state
- reporting Alfred as online, degraded, blocked, or offline based on local checks
- inspecting Alfred-relevant institutional inputs such as mailbox artifacts, work package state, decision queue artifacts, validation/readiness summaries, operations board artifacts, or other existing local sources
- producing a bounded duty summary suitable for Operations Center display
- identifying whether Alfred needs Steward attention
- recording source artifact references used in the duty run
- exposing local CLI or repo-native command access for running or inspecting Alfred duty status

## Out of Scope
Do not implement unrestricted autonomous action.

Do not allow Alfred to approve, merge, validate, or institutionalize work.

Do not allow Alfred to execute work packages automatically.

Do not implement Helen's duty runner in this package.

Do not implement a general resident conversation engine in this package.

Do not require cloud services, external authentication, or internet access.

Do not create a new mailbox system, personnel registry, governance authority, or validation authority.

Do not edit `estate_ledger/ledger.md` or `development/devlog.md`.

## Required Behavior
- Alfred can be brought online locally through a safe command or service runner.
- Alfred presence integrates with the resident runtime presence model.
- Alfred's Resident Card and Operations Center surfaces can display duty-run status where available.
- Alfred's duty runner must degrade gracefully when optional source artifacts are missing.
- Alfred must distinguish informational findings from actions requiring Steward attention.
- Alfred must preserve source-of-truth boundaries: summaries are operational views, not canonical authority.
- Alfred must leave a local auditable record of duty runs or duty state sufficient for validation.

## Safety and Authority Constraints
- Alfred may summarize and route; Alfred may not authorize.
- Alfred may identify decisions; Alfred may not make Steward decisions.
- Alfred may surface validation blockers; Alfred may not declare production readiness without validation artifacts.
- Alfred may point to work packages; Alfred may not execute them automatically.
- Do not store secrets.
- Do not send external notifications unless an existing authorized local notification path explicitly supports it and this package only integrates non-destructively.
- Preserve local-first operation.
- Do not stage broad paths.

## Required CLI / Command Surface
Add or reuse local command surfaces consistent with existing Estate CLI conventions. Acceptable commands may include:

```bash
PYTHONPATH=src python -m estate.cli.main alfred-duty --json
PYTHONPATH=src python -m estate.cli.main resident-duty --resident Alfred --json
PYTHONPATH=src python -m estate.cli.main resident-presence --resident Alfred --json
```

Use existing command names if the repository already defines a better convention. Document the final command surface in the completion receipt.

## Required Artifacts
Expected artifacts may include:

- Alfred duty runner module
- runtime Alfred duty state JSON or equivalent local state artifact
- integration with resident presence state
- integration with Resident Card or Operations Center surfaces where appropriate
- tests for Alfred duty execution, missing-artifact degradation, presence updates, and CLI output
- validation recipe for WP-0107
- `collaboration/work_packages/completions/WP-0107_codex_done.json`

## Tests
Verify:

- Alfred duty runner can execute locally without internet access.
- Alfred presence updates from the duty runner.
- Missing mailbox, decision queue, or operations artifacts degrade gracefully.
- Duty summary includes source artifact references.
- Needs-Steward state is set only when supported by local evidence.
- CLI JSON output is valid.
- Operations Center or Resident Card integration displays Alfred duty status if those surfaces are present.
- No governance, validation, merge, or Steward authority is changed.

## Validation Recipe Requirement
Add or update the validation recipe for WP-0107. The recipe must be registered in the existing validation framework and must not return `no_recipe`. Classify checks as required or observational, use local-first non-destructive commands, and ensure this package can be evaluated by:

```bash
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0107 --json
PYTHONPATH=src python -m estate.cli.main validation-production-readiness --json
```

## Codex Completion Receipt Requirement
Create `collaboration/work_packages/completions/WP-0107_codex_done.json` with at least:

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
- `validation_recipe_status`
- `production_readiness_command_status` if run
- final Alfred duty command surface
- source artifacts inspected by the duty runner
- explicit authority limitations

## Production Readiness Requirement
Run or document the equivalent of:

```bash
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0107 --json
PYTHONPATH=src python -m estate.cli.main validation-production-readiness --json
```

If production readiness remains blocked by downstream resident conversation session, action authorization, or service orchestration work, record that as an expected limitation rather than claiming Alfred is fully autonomous.

## Demonstration Requirements
Document exact commands run and observed status. Include sample Alfred duty JSON output where practical, including presence status, duty summary, source artifact references, and needs-Steward state.

## Completion Signal
Create `collaboration/work_packages/completions/WP-0107_codex_done.json` using the standard completion schema.

Set `ready_for_ca_review=true` only if tests, receipt metadata, validation recipe status, and production-readiness obligations are satisfied or explicitly documented with limitations.

## Merge Class
Class A unless Alfred authority, Steward decision authority, mailbox authority, validation authority, or automatic action semantics are changed; escalate to Class B if those semantics are altered.
