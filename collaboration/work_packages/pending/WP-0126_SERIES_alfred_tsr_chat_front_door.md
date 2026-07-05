# SERIES TASK WP-0126 — Alfred TSR Chat Front Door

## Codex Command

Read collaboration/work_packages/pending/WP-0126_SERIES_alfred_tsr_chat_front_door.md and do exactly what it says.

## Mode

SERIES

## Mission

Make Alfred directly interactable from the Office of the Steward / Operations Center UI.

Alfred has been stood up as a first-class Estate resident, but he is still effectively command-initiated. That is not sufficient. Alfred must become the Steward's first point of contact with the Estate: always available while the local Operations Center is running, reachable from the UI, and capable of accepting typed requests through a chat-style interface.

This package is not a documentation exercise. It must add working interaction.

## Problem Statement

The Operations Center currently exposes a large amount of useful institutional state, but it provides almost no interaction.

The Estate has state.

It does not yet have enough behavior.

Alfred is supposed to be critical to the Estate and should function like a local resident assistant: a practical TSR-style presence in the Office, not merely a CLI command whose output can be displayed after the fact.

The Steward must be able to open the server-based UI and talk to Alfred.

## TSR Interpretation

For this work package, TSR means:

- Alfred is available for interaction for as long as the local Operations Center server is running.
- Alfred can accept user input from the UI without requiring the Steward to open a terminal and run a CLI command manually.
- Alfred can produce a response visible in the UI.
- Alfred conversation turns are persisted as Estate artifacts.
- Alfred's availability is visible from the Office front door.

This does not require background daemon autonomy beyond the running local server. Do not introduce unrelated always-on services, cloud dependencies, secret stores, or external APIs.

## Preconditions

Before work begins:

1. Confirm WP-0122 is merged and Alfred is operationally stood up.
2. Confirm WP-0123 is merged and Helen is online.
3. Confirm WP-0124 is merged and Chief Architect #5 is onboarded.
4. Confirm WP-0125 is merged and the Engineering Department exists.
5. Confirm production-readiness validation runs.
6. Confirm the Operations Center / Steward Command Center server starts locally or identify the current server startup defect.

If server startup fails because of an existing bug, repair the smallest safe local-first server defect required to make Alfred chat accessible.

## Scope

In scope:

1. Add a visible Alfred chat panel to the Office of the Steward / Operations Center UI.
2. Make Alfred the front-door interaction point from the Home or Alfred tab.
3. Add a local HTTP endpoint for submitting Alfred chat prompts from the UI.
4. Add a local HTTP endpoint or page refresh mechanism for reading Alfred conversation history.
5. Persist Alfred conversation turns using existing resident conversation/session artifacts where possible.
6. Route submitted prompts through the existing Alfred task/request/conversation machinery where possible.
7. Return a useful Alfred response in the UI.
8. Make the interface local-only and explicit about authority boundaries.
9. Ensure Alfred cannot silently execute work packages or bypass Steward authorization through chat.
10. Record every chat interaction as an Estate artifact or resident conversation turn.
11. Add validation recipe and completion receipt for WP-0126.

Out of scope:

- Full natural-language autonomous execution.
- External LLM/API integration unless already present and explicitly local-first.
- Cloud chat services.
- Long-running background worker orchestration beyond the local Operations Center server lifetime.
- Giving Alfred authority to execute, merge, delete, or modify institutional artifacts without existing authorization rules.
- Building the full command palette.
- Building external Codex telemetry.
- Rebuilding the whole UI.

## Required User Experience

When the Steward opens the Operations Center UI:

1. Alfred must be visible as an available resident/front-door assistant.
2. There must be a text input area for typing to Alfred.
3. There must be a submit/send action.
4. Alfred must return a visible response.
5. Prior conversation turns must be visible or reloadable.
6. The UI must make clear that Alfred chat is local-first and does not bypass Steward authorization.

Minimum acceptable interaction:

```text
Steward: Alfred, what should I look at first?
Alfred: Current Estate status: [...]. Recommended next action: [...].
```

The response may be deterministic and artifact-driven at first. It does not need to be a full LLM conversation if no local model is wired yet. It must still be useful and must be generated through a real code path, not a static placeholder.

## Implementation Guidance

Prefer extending existing modules:

- `src/estate/core/steward_command_center.py`
- `src/estate/core/alfred.py`
- `src/estate/core/resident_conversation_sessions.py`
- existing resident conversation artifacts
- existing Alfred request/task functions

Add the smallest necessary server handler support to accept local POST requests from the Office UI.

