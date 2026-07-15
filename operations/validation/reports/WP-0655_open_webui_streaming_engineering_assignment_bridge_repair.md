# WP-0655 Open WebUI Streaming Engineering Assignment Bridge Repair Validation

Date: 2026-07-15

## Scope

Validated that the Open WebUI engineering-assignment command is bridged through the existing Helen workforce, Grace operations, and Dispatch workflow for both non-streaming and streaming chat requests.

## Checks

- Non-streaming command path still returns an OpenAI-compatible `chat.completion` response.
- Streaming command path returns OpenAI-compatible `chat.completion.chunk` events and a final `finish_reason: stop` chunk through `chat_completion_stream`.
- Streaming command path bypasses ordinary resident conversation handling for the engineering assignment command.
- Streaming command path creates exactly one Helen workforce request, one Helen workforce assessment, one Grace objective, one Grace action, and one Dispatch queue item.
- Resident-visible streaming content confirms initiation through Helen, Grace, and Dispatch.
- Resident-visible streaming content avoids forbidden implementation phrases.
- Governance flags remain false for provider execution, privileged execution, and second-system creation.
- Normal non-command streaming resident chat remains covered by the existing SSE chunk regression test.

## Automated Validation

```text
pytest -q tests/test_openwebui_engineering_workflow.py tests/test_resident_gateway.py
.................                                                        [100%]
17 passed in 0.55s
```

## Manual Open WebUI Acceptance

Not performed in this environment. Post-merge validation should restart Estate Core and send the exact WP-0655 command through Grace in Open WebUI.
