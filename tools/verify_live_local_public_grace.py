import asyncio
import json
import sys
from pathlib import Path
sys.path.insert(0, r"A:\AI\OpenWebUI\.venv\Lib\site-packages")
from open_webui.utils.mcp.client import MCPClient

SECRETS=Path(r"A:\theestate-data\live\comms8\secrets.env")
OUT=Path(r"A:\theestate-data\live-estate-blue-promotion-20260806\live-local-public-grace.json")
REQUEST_ID="ec8-6a850f4ab32743d2"
def secret(): return next(x.split('=',1)[1] for x in SECRETS.read_text().splitlines() if x.startswith('ESTATE_COMMS8_LIVE_CLIENT_SECRET='))
def unwrap(v):
    if isinstance(v,list) and v and isinstance(v[0],dict) and 'text' in v[0]:
        try:return json.loads(v[0]['text'])
        except Exception:return v
    return v
async def read(url):
    c=MCPClient(); await c.connect(url,headers={'Authorization':'Bearer '+secret()}); x=unwrap(await c.call_tool('estate_comms8_read_request',{'request_id':REQUEST_ID})); await c.disconnect(); return x
async def main():
    local=await read('http://127.0.0.1:11811/mcp'); public=await read('https://estate-comms8-live.ionoge.com/mcp')
    def shape(x): return {'request_id':x.get('request_id'),'workflow_id':x.get('workflow_id'),'state':x.get('state'),'response_status':(x.get('response') or {}).get('status'),'event_names':[e.get('event') for e in x.get('events',[])]}
    ls,ps=shape(local),shape(public); match=ls==ps and ls['state']=='resolved' and 'resolved' in ls['event_names']
    result={'local':ls,'public':ps,'local_public_match':match,'grace_retrieval':'passed' if match else 'failed'}
    OUT.write_text(json.dumps(result,indent=2)+'\n'); print(json.dumps(result))
asyncio.run(main())
