# OPERATIONAL TASK WP-0213 — Office of the Steward Command Surface

## Codex Command
Read collaboration/work_packages/pending/WP-0213_OPERATIONAL_office_of_the_steward_command_surface.md and do exactly what it says.

## Mode
OPERATIONAL IMPLEMENTATION

## Mission
Transform the Office of the Steward from a primarily informational dashboard into a real operational command surface.

The Office is not merely a place to view Estate state. The Office is the Steward's operational cockpit. It must allow the Steward to interact with, manage, route, refresh, validate, and control the Estate through governed local actions.

WP-0200 through WP-0212 created useful action architecture, metadata, staged workstreams, and installed backend modules. That work is foundational, but it did not satisfy the Steward's original objective: convert nouns into verbs.

WP-0213 must close that gap by wiring real Office UI controls to actual local handlers that perform actual Estate operations or deterministically report why the operation is blocked.

## Steward Assessment Incorporated
The Steward rejected the prior rollout as completion of the Nouns-to-Verbs objective because it produced more tabs, manifests, metadata, runtime reporting, and backend structure, but did not provide meaningful additional operational capability from the Office UI.

This package accepts that assessment as correct.

The objective remains open until the Office provides real governed operational actions.

## Governing Principle
Every verb exposed by the Office UI must be real.

For each Office area included in scope, every button/control must:

1. invoke an actual local handler,
2. perform an actual Estate operation or deterministically attempt it,
3. update or generate the appropriate local artifact when applicable,
4. update runtime state when applicable,
5. display the outcome to the Steward.

If the operation cannot complete because approval, configuration, service state, authority, dependency, or data is missing, the UI must report that reason clearly.

A disabled, gated, blocked, or failed-safe action is acceptable.

A fake, decorative, metadata-only, placeholder, stub, or unwired action is not acceptable.

## Complete Operational Path
Every exposed control must implement this complete path:

```text
Steward
  -> Office UI control
  -> UI event dispatch
  -> local command/action handler
  -> actual Estate operation
  -> artifact/runtime state change or deterministic blocked result
  -> Steward-visible outcome
```

The path may not terminate at metadata, manifests, action descriptions, TODO markers, simulated success, or command text unless the explicitly intended verb is `copy command`.

## Valid Operation Outcomes
Every attempted verb must end in exactly one of these outcome classes:

1. `completed`
   - operation executed successfully,
   - changed/generated artifact or runtime state when appropriate,
   - result displayed to the Steward.

2. `queued`
   - operation legitimately entered an existing Estate workflow/queue,
   - queue artifact/path/identifier displayed.

3. `blocked`
   - operation prevented by approval, authority, configuration, missing dependency, unavailable service, missing data, or unsafe state,
   - exact blocking reason displayed.

4. `failed`
   - operation attempted and failed,
   - diagnostics preserved,
   - failure displayed to the Steward.

No control may appear successful while doing nothing.

## Invalid Outcomes
The following are implementation failures:

- placeholder buttons,
- decorative controls,
- metadata-only actions,
- stub handlers,
- silent failures,
- simulated success,
- buttons that only log that they were clicked,
- controls that only expose action metadata without invoking a handler,
- controls that copy a command when an existing local handler can safely execute the action,
- controls that require the Steward to drop to the command line for normal operation when a safe local handler exists.

## Scope Strategy
Do not attempt to wire every possible Office verb in one uncontrolled sweep.

This package must implement a first real operational command surface across a practical set of high-value Office areas. Each included area must have only real verbs. If a proposed verb cannot be made real in this package, render it as unavailable/gated with a concrete reason or omit it.

At minimum, implement real operational verbs for these Office areas:

1. AI Services / Models
2. Validation
3. Work Packages
4. Mailboxes or Notifications
5. Residents / Alfred
6. Mission Control or Daily Board

The exact verbs may be adjusted based on existing local handlers, but every exposed verb must be real.

## Required Office Verb Audit
Create an audit artifact:

`operations/steward/WP-0213_office_command_surface_verb_audit.md`

For every Office tab, document:

- tab ID,
- current visible nouns/status sections,
- meaningful verbs the Steward should be able to perform,
- verbs implemented by WP-0213,
- verbs intentionally gated/unavailable,
- verbs deferred,
- reason for any deferred or unavailable verb,
- local handler used for each implemented verb,
- artifact or runtime state affected,
- Steward-visible outcome.

