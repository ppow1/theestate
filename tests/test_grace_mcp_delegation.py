import json
import sys

sys.path.insert(0, r"A:\theestate-ops003\src")
from estate.core.resident_gateway import _mcp_arguments, _mcp_function_specs, _mcp_tool_request_response, _mcp_tool_result_response


TOOLS = [{"type": "function", "function": {"name": "estate_comms8_create_reasoning_request", "parameters": {}}}, {"type": "function", "function": {"name": "estate_comms8_list_requests", "parameters": {}}}]


def test_create_requires_explicit_arguments():
    assert _mcp_arguments(TOOLS[0]["function"]["name"], "create the request") is None


def test_create_arguments_are_forwardable_without_state_mutation():
    args = _mcp_arguments(TOOLS[0]["function"]["name"], 'workflow_id="wf-1" objective="bounded test" input_data={} idempotency_key="wf-1:1"')
    assert args == {"workflow_id": "wf-1", "objective": "bounded test", "input_data": {}, "idempotency_key": "wf-1:1"}


def test_explicit_create_emits_tool_call_not_result():
    body = _mcp_tool_request_response({"model": "estate/grace-grounded-test", "tools": TOOLS, "messages": [{"role": "user", "content": 'Call estate_comms8_create_reasoning_request workflow_id="wf-1" objective="bounded test" input_data={} idempotency_key="wf-1:1"'}]})
    assert body["choices"][0]["message"]["tool_calls"]
    assert body["estate"]["mcp_invocation"] == "delegated_to_openwebui"


def test_tool_result_is_returned_verbatim():
    body = _mcp_tool_result_response({"model": "estate/grace", "messages": [{"role": "user", "content": "call it"}, {"role": "tool", "content": '{"request_id":"authoritative-1"}'}]})
    assert body["choices"][0]["message"]["content"] == '{"request_id":"authoritative-1"}'
    assert body["estate"]["mcp_result"] == "authoritative_tool_result"


def test_explicit_read_request_is_delegated_without_mutation():
    name = "estate-comms8-live_estate_comms8_read_request"
    tools = [{"type": "function", "function": {"name": name, "parameters": {}}}]
    body = _mcp_tool_request_response({"model": "estate/grace", "tools": tools, "messages": [{"role": "user", "content": f'Call {name} request_id="ec8-fixture".'}]})
    call = body["choices"][0]["message"]["tool_calls"][0]
    assert call["function"]["name"] == name
    assert json.loads(call["function"]["arguments"]) == {"request_id": "ec8-fixture"}


def test_natural_language_read_selects_enabled_comms8_action():
    name = "estate_comms8_read_request"
    tools = [{"type": "function", "function": {"name": name, "parameters": {}}}]
    body = _mcp_tool_request_response({
        "model": "estate/grace",
        "tools": tools,
        "messages": [{"role": "user", "content": "Read Estate Comms8 request ec8-12345678 and return its authoritative state."}],
    })
    call = body["choices"][0]["message"]["tool_calls"][0]
    assert call["function"]["name"] == name
    assert json.loads(call["function"]["arguments"]) == {"request_id": "ec8-12345678"}


def test_comms8_lifecycle_claim_without_call_is_truthful_error():
    body = _mcp_tool_request_response({
        "model": "estate/grace",
        "tools": [{"type": "function", "function": {"name": "estate_comms8_read_request", "parameters": {}}}],
        "messages": [{"role": "user", "content": "Comms8 claimed and resolved the request."}],
    })
    assert "native_tool_call_required" in body["estate"]["reason"]
