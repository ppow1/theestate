# SERIES TASK WP-0110 — Resident Action Authority Boundary

## Codex Command
Read `collaboration/work_packages/pending/WP-0110_SERIES_resident_action_authority_boundary.md` and do exactly what it says.

## Mode
SERIES

## Mission
Create the Resident Action Authority Boundary so Alfred, Helen, and future Estate residents can come online with explicit, enforceable limits on what they may observe, summarize, propose, request, draft, route, and execute.

## Background
WP-0106 establishes resident runtime presence. WP-0107 brings Alfred online as a bounded coordination resident. WP-0108 brings Helen online as a bounded onboarding/HR-adjacent resident. WP-0109 creates resident conversation sessions and audit trails while explicitly avoiding making conversations authoritative by themselves.

The Estate now needs a durable authority boundary that separates resident visibility and conversation from resident authority. Standing up Alfred and Helen safely requires more than resident presence and duty summaries; it requires a local, auditable rule layer that prevents residents from accidentally gaining governance, validation, merge, personnel, or execution authority merely because they are online.

## Scope
Implement a local-first Resident Action Authority Boundary for Alfred, Helen, and future residents.

The boundary should support, at minimum:

- resident identity
- requested action category
- action target or artifact path where applicable
- authority classification
- whether the action is allowed, denied, requires Steward approval, or requires escalation
- reason for the decision
- source artifact references
- audit record generation
- integration points for resident duty runners and conversation sessions

Define action categories such as:

- observe
- summarize
- search
- draft
- propose
- route
- request Steward decision
- create work package draft
- update resident runtime state
- send mailbox/message artifact
- run validation command
- execute work package
- approve/merge work
- modify personnel identity
- modify governance artifact
- external notification or network action

The exact categories may be refined to fit existing Estate conventions, but the package must make clear which actions are non-authoritative, which require approval, and which are denied to residents.

## Out of Scope
Do not grant Alfred or Helen new authority.

Do not implement unrestricted autonomous action.

Do not implement automatic work package execution.

Do not allow residents to approve, merge, validate, institutionalize, hire, terminate, or modify governance by default.

Do not introduce cloud services, external identity providers, or internet-dependent authorization.

Do not create a new governance system if existing governance artifacts can define or constrain the boundary.

Do not edit `estate_ledger/ledger.md` or `development/devlog.md`.

## Required Behavior
- Provide a reusable authority-check function or module for resident actions.
- Make the default behavior safe: unknown action categories must be denied or require Steward approval, not allowed silently.
- Alfred and Helen must have explicit allowed and denied action categories.
- Duty runners should be able to consult the boundary before surfacing or attempting actions.
- Conversation sessions should label outcomes according to the boundary.
- Boundary decisions must be locally auditable.
- The Operations Center should be able to display clear authority status or limitations where practical.
- Preserve source-of-truth boundaries: the authority boundary records operational permission checks, not constitutional authority changes.

## Safety and Authority Constraints
- Resident online status does not imply resident authority.
- Resident conversation does not imply Steward approval.
- Resident duty summaries do not imply validation success.
- Resident action proposals do not imply execution authority.
- Unknown or ambiguous actions must not proceed automatically.
- Preserve local-first operation.
- Do not store secrets.
- Do not broad-stage generated artifacts.

## Required CLI / Command Surface
Add or reuse local command surfaces consistent with existing Estate CLI conventions. Acceptable commands may include:

```bash
PYTHONPATH=src python -m estate.cli.main resident-authority check --resident Alfred --action summarize --json
PYTHONPATH=src python -m estate.cli.main resident-authority check --resident Helen --action modify-personnel --json
PYTHONPATH=src python -m estate.cli.main resident-authority list --resident Alfred --json
```

Use existing command names if the repository already defines a better convention. Document the final command surface in the completion receipt.

## Required Artifacts
Expected artifacts may include:

- resident authority boundary module
- resident action category definitions
- local audit record shape or storage path for authority decisions
- integration with Alfred duty runner where available
- integration with Helen duty runner where available
- integration with resident conversation session outcomes where available
- tests for allowed, denied, unknown, and approval-required actions
- validation recipe for WP-0110
- `collaboration/work_packages/completions/WP-0110_codex_done.json`

## Tests
Verify:

- Alfred can observe, summarize, route, and request Steward attention where allowed.
- Alfred cannot approve, merge, validate, institutionalize, or execute work packages automatically.
- Helen can observe and summarize onboarding/personnel-adjacent state where allowed.
- Helen cannot create, approve, terminate, or modify personnel identities by default.
- Unknown resident actions are denied or require Steward approval.
- Boundary decisions include reasons and source references where applicable.
- CLI JSON output is valid.
- Duty runners and/or conversation sessions can consume the boundary if those modules are present.
- No governance, validation, merge, personnel, or Steward authority is changed.

## Validation Recipe Requirement
Add or update the validation recipe for WP-0110. The recipe must be registered in the existing validation framework and must not return `no_recipe`. Classify checks as required or observational, use local-first non-destructive commands, and ensure this package can be evaluated by:

```bash
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0110 --json
PYTHONPATH=src python -m estate.cli.main validation-production-readiness --json
```

## Codex Completion Receipt Requirement
Create `collaboration/work_packages/completions/WP-0110_codex_done.json` with at least:

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
- final resident authority command surface
- explicit Alfred authority boundaries
- explicit Helen authority boundaries
- audit storage path or not-applicable rationale

## Production Readiness Requirement
Run or document the equivalent of:

```bash
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0110 --json
PYTHONPATH=src python -m estate.cli.main validation-production-readiness --json
```

If production readiness remains blocked because downstream UI or service orchestration has not consumed the boundary everywhere, record that limitation explicitly.

## Demonstration Requirements
Document exact commands run and observed status. Include sample authority-check JSON for:

- Alfred summarizing operations state
- Alfred attempting to execute a work package
- Helen summarizing onboarding state
- Helen attempting to modify personnel identity
- unknown action category handling

## Completion Signal
Create `collaboration/work_packages/completions/WP-0110_codex_done.json` using the standard completion schema.

Set `ready_for_ca_review=true` only if tests, receipt metadata, validation recipe status, and production-readiness obligations are satisfied or explicitly documented with limitations.

## Merge Class
Class A if the package only enforces existing authority boundaries.

Escalate to Class B if it grants new resident authority, changes governance authority, changes personnel authority, changes validation authority, changes merge authority, or introduces automatic execution semantics.
