# WP-0655 — Open WebUI Streaming Engineering Assignment Bridge Repair

Status: Pending
Owner: Resident Runtime Implementation Stream
Execution Target: Codex
Priority: Immediate

## Objective

Repair the Open WebUI engineering-assignment bridge introduced by PR #355 so the exact chat command works when Open WebUI sends `stream: true`.

The current non-streaming path correctly calls the existing Helen workforce, Grace operations, and Dispatch runtimes. The streaming path bypasses that bridge, falls through to ordinary resident conversation handling with action `conversation`, and produces an incorrect blocked response mentioning an unknown action category.

Do not redesign the workflow. Extend the existing bridge to the streaming path.

## Reproduce

Using model `estate/grace` through Open WebUI, send:

```text
Initiate Engineering Department assignment: verify the Open WebUI engineering assignment workflow by creating one bounded validation smoke-test assignment.
```

Observed incorrect result:

- request is treated as ordinary conversation;
- no Helen staffing request or assessment is created;
- no Grace operational objective/action is created;
- no Dispatch request is created;
- resident-visible output leaks implementation language such as `unknown action category 'conversation'`, `authority status`, and `blocked`.

## Root Cause

In `src/estate/core/resident_gateway.py`:

- `_non_streaming_chat_completion(...)` invokes `initiate_engineering_assignment_from_chat(...)` before ordinary chat handling;
- `_streaming_chat_completion(...)` does not invoke the engineering workflow bridge and instead calls `_chat_result(...)`, which sends the request to `process_chat(..., action="conversation")`.

Open WebUI normally uses the streaming path.

## Required Implementation

1. Detect the existing engineering-assignment command in both streaming and non-streaming requests.
2. Reuse `initiate_engineering_assignment_from_chat(...)`; do not duplicate Helen, Grace, or Dispatch business rules.
3. When the command is detected with `stream: true`:
   - initiate the same governed workflow exactly once;
   - do not fall through to `_chat_result(...)` or `process_chat(..., action="conversation")`;
   - return a valid OpenAI-compatible streaming response;
   - include the human-readable assignment summary;
   - preserve the `estate.engineering_assignment` metadata envelope where the current streaming contract permits it;
   - emit a proper final `finish_reason: stop` chunk.
4. Preserve the existing non-streaming behavior.
5. Preserve session identifiers and resident identity metadata.
6. Do not execute providers or workers from chat.
7. Do not create another scheduler, queue, dispatch layer, authority engine, or execution path.
8. Preserve these truthful flags:
   - `provider_execution_performed = false`
   - `second_execution_system_created = false`
   - `privileged_action_executed = false`
9. Ensure the command produces the existing governed artifacts:
   - Helen workforce request;
   - Helen workforce assessment;
   - Grace objective/action;
   - Dispatch request.
10. Prevent resident-visible leakage of these phrases for this command path:
   - `unknown action category`
   - `authority status`
   - `this action is blocked`
   - `blocked by default`
   - `routing guidance`

## Architectural Boundaries

- Open WebUI remains only the front end.
- The Estate Resident Gateway remains authoritative.
- Helen owns staffing and qualification evidence.
- Grace owns operational assignment and supervision after staffing.
- Dispatch remains the execution handoff authority.
- Chat initiation creates governance artifacts only.
- No worker execution, provider execution, code merge, final acceptance, hiring expansion, or constitutional authority is granted.

## Likely Files

- `src/estate/core/resident_gateway.py`
- `tests/test_openwebui_engineering_workflow.py`
- `tests/test_resident_gateway.py`

Modify other files only if required by the existing streaming-envelope architecture.

## Tests

Add focused tests proving:

1. The exact command with `stream: false` still succeeds.
2. The exact command with `stream: true` initiates the workflow.
3. Streaming creates each governed artifact exactly once.
4. Streaming does not call ordinary resident conversation handling for the command.
5. Streaming returns valid OpenAI-compatible chunks and a final stop chunk.
6. The visible content states that the assignment was initiated through Helen, Grace, and Dispatch.
7. The response does not contain forbidden implementation language.
8. The workflow flags remain false for provider execution, privileged execution, and second-system creation.
9. Normal non-command streaming resident chat remains unchanged.

Run at minimum:

```text
pytest -q tests/test_openwebui_engineering_workflow.py tests/test_resident_gateway.py
```

Run any additional focused streaming tests required by modified code. Record unrelated full-suite failures honestly; do not weaken unrelated tests.

## Manual Acceptance

After merge, restart Estate Core and use Grace in Open WebUI to send exactly:

```text
Initiate Engineering Department assignment: verify the Open WebUI engineering assignment workflow by creating one bounded validation smoke-test assignment.
```

Acceptance requires:

- a natural success response, not an authority error;
- Helen request and assessment created;
- Grace objective/action created;
- Dispatch request created;
- no provider or worker execution from chat;
- no duplicate artifacts from one streamed request.

Do not claim manual Open WebUI acceptance passed unless it was actually performed.

## Deliverables

- bounded streaming-path repair;
- focused regression tests;
- validation report under `operations/validation/reports/`;
- completion receipt under `collaboration/work_packages/completions/`;
- pull request against `main`;
- concise PR description with files changed, tests, known failures, authority preserved, and manual acceptance status.

Do not merge the pull request. Stop after opening it and report the PR URL and exact post-merge validation command.