# WP-0673 — Engineering Evidence, Validation, Integration, and Acceptance Lifecycle

Status: Pending  
Priority: High  
Owner: Chief Architect  
Execution lane: Codex  
Campaign: CAMPAIGN-0670 Engineering Department Operationalization  
Depends on: WP-0670, WP-0671, WP-0672

## Objective

Define and operationalize the Engineering Department lifecycle for producing, preserving, validating, integrating, reviewing, and accepting engineering evidence across a coordinated campaign.

The package must ensure that engineering completion is determined by durable evidence and governed acceptance rather than by worker assertion, chat history, branch state, or an unverified completion message.

## Required Inputs

Review at minimum:

- `operations/departments/engineering/engineering_department_charter.md`
- `operations/departments/engineering/engineering_department_operating_guide.md`
- outputs and completion evidence from WP-0670, WP-0671, and WP-0672
- current work-package validation contracts and implementations
- current validation recipes and reports under `operations/validation/`
- current work-package completion receipt conventions
- current PTM campaign, dependency, readiness, and acceptance contracts
- current operational-readiness closure controller and evidence
- repository branch, PR, integration, and review conventions
- current dispatch and provider execution evidence contracts

## Required Work

### 1. Engineering evidence contract

Define the minimum evidence bundle required from every engineering work package, including:

- work-package identity and campaign identity;
- execution lane and provider identity;
- branch and commit identifiers;
- changed-file inventory;
- implementation summary;
- commands executed;
- test and validation results;
- generated reports and artifacts;
- unresolved warnings and limitations;
- dependency and contract impact;
- rollback or recovery notes;
- requested acceptance lane;
- completion receipt path.

Evidence must be durable, repository-addressable, and attributable to the executing worker or provider.

### 2. Validation lifecycle

Define the governed path:

```text
implementation complete
  -> self-validation
  -> package validation
  -> integration validation
  -> campaign checkpoint validation
  -> operational-readiness validation
  -> acceptance preparation
```

For each stage specify:

- responsible party;
- required inputs;
- validation recipe or command source;
- pass, fail, blocked, and not-applicable outcomes;
- evidence path;
- retry and bounded-rework rules;
- escalation conditions;
- prohibition on self-approval.

### 3. Integration contract

Define how package branches and PRs are integrated without losing campaign-level truth. Cover:

- one-PR-per-package default;
- grouped integration PR exceptions;
- contract-freeze and shared-file controls;
- merge-order rules;
- midpoint integration branches or checkpoints;
- conflict ownership;
- stale-base and superseded-package handling;
- validation required after merge;
- evidence links from campaign state to merged commits.

### 4. Acceptance model

Distinguish clearly among:

- worker completion;
- provider completion;
- validation pass;
- integration completion;
- Chief Architect engineering acceptance;
- Steward final institutional acceptance;
- operational-readiness closure;
- archival closure.

No state may be treated as equivalent to a later protected state.

### 5. Completion receipts

Standardize human-readable and machine-readable completion receipts. Define required fields, naming conventions, authority signatures or acknowledgements, and references to validation and merge evidence.

### 6. Failure and recovery

Define treatment for:

- partial implementation;
- validation failure;
- missing validation recipe;
- flaky or contradictory tests;
- integration conflict;
- provider failure;
- branch abandonment;
- duplicate completion receipts;
- stale evidence;
- post-merge regression;
- acceptance rejection.

All failure paths must preserve evidence and return the package to an explicit state.

## Deliverables

Create or update:

1. `docs/operations/Engineering_Evidence_and_Completion_Contract_v1.md`
2. `docs/operations/Engineering_Validation_and_Integration_Lifecycle_v1.md`
3. `docs/operations/Engineering_Acceptance_and_Closure_Model_v1.md`
4. engineering completion-receipt templates under the canonical templates location
5. required validation recipe updates or additions
6. campaign checkpoint evidence format for CAMPAIGN-0670
7. `collaboration/work_packages/completions/WP-0673_completion_receipt.md`

## Non-Goals

- no second validation framework;
- no second acceptance authority;
- no replacement of PTM or operational-readiness closure;
- no automatic merging;
- no worker self-approval;
- no implementation of unrelated engineering features.

## Validation

Before claiming completion, verify that:

- each lifecycle state is distinct and has an authoritative evidence source;
- every package can be traced from intake through merged commit and acceptance preparation;
- validation failures cannot be recorded as completion;
- completion receipts cannot substitute for missing validation;
- campaign checkpoints reference existing package and PR evidence;
- Chief Architect and Steward acceptance boundaries remain intact;
- no duplicate validation, readiness, or acceptance system was introduced.

## Acceptance Criteria

The Engineering Department must have one explicit, reproducible lifecycle by which a fresh worker can determine what evidence to produce, how work is validated, how branches are integrated, which office accepts engineering truth, and when a package or campaign may legitimately close.

## Delivery

Open a pull request for Chief Architect review. Do not merge. Preserve all validation evidence and create the required completion receipt.