# Engineering Department Operating Guide

## Proposing Engineering Work

Engineering work is proposed through Steward direction, Chief Architect recommendations, Operations Board items, validation findings, CueMastery backlog discovery, or resident/runtime handoff notes. Proposals should state the product/system affected, expected value, likely files or surfaces, validation needs, and any authority questions.

## Converting Work into a Work Package

A proposal becomes a work package when it has a clear mission, scope, out-of-scope boundaries, required outputs, validation commands, and completion criteria. The work package remains the durable unit of planning, implementation, review, and completion.

## Codex and Local Execution

Codex/local execution should inspect current repository artifacts, make bounded changes on the current branch, run applicable tests, update durable documentation/runtime outputs, and commit reviewable work. Local execution is preferred where practical to avoid renewed dependence on external conversational limits.

## Validation Discipline

Engineering runs targeted tests for changed behavior, required work-package validation commands, and production-readiness validation when the package affects readiness. New helper behavior for department discovery, service catalog, capability registry, or operations surfaces requires targeted tests.

## Completion Receipts

Completion receipts are created under `collaboration/work_packages/completions/` and must include the work package ID, completion status, timestamp, branch, summary, files changed, tests run, known limitations, review readiness, and PR/merge authority metadata or an explicit not-applicable reason.

## Chief Architect Review

Engineering requests Chief Architect review when architecture changes, authority boundaries are involved, validation semantics change, CueMastery execution plans become implementation commitments, or a package reaches completion and is ready for production-readiness acceptance.

## Blocker Escalation

Blockers are escalated with exact evidence: failing command, missing artifact, unclear authority, dependency unknown, or governance decision needed. Engineering does not silently work around blockers by bypassing governance or weakening validation.

## CueMastery Prioritization

CueMastery is the initial primary engineering objective. CueMastery work is prioritized after preserving Estate operational readiness: first discovery, then backlog shaping, then small validated implementation work packages, then broader product execution.

## Intake and Routing Rules

- Product implementation and code maintenance route to Engineering.
- Architecture questions route to Chief Architects with Engineering support.
- Hiring/onboarding routes to Helen/HR.
- Runtime coordination routes through Alfred where authorized.
- Production-readiness semantics route to Validation and Chief Architect review.
- Steward authority questions route to the Steward.

## What Not To Do

- Do not make hidden ad hoc changes outside a work package.
- Do not treat unvalidated implementation as complete.
- Do not bypass Steward, Chief Architect, Helen/HR, Alfred/runtime, or validation governance.
- Do not create duplicate registries when existing Estate surfaces can represent the department.
- Do not expand Engineering into unnecessary bureaucracy before CueMastery execution requires it.
