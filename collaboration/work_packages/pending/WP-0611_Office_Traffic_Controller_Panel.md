# WP-0611 - Office Traffic Controller Panel

Status: Pending  
Author: Chief Architect #6  
Intended Executor: Codex  
Classification: Estate Internal

## Mission

Implement the first Office of the Steward panel for the Traffic Controller / Operations Manager layer.

WP-0610 creates operations reviews, decisions, and runtime artifacts. This package makes those artifacts visible and usable in the Office of the Steward.

The Steward should be able to see operational posture, recommendations, blocked items, assignment gaps, provider capacity warnings, and available operations decisions without opening raw runtime files.

This package does not implement the Operations Manager core and does not run providers.

## Required Reading

Read these before implementation:

- `AI_START_HERE.md`
- `AI_HINTS.md`
- `docs/governance/Estate_Orientation_Handbook.md`
- `docs/governance/Estate_Manual.md`
- `docs/governance/Estate_Vision_and_Architecture.md`
- `docs/governance/Capability_Lifecycle_States_v1.md`
- `docs/governance/Practical_Worker_Onboarding_Addendum.md`
- `docs/collaboration/Estate_Collaboration_Layer_v1.md`
- `docs/collaboration/Estate_Collaboration_Standard_v1.md`
- `docs/architecture/execution_provider_operational_visibility_requirements.md`
- `docs/architecture/planning_pipeline.md`
- `collaboration/work_packages/pending/WP-0602_Office_Operational_Activity_Panel.md`
- `collaboration/work_packages/pending/WP-0605_Office_Intake_Decision_Controls.md`
- `collaboration/work_packages/pending/WP-0610_Traffic_Controller_Operations_Manager.md`

If WP-0602, WP-0605, or WP-0610 have already been implemented, inspect their actual files and integrate with them. Do not duplicate Office loaders, decision handlers, or runtime models.

## Architectural Intent

The Office of the Steward must become a live command center.

Operational visibility is not enough if the Steward cannot see what decisions are needed next. This panel makes the Traffic Controller / Operations Manager layer visible in the Office.

Preserve this distinction:

- Traffic Controller / Operations Manager recommends and records operational movement.
- Orchestrator mechanically schedules and dispatches.
- Providers perform work.
- Office displays state and exposes governed controls.

Every exposed control must be real. No fake buttons. No placeholder success. No silent failure.

## Scope

Implement:

1. Office loader for operations-control summary artifacts.
2. Office display for operational posture.
3. Office display for recommended actions.
4. Office display for items requiring Steward attention.
5. Office display for assignment gaps and provider warnings.
6. Real decision controls where existing Office action plumbing supports them.
7. Empty, stale, and malformed artifact states.
8. Classification-aware summary redaction.
9. Tests for loader, rendering, redaction, and decision behavior.
10. Concise integration documentation.

## Out of Scope

Do not implement Operations Manager core logic, Orchestrator runtime, provider execution, scheduling algorithm, worker provisioning, Alfred redesign, Helen redesign, Ingrid redesign, new office creation, unrelated Office navigation redesign, or live network calls.

## Implementation Targets

Use existing Office of the Steward conventions. Discover the current Office source structure before editing.

Likely areas to inspect:

- existing Office operational activity panel from WP-0602,
- existing intake decision controls from WP-0605,
- existing local runtime data loaders,
- existing backend or local bridge routes,
- existing status and validation panels.

Preferred runtime inputs:

- `runtime/operations/control/status/latest.json`
- `runtime/operations/control/status/summary.json`
- `runtime/operations/control/status/summary.md`
- `runtime/operations/control/reviews/`
- `runtime/operations/control/decisions/`

Preferred documentation:

- `docs/integration/office_traffic_controller_panel.md`

## Display Requirements

The Office panel must show operational posture, timestamp of latest review, stale state, source artifacts inspected, items requiring Steward attention, boundary review requirements, provider availability or capacity warnings, assignment gaps, blocked work, recommended next actions, latest operations decisions, and safe summaries only.

## Recommended Action Display

Recommended actions should show action type, target type, target ID when safe, priority, reason or safe summary, Steward approval requirement, boundary review requirement, and available real controls where supported.

## Allowed Office Controls

Expose only controls backed by real handlers.

Allowed initial controls:

- assign,
- reprioritize,
- hold,
- release,
- defer,
- cancel,
- escalate,
- request boundary review,
- request revision,
- request validation.

If a control cannot be implemented safely, show it as unavailable with an explanation rather than exposing a fake button.

## Control Behavior

Each exposed control must validate the request, call a real local handler or backend route, write an operations decision artifact or call the WP-0610 decision helper, update operations summary or status when appropriate, emit or prepare an operational event when available, and display success, blocked, or failure result.

No control may directly run providers.

## Stale and Missing Data Behavior

If no operations-control artifacts exist, show an honest empty state with expected artifact paths and runtime-access information. Do not show fake healthy status.

If latest review is older than a reasonable threshold, mark it stale. Suggested threshold: 15 minutes for active operations posture and 24 hours for historical summary. If timestamps cannot be parsed, mark state uncertain.

## Boundary and Redaction Behavior

Public and Estate Internal summaries may display normally. Restricted, Steward Only, and Local Only summaries must be redacted unless metadata marks `summary_safe: true`. Structural fields may display unless explicitly restricted. Do not preview raw prompts, secrets, credentials, private source material, or raw local-only content.

## Tests

Add tests covering:

1. Loader handles missing operations artifacts.
2. Loader handles valid summary artifact.
3. Loader handles malformed summary without crashing.
4. Stale review is marked stale.
5. Recommended actions render.
6. Steward-attention items render prominently.
7. Provider capacity warnings render.
8. Assignment gaps render.
9. Restricted, Steward Only, and Local Only summaries are redacted by default.
10. Summary-safe metadata allows display.
11. Real decision action writes or invokes a decision artifact path.
12. Unsupported control is shown unavailable rather than fake-success.
13. Empty state renders honestly.

Use existing repository test style.

## Documentation

Create `docs/integration/office_traffic_controller_panel.md` with purpose, runtime artifact inputs, panel sections, supported controls, unavailable-control behavior, stale behavior, redaction behavior, relationship to WP-0610, and relationship to Office activity and intake decision panels.

Keep it concise.

## Acceptance Criteria

Complete when:

- Office can consume operations-control artifacts,
- Office displays operational posture and recommended actions,
- items needing Steward attention are visible,
- sensitive summaries are redacted by default,
- stale and missing artifact states are honest,
- exposed controls are real and backed by decision artifacts or WP-0610 helpers,
- unsupported controls are not faked,
- tests pass,
- documentation exists,
- no provider execution is implemented,
- no new office is created.

## Validation

Run relevant Office tests and audit. At minimum try:

```powershell
Clear-Host
cd A:\theestate
.\estate.bat audit
```

If repository conventions include targeted frontend or backend tests for Office components, run those and report actual commands.

Produce an implementation summary with files changed, tests run, audit result, Office panel behavior summary, controls implemented, unsupported controls intentionally withheld, blocked items, and recommended follow-up package.

## Do Not Touch

Do not modify archived institutional memory, Alfred responsibility definitions, Helen responsibility definitions, Ingrid responsibility definitions, provider execution code, Orchestrator runtime core, unrelated Office pages, or unrelated navigation architecture.

## Expected Follow-On Packages

Do not implement these now:

- WP-0612 Orchestrator policy rules and priority management.
- WP-0613 Execution Provider Adapter Contract.
- WP-0614 Office control plane overview.
