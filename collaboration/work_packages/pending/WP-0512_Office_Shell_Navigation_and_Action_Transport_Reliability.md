# WP-0512 - Office Shell, Navigation, and Action Transport Reliability

Status: Proposed
Priority: High
Owner: Chief Architect #5
Classification: Estate Internal

## Mission

Repair the shared Office shell so every later operational control has a reliable browser foundation.

This package must fix tab routing, navigation state, action submission, progress indication, structured error handling, payload refresh, stale-data detection, and action-result rendering. It must not redesign the Office visually or create a new frontend framework.

## Required Standard

```text
A browser action is complete only when the request reaches the registered handler, returns a structured result, updates the relevant payload, and the changed state is visible without manual source inspection.
```

## Scope

Implement:

1. Deterministic tab and panel routing.
2. Safe startup-tab restoration from Settings.
3. Back/forward and direct-hash navigation behavior.
4. Preservation of active tab and entered form state during targeted refreshes.
5. One canonical browser action transport.
6. Request IDs and duplicate-submit protection.
7. In-progress, completed, blocked, and failed UI states.
8. Diagnostics and artifact-reference rendering.
9. Targeted refresh after state-changing actions.
10. Stale payload/version detection and visible warning.
11. Recovery from malformed action responses or unavailable local server.
12. Tests covering actual request-to-render behavior.

## Required Reading

```text
src/estate/core/steward_command_center.py
src/estate/core/office_command_surface.py
src/estate/core/operations_center_settings.py
tests/test_steward_command_center.py
tests/test_office_command_surface.py
```

Also consume the WP-0511 audit results when available.

## Constraints

Do not:

- create React, Vue, or another framework;
- create a second action endpoint;
- allow arbitrary handler or shell execution;
- report success based only on HTTP 200;
- refresh the entire page after every action when a targeted refresh is sufficient;
- erase unsaved user input without warning.

## Expected Artifacts

Modify as needed:

```text
src/estate/core/steward_command_center.py
src/estate/core/office_command_surface.py
```

Create:

```text
tests/test_office_shell_functional.py
docs/integration/office_shell_action_transport.md
collaboration/work_packages/completions/WP-0512_codex_done.json
```

Register a WP-0512 validation recipe.

## Test Requirements

Tests must prove:

- all configured tabs route to real panels;
- invalid tabs fall back safely;
- direct navigation and browser history work;
- duplicate submissions are blocked;
- action request IDs are returned and displayed;
- completed, blocked, and failed results render distinctly;
- diagnostics and artifacts are visible;
- targeted refresh reflects changed state;
- stale payloads are detected;
- malformed JSON and unavailable endpoints show recoverable errors;
- no arbitrary action ID can invoke unregistered code.

## Acceptance Criteria

1. Shared navigation is deterministic and persistent.
2. Browser actions use one canonical transport.
3. Duplicate actions are prevented.
4. Failures are visible and diagnostic.
5. State-changing actions refresh the relevant surface.
6. Stale data is not silently presented as current.
7. Existing Office actions continue to work.
8. Focused tests and WP-0512 validation pass.
9. No new framework, command bus, or parallel Office is created.

## Codex Handoff

```text
Read collaboration/work_packages/pending/WP-0512_Office_Shell_Navigation_and_Action_Transport_Reliability.md and do exactly what it says.
```
