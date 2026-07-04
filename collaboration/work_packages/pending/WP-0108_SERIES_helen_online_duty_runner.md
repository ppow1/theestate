# SERIES TASK WP-0108 — Helen Online Duty Runner

## Codex Command
Read `collaboration/work_packages/pending/WP-0108_SERIES_helen_online_duty_runner.md` and do exactly what it says.

## Mode
SERIES

## Mission
Create Helen's first local online duty runner so Helen can appear and operate as an Estate resident service with bounded HR/onboarding duties, visible runtime state, mailbox awareness, and Operations Center presence.

## Background
The Estate has already created the Steward Command Center skeleton, Resident Card framework, Resident Conversations workspace, and the Resident Runtime Presence Model in WP-0106. Alfred's online duty runner begins the coordination-resident path in WP-0107. Helen now needs a bounded duty runner for personnel-facing onboarding and HR-adjacent operational visibility.

Helen's purpose is not to become a governance authority. Bringing Helen online means making her operationally visible and duty-aware for defined HR/onboarding functions while preserving Steward authority, personnel boundaries, mailbox source-of-truth rules, and future auditability.

## Scope
Implement a local-first Helen duty runner that builds on the resident presence model from WP-0106.

The runner should support, at minimum:

- loading Helen's resident identity and mailbox linkage from existing Estate artifacts where available
- updating Helen's runtime presence state
- reporting Helen as online, degraded, blocked, or offline based on local checks
- inspecting Helen-relevant institutional inputs such as onboarding manifests, personnel identity artifacts, mailbox artifacts, resident cards, Chief Architect onboarding references, HR-related work packages, or other existing local sources
- producing a bounded duty summary suitable for Operations Center display
- identifying whether Helen needs Steward attention
- recording source artifact references used in the duty run
- exposing local CLI or repo-native command access for running or inspecting Helen duty status

## Out of Scope
Do not implement unrestricted autonomous HR action.

Do not allow Helen to create, approve, terminate, or modify personnel identities without explicit future authority and validation.

Do not allow Helen to approve, merge, validate, or institutionalize work.

Do not allow Helen to execute work packages automatically.

Do not implement Alfred's duty runner in this package.

Do not implement a general resident conversation engine in this package.

Do not require cloud services, external authentication, or internet access.

Do not create a new mailbox system, personnel registry, governance authority, or validation authority.

Do not edit `estate_ledger/ledger.md` or `development/devlog.md`.

## Required Behavior
- Helen can be brought online locally through a safe command or service runner.
- Helen presence integrates with the resident runtime presence model.
- Helen's Resident Card and Operations Center surfaces can display duty-run status where available.
- Helen's duty runner must degrade gracefully when optional source artifacts are missing.
- Helen must distinguish informational findings from actions requiring Steward attention.
- Helen must preserve source-of-truth boundaries: summaries are operational views, not canonical authority.
- Helen must leave a local auditable record of duty runs or duty state sufficient for validation.
- Helen must treat onboarding/personnel-related data as sensitive institutional context and avoid broad disclosure or mutation.

## Safety and Authority Constraints
- Helen may summarize onboarding/personnel operational state; Helen may not authorize personnel changes.
- Helen may identify onboarding blockers; Helen may not complete onboarding by assertion.
- Helen may surface HR-related artifacts; Helen may not create new HR governance.
- Helen may point to work packages; Helen may not execute them automatically.
- Do not store secrets.
- Do not send external notifications unless an existing authorized local notification path explicitly supports it and this package only integrates non-destructively.
- Preserve local-first operation.
- Do not stage broad paths.

## Required CLI / Command Surface
Add or reuse local command surfaces consistent with existing Estate CLI conventions. Acceptable commands may include:

```bash
PYTHONPATH=src python -m estate.cli.main helen-duty --json
PYTHONPATH=src python -m estate.cli.main resident-duty --resident Helen --json
PYTHONPATH=src python -m estate.cli.main resident-presence --resident Helen --json
```

Use existing command names if the repository already defines a better convention. Document the final command surface in the completion receipt.

## Required Artifacts
Expected artifacts may include:

- Helen duty runner module
- runtime Helen duty state JSON or equivalent local state artifact
- integration with resident presence state
- integration with Resident Card or Operations Center surfaces where appropriate
- tests for Helen duty execution, missing-artifact degradation, presence updates, and CLI output
- validation recipe for WP-0108
- `collaboration/work_packages/completions/WP-0108_codex_done.json`

## Tests
Verify:

- Helen duty runner can execute locally without internet access.
- Helen presence updates from the duty runner.
- Missing mailbox, onboarding, personnel, or HR artifacts degrade gracefully.
- Duty summary includes source artifact references.
- Needs-Steward state is set only when supported by local evidence.
- CLI JSON output is valid.
- Operations Center or Resident Card integration displays Helen duty status if those surfaces are present.
- No governance, validation, merge, personnel, HR, or Steward authority is changed.

## Validation Recipe Requirement
Add or update the validation recipe for WP-0108. The recipe must be registered in the existing validation framework and must not return `no_recipe`. Classify checks as required or observational, use local-first non-destructive commands, and ensure this package can be evaluated by:

```bash
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0108 --json
PYTHONPATH=src python -m estate.cli.main validation-production-readiness --json
```

## Codex Completion Receipt Requirement
Create `collaboration/work_packages/completions/WP-0108_codex_done.json` with at least:

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
- final Helen duty command surface
- source artifacts inspected by the duty runner
- explicit authority limitations

## Production Readiness Requirement
Run or document the equivalent of:

```bash
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0108 --json
PYTHONPATH=src python -m estate.cli.main validation-production-readiness --json
```

If production readiness remains blocked by downstream resident conversation session, action authorization, or service orchestration work, record that as an expected limitation rather than claiming Helen is fully autonomous.

## Demonstration Requirements
Document exact commands run and observed status. Include sample Helen duty JSON output where practical, including presence status, duty summary, source artifact references, and needs-Steward state.

## Completion Signal
Create `collaboration/work_packages/completions/WP-0108_codex_done.json` using the standard completion schema.

Set `ready_for_ca_review=true` only if tests, receipt metadata, validation recipe status, and production-readiness obligations are satisfied or explicitly documented with limitations.

## Merge Class
Class A unless Helen authority, personnel authority, Steward decision authority, mailbox authority, validation authority, or automatic action semantics are changed; escalate to Class B if those semantics are altered.
