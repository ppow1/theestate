# WP-4003 — Helen Operational Readiness and Grace Hiring Gate

Status: Pending
Owner: Resident Runtime Implementation Stream
Execution Target: Codex
Depends On: WP-4000, WP-4001
Classification: Estate Internal

## Objective

Prove that Helen is operationally ready to perform governed Human Resources and Workforce Development work, then establish a deterministic gate for whether Grace may enter hiring and onboarding.

## Required Scope

- Aggregate Helen identity, model, chat, workforce, authority, privacy, mailbox, and registration evidence.
- Produce one machine-readable readiness record and one human-readable report.
- Add a `helen-readiness` CLI surface with JSON output.
- Evaluate Grace prerequisites without appointing, activating, or onboarding Grace.
- Distinguish `ready`, `ready_with_limitations`, and `not_ready`.
- Record missing evidence and the exact next action for every failed gate.

## Required Gate Checks

1. Helen resident identity resolves.
2. Helen chat uses a Helen-specific prompt.
3. Local provider or truthful fallback state is visible.
4. Workforce request and assessment commands operate.
5. Privacy and classification boundaries remain intact.
6. Employee identity, mailbox, office, reporting line, and security rating resolve.
7. Helen can produce a governed hiring recommendation without granting authority.
8. Grace's office and role authorization evidence exists.
9. Grace's resident package and validation artifacts exist.
10. Steward-reserved appointment remains unperformed.

## Deliverables

- `runtime/residents/helen/readiness.json`
- `operations/residents/helen/Helen_Operational_Readiness_Report.md`
- focused tests
- `operations/validation/reports/WP-4003_helen_operational_readiness.md`
- `collaboration/work_packages/completions/WP-4003_codex_done.json`

## Boundaries

Do not appoint Grace. Do not fabricate manual Open WebUI validation. Do not expose private workforce records. Do not create a second readiness registry.

## Acceptance Criteria

- readiness is deterministic and evidence-linked;
- missing evidence blocks Grace correctly;
- all authority flags remain false;
- Helen's readiness can be inspected through CLI and existing Office status surfaces;
- all focused tests pass.

## Codex Handoff

```text
Read collaboration/work_packages/pending/WP-4003_Helen_Operational_Readiness_and_Grace_Hiring_Gate.md and do exactly what it says.
```
