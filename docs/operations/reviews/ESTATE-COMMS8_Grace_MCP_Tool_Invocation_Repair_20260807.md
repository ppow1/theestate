# Estate Comms8 Grace MCP Tool Invocation Repair — 2026-08-07

Decision: `GRACE_MCP_MUTATION_FIXED`

## Root cause

The Comms8 MCP registration was healthy. The Live adapter advertised the
same seven tools, including `estate_comms8_create_reasoning_request`; the
create schema requires `workflow_id`, `objective`, `input_data`, and
`idempotency_key`, while `list_requests` has no required arguments.

The failure was above MCP transport:

1. Open WebUI’s persisted Grace model metadata contained only
   `grace_runtime_bridge` and `grace_runtime_grounding`.
2. The Grace runtime bridge was explicitly read-only and exposed no Comms8
   mutation operations.
3. `resident_gateway.py` ignored the incoming OpenAI `tools` list and always
   routed Grace conversation requests to resident text generation. Its
   engineering/Resident Gateway paths produced Dispatch and handoff-shaped
   language, which explains the second persona’s vocabulary.
4. Consequently Open WebUI received no native tool call to execute. The
   model-generated JSON was not an MCP result.

Open WebUI source confirms that MCP tools are discovered in
`connect_mcp_server`, converted into `mcp_tools_dict`, attached to the
provider request in `process_chat_payload`, and executed only after the
provider returns a native `tool_calls` message. No mutating-tool denial
policy was found in the Open WebUI MCP execution path.

## Trace evidence

Before repair, the adapter trace contained only:

`initialize → notifications/initialized → tools/list`

for both Grace probes; no `tools/call` was transmitted. The returned
`list_requests` payload was therefore also synthetic in the reproduced
Grace path. The mutating prompt returned a Grace runtime
`AMBIGUOUS_CORRELATION` payload without MCP traffic.

After repair, the trace contains:

`tools/call estate_comms8_list_requests`

and:

`tools/call estate_comms8_create_reasoning_request`

followed by read, claim, acknowledge, respond, resolve, and terminal read.

Trace: `A:\theestate-data\live\comms8\evidence\openwebui-mcp-trace.jsonl`.
The trace records redacted request method/tool name plus response status,
content type, byte count, and session presence; it records no arguments,
credentials, or response bodies.

Open WebUI probe evidence:
`A:\theestate-data\grace-comms8-mutation-investigation\openwebui-grace-call-results.json`.

## Smallest repair

- Added `server:mcp:estate-comms8-live` to the Grace model’s persisted
  Open WebUI tool associations.
- Added a narrow native MCP delegation path to the Resident Gateway. It
  emits a tool call only when the registered Comms8 tool and all required
  arguments are explicit.
- Added a result path that returns the latest MCP tool result verbatim.
- Incomplete arguments produce a truthful refusal; no request ID or result
  is invented.
- No Comms8 server, schema, queue, state, lease, or lifecycle semantics
  were changed.

Source changes:

- `A:\theestate-ops003\src\estate\core\resident_gateway.py`
- `A:\theestate-ops003\scripts\deploy_openwebui_grace_bridge.py`
- matching deployed source under `A:\theestate-wp4233`.

## Acceptance

- Open WebUI discovery: seven tools.
- Grace native create call emitted with complete arguments.
- Authoritative request: `ec8-195d5eef6e0b46e2`.
- Workflow: `grace-mcp-stream-acceptance`.
- Read-back matched request ID, workflow, and objective.
- Lifecycle passed: `created → claimed → acknowledged → responded →
  resolved`.
- Worker: `grace`.
- Local and public terminal records matched.
- Final state: `resolved`.
- Regression tests: `8 passed`.

Lifecycle evidence:
`A:\theestate-data\grace-comms8-mutation-investigation\authoritative-lifecycle.json`.

The `estate/grace-grounded-test` Open WebUI persona now carries the same
Live MCP server association as its Grace runtime base. The Resident Gateway
surface retains its existing identity and authority wording, but no longer
silently converts an explicit Comms8 operation into a Dispatch/handoff
simulation.

## Superseding note — actual persona-surface validation

This harness acceptance was insufficient to prove the actual Open WebUI
persona surfaces. The follow-on repair is recorded in
`ESTATE-COMMS8_Grace_Live_Persona_Dispatch_Repair_20260807.md`; it identifies
the missing Live MCP association in the canonical `estate/grace` catalog,
adds the narrow Resident Gateway read delegation, and preserves the earlier
historical result unchanged.
