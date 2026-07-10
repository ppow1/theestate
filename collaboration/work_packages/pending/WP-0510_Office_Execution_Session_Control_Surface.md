# WP-0510 - Office Execution Session Control Surface

Status: Proposed
Priority: High
Owner: Chief Architect #5
Boundary Authority: Ingrid / Privacy and Boundary Office
Primary Consumers: Steward, Office of the Steward, Traffic Controller / Operations Manager, Execution Session Controller, Execution Attempt Runtime, Result Reconciliation, Audit / Validation
Classification: Estate Internal
Created: 2026-07-10

## Provider Assignment Guidance

Recommended implementation provider:

```text
codex_cloud_web
```

Provider rationale:

```text
This package requires repository implementation across the existing Office command surface, Office web payload, local HTTP action handler, execution session controller, tests, and documentation. It should not require live provider execution, local GPU access, or network-dependent testing.
```

Local runtime required:

```text
false
```

Local runtime requirement details:

```text
All implementation and deterministic validation must use existing local command handlers, isolated temporary Estate roots, fake provider runners, and synthetic execution-session fixtures. No live Codex CLI execution is required.
```

Capacity note:

```text
Use Codex Cloud/Web. Do not invoke a live execution provider during implementation or tests.
```

## Codex Command

```text
Read this work package and do exactly what it says.

Do not exceed the stated scope.

Build functioning Office controls, not decorative cards or status-only views.

Do not create new offices, registries, queues, providers, event systems, or parallel execution paths.

Do not perform live provider calls during implementation or deterministic validation.

Do not auto-approve, auto-authorize, auto-retry, auto-merge, or grant institutional acceptance.
```

## Mission

Add a real execution-session control surface to the Office of the Steward website.

The Office must allow the Steward to perform governed local execution-session actions through the browser using the existing Office command-action transport and the existing execution-session, attempt, cancellation, recovery, and reconciliation runtimes.

This package must not merely display execution state. It must provide controls that actually invoke Estate handlers, write durable artifacts, change legitimate runtime state, and return clear success, blocked, or failed results to the Steward.

The required principle is:

```text
A control must control something.
A button that only refreshes a card is not an execution control.
A disabled placeholder is not completion.
```

## Background

The Office already has a local command-surface framework in:

```text
src/estate/core/office_command_surface.py
src/estate/core/steward_command_center.py
```

That framework can register controls, invoke Python handlers, persist `OfficeActionResult` records, and return results through the local Office HTTP surface.

The CA5 execution chain now provides:

```text
execution-session preview
execution-session start
execution-session resume
execution-session status
execution-session report
execution-attempt cancel-request
execution-attempt inspect-recovery
execution-attempt release-stale
execution-attempt retry-eligibility
execution-result-reconciliation inspect/reconcile/report
```

These capabilities are operational but primarily CLI-oriented. WP-0510 must expose the appropriate actions through the Office of the Steward as functioning browser controls.

The Office is the Steward's command center, not a billboard.

## Required Reading

Before implementation, read:

```text
AI_START_HERE.md
AI_HINTS.md
docs/governance/Estate_Manual.md
docs/governance/Institutional_Operations_Doctrine.md
docs/integration/governed_execution_session_controller.md
docs/integration/execution_attempt_lease_cancellation_recovery.md
docs/integration/execution_result_reconciliation.md
docs/integration/steward_authorized_live_codex_execution.md
src/estate/core/steward_command_center.py
src/estate/core/office_command_surface.py
src/estate/core/execution_session_controller.py
src/estate/core/execution_attempt_runtime.py
src/estate/core/execution_result_reconciliation_runtime.py
src/estate/core/execution_dispatch.py
src/estate/cli/main.py
tests/test_office_command_surface.py
tests/test_steward_command_center.py
tests/test_execution_session_controller.py
tests/test_execution_attempt_runtime.py
tests/test_execution_result_reconciliation_runtime.py
```

