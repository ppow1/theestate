# WP-0670 — Engineering Department Current-State and Gap Assessment

Status: Pending
Owner: Chief Architect
Execution lane: Codex
Campaign: CAMPAIGN_0670_ENGINEERING_DEPARTMENT_OPERATIONALIZATION

## Objective

Produce a complete current-state map of the Estate Engineering Department and identify the minimum changes required to operationalize it as a campaign-execution institution.

## Required Inputs

- `operations/departments/engineering/engineering_department_charter.md`
- `operations/departments/engineering/engineering_department_operating_guide.md`
- `operations/departments/engineering/WP-0125_engineering_department_establishment_report.md`
- `collaboration/campaigns/CAMPAIGN_0550_LOCAL_ENGINEERING_DEPARTMENT_FIRST_OPERATIONAL_SLICE.md`
- `src/estate/core/local_engineering_department.py`
- `src/estate/cli/local_engineering_department.py`
- `src/estate/core/openwebui_engineering_workflow.py`
- current PTM, dispatch, validation, readiness, provider, mailbox, and work-package contracts.

## Required Work

1. Inventory every current Engineering Department artifact, command surface, runtime component, report, queue seam, campaign convention, and authority statement.
2. Classify each artifact as canonical, active, partial, stale, superseded, experimental, or duplicate.
3. Trace the current path from approved idea to campaign, work package, staffing, dispatch, execution, validation, integration, acceptance, and archive.
4. Identify where the path currently requires direct Steward prompting.
5. Identify conflicts among Engineering, Grace, Helen, Alfred, Chief Architect, PTM, dispatch, and validation responsibilities.
6. Identify missing durable records, APIs, status surfaces, recovery paths, and continuity instructions.
7. Produce an explicit reuse map and a prohibition list for systems that must not be duplicated.

## Deliverables

- `docs/architecture/engineering_department_current_state_map.md`
- `docs/architecture/engineering_department_gap_and_overlap_assessment.md`
- `docs/architecture/engineering_department_canonical_reuse_map.md`
- `collaboration/work_packages/completions/WP-0670_completion_receipt.md`

## Validation

The assessment must cite repository paths for every conclusion, distinguish observed behavior from proposed behavior, and account for all known engineering campaign and local-execution assets.

## Acceptance Criteria

A fresh architect must be able to determine what already exists, what is authoritative, what is missing, and which existing mechanisms downstream packages must extend rather than replace.

## Delivery

Open a PR for Chief Architect review. Do not merge. Do not implement production behavior.
