# Estate PTM End-to-End Acceptance Validation Package

Status: Draft validation package for `TEST-PTM-001B`
Campaign: `PTM-07`
Integration checkpoint: Gate E — validation and rollout go/no-go
Authority baseline: Steward / Chief Architect acceptance of WP-0658, WP-0660, and WP-0661 on 2026-07-16

## Purpose

This package defines the formal end-to-end acceptance evidence required before the complete Estate Project and Task Management (PTM) build can advance from validation to rollout planning. It is a validation artifact only: it does not authorize production implementation, create a second queue, create a second registry, create a second scheduler, or alter established Steward, Chief Architect, Helen, Grace, Traffic Controller, or dispatch authority boundaries.

## Source-backed scope

The validation package covers the accepted `TEST-PTM-001B` scope: files, links, Mermaid diagrams, replay results, governance gates, permissions, and proof that no second execution path was introduced. The scope is bounded by these upstream controls:

- `TEST-PTM-001B` depends on `KPI-PTM-001`, `DISPATCH-PTM-001`, `MIG-PTM-001B`, `UI-PTM-002`, and `CONV-PTM-001`.
- Gate E is the validation and rollout go/no-go checkpoint after `TEST-PTM-001B` and before rollout packages.
- Rollout remains serialized after formal validation.
- Codex is the only execution lane for this implementation cycle; local RTX 4090 worker routing is inactive.

## Entry criteria

Formal E2E validation may begin only when all criteria below are satisfied or explicitly waived by the Chief Architect:

1. Dependency completion receipts exist for `KPI-PTM-001`, `DISPATCH-PTM-001`, `MIG-PTM-001B`, `UI-PTM-002`, and `CONV-PTM-001`.
2. The branch under validation is current with the relevant campaign integration branch and has no known manifest drift.
3. Contract-freeze evidence exists for event, ID, projection, intake, workspace/deep-link, schedule, dispatch, migration, KPI, validation, and conversation command surfaces.
4. No unresolved stop/replan note requires a frozen contract change.
5. `TEST-PTM-001A` replay and policy-validation plan exists or is explicitly waived for the Gate E review.

## Required evidence bundle

Produce a single Gate E evidence bundle with the following sections.

| Evidence section | Required contents | Blocking failure examples |
| --- | --- | --- |
| Repository integrity | Commit SHA, branch, manifest paths, package list, and validation timestamp. | Missing dependency package, uncommitted validation changes, manifest mismatch. |
| Documentation and link validation | Results for Markdown syntax where available, relative path/link checks, and Mermaid render or parse checks for changed diagrams. | Broken required link, invalid diagram in required PTM docs, untraceable package reference. |
| Schema and contract replay | Replay or dry-run output from `TEST-PTM-001A`; evidence that event, ID, projection, intake, schedule, dispatch, KPI, migration, UI, and conversation command contracts remain compatible. | Replay failure, incompatible event or projection field, unapproved schema drift. |
| Governance and authority checks | Evidence that the implementation reused existing governance roles, existing Dispatch Queue, and accepted review gates. | Second queue, second registry, second scheduler, new governance authority, self-acceptance. |
| Permission and route checks | Evidence that PTM workspace/deep links, Office compact card links, and Resident command responses resolve only to authorized surfaces. | Broken route, unauthorized command, inaccessible required route. |
| Dispatch and migration chain | Trace from task to dispatch evidence and pilot migration evidence. | Missing dispatch evidence, missing pilot migration receipt, unverifiable SHA or source mapping. |
| KPI acceptance | KPI registry/dashboard quality evidence and acceptance threshold summary. | Missing required KPI, stale dashboard input, threshold not defined. |
| Rollout readiness | Go/no-go recommendation, known residual risks, explicit rollout blockers, and required Chief Architect/Steward decisions. | Unresolved blocker without owner, rollout recommended despite failed validation. |

## Minimum validation command set

Run these commands from the repository root unless a future implementation package replaces them with equivalent project-specific commands:

```bash
git status --short
git diff --check
python -m pytest tests/test_work_package_validation.py tests/test_validation_handoff_artifact_workflow.py tests/test_post_merge_validation_pipeline.py
```

If the future PTM implementation adds dedicated validation commands, append them to the evidence bundle instead of replacing the commands above. Any skipped command must include the exact reason, the affected acceptance criterion, and the waiver owner.

## Acceptance checklist

Gate E can recommend rollout only when every item below is true:

- All dependency receipts or Chief Architect waivers are present.
- Required commands pass or have documented Chief Architect waivers.
- Every required evidence-bundle section is populated.
- No frozen upstream contract was changed without a stop/replan decision.
- No second dispatch queue, second registry, second scheduler, or new governance authority was introduced.
- Residual risks are classified with owners and rollout impact.
- Chief Architect review is complete and Steward acceptance is requested where authority or rollout gates are implicated.

## Promotion notes for a future Pending package

A future executable validation package should instantiate this artifact as the Gate E validation template, bind it to the final PTM implementation file paths, and attach command outputs under the package completion receipt. If any dependency path, route contract, or evidence source changes before execution, stop and replan rather than silently broadening this validation package.
