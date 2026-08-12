import asyncio, json, urllib.request
from pathlib import Path
import sys
sys.path.insert(0, r"A:\AI\OpenWebUI\.venv\Lib\site-packages")
from open_webui.utils.mcp.client import MCPClient

ROOT = Path(r"A:\theestate-data\grace-comms8-live-dispatch-repair-20260807")
REQUEST_ID = "ec8-3f24f4aadcd947c9"
NAME = "estate-comms8-live_estate_comms8_read_request"

def gateway(payload):
    req=urllib.request.Request("http://127.0.0.1:11435/v1/chat/completions",json.dumps(payload).encode(),{"Content-Type":"application/json"},method="POST")
    with urllib.request.urlopen(req,timeout=30) as r: return json.loads(r.read())
def secret():
    for line in Path(r"A:\theestate-data\live\comms8\secrets.env").read_text().splitlines():
        if line.startswith("ESTATE_COMMS8_LIVE_CLIENT_SECRET="): return line.split("=",1)[1]
    raise RuntimeError("Live credential missing")
def text(v): return v[0]["text"] if isinstance(v,list) and v and isinstance(v[0],dict) and "text" in v[0] else json.dumps(v)

async def read(c): return json.loads(text(await c.call_tool("estate_comms8_read_request", {"request_id": REQUEST_ID})))
async def main():
    tools=[{"type":"function","function":{"name":NAME,"description":"Estate Comms8 read request","parameters":{"type":"object","required":["request_id"]}}}]
    prompt=f'Call {NAME} with request_id="{REQUEST_ID}" and return only the authoritative result.'
    call=gateway({"model":"estate/grace","messages":[{"role":"user","content":prompt}],"tools":tools,"stream":False})
    tcs=(((call.get("choices") or [{}])[0].get("message") or {}).get("tool_calls") or [])
    if len(tcs)!=1 or tcs[0].get("function",{}).get("name")!=NAME: raise RuntimeError("Resident Gateway did not emit exact read delegation")
    args=json.loads(tcs[0]["function"]["arguments"])
    if args!={"request_id":REQUEST_ID}: raise RuntimeError("Resident Gateway changed read arguments")
    local=MCPClient(); public=MCPClient()
    await local.connect("http://127.0.0.1:11811/mcp",headers={"Authorization":"Bearer "+secret()})
    await public.connect("https://estate-comms8-live.ionoge.com/mcp",headers={"Authorization":"Bearer "+secret()})
    local_row=await read(local); public_row=await read(public)
    tool_content=json.dumps(public_row,sort_keys=True)
    returned=gateway({"model":"estate/grace","messages":[{"role":"user","content":prompt},{"role":"assistant","tool_calls":tcs},{"role":"tool","tool_call_id":tcs[0].get("id"),"name":NAME,"content":tool_content}],"tools":tools,"stream":False})
    content=(((returned.get("choices") or [{}])[0].get("message") or {}).get("content") or "")
    returned_row=json.loads(content)
    ok=(local_row==public_row and returned_row.get("request_id")==REQUEST_ID and returned_row.get("state")=="queued")
    evidence={"classification":"RESIDENT_GATEWAY_READ_RESULT_RETURNED","persona":"Grace (Estate Resident Gateway)","native_tool_name":NAME,"request_id":REQUEST_ID,"local_public_equal":local_row==public_row,"returned_request_id_matches":returned_row.get("request_id")==REQUEST_ID,"state":returned_row.get("state"),"claim_present":bool(returned_row.get("claim")),"response_present":bool(returned_row.get("response")),"resolution_present":bool(returned_row.get("resolution")),"passed":ok}
    ROOT.mkdir(parents=True,exist_ok=True); (ROOT/"resident-gateway-live-read.json").write_text(json.dumps(evidence,indent=2)+"\n"); print(json.dumps(evidence,indent=2))
    for client in (local, public):
        try:
            await client.disconnect()
        except BaseException:
            pass
    if not ok: raise RuntimeError("Resident Gateway read acceptance failed")
asyncio.run(main())
