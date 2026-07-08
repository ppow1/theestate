# WP-0602 - Office Operational Activity Panel

Status: Pending  
Author: Chief Architect #6  
Intended Executor: Codex  
Classification: Estate Internal

## Mission

Implement the first Office of the Steward operational activity panel that consumes shared operational status artifacts and displays current Estate activity.

The Steward must be able to see what is running, blocked, awaiting approval, recently completed, failed, or idle without inspecting terminals, browser tabs, chat scrollback, or raw runtime files.

This package consumes the operational status files produced by WP-0601. It does not implement the event feed itself.

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
- `collaboration/work_packages/pending/WP-0601_Operational_Event_Feed_and_Office_Status.md`

If WP-0601 has already been implemented, inspect the actual runtime status artifact shape and use it as source of truth.

If WP-0601 has not been implemented yet, create the Office panel using the contract in WP-0601 and include safe fallback behavior when files are absent.

## Architectural Intent

Turn operational visibility into a Steward-facing command surface.

This is not a static dashboard decoration. Every displayed item must come from a real status artifact or explicitly state that no status artifact exists.

The panel should support this line:

`governed dispatch -> visible activity -> structured events -> auditable result -> Steward-visible decision state`

## Scope

Implement:

1. Office-side loader for operational status artifacts.
2. UI or view component showing active work.
3. UI or view component showing blocked and attention-required work.
4. UI or view component showing recent completed/failed work.
5. Clear empty state when no status artifacts exist.
6. Clear stale state when status artifacts are old.
7. Classification-aware summary display.
8. Tests for loader and rendering behavior.
9. Concise documentation of the panel and expected status files.

## Out of Scope

Do not implement:

- operational event writer,
- full Orchestrator,
- scheduler,
- provider execution,
- Alfred redesign,
- Helen redesign,
- Ingrid redesign,
- new office,
- mailbox redesign,
- live websocket streaming unless already present and trivial to reuse.

Do not invent fake activity.

## Implementation Targets

Use existing Office of the Steward conventions. Discover the current UI/app structure before editing.

Likely areas to inspect:

- Office of the Steward app/source directory,
- existing dashboard/status components,
- existing local runtime data loaders,
- existing API routes or local file bridges,
- existing validation/status panels.

Preferred runtime inputs:

- `runtime/operations/status/latest.json`
- `runtime/operations/status/active.json`
- `runtime/operations/status/recent.json`
- `runtime/operations/status/summary.md`

If the Office cannot directly read local runtime files from the frontend, implement or reuse the existing backend/local bridge pattern. Do not create a second unrelated data access pattern.

## Display Requirements

The panel must show, at minimum:

- worker or provider,
- current assignment or work package,
- state,
- elapsed time,
- provider type,
- budget source when available,
- security classification,
- validation status,
- whether Steward attention is required,
- last message or safe summary,
- artifact paths when safe and useful.

## Activity Groups

Display activity grouped as:

1. Active
2. Awaiting Approval
3. Blocked / Attention Required
4. Validation
5. Recently Completed
6. Failed / Cancelled

If there are no items in a group, show a compact empty state rather than hiding the entire panel.

## Stale Data Behavior

If latest status is older than a reasonable threshold, clearly mark it stale.

Suggested default threshold:

- 15 minutes for active/running activity,
- 24 hours for recent terminal activity.

If the timestamp cannot be parsed, mark the status as uncertain rather than failing the whole panel.

## Boundary and Classification Behavior

The Office panel must not leak sensitive content.

Rules:

- Public and Estate Internal messages may be displayed normally.
- Restricted, Steward Only, and Local Only messages should display a generic summary unless the status metadata marks the summary safe.
- Always display non-sensitive structural fields such as state, provider, assignment, classification, validation status, and attention requirement.
- If an artifact path is sensitive or local-only, show the classification and omit direct content preview.

This is not full Ingrid enforcement. It is safe display behavior for the Office surface.

## Empty State Behavior

If no operational status files exist, the panel should display:

- no active operational status found,
- expected status artifact paths,
- whether the loader could access the runtime directory,
- no fake green status.

## Error Behavior

If a status file is malformed:

- show an error state for that file,
- continue loading other status files when possible,
- do not crash the Office,
- include enough information for a developer to fix the malformed artifact.

## Tests

Add tests covering:

1. Loader handles missing files.
2. Loader handles valid latest status.
3. Loader handles valid active status.
4. Loader handles valid recent status.
5. Loader handles malformed JSON without crashing.
6. Active activity renders.
7. Blocked or attention-required activity renders prominently.
8. Completed activity renders in recent group.
9. Restricted/Steward Only/Local Only messages are redacted unless summary-safe metadata exists.
10. Stale data is marked stale.
11. Empty state renders honestly.

Use existing repository test style.

## Documentation

Create or update concise integration documentation, preferred path:

- `docs/integration/office_operational_activity_panel.md`

Include:

- purpose,
- status artifact inputs,
- display groups,
- stale behavior,
- classification behavior,
- test command,
- relationship to WP-0601.

## Acceptance Criteria

Complete when:

- Office can consume operational status artifacts.
- Office displays active, blocked, awaiting approval, validation, recent completed, and failed/cancelled groups.
- Missing status artifacts produce honest empty state.
- Malformed artifacts do not crash the Office.
- Sensitive summaries are redacted by default.
- Stale status is visible as stale.
- Tests pass.
- Documentation exists.
- No fake activity or placeholder success state is introduced.
- No new office or duplicated registry is created.

## Validation

Run the relevant frontend/backend tests according to repository convention.

At minimum, run any available targeted tests for the Office component and loader, then run audit:

```powershell
Clear-Host
cd A:\theestate
.\estate.bat audit
```

If the repository uses a specific test command for the Office, use it and report the actual command.

Produce an implementation summary with:

- files changed,
- tests run,
- audit result,
- screenshots or textual rendering summary if available,
- blocked items,
- recommended follow-up work package.

## Do Not Touch

Do not modify:

- archived institutional memory,
- Alfred responsibility definitions,
- Helen responsibility definitions,
- Ingrid responsibility definitions,
- operational event feed writer except for import compatibility,
- unrelated Office pages,
- unrelated navigation architecture.

## Expected Follow-On Packages

Do not implement these now:

- WP-0603 Orchestrator intake contract.
- WP-0604 Provider registration and capability discovery.
- WP-0605 Office action controls for approved operational decisions.
