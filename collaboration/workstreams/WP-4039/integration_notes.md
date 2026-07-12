# WP-4039 Integration Notes

WP-4039 is staged and uninstalled. Future installation may copy or adapt `src/multi_resident_room.py` into a new canonical module such as `src/estate/core/multi_resident_conversation.py` after review.

## Future Open WebUI-compatible adapter

A future adapter can expose a room as an OpenAI-compatible model or conversation surface using a controlled identifier such as `estate/room/<room-id>` or a generic endpoint such as `estate/conference-room`. These identifiers are examples, not constitutional truth.

The adapter should:

1. Authenticate the caller and load an existing room snapshot.
2. Normalize addressing such as “Alfred” or “Helen and Grace” into resident IDs before calling the staged core.
3. Submit the human turn with an idempotency key.
4. Call `plan_resident_turns` for deterministic speaker plans.
5. For each plan, assemble the adapter-side prompt from shared context plus the resident-specific packet returned by `filtered_context_for`.
6. Call the approved model provider outside this staged module.
7. Record each adapter result with `record_resident_turn`.
8. Return separate, clearly attributed assistant messages so Open WebUI can display each resident identity without flattening responses.

## Office projection

`office_projection` provides a read-only payload with room name, status, classification, participants and states, current mode, active topic, invited speakers, last activity, blocked reasons, transcript/session references, and safe actions. WP-4039 does not create or modify Office tabs.

## Dependencies and conflicts

Future installation depends on installed resident runtime foundations, active resident/gateway patterns, and existing session/context/capability/delegation/model-assignment contracts. Integration may conflict with active gateway routing, resident registry, mailbox, Dispatch, model-control, and Office UI files; this package intentionally avoids those files.