Also inspect the actual HTML, JavaScript, request handler, action endpoint, payload shape, and current tab/control rendering in `steward_command_center.py`. Do not assume the UI plumbing works merely because action metadata exists.

## Scope

This package must implement:

1. A dedicated Office execution-session workspace or panel using the existing Office structure.
2. Real Office action handlers for execution-session preview, start, resume, status refresh, and report generation.
3. Real Office action handlers for cancellation request, recovery inspection, retry-eligibility inspection, and explicit stale-lease release.
4. Real Office action handlers for result-reconciliation inspection and explicit reconciliation when appropriate.
5. Input controls for required IDs, authorization paths/references, reasons, and confirmations.
6. Explicit confirmation controls for live execution and stale-lease release.
7. Action-result rendering that shows completed, blocked, and failed outcomes with artifact references.
8. Session, attempt, lease, cancellation, result, reconciliation, and validation references in the workspace.
9. Safe refresh after successful actions so the user sees changed state immediately.
10. Durable action result records through the existing Office action-result log.
11. Deterministic tests proving browser action requests invoke real handlers and modify isolated runtime state.
12. Clear disabled states only when a required capability or input is genuinely unavailable.
13. Integration documentation and a completion receipt.
14. A WP-0510 validation recipe.

## Required Functional Controls

At minimum, implement these controls.

### Session controls

```text
Preview execution session
Start execution session
Resume execution session
Refresh execution-session status
Generate/open execution-session report
```

### Attempt controls

```text
Request cancellation
Inspect recovery state
Inspect retry eligibility
Release stale lease
```

### Result controls

```text
Inspect execution result reconciliation
Reconcile execution result
Generate/open reconciliation report
```

Exact button labels may be adjusted for clarity.

## Control Semantics

### Preview execution session

Must:

- invoke the existing execution-session preview path;
- require dispatch ID and authorization reference/path as applicable;
- perform no provider call;
- return session ID, readiness, blocking reasons, and artifact references;
- write a real preview/session artifact.

### Start execution session

Must:

- invoke the existing execution-session start path;
- require dispatch ID, authorization evidence, and explicit confirmation;
- preserve all existing Steward and Traffic Controller gates;
- use no hidden authorization defaults;
- return blocked when evidence is missing;
- never bypass the live-execution gate or attempt lease;
- never be exercised with a live provider in deterministic tests.

### Resume execution session

Must:

- invoke the existing resume path;
- require session ID;
- preserve ambiguous-provider-call protection;
- never repeat a provider call when existing evidence makes execution uncertain.

### Request cancellation

Must:

- invoke the existing attempt cancellation-request mechanism;
- require dispatch ID, attempt ID, actor, and reason;
- record a durable cancellation request;
- not claim the provider stopped until confirmed by existing runtime evidence.

### Inspect recovery and retry eligibility

Must:

- invoke existing attempt-runtime inspection functions;
- return actual classification and blocking reasons;
- not start a retry;
- not create retry authorization.

### Release stale lease

Must:

- invoke the existing explicit stale-release path;
- require dispatch ID, attempt ID, reason, and explicit confirmation;
- remain blocked for non-stale attempts;
- record release evidence.

### Reconcile execution result

Must:

- invoke the existing reconciliation runtime;
- require dispatch/result identifiers or references consistent with the existing contract;
- be idempotent;
- never grant institutional acceptance;
- surface Validation state and evidence when reached.

## Office Workspace Requirements

Add a clear execution workspace, preferably as a new Office tab:

```text
Execution Control
```

The workspace must include:

```text
Selected dispatch ID
Selected session ID
Selected attempt ID
Selected adapter request ID
Authorization record path/reference
Current session state
Current stage
Provider
Workspace commit
Lease state
Cancellation state
Result state
Reconciliation state
Validation reference
Attention required
Blocking/failure reason
Last Office action result
```

The UI must allow the Steward to select or enter the relevant IDs without editing source files or using the CLI.

