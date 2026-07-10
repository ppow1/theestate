# WP-0633 - Cross-Department Operational Coordination

Status: Proposed
Priority: High
Owner: Chief Architect #6
Classification: Estate Internal
Depends on: WP-0632

## Mission

Allow Operations to coordinate approved work across Engineering, Character Architecture, Workforce, and other departments through one governed operational flow rather than manual Steward relaying.

## Required Implementation

- Model department requests, commitments, dependencies, handoffs, service-level expectations, blockers, and acknowledgements.
- Reuse the Collaboration Layer, work-package lifecycle, Operations Runtime, Traffic Controller constraints, and campaign engine.
- Provide department inbox/outbox views and cross-department dependency status.
- Allow Operations Manager to sequence and coordinate work within delegated authority.
- Escalate unresolved contention, authority conflicts, or missed commitments.

Expected files:

```text
src/estate/core/department_coordination.py
src/estate/core/department_coordination_runtime.py
tests/test_department_coordination.py
tests/test_department_coordination_runtime.py
docs/integration/cross_department_operational_coordination.md
```

## Acceptance

- A campaign can request work from multiple departments and track acknowledgements.
- Cross-department dependencies block and release correctly.
- Operations can resolve routine sequencing without Steward intervention.
- Departmental authority and execution-provider boundaries remain intact.
- Completion receipt: `collaboration/work_packages/completions/WP-0633_codex_done.json`.

## Codex Handoff

```text
Read collaboration/work_packages/pending/WP-0633_Cross_Department_Operational_Coordination.md and do exactly what it says.
```
