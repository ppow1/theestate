import json
import urllib.request

names = [
    "estate-comms8-live_estate_comms8_create_reasoning_request",
    "estate-comms8-live_estate_comms8_list_requests",
]
tools = [{"type": "function", "function": {"name": name, "description": "Estate Comms8 tool", "parameters": {"type": "object"}}} for name in names]

def call(text, messages=None):
    body = {"model": "estate/grace", "messages": messages or [{"role": "user", "content": text}], "tools": tools, "stream": False}
    req = urllib.request.Request("http://127.0.0.1:11435/v1/chat/completions", json.dumps(body).encode(), {"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=20) as response:
        return json.loads(response.read())

read = call("Call estate-comms8-live_estate_comms8_list_requests with claim_next=false.")
create = call('Call estate-comms8-live_estate_comms8_create_reasoning_request with workflow_id="grace-gateway-test", objective="bounded gateway test", input_data={}, idempotency_key="grace-gateway-test-1".')
tool = {"role": "tool", "content": '{"status":"AUTHORITATIVE_RESULT","request_id":"fixture-not-real"}'}
result = call("Report only the tool result.", [{"role":"user","content":"Call the MCP tool."}, tool])
print(json.dumps({"read": read, "create": create, "tool_result": result}, indent=2))
