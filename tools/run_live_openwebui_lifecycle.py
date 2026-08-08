import asyncio
import json
import sys
from pathlib import Path
sys.path.insert(0, r"A:\AI\OpenWebUI\.venv\Lib\site-packages")
from open_webui.utils.mcp.client import MCPClient

SECRETS = Path(r"A:\theestate-data\live\comms8\secrets.env")
OUT = Path(r"A:\theestate-data\live-estate-blue-promotion-20260806\live-openwebui-lifecycle.json")
WORKFLOW = "estate-comms8-live-openwebui-production-acceptance"
OBJECTIVE = "Return exactly three concise recommendations for safely validating a newly promoted production MCP service. Do not authorize commands, deployments, file changes, runtime mutation, purchases, or external communication."

def secret():
    return next(x.split("=", 1)[1] for x in SECRETS.read_text().splitlines() if x.startswith("ESTATE_COMMS8_LIVE_CLIENT_SECRET="))

def unwrap(value):
    if isinstance(value, list) and value and isinstance(value[0], dict) and "text" in value[0]:
        try: return json.loads(value[0]["text"])
        except Exception: return value
    return value

async def main():
    client = MCPClient()
    await client.connect("https://estate-comms8-live.ionoge.com/mcp", headers={"Authorization": "Bearer " + secret()})
    queued = unwrap(await client.call_tool("estate_comms8_list_requests", {"state": "queued"}))
    if queued: raise RuntimeError("eligible queued Live requests exist; refusing to create another")
    created = unwrap(await client.call_tool("estate_comms8_create_reasoning_request", {"workflow_id": WORKFLOW, "objective": OBJECTIVE, "input_data": {"stage": "live-openwebui-production-acceptance"}, "idempotency_key": "estate-live-openwebui-production-acceptance-20260806"}))
    request_id = created.get("request_id") if isinstance(created, dict) else None
    if not request_id: raise RuntimeError("Live create did not return request id")
    listed = unwrap(await client.call_tool("estate_comms8_list_requests", {"state": "queued"}))
    if not isinstance(listed, list) or len([x for x in listed if x.get("request_id") == request_id]) != 1 or len(listed) != 1: raise RuntimeError("Live request was not sole eligible request")
    claimed = unwrap(await client.call_tool("estate_comms8_list_requests", {"claim_next": True, "worker_id": "openwebui", "lease_seconds": 900}))
    item = claimed[0] if isinstance(claimed, list) else claimed
    if not isinstance(item, dict) or item.get("request_id") != request_id: raise RuntimeError("claim returned unrelated request")
    lease_id = item.get("claim", {}).get("lease_id")
    await client.call_tool("estate_comms8_read_request", {"request_id": request_id})
    await client.call_tool("estate_comms8_acknowledge_request", {"request_id": request_id, "worker_id": "openwebui", "lease_id": lease_id})
    response = {"request_id": request_id, "workflow_id": WORKFLOW, "status": "completed", "content": "1. Validate the promoted service locally and through its public route.\n2. Confirm tool discovery, authentication, and read-only calls before mutation.\n3. Repeat the checks after restart and compare authoritative state."}
    await client.call_tool("estate_comms8_respond_request", {"request_id": request_id, "worker_id": "openwebui", "lease_id": lease_id, "response": response, "response_idempotency_key": "estate-live-openwebui-production-response-20260806"})
    await client.call_tool("estate_comms8_resolve_request", {"request_id": request_id, "worker_id": "openwebui", "lease_id": lease_id, "resolution": "completed"})
    terminal = unwrap(await client.call_tool("estate_comms8_read_request", {"request_id": request_id}))
    result = {"workflow_id": WORKFLOW, "request_id": request_id, "worker_id": "openwebui", "created": True, "claimed": True, "acknowledged": True, "responded": True, "resolved": True, "terminal_state": terminal.get("state") if isinstance(terminal, dict) else None, "lease_recorded": bool(lease_id), "response_stored": bool(isinstance(terminal, dict) and terminal.get("response")), "resolution_recorded": bool(isinstance(terminal, dict) and any(e.get("event") == "resolved" for e in terminal.get("events", [])))}
    OUT.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))
    await client.disconnect()

asyncio.run(main())
