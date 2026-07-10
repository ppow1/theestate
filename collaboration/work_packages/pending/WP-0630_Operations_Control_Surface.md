# WP-0630 - Operations Control Surface

Status: Proposed
Priority: High
Owner: Chief Architect #6
Classification: Estate Internal
Depends on: WP-0627, WP-0628, WP-0629

## Mission

Provide a real Office control surface for the Operations Runtime, scheduler, watches, audit admission, and service health so the Steward can supervise the system without using PowerShell for routine control.

## Required Implementation

- Extend the existing Office of the Steward; do not create a separate dashboard application.
- Show host state, heartbeat, active cycle, scheduled jobs, enabled watches, admitted audits, holds, cleanroom workspace state, latest verdicts, and faults.
- Provide real controls for start/stop/restart host, enable/disable jobs and watches, place/release holds, trigger one bounded cycle, and inspect evidence.
- Every button must invoke an existing canonical handler and return truthful status.
- Preserve role and boundary checks.

Expected touchpoints:

```text
src/estate/core/steward_command_center.py
src/estate/core/office_command_surface.py
src/estate/cli/main.py
tests/test_operations_control_surface.py
docs/integration/operations_control_surface.md
```

## Acceptance

- No decorative controls.
- State changes persist and survive reload.
- Failures identify the failed handler and retain evidence.
- The Steward can supervise normal operations without terminal commands.
- The surface does not grant final acceptance or bypass Traffic Controller constraints.
- Completion receipt: `collaboration/work_packages/completions/WP-0630_codex_done.json`.

## Codex Handoff

```text
Read collaboration/work_packages/pending/WP-0630_Operations_Control_Surface.md and do exactly what it says.
```
