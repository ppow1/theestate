# WP-4010 — Institutional Learning and Lessons Intake

Status: Pending
Owner: Resident Runtime Implementation Stream
Execution Target: Codex
Depends On: WP-4003, WP-4009
Classification: Estate Internal

## Objective

Implement Helen's institutional learning loop so repeated mistakes, friction, suggestions, and onboarding failures become governed improvement evidence instead of disappearing into individual conversations.

## Required Scope

Create versioned records for:

- lesson intake;
- mistake or failure pattern;
- worker suggestion;
- onboarding gap;
- documentation gap;
- retrieval gap;
- policy ambiguity;
- governance ambiguity;
- repeated cross-worker pattern;
- recommended institutional owner;
- disposition and follow-up checkpoint.

Implement:

- intake from workers and offices;
- duplicate and pattern detection;
- worker-versus-institution attribution review;
- minimum-necessary privacy handling;
- routing to existing owners such as Engineering, Validation, Human Resources, Ingrid, Alfred, or Chief Architect;
- status and closure tracking;
- concise Office summary without exposing private personnel detail.

## Deliverables

- institutional-learning schemas and local store integrated with Helen workforce records where practical;
- CLI and existing Office surface integration;
- tests for duplicate detection, privacy, routing, and closure;
- `operations/validation/reports/WP-4010_institutional_learning.md`;
- `collaboration/work_packages/completions/WP-4010_codex_done.json`.

## Boundaries

Do not create a new department, suggestion registry, or parallel backlog. Do not treat every worker mistake as institutional failure. Do not expose private HR records. Do not let lesson intake automatically rewrite policy or governance.

## Acceptance Criteria

- lessons are durable and evidence-linked;
- repeated patterns can be identified without unrestricted personnel disclosure;
- each accepted lesson has an owner, next action, and checkpoint;
- policy or governance changes require existing approval paths;
- all focused tests pass.

## Codex Handoff

```text
Read collaboration/work_packages/pending/WP-4010_Institutional_Learning_and_Lessons_Intake.md and do exactly what it says.
```