If `SimpleHTTPRequestHandler` is currently only serving static files, extend it carefully or add a local-only request handler for Alfred chat endpoints.

Suggested local endpoints:

```text
GET  /api/alfred/chat
POST /api/alfred/chat
```

or the nearest convention that fits the current server code.

The endpoint should reject non-loopback exposure assumptions. Preserve local-only behavior.

## Alfred Response Rules

Initial Alfred responses may be deterministic and artifact-driven.

At minimum, Alfred should be able to respond to prompts by summarizing:

- current production-readiness status
- current resident status
- pending work packages
- recent activity
- known next actions
- requested artifact search or command suggestions if available

If the prompt cannot be handled, Alfred should say what he can currently do and recommend a concrete next action.

Do not fake a general AI model.

## Required Artifacts

Create:

`operations/residents/alfred/WP-0126_alfred_chat_front_door_report.md`

Create machine-readable companion:

`runtime/residents/alfred/WP-0126_alfred_chat_front_door_report.json`

The report must include:

- current git commit
- server startup status
- endpoint paths added
- UI panels/components changed
- conversation persistence path
- example prompt and response
- authority boundaries
- tests run
- validation commands run
- known limitations
- recommended next action

## Required Tests

Add or update tests for:

1. Alfred chat endpoint exists or server handler can process a local Alfred chat request.
2. A submitted prompt produces a response.
3. Conversation turn is persisted.
4. Alfred chat does not claim authority to execute work packages without authorization.
5. Command Center / Operations Center HTML includes Alfred chat input and send action.
6. Existing Alfred duty/presence tests remain passing.

Run:

```bash
PYTHONPATH=src pytest tests/test_work_package_validation.py tests/test_production_readiness_validation.py -q
PYTHONPATH=src python -m pytest tests/test_alfred_duty.py tests/test_resident_presence.py tests/test_resident_conversation_sessions.py
```

If an exact listed test file does not exist, use the closest existing resident conversation/server/UI test file and document the substitution.

## Required Validation Commands

Run or document equivalent:

```bash
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0122 --json
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0123 --json
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0124 --json
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0125 --json
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0126 --json
PYTHONPATH=src python -m estate.cli.main validation-production-readiness --json
```

Also run or document equivalent local smoke checks:

```bash
PYTHONPATH=src python -m estate.cli.main steward-command-center
PYTHONPATH=src python -m estate.cli.main operations-center status --json
PYTHONPATH=src python -m estate.cli.main operations-center start --host 127.0.0.1 --port 8765 --json
```

If `operations-center start` still fails due to the known local wrapper defect, either repair it as part of this package or document why direct `steward-command-center --serve` is the supported temporary startup path.

## Required Outputs

Update or create as applicable:

- Alfred chat/front-door UI changes
- local server endpoint changes
- conversation persistence artifacts
- Alfred front-door report Markdown and JSON
- validation recipe registration for WP-0126
- validation reports/runtime JSON for WP-0126
- regenerated production-readiness and coverage artifacts
- `collaboration/work_packages/completions/WP-0126_codex_done.json`

## WP-0126 Self-Validation Recipe

Add a recipe for WP-0126 that verifies:

- Alfred chat/front-door report exists
- JSON companion parses
- Operations Center / Steward Command Center HTML contains an Alfred chat input
- HTML contains a send/submit action for Alfred
- local Alfred chat endpoint or equivalent interaction path exists
- an example Alfred prompt/response is recorded
- conversation persistence path is recorded
- authority boundaries are explicitly reported
- WP-0122, WP-0123, WP-0124, and WP-0125 remain passing
- production-readiness validation executes successfully
- WP-0126 receipt is complete

Use cross-platform Python checks only.

## Completion Artifact

Create:

`collaboration/work_packages/completions/WP-0126_codex_done.json`

It must include:

- `work_package_id = WP-0126`
- `codex_status = done`
- `completed_at`
- `branch`
- `summary`
- UI changes made
- server endpoints added
- conversation persistence path
- example prompt/response
- tests run
- validation commands run
- server startup status
- authority boundaries
- known limitations
- recommended next action
- `ready_for_ca_review = true`
- `merge_authority = ca_verified_auto_merge_allowed`

## Acceptance Criteria

WP-0126 is complete when the Steward can open the local Operations Center / Office UI and type to Alfred through a visible chat interface, Alfred returns a useful response, and the interaction is persisted as Estate resident conversation evidence without bypassing authority boundaries.

## Merge Class

Class A. Escalate only if implementation requires changing Steward authority, Alfred authority, resident authority, server exposure/security policy, or production-readiness semantics.