Do not hide all controls behind a raw JSON text box unless an existing Office convention requires one. Prefer labeled fields with a compact advanced-parameters area only where necessary.

## Request/Response Requirements

The Office action endpoint must:

- accept structured action IDs and parameters;
- validate input types and required fields;
- reject unknown or gated actions;
- invoke `execute_office_action(...)` or the existing canonical action dispatcher;
- return structured JSON;
- preserve diagnostics paths on failure;
- never execute arbitrary Python functions or shell commands from user input;
- never accept an unrestricted handler name from the browser;
- never expose secrets, raw prompts, or authentication paths.

## Office Action Handlers

Extend `office_command_surface.py` with focused handlers, likely including equivalents of:

```text
execution_session_preview
execution_session_start
execution_session_resume
execution_session_status
execution_session_report
execution_attempt_cancel_request
execution_attempt_inspect_recovery
execution_attempt_retry_eligibility
execution_attempt_release_stale
execution_result_inspect_reconciliation
execution_result_reconcile
execution_result_report
```

Handlers must call existing core functions directly. Do not invoke the CLI through subprocesses.

Each handler must return a truthful `OfficeActionResult` containing:

```text
action_id
action_label
target_tab
outcome
steward_message
source_handler
artifacts_read
artifacts_written
runtime_state_changed
authority_gating_status
diagnostics_path when failed
```

## UI Behavior Requirements

The browser must:

- render available controls as actual enabled controls;
- render gated controls with the specific unmet requirement;
- disable duplicate submission while an action request is in flight;
- show an in-progress state;
- show success, blocked, and failed outcomes distinctly;
- show diagnostics/artifact references returned by the action;
- refresh relevant Office payload after state-changing actions;
- preserve entered IDs across refresh where practical;
- avoid silently swallowing request or JSON errors;
- not claim completion merely because an HTTP request returned 200.

## Safety and Authority Boundaries

The control surface must preserve:

```text
Traffic Controller authorization
Steward approval
Dispatch readiness
Live-execution confirmation
Attempt lease ownership
Cancellation semantics
Reconciliation semantics
Validation as evidence
Institutional acceptance outside provider execution
```

The Office may conduct an already-governed action. It may not manufacture missing authority.

## Out Of Scope

This package must not:

- redesign the entire Office website;
- repair unrelated Office tabs;
- create a new web framework;
- replace the existing local HTTP server;
- create a second Office command bus;
- create a second execution-session controller;
- create a second attempt runtime;
- create a second reconciliation runtime;
- select providers autonomously;
- authorize movement;
- automatically approve live execution;
- automatically retry;
- automatically merge or accept provider output;
- automatically release non-stale leases;
- perform live provider calls during tests;
- add cloud authentication or remote exposure;
- grant institutional acceptance.

A broader Office website audit and repair package should follow separately after WP-0510.

## Expected Artifacts

Modify as needed:

```text
src/estate/core/office_command_surface.py
src/estate/core/steward_command_center.py
```

Create focused tests, preferably:

```text
tests/test_office_execution_session_controls.py
```

Create integration documentation:

```text
docs/integration/office_execution_session_control_surface.md
```

Create completion receipt:

```text
collaboration/work_packages/completions/WP-0510_codex_done.json
```

Add deterministic validation recipe for:

```text
WP-0510
```

Modify existing execution modules only when a verified integration defect prevents the Office control from using the canonical function. Keep any such repair minimal and document it.

## Test Requirements

Tests must cover:

