# Grace grounding policy

The Grace model filter marks prompts containing operational-state terms and appends a mandatory runtime-grounding instruction. If the current response contains no structured runtime result status, the filter replaces the assistant claim with an explicit inability to state operational facts.

Runtime statuses are `AUTHORITATIVE_RESULT`, `NO_RECORD`, `AMBIGUOUS_CORRELATION`, `RUNTIME_UNAVAILABLE`, `OPERATION_UNAVAILABLE`, `UNAUTHORIZED`, and `MALFORMED_RUNTIME_RESPONSE`. Conversation-only prompts are not intercepted. Missing data is never converted into a narrative, ID, checkpoint, schedule, handoff, or approval.
