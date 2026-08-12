import asyncio
import json
import sys
from pathlib import Path
sys.path.insert(0, r"A:\AI\OpenWebUI\.venv\Lib\site-packages")
from open_webui.utils.mcp.client import MCPClient
S=Path(r"A:\theestate-data\live\comms8\secrets.env")
REQUEST_ID="ec8-195d5eef6e0b46e2"
def sec(): return next(x.split('=',1)[1] for x in S.read_text().splitlines() if x.startswith('ESTATE_COMMS8_LIVE_CLIENT_SECRET='))
def unwrap(v):
    if isinstance(v,list) and v and isinstance(v[0],dict) and 'text' in v[0]:
        try:return json.loads(v[0]['text'])
        except Exception:return v
    return v
async def read(url):
    c=MCPClient(); await c.connect(url,headers={'Authorization':'Bearer '+sec()}); x=unwrap(await c.call_tool('estate_comms8_read_request',{'request_id':REQUEST_ID})); await c.disconnect(); return x
async def main():
    c=MCPClient(); await c.connect('https://estate-comms8-live.ionoge.com/mcp',headers={'Authorization':'Bearer '+sec()}); specs=await c.list_tool_specs(); await c.disconnect()
    names=[x['name'] for x in specs]; create=next(x for x in specs if x['name']=='estate_comms8_create_reasoning_request'); listing=next(x for x in specs if x['name']=='estate_comms8_list_requests')
    local=await read('http://127.0.0.1:11811/mcp'); public=await read('https://estate-comms8-live.ionoge.com/mcp')
    shape=lambda x:{'request_id':x.get('request_id'),'workflow_id':x.get('workflow_id'),'objective':x.get('objective'),'state':x.get('state'),'events':[e.get('event') for e in x.get('events',[])]}
    result={'tool_count':len(names),'tool_names':names,'create_required':create['parameters'].get('required'),'list_required':listing['parameters'].get('required'),'local':shape(local),'public':shape(public),'local_public_match':shape(local)==shape(public),'lifecycle_complete':shape(public)['state']=='resolved'}
    print(json.dumps(result,indent=2))
asyncio.run(main())
