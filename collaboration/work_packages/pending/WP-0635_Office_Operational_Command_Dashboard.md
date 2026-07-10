# WP-0635 - Office Operational Command Dashboard

Status: Proposed
Priority: High
Owner: Chief Architect #6
Classification: Estate Internal
Depends on: WP-0630, WP-0631, WP-0632, WP-0634

## Mission

Turn the Office of the Steward into a live executive command dashboard for Estate operations, with truthful telemetry, exceptions, campaigns, departments, repositories, audits, and recovery state in one coherent view.

## Required Implementation

- Extend existing Office surfaces.
- Show runtime host health, scheduler posture, watch state, repository targets, campaign progress, department commitments, active audits, Ring 2 queue, provider capacity warnings, recovery state, and exceptions requiring Steward attention.
- Provide drill-down from summary to canonical evidence.
- Distinguish operational progress, validation evidence, and institutional acceptance.
- Add filtering by repository, department, campaign, severity, and age.
- Preserve classification-safe summaries.

Expected touchpoints:

```text
src/estate/core/steward_command_center.py
src/estate/core/office_command_surface.py
tests/test_office_operational_command_dashboard.py
docs/integration/office_operational_command_dashboard.md
```

## Acceptance

- Dashboard refreshes from durable runtime artifacts.
- Every actionable control has a real handler.
- Exceptions are prioritized without hiding background progress.
- Multi-repository and cross-department state are visible.
- No automatic acceptance or provider bypass is introduced.
- Completion receipt: `collaboration/work_packages/completions/WP-0635_codex_done.json`.

## Codex Handoff

```text
Read collaboration/work_packages/pending/WP-0635_Office_Operational_Command_Dashboard.md and do exactly what it says.
```
