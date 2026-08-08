import asyncio, json, urllib.request
from pathlib import Path
import sys
sys.path.insert(0, r"A:\AI\OpenWebUI\.venv\Lib\site-packages")
from open_webui.utils.mcp.client import MCPClient

ROOT = Path(r"A:\theestate-data\grace-comms8-live-dispatch-repair-20260807")
SECRET = Path(r"A:\theestate-data\live\comms8\secrets.env")
WORKFLOW = "estate-comms8-live-grace-chatgpt-roundtrip-test"
IDEMPOTENCY = "grace-chatgpt-roundtrip-20260807-01"
OBJECTIVE = "Ask ChatGPT to provide exactly three concise recommendations for improving the restartability of a local service that depends on a browser session, an MCP server, and a reverse tunnel. This is advisory reasoning only. Do not authorize commands, deployments, file changes, runtime mutation, purchases, or external communication."
INPUT_DATA = {"test": "Grace to ChatGPT to Grace production roundtrip", "expected_response": "exactly three concise recommendations"}
CREATE = "estate-comms8-live_estate_comms8_create_reasoning_request"

def secret():
    for line in SECRET.read_text().splitlines():
        if line.startswith("ESTATE_COMMS8_LIVE_CLIENT_SECRET="):
            return line.split("=", 1)[1]
    raise RuntimeError("Live credential is unavailable")

def gateway(payload):
    req = urllib.request.Request("http://127.0.0.1:11435/v1/chat/completions", json.dumps(payload).encode(), {"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.loads(response.read())

def result_text(value):
    if isinstance(value, list) and value and isinstance(value[0], dict) and "text" in value[0]:
        return value[0]["text"]
    return json.dumps(value)

async def main():
    specs = [{"type": "function", "function": {"name": CREATE, "description": "Estate Comms8 create reasoning request", "parameters": {"type": "object", "required": ["workflow_id", "objective", "input_data", "idempotency_key"]}}}]
    prompt = f"Invoke {CREATE} with workflow_id=\"{WORKFLOW}\", objective=\"{OBJECTIVE}\", input_data={json.dumps(INPUT_DATA)}, idempotency_key=\"{IDEMPOTENCY}\". Return only the authoritative tool result."
    call_body = gateway({"model": "estate/grace", "messages": [{"role": "user", "content": prompt}], "tools": specs, "stream": False})
    tool_calls = (((call_body.get("choices") or [{}])[0].get("message") or {}).get("tool_calls") or [])
    if len(tool_calls) != 1 or tool_calls[0].get("function", {}).get("name") != CREATE:
        raise RuntimeError("Grace Standard did not emit the exact Comms8 native tool call")
    args = json.loads(tool_calls[0]["function"]["arguments"])
    if args != {"workflow_id": WORKFLOW, "objective": OBJECTIVE, "input_data": INPUT_DATA, "idempotency_key": IDEMPOTENCY}:
        raise RuntimeError("native tool arguments did not match the requested schema")

    client = MCPClient()
    await client.connect("https://estate-comms8-live.ionoge.com/mcp", headers={"Authorization": "Bearer " + secret()})
    created_raw = await client.call_tool("estate_comms8_create_reasoning_request", args)
    created = json.loads(result_text(created_raw))
    request_id = created.get("request_id")
    if not request_id or created.get("state") != "queued":
        raise RuntimeError("authoritative create did not return one queued request")

    tool_message = {"role": "tool", "tool_call_id": tool_calls[0].get("id"), "name": CREATE, "content": result_text(created_raw)}
    returned = gateway({"model": "estate/grace", "messages": [{"role": "user", "content": prompt}, {"role": "assistant", "tool_calls": tool_calls}, tool_message], "tools": specs, "stream": False})
    returned_content = (((returned.get("choices") or [{}])[0].get("message") or {}).get("content") or "")
    returned_json = json.loads(returned_content)
    if returned_json.get("request_id") != request_id:
        raise RuntimeError("Resident Gateway did not return the authoritative request identity")
    read_raw = await client.call_tool("estate_comms8_read_request", {"request_id": request_id})
    read = json.loads(result_text(read_raw))
    if read.get("request_id") != request_id or read.get("state") != "queued":
        raise RuntimeError("read-back did not prove the same queued request")
    await client.disconnect()
    evidence = {"classification": "GRACE_NATIVE_CREATE_AND_RESULT_RETURN_PASSED", "persona": "Grace Standard", "gateway_model": "estate/grace", "native_tool_name": CREATE, "request_id": request_id, "workflow_id": WORKFLOW, "idempotency_key": IDEMPOTENCY, "state": read.get("state"), "claim_present": bool(read.get("claim")), "acknowledgement_present": bool(read.get("acknowledgement")), "response_present": bool(read.get("response")), "resolution_present": bool(read.get("resolution")), "returned_request_id_matches": True, "chatgpt_roundtrip_processed": False}
    ROOT.mkdir(parents=True, exist_ok=True)
    (ROOT / "grace-standard-live-creation.json").write_text(json.dumps(evidence, indent=2) + "\n")
    print(json.dumps(evidence, indent=2))

asyncio.run(main())
