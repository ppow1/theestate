# SERIES TASK WP-0080 — Helen Employee Onboarding Orchestrator

## Codex Command
Read `collaboration/work_packages/pending/WP-0080_SERIES_helen_employee_onboarding_orchestrator.md` and do exactly what it says.

## Mission
Implement the Helen Employee Onboarding Orchestrator so Helen can execute the Estate's existing employee onboarding process end-to-end after Steward authorization.

This package should connect existing personnel, mailbox, onboarding, resolver, and document systems into one safe operational workflow. It should not create a parallel onboarding system.

## Context
Chief Architect review indicates the Estate already has most onboarding infrastructure:

- Helen as Employee #6
- Human Resources office and mailbox
- personnel registry integration
- personnel resolver integration
- Onboarding Checklist v1
- mailbox infrastructure
- mailbox indexing
- document registry
- work package system
- validation framework
- Alfred as Employee #7 for operational coordination

The missing piece is orchestration: Helen needs a command/service that performs the existing checklist reliably.

## Scope
Create or extend a local Helen/HR onboarding command or service such as:

- `estate hr onboard`
- `estate helen onboard`

Follow existing repository conventions for CLI naming and command structure.

The workflow should support collecting or accepting:

- name
- department
- office
- role
- classification
- onboarding package type
- Steward authorization evidence where required

The orchestrator should perform the existing onboarding sequence where supported by existing systems:

1. Determine next available Employee ID using existing authority/source data.
2. Create or update the personnel registry entry.
3. Assign or create the employee mailbox.
4. Create mailbox folders if required by existing mailbox convention.
5. Update mailbox index.
6. Generate the correct onboarding packet/message.
7. Include required documents and historical memoranda where applicable.
8. Deliver the onboarding packet to the new mailbox.
9. Set employee status to `onboarding`.
10. Verify the employee is visible through personnel resolver and mailbox resolver outputs.
11. Produce an auditable onboarding result.

## Possible Outputs
Use existing patterns where possible. Possible artifacts include:

- `operations/hr/onboarding_runs/`
- `runtime/hr/onboarding_result.json`
- HR mailbox outgoing/institutional message artifacts
- personnel registry update outputs
- mailbox index update outputs

## Behavior Requirements
- Steward authorization must be respected where governance requires it.
- Helen may prepare and execute onboarding only within HR authority.
- Do not mint employee identities outside existing authority rules.
- Do not silently overwrite existing personnel or mailbox records.
- If required inputs are missing, fail safely with a clear message.
- The onboarding result must identify each completed step and each skipped/unavailable step.
- Existing resolver outputs should be used to confirm visibility.
- The workflow should be local-first and scriptable.

## Constraints
Do not create a new personnel registry. Do not create a new mailbox system. Do not create a new onboarding doctrine or parallel onboarding document. Do not bypass Steward authorization. Do not change constitutional authority. Do not edit `estate_ledger/ledger.md` or `development/devlog.md`.

## Tests
Verify:

- successful onboarding with valid inputs
- missing required input handling
- duplicate employee or mailbox protection
- mailbox creation/index update behavior
- onboarding packet creation
- resolver visibility confirmation
- authority/authorization failure mode
- clear audit/result artifact generation

## Completion Signal
Create `collaboration/work_packages/completions/WP-0080_codex_done.json` using the standard completion schema.

## Merge Class
Class A unless implementation changes personnel authority, identity issuance authority, or governance semantics; escalate to Class B if those boundaries change.