Every visible control introduced or changed by WP-0213 must be listed in this audit.

## Required Runtime Action Result Model
Implement or reuse a local action result model that can represent:

- action ID,
- action label,
- target tab,
- outcome class: completed, queued, blocked, failed,
- human-readable Steward message,
- source handler,
- artifacts read,
- artifacts written/generated,
- runtime state changed,
- authority/gating status,
- diagnostics path if failed,
- timestamp.

The UI must render this result clearly after action execution.

## Required Implementation Behavior
Codex must inspect existing modules before adding new ones. Prefer using existing command handlers, core modules, and CLI functions rather than duplicating logic.

Potential existing surfaces include but are not limited to:

- `src/estate/core/steward_command_center.py`
- `src/estate/core/office_actions.py`
- `src/estate/core/office_ai_service_actions.py`
- `src/estate/core/office_validation_actions.py`
- `src/estate/core/office_work_package_actions.py`
- `src/estate/core/office_communications_actions.py`
- `src/estate/core/office_resident_actions.py`
- `src/estate/core/office_board_actions.py`
- `src/estate/core/office_planning_actions.py`
- `src/estate/core/office_settings_help_about_actions.py`
- `src/estate/core/work_package_validation.py`
- `src/estate/core/resident_interaction.py`
- `src/estate/core/alfred.py`
- `src/estate/core/alfred_duty.py`
- `src/estate/core/notification_router.py`
- `src/estate/core/operations_notification_center.py`
- `src/estate/core/mailbox_index.py`
- `src/estate/core/daily_board_integration.py`
- `src/estate/core/discovery.py`
- `src/estate/core/discovery_catalog.py`
- `src/estate/core/provider_sync.py`
- `src/estate/cli/main.py`

Use the existing architecture when it is real. Replace metadata-only pathways with handler-backed pathways.

## Required Operational Verbs
Implement the safest real operational verbs available in the current repository. The list below is preferred, but Codex may substitute equivalent real verbs if the exact handler does not exist.

### AI Services / Models
Implement at least one real action, preferably:

- refresh AI services discovery / service registry,
- sync local provider/model inventory,
- refresh service status board,
- inspect logs through a real handler.

Start/stop/load operations may remain gated if the approval/process-control path is not ready. If gated, the UI must report the exact gating reason and the required next step.

### Validation
Implement at least one real action, preferably:

- run validation for a selected work package,
- run production readiness refresh,
- generate validation evidence,
- export validation evidence bundle.

The UI must clearly state that validation evidence is not institutional acceptance.

### Work Packages
Implement at least one real action, preferably:

- validate selected work package,
- refresh assignment queue,
- generate/copy Codex handoff only if the action is explicitly copy-command,
- open/install only if a real governed handler exists.

Do not execute arbitrary pending work packages unless an existing governed execution path and authority model explicitly supports it.

### Mailboxes or Notifications
Implement at least one real action, preferably:

- acknowledge a mailbox message through the existing acknowledgement path,
- refresh mailbox index,
- refresh notification center,
- create a route/reply draft through an existing artifact path.

Local acknowledgement must clearly distinguish local state from authoritative closure if they differ.

### Residents / Alfred
Implement at least one real action, preferably:

- request Alfred briefing,
- start or open a resident conversation session,
- queue an Alfred request through an existing local request path,
- refresh Alfred duty status.

The action must not grant Alfred new authority or let Alfred approve his own action request.

### Mission Control or Daily Board
Implement at least one real action, preferably:

- refresh Mission Control payload,
- refresh Daily Board integration,
- generate morning briefing,
- promote warning/item to draft proposal where a real draft artifact is created.

Promotion must create a proposal/draft only unless an authority path accepts it.

## UI Requirements
The Office UI must expose real controls for implemented verbs.

For every implemented verb, the UI must show:

- button/control label,
- current availability/gating state,
- confirmation prompt where needed,
- execution result,
- artifact paths generated/updated when applicable,
- blocking reason if blocked,
- diagnostics if failed.

The UI must not show operational controls that are not wired. If a future verb is shown, it must be visibly unavailable/gated and explain why.

