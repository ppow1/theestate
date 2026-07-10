# WP-0632 - Operational Campaign Engine

Status: Proposed
Priority: High
Owner: Chief Architect #6
Classification: Estate Internal
Depends on: WP-0628, WP-0631

## Mission

Give the Operations Manager a governed mechanism for advancing approved multi-step initiatives over time without requiring the Steward to trigger each step manually.

## Required Implementation

- Represent an approved campaign as goals, phases, dependencies, entry criteria, exit criteria, delegated authority, holds, escalation conditions, and evidence requirements.
- Use existing work packages, dispatch, scheduler, Traffic Controller, provider recommendation, and validation systems.
- Support start, pause, resume, advance, block, cancel, and complete.
- Allow Operations Manager directives only within pre-approved campaign authority.
- Persist campaign state and event history.
- Surface next eligible actions, blockers, tempo, and exceptions.

Expected files:

```text
src/estate/core/operational_campaigns.py
src/estate/core/operational_campaign_runtime.py
tests/test_operational_campaigns.py
tests/test_operational_campaign_runtime.py
docs/integration/operational_campaign_engine.md
```

## Acceptance

- A campaign advances automatically through eligible routine phases.
- Movement still passes Traffic Controller constraints.
- Provider work still uses dispatch and adapter seams.
- Governance or authority exceptions escalate instead of improvising.
- Campaign completion is not institutional acceptance.
- Completion receipt: `collaboration/work_packages/completions/WP-0632_codex_done.json`.

## Codex Handoff

```text
Read collaboration/work_packages/pending/WP-0632_Operational_Campaign_Engine.md and do exactly what it says.
```
