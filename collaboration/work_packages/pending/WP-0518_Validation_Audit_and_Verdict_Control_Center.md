# WP-0518 - Validation, Audit, and Verdict Control Center

Status: Proposed
Priority: High
Owner: Chief Architect #5
Classification: Estate Internal

## Mission

Expose real validation and audit operations through the Office without confusing evidence with institutional acceptance.

## Required Controls

- inspect pending, running, completed, and failed validation;
- open validation evidence and completion receipts;
- request supported validation or revalidation;
- acknowledge failures;
- inspect automatic-validator status;
- open audit and verdict artifacts;
- retry only through existing governed mechanisms;
- filter by result, package, date, owner, and attention state.

## Boundaries

Reuse existing validation, audit, verdict, and automatic-validator runtimes. Do not create a second validator, acceptance authority, verdict registry, or retry queue. Validation results are evidence, not institutional acceptance.

## Functional Standard

Controls must invoke canonical handlers, produce durable evidence or legitimate state changes, refresh the Office, and return truthful completed, blocked, or failed outcomes.

## Testing

Prove browser-to-handler-to-evidence-to-render behavior for inspection, validation requests, revalidation, failure acknowledgement, automatic-validator status, audit/verdict navigation, filtering, and governed retry.

## Acceptance Criteria

1. Validation and audit operations are serviceable from the Office.
2. Evidence and completion receipts open correctly.
3. Revalidation and retry preserve governance.
4. Automatic-validator status is truthful.
5. No control grants institutional acceptance.
6. Focused tests and WP-0518 validation pass.

## Completion Receipt

```text
collaboration/work_packages/completions/WP-0518_codex_done.json
```

## Codex Handoff

```text
Read collaboration/work_packages/pending/WP-0518_Validation_Audit_and_Verdict_Control_Center.md and do exactly what it says.
```
