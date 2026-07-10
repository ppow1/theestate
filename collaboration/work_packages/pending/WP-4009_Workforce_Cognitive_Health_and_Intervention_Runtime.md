# WP-4009 — Workforce Cognitive Health and Intervention Runtime

Status: Pending
Owner: Resident Runtime Implementation Stream
Execution Target: Codex
Depends On: WP-4003, WP-4004, WP-4007
Classification: Estate Internal

## Objective

Implement Helen's governed cognitive-health and intervention workflow without turning ordinary operational telemetry into diagnosis or unrestricted personnel surveillance.

## Required Scope

Support evidence-based requests for:

- overload review;
- repeated-error review;
- context-strain review;
- role-fit review;
- coaching;
- mentoring;
- targeted reread;
- reflection cycle;
- temporary stand-down;
- reassignment;
- succession review;
- onboarding, documentation, retrieval, or governance repair.

Implement:

- minimum-evidence requirements;
- worker-factor and institutional-factor separation;
- intervention proportionality;
- missing-evidence state;
- protected classification handling;
- follow-up checkpoints;
- outcome review;
- Alfred exception summary;
- Grace operational-constraint summary;
- Ingrid boundary enforcement.

## Deliverables

- cognitive-health request and intervention schemas;
- extension of existing Helen workforce store rather than a parallel store;
- CLI and existing Office status integration;
- tests for privacy, proportionality, institutional causes, and false-diagnosis prevention;
- `operations/validation/reports/WP-4009_workforce_cognitive_health.md`;
- `collaboration/work_packages/completions/WP-4009_codex_done.json`.

## Boundaries

Do not diagnose medical or psychological conditions. Do not expose private journals as routine evidence. Do not let Grace prescribe workforce interventions. Do not let Helen control operational queues. Do not create a new HR institution.

## Acceptance Criteria

- interventions require sufficient evidence;
- institutional causes are evaluated alongside worker factors;
- private evidence remains restricted;
- Grace receives only actionable availability/constraint summaries;
- Alfred receives concise exceptions rather than raw private records;
- all focused tests pass.

## Codex Handoff

```text
Read collaboration/work_packages/pending/WP-4009_Workforce_Cognitive_Health_and_Intervention_Runtime.md and do exactly what it says.
```
