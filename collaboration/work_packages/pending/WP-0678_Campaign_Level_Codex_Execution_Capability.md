# WP-0678 — Campaign-Level Codex Execution Capability

Status: Pending  
Priority: High  
Owner: Chief Architect  
Execution lane: Codex  
Campaign: Engineering campaign execution enablement  
Authority basis: Steward direction and CAMPAIGN-0670 Engineering Department Operationalization

## Objective

Implement the missing campaign-level Codex execution capability so an approved engineering campaign can be handed to Codex once, executed on one campaign branch, recorded as one bounded commit per atomic work package, advanced through dependency-aware sequential or approved parallel execution, paused at internal review gates, resumed after interruption, reconciled after partial failure, and presented as one campaign pull request for human review and protected acceptance.

## Authoritative Inputs

1. `collaboration/campaigns/CAMPAIGN_0670_ENGINEERING_DEPARTMENT_OPERATIONALIZATION.md`
2. The approved canonical campaign document and its canonical work packages.
3. Existing PTM, dispatch, readiness, validation, mailbox, repository-evidence, and acceptance systems.
4. Existing Codex bridge and provider-adapter boundaries.

## Constitutional Safeguard

Do not create a second scheduler, dispatch queue, validation path, campaign authority, acceptance authority, or constitutional role. Codex is an execution mechanism. The runtime manifest and package records are derived execution views of an already approved authoritative campaign and its work packages; they do not approve, supersede, or redefine those canonical sources or any existing governance system.

## Required Capability

1. Register one approved campaign manifest containing the canonical source, campaign identity, non-protected campaign branch, recorded approving authority, ordered atomic work packages, dependencies, approved parallel groups, and internal review gates.
2. Reject missing approval, protected branches, duplicate package identifiers, unknown dependencies or gate feeders, and parallel groups not explicitly approved by the campaign.
3. Keep execution on the declared campaign branch and preserve one bounded commit per atomic work package.
4. Return only dependency-eligible work. Sequential work remains sequential; parallel launches are limited to an explicitly approved group.
5. Pause at each configured internal review gate and require an identified reviewer before continuation.
6. Persist campaign state and an append-only transition history so execution can resume after interruption without relying on terminal or chat memory.
7. Stop on partial failure and require explicit reconciliation. A retry returns failed work to dependency planning; a skip remains non-successful and pauses for a governing decision.
8. Retain completed commits through restart and reconciliation, and fail closed on branch mismatch, premature launch, gate bypass, or duplicate commit recording.
9. After all packages and internal gates complete, expose `awaiting_acceptance` readiness and the evidence needed to present one campaign pull request. Do not create, merge, or accept that pull request automatically.

## Runtime Record Contract

- `CodexCampaignManifest` is a durable, derived runtime representation sourced from a previously approved canonical campaign.
- `CodexCampaignPackage` points to a canonical work-package source and adds execution-only state such as attempt count, failure, and bounded commit.
- Runtime registration records existing approval; it does not perform campaign approval, readiness validation, dispatch, package validation, or acceptance.
- Provider adapters may consume eligible package identifiers and report execution results, but do not acquire institutional authority.

## Required Deliverables

- `src/estate/core/codex_campaign_execution.py`
- `tests/test_codex_campaign_execution.py`
- `docs/architecture/codex_campaign_execution_capability.md`
- `collaboration/work_packages/completions/WP-0678_completion_receipt.md`

## Validation

At minimum run:

- `python -m pytest -q tests/test_codex_campaign_execution.py`
- `python -m compileall -q src/estate/core/codex_campaign_execution.py`

## Acceptance Criteria

This work package is complete only when:

- approved campaign topology is represented without becoming a competing authority;
- branch, dependency, approved-parallelism, gate, and bounded-commit rules fail closed;
- restart and partial-failure reconciliation preserve durable evidence;
- every internal review gate requires identified approval before execution continues;
- all completed work can be presented as one campaign pull request without automated merge or acceptance;
- tests and compilation checks pass; and
- no duplicate scheduler, dispatch, validation, readiness, mailbox, repository-evidence, or acceptance mechanism is introduced.

## Acceptance Boundary

Implementation completion and `awaiting_acceptance` are evidence states only. Package acceptance, campaign merge, and protected campaign acceptance remain with the applicable human authority under the canonical governance systems.

## Codex Handoff

> Read this work package and its authoritative inputs completely. Implement only the bounded runtime execution capability. Preserve canonical campaign and work-package authority, run the required validation, create one bounded commit, open a pull request, and do not merge.
