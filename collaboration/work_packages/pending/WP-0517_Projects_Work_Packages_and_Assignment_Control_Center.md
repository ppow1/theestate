# WP-0517 - Projects, Work Packages, and Assignment Control Center

Status: Proposed
Priority: High
Owner: Chief Architect #5
Classification: Estate Internal

## Mission

Make the Office Projects and Work Packages surfaces operational for governed work management.

## Required Controls

- open work-package source and completion receipt;
- refresh assignment and pipeline state;
- assign or reassign through existing governed mechanisms;
- change supported priority or status;
- promote a package into the next canonical workflow state;
- open validation evidence;
- route to related pull request, commit, and operational evidence;
- filter, search, and sort;
- expose blockers and the required next action.

## Boundaries

Do not create a parallel work-package registry, assignment queue, validation system, or promotion path. Do not bypass Steward, Traffic Controller, Chief Architect, or validation boundaries.

## Functional Standard

Every state-changing action must call a canonical Estate runtime, write durable evidence, refresh the Office payload, and report completed, blocked, or failed truthfully.

## Testing

Prove browser-to-handler-to-artifact-to-render behavior for refresh, assignment, supported state transitions, promotion, evidence navigation, filtering, and blocker display.

## Acceptance Criteria

1. Projects and Work Packages are real control surfaces.
2. Assignment and supported transitions persist.
3. Promotion follows canonical workflow rules.
4. Validation evidence is not mislabeled as institutional acceptance.
5. Related PR, commit, receipt, and evidence references are serviceable.
6. Focused tests and WP-0517 validation pass.

## Completion Receipt

```text
collaboration/work_packages/completions/WP-0517_codex_done.json
```

## Codex Handoff

```text
Read collaboration/work_packages/pending/WP-0517_Projects_Work_Packages_and_Assignment_Control_Center.md and do exactly what it says.
```