- execution workspace/tab appears in the Office payload and rendered HTML;
- required controls are registered as available actions;
- preview invokes the real session controller and writes preview evidence;
- preview records no provider call;
- start without confirmation is blocked;
- start without authorization evidence is blocked;
- fake-runner start invokes exactly one provider call;
- session status and report controls return real artifacts;
- resume invokes the real resume path and preserves duplicate-call protection;
- cancellation request writes a real cancellation artifact;
- recovery inspection returns real classification;
- retry eligibility does not start a retry;
- stale release requires explicit confirmation;
- non-stale release is blocked;
- reconciliation invokes the real reconciliation runtime;
- reconciliation does not grant institutional acceptance;
- browser action endpoint rejects unknown action IDs;
- browser action endpoint rejects missing required fields;
- action-result UI distinguishes completed, blocked, and failed;
- state refresh occurs after successful mutation;
- no live provider, network, GPU, Ollama, ChatGPT, or Codex CLI calls.

## Validation Rings

### Ring 0 - Static / Structural Validation

Verify Office handlers, registered controls, execution workspace, tests, documentation, completion receipt, and validation recipe exist.

### Ring 1 - Deterministic Functional Validation

Likely commands:

```text
python -m py_compile src/estate/core/office_command_surface.py src/estate/core/steward_command_center.py
pytest -q tests/test_office_execution_session_controls.py tests/test_office_command_surface.py tests/test_steward_command_center.py tests/test_execution_session_controller.py tests/test_execution_attempt_runtime.py tests/test_execution_result_reconciliation_runtime.py
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0510 --json
```

All provider behavior must use fakes.

### Ring 2 - Office Interaction Review

The automated validator or local review should verify through the rendered local Office:

1. Open Execution Control.
2. Enter a deterministic fixture dispatch and authorization.
3. Run Preview.
4. Confirm real session artifacts appear.
5. Attempt Start without confirmation and observe a truthful block.
6. Run deterministic fake-start through the test harness, not the live provider.
7. Request cancellation on a fixture attempt.
8. Inspect recovery and retry eligibility.
9. Inspect and reconcile a fixture result.
10. Confirm action results and changed state appear immediately.

## Completion Receipt Requirements

The completion receipt must include:

```text
work_package_id
status
owner
files_reviewed
files_created
files_modified
validation_commands_run
validation_results
office_tab_added
functional_controls_added
action_handlers_added
browser_endpoint_modified
session_controller_called_directly
attempt_runtime_called_directly
reconciliation_runtime_called_directly
live_provider_calls_made
fake_provider_runner_used
automatic_retry_implemented
automatic_authorization_implemented
institutional_acceptance_behavior_modified
runtime_artifacts_written
known_limitations
ready_for_ca_review
```

The receipt must explicitly state:

```text
functional_controls_added: true
session_controller_called_directly: true
attempt_runtime_called_directly: true
reconciliation_runtime_called_directly: true
live_provider_calls_made: false
fake_provider_runner_used: true
automatic_retry_implemented: false
automatic_authorization_implemented: false
institutional_acceptance_behavior_modified: false
```

## Acceptance Criteria

This package is complete when:

1. The Office contains a visible Execution Control workspace.
2. Preview, start, resume, status, report, cancellation, recovery, retry-eligibility, stale-release, and reconciliation controls invoke real Estate handlers.
3. Controls write or update genuine runtime artifacts where applicable.
4. Action results truthfully report completed, blocked, or failed outcomes.
5. Start and stale release require explicit confirmations.
6. Missing authority remains blocked.
7. Preview performs no provider call.
8. Deterministic start uses a fake runner and calls it exactly once.
9. Cancellation does not falsely claim provider termination.
10. Retry eligibility does not start a retry.
11. Reconciliation does not grant institutional acceptance.
12. The browser cannot invoke arbitrary handlers or shell commands.
13. Focused tests pass.
14. WP-0510 validation passes.
15. Completion receipt exists and is ready for Chief Architect review.
16. No new office, registry, queue, provider, event system, or competing execution path is created.

## Steward / Chief Architect Note

This is a CA5 500-series implementation package.

The purpose is not to add another dashboard. The purpose is to let the Steward operate the execution system from the Office through real, governed controls.

A separate follow-on package should perform a broad functional audit of the entire Office website, identify nonfunctional controls and broken workflows, and repair them in prioritized implementation waves.
