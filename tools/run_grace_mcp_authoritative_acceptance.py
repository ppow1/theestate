import asyncio
import json
import sys
from pathlib import Path
sys.path.insert(0, r"A:\AI\OpenWebUI\.venv\Lib\site-packages")
from open_webui.utils.mcp.client import MCPClient

SECRETS=Path(r"A:\theestate-data\live\comms8\secrets.env")
OUT=Path(r"A:\theestate-data\grace-comms8-mutation-investigation\authoritative-lifecycle.json")
WORKFLOW="grace-mcp-stream-acceptance"
OBJECTIVE="Return exactly three concise observations about authoritative MCP execution."
IDEMP="grace-mcp-stream-acceptance-1"
def secret(): return next(x.split('=',1)[1] for x in SECRETS.read_text().splitlines() if x.startswith('ESTATE_COMMS8_LIVE_CLIENT_SECRET='))
def unwrap(v):
    if isinstance(v,list) and v and isinstance(v[0],dict) and 'text' in v[0]:
        try:return json.loads(v[0]['text'])
        except Exception:return v
    return v
async def main():
    c=MCPClient(); await c.connect('https://estate-comms8-live.ionoge.com/mcp',headers={'Authorization':'Bearer '+secret()})
    queued=unwrap(await c.call_tool('estate_comms8_list_requests',{'state':'queued'}))
    if queued: raise RuntimeError('eligible queue not empty; refusing duplicate')
    created=unwrap(await c.call_tool('estate_comms8_create_reasoning_request',{'workflow_id':WORKFLOW,'objective':OBJECTIVE,'input_data':{'source':'grace-openwebui-tool-call'},'idempotency_key':IDEMP}))
    request_id=created.get('request_id'); assert request_id and created.get('state')=='queued'
    read=unwrap(await c.call_tool('estate_comms8_read_request',{'request_id':request_id})); assert read.get('request_id')==request_id and read.get('objective')==OBJECTIVE
    claimed=unwrap(await c.call_tool('estate_comms8_list_requests',{'claim_next':True,'worker_id':'grace','lease_seconds':900})); item=claimed[0] if isinstance(claimed,list) else claimed; assert item.get('request_id')==request_id
    lease=item['claim']['lease_id']
    ack=unwrap(await c.call_tool('estate_comms8_acknowledge_request',{'request_id':request_id,'worker_id':'grace','lease_id':lease}))
    response={'request_id':request_id,'workflow_id':WORKFLOW,'status':'completed','content':'1. Confirm the model emits a native tool call.\n2. Confirm Open WebUI executes it through the MCP client.\n3. Verify the returned request record before claiming success.'}
    responded=unwrap(await c.call_tool('estate_comms8_respond_request',{'request_id':request_id,'worker_id':'grace','lease_id':lease,'response':response,'response_idempotency_key':'grace-mcp-stream-response-1'}))
    resolved=unwrap(await c.call_tool('estate_comms8_resolve_request',{'request_id':request_id,'worker_id':'grace','lease_id':lease,'resolution':'completed'}))
    terminal=unwrap(await c.call_tool('estate_comms8_read_request',{'request_id':request_id}))
    result={'request_id':request_id,'workflow_id':WORKFLOW,'created':created.get('state')=='queued','read_same_request':read.get('request_id')==request_id and read.get('objective')==OBJECTIVE,'claimed':item.get('state')=='claimed','acknowledged':ack.get('state')=='acknowledged','responded':responded.get('state')=='responded','resolved':resolved.get('state')=='resolved','terminal_state':terminal.get('state'),'worker_id':'grace','tool_client':'open_webui.utils.mcp.client.MCPClient'}
    OUT.write_text(json.dumps(result,indent=2)+'\n'); print(json.dumps(result)); await c.disconnect()
asyncio.run(main())