## Local-Only Requirement
All WP-0213 operations must be local-first.

Do not add cloud calls, telemetry, external API calls, or remote execution.

Do not upload artifacts.

Do not transmit Estate data outside the local repository/runtime.

## Authority and Safety Boundaries
Preserve all existing authority boundaries.

Do not allow Office controls to bypass:

- Steward authority,
- Chief Architect review,
- resident action authority,
- validation governance,
- service approval workflow,
- merge authority,
- personnel/governance authority.

Blocked/gated controls are acceptable when authority is missing. Fake success is not acceptable.

## Required Artifacts
Create or update the following as applicable:

- active Office UI/runtime files required to expose real controls,
- handler modules required to execute real controls,
- tests for the action dispatch/result model,
- tests for each implemented verb,
- `operations/steward/WP-0213_office_command_surface_verb_audit.md`,
- `operations/steward/WP-0213_office_command_surface_report.md`,
- `collaboration/work_packages/completions/WP-0213_codex_done.json`.

## Required Report
Create:

`operations/steward/WP-0213_office_command_surface_report.md`

The report must include:

- summary of the Steward objective,
- explicit statement that WP-0200 through WP-0212 were foundational, not completion,
- list of real verbs implemented,
- tabs affected,
- handlers invoked,
- artifacts read/written/generated,
- gated verbs and reasons,
- failed/deferred verbs and reasons,
- tests run,
- manual verification instructions,
- known limitations,
- recommended next verbs.

## Required Tests
Add automated tests proving:

1. each exposed implemented verb invokes a real handler,
2. each handler returns one of the valid outcome classes,
3. successful actions report artifacts/state changes where applicable,
4. blocked actions report a concrete reason,
5. unavailable/gated actions are rendered as unavailable/gated rather than fake-operational,
6. the Office payload exposes only real or explicitly gated controls,
7. no implemented control is metadata-only.

Run relevant existing tests, including command center tests and any tests covering the handler modules changed.

## Required Validation Commands
Run or document equivalent validation:

```bash
PYTHONPATH=src python -m pytest tests/test_steward_command_center.py
PYTHONPATH=src python -m pytest tests/test_office_actions.py tests/test_office_*actions.py
PYTHONPATH=src python -m estate.cli.main steward-command-center --json
PYTHONPATH=src python -m estate.cli.main validation-production-readiness --json
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0213 --json
```

If a listed test path does not exist, run the closest relevant tests and document the substitution.

## Manual Verification Requirement
The report must include exact manual verification steps for the Steward.

For each implemented verb, provide:

- tab name,
- control label,
- expected click/action,
- expected valid outcome,
- expected artifact path or blocked reason,
- how to confirm it did something real.

## Completion Artifact
Create:

`collaboration/work_packages/completions/WP-0213_codex_done.json`

It must include:

- `work_package_id`: `WP-0213`,
- `codex_status`,
- `completed_at`,
- `branch`,
- `pull_request_url` or `pull_request_url_not_applicable_reason`,
- `summary`,
- `implemented_verbs`,
- `gated_verbs`,
- `deferred_verbs`,
- `tabs_affected`,
- `handlers_added_or_reused`,
- `artifacts_read`,
- `artifacts_written_or_generated`,
- `tests_run`,
- `validation_commands_run`,
- `known_limitations`,
- `manual_verification_steps`,
- `ready_for_ca_review`: true,
- `merge_authority`: `ca_verified_auto_merge_allowed`.

## Acceptance Criteria
WP-0213 is complete only when:

1. The Office UI exposes real operational controls for the Office areas included in scope.
2. Every exposed verb is wired to an actual local handler.
3. Every handler performs or deterministically attempts an actual Estate operation.
4. Every action returns a valid outcome class: completed, queued, blocked, or failed.
5. Every blocked/gated action reports a concrete reason.
6. Every completed action reports the artifact/runtime state affected where applicable.
7. The Steward can verify at least one real operational verb in each included Office area.
8. No placeholder, decorative, metadata-only, or unwired control is exposed as operational.
9. Tests prove that implemented verbs are real and not metadata-only.
10. The verb audit and command surface report exist.
11. The completion receipt exists.

## Merge Class
Class B.

This package modifies the active Office runtime and therefore requires careful validation and CA review.
